import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from runtime.agent import AgentError, build_system_prompt, dispatch_tool, git_readonly, load_memingo_core, run_agent, run_review_cycle, save_task_history, read_task_history, github_public_api, git_mutation

class AgentToolTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name).resolve()
    def tearDown(self):
        self.temp.cleanup()
    def test_read_file(self):
        (self.root/"hello.txt").write_text("hola",encoding="utf-8")
        self.assertEqual(dispatch_tool(self.root,"read_file",{"path":"hello.txt"}),"hola")
    def test_secret_read_is_blocked(self):
        (self.root/".env").write_text("TOKEN=secret",encoding="utf-8")
        self.assertIn("blocked",dispatch_tool(self.root,"read_file",{"path":".env"}))
    def test_write_requires_approval(self):
        with patch("builtins.input",return_value="n"):
            result=dispatch_tool(self.root,"write_file",{"path":"new.txt","content":"hello"})
        self.assertIn("declined",result)
        self.assertFalse((self.root/"new.txt").exists())
    def test_write_after_approval(self):
        with patch("builtins.input",return_value="y"):
            result=dispatch_tool(self.root,"write_file",{"path":"new.txt","content":"hello"})
        self.assertIn("Saved",result)
        self.assertEqual((self.root/"new.txt").read_text(encoding="utf-8"),"hello")
    def test_git_inspection_requires_repository(self):
        with self.assertRaises(Exception):
            git_readonly(self.root, "status")

    def test_git_status_uses_fixed_read_only_command(self):
        (self.root / ".git").mkdir()
        from unittest.mock import Mock
        with patch("runtime.agent.subprocess.run", return_value=Mock(returncode=0, stdout="## main\\n")) as run:
            self.assertEqual(git_readonly(self.root, "status"), "## main\\n")
        self.assertEqual(run.call_args.args[0], ["git", "status", "--short", "--branch"])
        self.assertFalse(run.call_args.kwargs["shell"])

    def test_final_response(self):
        def fake(messages,**kwargs):
            return {"role":"assistant","content":"Project inspected."}
        self.assertEqual(run_agent("inspect",self.root,api_key="test",model="test",request_fn=fake),"Project inspected.")
    def test_tool_call_round_trip(self):
        count={"n":0}
        def fake(messages,**kwargs):
            count["n"]+=1
            if count["n"]==1:
                return {"role":"assistant","content":None,"tool_calls":[{"id":"c1","type":"function","function":{"name":"list_files","arguments":"{}"}}]}
            self.assertEqual(messages[-1]["role"],"tool")
            return {"role":"assistant","content":"Done."}
        self.assertEqual(run_agent("list files",self.root,api_key="test",model="test",request_fn=fake),"Done.")
    def test_review_cycle_stops_when_clean(self):
        reports = ["Tests passed.\\nMEMECODE_REVIEW: CLEAN"]
        with patch("runtime.agent.run_agent", side_effect=reports) as run:
            result = run_review_cycle("review project", self.root, api_key="x",
                                      model="test", max_repair_rounds=3)
        self.assertEqual(result, reports)
        self.assertEqual(run.call_count, 1)

    def test_review_cycle_has_a_hard_round_limit(self):
        reports = ["MEMECODE_REVIEW: NEEDS_WORK"] * 3
        with patch("runtime.agent.run_agent", side_effect=reports) as run:
            result = run_review_cycle("review project", self.root, api_key="x",
                                      model="test", max_repair_rounds=99)
        self.assertEqual(len(result), 3)
        self.assertEqual(run.call_count, 3)

    def test_task_history_round_trip(self):
        save_task_history(self.root, "make a demo", "Created demo.")
        records = read_task_history(self.root)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["task"], "make a demo")
        self.assertEqual(records[0]["result"], "Created demo.")

    def test_task_text_cannot_change_history_destination(self):
        save_task_history(self.root, "../outside", "recorded as plain text")
        self.assertTrue((self.root / ".memecode" / "history.jsonl").is_file())
        self.assertFalse((self.root.parent / ".memecode" / "history.jsonl").exists())

    def test_github_api_rejects_invalid_owner(self):
        with self.assertRaises(AgentError):
            github_public_api("../bad", "repo", "")

    def test_github_api_uses_read_only_get(self):
        from unittest.mock import Mock, patch
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.read.return_value = b'{"full_name":"owner/repo","default_branch":"main"}'
        with patch("runtime.agent.urllib.request.urlopen", return_value=response) as open_url:
            payload = github_public_api("owner", "repo", "")
        self.assertIn("owner/repo", payload)
        self.assertEqual(open_url.call_args.args[0].method, "GET")

    def test_branch_creation_requires_approval(self):
        import subprocess
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        with patch("runtime.agent._approve", return_value=False):
            result = git_mutation(self.root, "branch", {"name": "feature/demo"})
        self.assertIn("declined", result)
        current = subprocess.run(["git", "branch", "--show-current"], cwd=self.root,
                                 capture_output=True, text=True, check=True)
        self.assertNotEqual(current.stdout.strip(), "feature/demo")

    def test_commit_requires_approval(self):
        import subprocess
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.name", "MemeCode Test"], cwd=self.root, check=True)
        (self.root / "demo.txt").write_text("demo", encoding="utf-8")
        subprocess.run(["git", "add", "demo.txt"], cwd=self.root, check=True)
        with patch("runtime.agent._approve", return_value=False):
            result = git_mutation(self.root, "commit", {"message": "Add demo"})
        self.assertIn("declined", result)
        log = subprocess.run(["git", "log", "-1", "--oneline"], cwd=self.root,
                             capture_output=True, text=True)
        self.assertNotEqual(log.returncode, 0)

    def test_approved_branch_creation_switches_branch(self):
        import subprocess
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        with patch("runtime.agent._approve", return_value=True):
            result = git_mutation(self.root, "branch", {"name": "feature/demo"})
        self.assertTrue(result)
        current = subprocess.run(["git", "branch", "--show-current"], cwd=self.root,
                                  capture_output=True, text=True, check=True)
        self.assertEqual(current.stdout.strip(), "feature/demo")

    def test_approved_commit_creates_local_commit(self):
        import subprocess
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.name", "MemeCode Test"], cwd=self.root, check=True)
        (self.root / "demo.txt").write_text("demo", encoding="utf-8")
        subprocess.run(["git", "add", "demo.txt"], cwd=self.root, check=True)
        with patch("runtime.agent._approve", return_value=True):
            result = git_mutation(self.root, "commit", {"message": "Add demo"})
        self.assertIn("Add demo", result)
        log = subprocess.run(["git", "log", "-1", "--format=%s"], cwd=self.root,
                             capture_output=True, text=True, check=True)
        self.assertEqual(log.stdout.strip(), "Add demo")

    def test_rejects_invalid_branch_name(self):
        (self.root / ".git").mkdir()
        with self.assertRaises(Exception):
            git_mutation(self.root, "branch", {"name": "../bad"})

    def test_step_limit(self):
        def fake(messages,**kwargs):
            return {"role":"assistant","content":None,"tool_calls":[{"id":"loop","type":"function","function":{"name":"list_files","arguments":"{}"}}]}
        with self.assertRaises(AgentError):
            run_agent("loop",self.root,api_key="test",model="test",max_steps=1,request_fn=fake)


    def test_builds_system_prompt_from_memingo_policy(self):
        config = {"name": "MemeCode", "role": "coding agent",
                  "policy": ["Inspect first.", "Ask before writes."],
                  "workflow": ["inspect", "plan", "test"]}
        prompt = build_system_prompt(config)
        self.assertIn("Inspect first.", prompt)
        self.assertIn("inspect -> plan -> test", prompt)

    def test_loads_policy_from_memingo_runtime(self):
        import json
        from unittest.mock import Mock, patch
        (self.root / "src").mkdir()
        (self.root / "src" / "agent_core.mgo").write_text('spill "{}"', encoding="utf-8")
        config = {"name": "MemeCode", "policy": ["Inspect first."]}
        completed = Mock(returncode=0, stdout=json.dumps(config), stderr="")
        with patch("runtime.agent.shutil.which", return_value="/usr/bin/memingo"), \
             patch("runtime.agent.subprocess.run", return_value=completed) as run:
            loaded = load_memingo_core(self.root)
        self.assertEqual(loaded["name"], "MemeCode")
        self.assertEqual(run.call_args.args[0][1:3], ["run", str(self.root / "src" / "agent_core.mgo")])

    def test_rejects_missing_memingo_core(self):
        with self.assertRaises(AgentError):
            load_memingo_core(self.root)


    @unittest.skipUnless(shutil.which("memingo"), "Memingo runtime is not installed")
    def test_real_memingo_core_outputs_agent_config(self):
        config = load_memingo_core(Path(__file__).parents[1])
        self.assertEqual(config["name"], "MemeCode")
        self.assertIn("inspect", config["workflow"])
        self.assertGreater(len(config["policy"]), 0)


    def test_auto_creates_private_config_and_example(self):
        from runtime.agent import setup_provider_config, config_file
        with patch.dict("os.environ", {"XDG_CONFIG_HOME": str(self.root / "config")}, clear=False):
            values = setup_provider_config(interactive=False)
            path = config_file()
            self.assertTrue(path.is_file())
            self.assertTrue((path.parent / ".env.example").is_file())
            self.assertEqual(values["MEMECODE_API_KEY"], "")
            self.assertEqual(values["MEMECODE_MODEL"], "gpt-4o-mini")
            if __import__("os").name != "nt":
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_config_round_trip_and_environment_override(self):
        import os
        from runtime.agent import _write_config, provider_settings, config_file
        config_home = self.root / "config"
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": str(config_home), "MEMECODE_API_KEY": "env-key"}, clear=False):
            path = config_file()
            _write_config(path, {"MEMECODE_API_KEY": "file-key", "MEMECODE_MODEL": "sample-model", "MEMECODE_BASE_URL": "https://example.test/v1"})
            settings = provider_settings()
            self.assertEqual(settings["MEMECODE_API_KEY"], "env-key")
            self.assertEqual(settings["MEMECODE_MODEL"], "sample-model")
            self.assertEqual(settings["MEMECODE_BASE_URL"], "https://example.test/v1")

    def test_setup_rejects_invalid_model_and_url(self):
        from runtime.agent import setup_provider_config, AgentError
        with patch.dict("os.environ", {"XDG_CONFIG_HOME": str(self.root / "config")}, clear=False), \
             patch("runtime.agent.getpass.getpass", return_value="sample-key"), \
             patch("builtins.input", side_effect=["bad model", "https://example.test/v1"]):
            with self.assertRaises(AgentError):
                setup_provider_config(interactive=True, force=True)

if __name__=="__main__":
    unittest.main()
