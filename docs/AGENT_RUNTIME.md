# Agent runtime slice

## What is included

- `Backend/AgentRuntime.py`: a bounded planner/executor loop. The model emits a strict JSON object; the runtime validates its shape and dispatches only through `Backend/ToolRegistry.py`.
- `Backend/ModelProviders.py`: Ollama-first inference using the standard library, with an optional OpenAI-compatible cloud endpoint fallback.
- `Backend/AgentCLI.py`: an experimental command-line harness to exercise the runtime independently of the legacy PyQt GUI.
- `tests/test_agent_runtime.py` and `tests/test_model_providers.py`: dependency-free unit tests.

## Run locally

1. Use Python 3.10.10 and open a terminal at the repository root.
2. Create/activate a virtual environment.
3. Start Ollama and pull a model compatible with your hardware. The default configured model is `qwen2.5:7b`; override it with `JARVIS_LOCAL_MODEL` if needed.
4. Run `python -m Backend.AgentCLI`.
5. Type `/exit` to quit.

Cloud fallback is optional. Configure all three variables to enable it:

- `JARVIS_CLOUD_BASE_URL`: base URL for an OpenAI-compatible API (for example, a provider's versioned API root; do not include `/chat/completions`).
- `JARVIS_CLOUD_MODEL`: provider-supported model identifier.
- `JARVIS_CLOUD_API_KEY`: API key, stored only in the local environment.

Do not commit a populated `.env`. Local inference may fail if Ollama is not running, the model is not downloaded, or the hardware cannot run it. In that case, the runtime fails with an actionable message unless cloud fallback is configured.

## Current limitations

This slice is not yet integrated into the legacy PyQt GUI, voice capture/TTS, or visual desktop control. The currently registered tools are allowlisted application launch, HTTP(S) browser opening, and bounded user-workspace file listing/search/read/create/write/delete/move. Existing writes, deletes, and moves require explicit approval. Arbitrary shell execution, app closing, system settings, purchases, and messaging remain disabled. Do not describe this slice as a fully functional desktop assistant yet.

## Validation

Run `python -m unittest discover -s tests -v`. GitHub Actions also runs the dependency-free suite on feature branch pushes. Passing unit tests do not replace Windows testing with the actual microphone, PyQt GUI, applications, and filesystem permissions.
