"""Interactive command-line harness for the new agent runtime.

Run from the repository root with: python -m Backend.AgentCLI
This is an incremental test harness, not a replacement for the legacy GUI yet.
"""
from __future__ import annotations

import os
from pathlib import Path

from Backend.AgentRuntime import AgentRuntime
from Backend.ModelProviders import LocalFirstModelRouter, ModelProviderError
from Backend.ToolRegistry import ToolRegistry
from Backend.Safety import default_allowed_roots


def confirm_action(tool_name, arguments) -> bool:
    print("\nJ.A.R.V.I.S wants approval for a consequential action:")
    print(f"  Tool: {tool_name}")
    for key, value in arguments.items():
        # Avoid echoing arbitrary long content or likely credential fields.
        if any(word in key.casefold() for word in ("password", "token", "secret", "api_key")):
            display = "[REDACTED]"
        else:
            display = str(value)
        if len(display) > 500:
            display = display[:500] + "... [truncated]"
        print(f"  {key}: {display}")
    answer = input("Approve this action? Type YES to continue: ").strip()
    return answer == "YES"


def main() -> int:
    roots = default_allowed_roots()
    print("J.A.R.V.I.S agent runtime — experimental CLI")
    print("Approved file roots:")
    for root in roots:
        print(f"  - {root}")
    print("Start Ollama with a model configured in JARVIS_LOCAL_MODEL.")
    print("Type /exit to quit. No arbitrary shell execution is enabled.\n")

    model = LocalFirstModelRouter()
    tools = ToolRegistry(roots)
    agent = AgentRuntime(model, tools)

    while True:
        try:
            command = input("You > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nJ.A.R.V.I.S > Session ended.")
            return 0
        if command.casefold() in {"/exit", "/quit"}:
            print("J.A.R.V.I.S > Goodbye.")
            return 0
        if not command:
            continue
        try:
            result = agent.run(command, confirm=confirm_action)
        except ModelProviderError as exc:
            print(f"J.A.R.V.I.S > Model unavailable: {exc}")
            continue
        print(f"J.A.R.V.I.S > {result.text}")
        print(f"  [success={result.success}, steps={result.steps}, provider={result.provider or 'unknown'}]")


if __name__ == "__main__":
    raise SystemExit(main())
