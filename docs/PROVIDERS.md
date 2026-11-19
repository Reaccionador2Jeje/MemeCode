# Model providers and troubleshooting

MemeCode selects its API protocol from the configured **API base URL**. Use the exact model identifier from the provider dashboard; a model's marketing name is not always its API ID.

## Supported protocols

### OpenAI-compatible Chat Completions

For OpenAI and compatible gateways such as OpenRouter, Groq, Together, and DeepSeek, use the API root supplied by that provider. Typical shape:

- Base URL: \`https://api.example.com/v1\`
- Model: the exact model slug from the provider
- API key: a key created with that provider

Do not append \`/chat/completions\` unless the provider explicitly tells you to use the full endpoint; MemeCode accepts either the API root or the complete endpoint.

### Anthropic Messages API

- Base URL: \`https://api.anthropic.com/v1\`
- Model: the exact Claude model ID enabled for the key
- API key: Anthropic API key

MemeCode uses the native Messages API and converts tool schemas and tool results to Anthropic's format.

### Google Gemini API

- Base URL: \`https://generativelanguage.googleapis.com/v1beta\`
- Model: the exact Gemini model ID enabled for the key, for example the current Flash or Pro model slug shown in Google AI Studio
- API key: Google AI Studio API key

MemeCode uses the native \`generateContent\` API and converts function declarations, calls, and results.

## Test before coding

1. Open MemeCode.
2. Type \`/setup\` and enter the provider's base URL, exact model ID, and API key.
3. Save the configuration.
4. Type \`/test\`.

The connection test sends a small text-only request. It checks the endpoint, authentication, model access, and response format without running project tools.

## Common errors

| Error | What it usually means | What to check |
|---|---|---|
| HTTP 401 / 403 | Key missing, invalid, revoked, or lacking access | Create a key at the selected provider and ensure it belongs to that provider |
| HTTP 404 | Wrong endpoint or model ID | Check the API base URL and exact model slug |
| HTTP 400 / 422 | Unsupported request parameter or API format | MemeCode retries without optional temperature and, if needed, without tools |
| HTTP 429 | Rate limit, exhausted quota, or billing restriction | Check provider quota, billing, and rate limits |
| Empty response | Model returned no text or tool calls | Check model access, output limits, and provider status |
| Connection / timeout | Network, DNS, TLS, or provider outage | Check internet access and provider status |

## Tool-calling compatibility

MemeCode uses model tool/function calling to inspect and edit project files. Some models or low-cost inference routes only support plain text. MemeCode tries a compatible request without optional temperature, then retries without tools if the provider rejects tool calling.

In text-only fallback mode, MemeCode displays a warning and does **not** claim that it edited files or ran commands. Choose a tool-capable model/route to use the full coding-agent workflow.

## Security

Keep API keys in MemeCode's private configuration file. Do not paste keys into source files, issue reports, screenshots, or public repositories. A connection test never prints the key.
