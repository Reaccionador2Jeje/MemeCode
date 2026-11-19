import io
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from runtime.agent import AgentError, provider_request, run_agent


def ok_response(payload):
    class Response:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read(self, limit=-1):
            return json.dumps(payload).encode("utf-8")
    return Response()


def http_error(code, message):
    body = json.dumps({"error": {"message": message}}).encode("utf-8")
    return urllib.error.HTTPError(
        "https://provider.example/v1/chat/completions",
        code, "Provider error", {}, io.BytesIO(body)
    )


class ProviderCompatibilityTests(unittest.TestCase):
    def test_openai_compatible_success(self):
        payload = {"choices": [{"message": {"role": "assistant", "content": "Hello!"}}]}
        with patch("runtime.agent.urllib.request.urlopen", return_value=ok_response(payload)) as open_url:
            result = provider_request(
                [{"role": "user", "content": "Hi"}],
                api_key="test-key", model="sample-model",
                base_url="https://provider.example/v1",
            )
        self.assertEqual(result["content"], "Hello!")
        request = open_url.call_args.args[0]
        self.assertEqual(request.full_url, "https://provider.example/v1/chat/completions")
        self.assertIn(b'"tools"', request.data)
        self.assertIn(b'"temperature"', request.data)

    def test_full_chat_completions_url_is_not_duplicated(self):
        payload = {"choices": [{"message": {"role": "assistant", "content": "ok"}}]}
        with patch("runtime.agent.urllib.request.urlopen", return_value=ok_response(payload)) as open_url:
            provider_request(
                [{"role": "user", "content": "Hi"}],
                api_key="test-key", model="sample-model",
                base_url="https://provider.example/v1/chat/completions",
            )
        self.assertEqual(
            open_url.call_args.args[0].full_url,
            "https://provider.example/v1/chat/completions",
        )

    def test_retries_without_temperature_when_model_rejects_it(self):
        payload = {"choices": [{"message": {"role": "assistant", "content": "works"}}]}
        with patch(
            "runtime.agent.urllib.request.urlopen",
            side_effect=[http_error(400, "temperature is not supported"), ok_response(payload)],
        ) as open_url:
            result = provider_request(
                [{"role": "user", "content": "Hi"}],
                api_key="test-key", model="reasoning-model",
                base_url="https://provider.example/v1",
            )
        self.assertEqual(result["content"], "works")
        self.assertEqual(open_url.call_count, 2)
        second_body = json.loads(open_url.call_args_list[1].args[0].data)
        self.assertNotIn("temperature", second_body)
        self.assertIn("tools", second_body)

    def test_falls_back_to_text_only_when_tools_are_unsupported(self):
        payload = {"choices": [{"message": {"role": "assistant", "content": "Text answer"}}]}
        with patch(
            "runtime.agent.urllib.request.urlopen",
            side_effect=[
                http_error(400, "tools are not supported by this model"),
                http_error(400, "tools are not supported by this model"),
                ok_response(payload),
            ],
        ) as open_url:
            result = provider_request(
                [{"role": "user", "content": "Explain this"}],
                api_key="test-key", model="text-only-model",
                base_url="https://provider.example/v1",
            )
        self.assertEqual(open_url.call_count, 3)
        self.assertFalse(result["_memecode_tool_support"])
        third_body = json.loads(open_url.call_args_list[2].args[0].data)
        self.assertNotIn("tools", third_body)
        self.assertNotIn("temperature", third_body)

    def test_native_anthropic_messages_api(self):
        payload = {"content": [{"type": "text", "text": "Anthropic works"}]}
        with patch("runtime.agent.urllib.request.urlopen", return_value=ok_response(payload)) as open_url:
            result = provider_request(
                [{"role": "system", "content": "Be concise."},
                 {"role": "user", "content": "Hi"}],
                api_key="anthropic-key", model="claude-test",
                base_url="https://api.anthropic.com/v1",
            )
        request = open_url.call_args.args[0]
        body = json.loads(request.data)
        self.assertEqual(request.full_url, "https://api.anthropic.com/v1/messages")
        self.assertEqual(request.get_header("X-api-key"), "anthropic-key")
        self.assertEqual(body["system"], "Be concise.")
        self.assertIn("tools", body)
        self.assertEqual(result["content"], "Anthropic works")

    def test_native_gemini_generate_content_api(self):
        payload = {"candidates": [{"content": {"parts": [{"text": "Gemini works"}]}}]}
        with patch("runtime.agent.urllib.request.urlopen", return_value=ok_response(payload)) as open_url:
            result = provider_request(
                [{"role": "system", "content": "Be concise."},
                 {"role": "user", "content": "Hi"}],
                api_key="gemini-key", model="gemini-test",
                base_url="https://generativelanguage.googleapis.com/v1beta",
            )
        request = open_url.call_args.args[0]
        body = json.loads(request.data)
        self.assertIn("/models/gemini-test:generateContent", request.full_url)
        self.assertEqual(request.get_header("X-goog-api-key"), "gemini-key")
        self.assertEqual(body["systemInstruction"]["parts"][0]["text"], "Be concise.")
        self.assertIn("tools", body)
        self.assertEqual(result["content"], "Gemini works")

    def test_gemini_function_calls_are_normalized(self):
        payload = {"candidates": [{"content": {"parts": [{
            "functionCall": {"name": "list_files", "args": {"path": "."}}
        }]}}]}
        with patch("runtime.agent.urllib.request.urlopen", return_value=ok_response(payload)):
            result = provider_request(
                [{"role": "user", "content": "List files"}],
                api_key="gemini-key", model="gemini-test",
                base_url="https://generativelanguage.googleapis.com/v1beta",
            )
        self.assertEqual(result["tool_calls"][0]["function"]["name"], "list_files")
        self.assertEqual(json.loads(result["tool_calls"][0]["function"]["arguments"]), {"path": "."})

    def test_provider_error_is_readable_and_does_not_retry_auth(self):
        with patch(
            "runtime.agent.urllib.request.urlopen",
            side_effect=http_error(401, "invalid API key"),
        ) as open_url:
            with self.assertRaisesRegex(AgentError, "HTTP 401.*invalid API key"):
                provider_request(
                    [{"role": "user", "content": "Hi"}],
                    api_key="bad-key", model="sample-model",
                    base_url="https://provider.example/v1",
                )
        self.assertEqual(open_url.call_count, 1)

    def test_rejects_empty_model_response_instead_of_silent_blank(self):
        payload = {"choices": [{"message": {"role": "assistant", "content": None}}]}
        with patch("runtime.agent.urllib.request.urlopen", return_value=ok_response(payload)):
            with self.assertRaisesRegex(AgentError, "sin texto ni herramientas"):
                run_agent(
                    "Do something", Path(tempfile.gettempdir()),
                    api_key="test-key", model="sample-model",
                )

    def test_text_only_fallback_warns_that_no_project_actions_were_run(self):
        def fake(messages, **kwargs):
            return {
                "role": "assistant",
                "content": "Here is a suggestion.",
                "_memecode_tool_support": False,
            }
        result = run_agent(
            "Edit a file", Path(tempfile.gettempdir()),
            api_key="test-key", model="sample-model", request_fn=fake,
        )
        self.assertIn("no admite llamadas a herramientas", result)
        self.assertIn("no ejecutó ni modificó archivos", result)

    def test_missing_key_and_invalid_url_are_explained(self):
        with self.assertRaisesRegex(AgentError, "Falta la API key"):
            provider_request([], api_key="", model="m", base_url="https://provider.example/v1")
        with self.assertRaisesRegex(AgentError, "https://"):
            provider_request([], api_key="k", model="m", base_url="provider.example/v1")


if __name__ == "__main__":
    unittest.main()
