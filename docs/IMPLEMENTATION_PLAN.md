# J.A.R.V.I.S Desktop Agent — Implementation Plan

## Product target

A Windows desktop assistant with text and voice input, hybrid local/cloud AI, and practical automation across applications, user files, browser workflows, developer tools, and selected system settings. It must remain responsive, auditable, cancellable, and safe by default.

## Existing repository baseline

The current project already includes a PyQt5 UI (`Frontend/GUI.py`), orchestration (`Main.py`), intent classification (`Backend/Model.py`), desktop automation (`Backend/Automation.py`), chat, real-time search, speech-to-text, text-to-speech, and image generation. Preserve these entry points initially; migrate behavior behind tested interfaces rather than replacing the whole app at once.

Known issues from source review: brittle comma/prefix intent parsing; fragile async/thread and file-backed GUI state; voice recognition flags/configuration that may prevent real microphone capture; app-opening fallback that may open arbitrary search results; Chrome close reporting success without closing it; image-generation requests without robust timeouts/status checks; documentation/dependency drift; and generated virtual-environment/cache artifacts in the repository. The source has not yet been executed on the target Windows machine, so these are source-review findings, not runtime test results.

## Phases and acceptance criteria

### Phase 1 — Security and repeatable baseline
- Rotate any real credentials committed to Git history; remove secrets from tracked files and add a placeholder `.env.example`.
- Remove `venv/`, `__pycache__/`, and bytecode artifacts from source control; keep `.gitignore` rules.
- Add unit-test infrastructure and a dependency-free safety policy module.
- Document supported Python version, environment setup, entry point, and known limitations.
- Acceptance: clean clone installs from documented requirements; tests run without cloud keys; no secrets are committed.

### Phase 2 — Tool interfaces
- Introduce typed tool requests/results and one registry for apps, files, browser, terminal, and settings.
- Use argument validation and `subprocess.run([...], shell=False)` for process execution; never let an LLM emit an unchecked shell string that is executed directly.
- Limit file operations to approved user workspaces and resolve paths before every operation.
- Acceptance: each tool has unit tests, timeout behavior, structured errors, and a deterministic success/failure result.

### Phase 3 — Planner and executor
- Replace prompt-prefix routing with structured plans validated against the tool registry.
- Execute one step at a time; apply policy checks before dispatch, persist task state, support cancellation, and verify the postcondition.
- Retry only safe/idempotent steps; do not blindly repeat writes, deletes, messages, purchases, or settings changes.
- Acceptance: mocked integration tests prove invalid tools are rejected and high-impact actions cannot bypass confirmation.

### Phase 4 — Voice and text parity
- Send typed text and transcribed speech to the same orchestration path.
- Repair microphone capture/language selection; keep speech work off the UI thread and provide a text fallback.
- Acceptance: both input paths produce the same normalized plan for equivalent requests and the GUI remains responsive.

### Phase 5 — Hybrid model routing and memory
- Define a provider interface for local inference (for example, Ollama) and optional cloud inference.
- Keep provider credentials in environment variables; add timeout, retry, and offline fallback behavior.
- Store task history and settings in a small local database; avoid logging secrets or unnecessary personal data.
- Acceptance: app starts without cloud credentials; local mode works when a compatible local model is installed; cloud mode fails gracefully.

### Phase 6 — End-to-end desktop workflows
- Validate launch/close app, file search/read/create, browser navigation, safe developer commands, volume, and approved system settings.
- Test failure paths, permission denial, path traversal, malformed model output, timeouts, and shutdown.
- Acceptance: Windows smoke-test checklist passes and every action reports verified outcomes rather than optimistic success.

## Autonomy and safety policy

- Run low-risk, reversible actions automatically when arguments are validated.
- Require explicit confirmation for overwrites, moves, deletes, closing applications, terminal execution, software installation, system settings, shutdown/restart, external messages, purchases, and other consequential actions.
- Block unknown tools by default. Never request administrator privileges as the normal operating mode.
- Treat webpage text, files, and model output as untrusted data, not as instructions that can override policy.
- Scope file operations to approved user folders; reject path traversal and non-HTTP(S) browser schemes.
- Keep an audit trail of the requested action, policy decision, result, and verification status.

## First implementation slice

`Backend/Safety.py` provides a dependency-free policy decision layer; `tests/test_safety.py` verifies unknown-tool denial, approved path boundaries, URL scheme restrictions, and confirmation requirements. This layer is intentionally not an executor and must be called by the eventual orchestrator before tool dispatch.
