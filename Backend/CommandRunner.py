"""Allowlisted, bounded command execution for developer workflows.

This is intentionally not a general shell. Commands are passed as argument lists
with shell=False, a validated working directory, a timeout, and capped output.
"""
from __future__ import annotations

import subprocess
import sys
import shutil
from pathlib import Path
from typing import Any, Callable, Iterable

from Backend.Safety import resolve_user_path


MAX_OUTPUT_CHARS = 12_000
DEFAULT_TIMEOUT_SECONDS = 30
MAX_TIMEOUT_SECONDS = 90


def validate_command(program: Any, args: Any) -> tuple[str, list[str]]:
    if not isinstance(program, str) or not isinstance(args, list):
        raise ValueError("program must be a string and args must be a list of strings")
    if any(not isinstance(arg, str) or "\x00" in arg for arg in args):
        raise ValueError("Every command argument must be a valid string")
    if len(args) > 30 or sum(len(arg) for arg in args) > 4_000:
        raise ValueError("Command arguments exceed the configured size limit")

    normalized = program.strip().casefold()
    if normalized in {"python", "python.exe", "py"}:
        if args == ["--version"] or args == ["-V"]:
            return sys.executable, args
        if args == ["-m", "unittest", "discover", "-s", "tests", "-v"]:
            return sys.executable, args
        if args == ["-m", "pytest", "tests"]:
            return sys.executable, args
        if args == ["-m", "compileall", "Backend", "tests"]:
            return sys.executable, args
        if args == ["-m", "pip", "check"]:
            return sys.executable, args
        raise PermissionError("Python command is not allowlisted. Only version, test, compile, and pip-check commands are enabled.")

    if normalized == "git":
        allowed = {
            ("status",),
            ("status", "--short"),
            ("diff", "--stat"),
            ("log", "--oneline", "-n", "10"),
            ("branch", "--show-current"),
            ("rev-parse", "--show-toplevel"),
            ("ls-files",),
        }
        if tuple(args) not in allowed:
            raise PermissionError("Git command is not allowlisted. Only read-only status, diff-stat, log, branch, root, and file-list commands are enabled.")
        executable = shutil.which("git")
        if not executable:
            raise FileNotFoundError("Git executable was not found on PATH.")
        return executable, args

    raise PermissionError("Executable is not allowlisted. Supported programs are Python test/diagnostic commands and selected read-only Git commands.")


def run_approved_command(
    arguments: dict[str, Any],
    *,
    allowed_roots: Iterable[str | Path] | None = None,
    runner: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    program, args = validate_command(arguments.get("program"), arguments.get("args"))
    cwd_value = arguments.get("cwd")
    cwd = resolve_user_path(cwd_value, allowed_roots)
    if not cwd.is_dir():
        raise ValueError("Working directory must be an existing directory inside an approved root.")
    timeout = arguments.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS)
    if isinstance(timeout, bool) or not isinstance(timeout, int) or not 1 <= timeout <= MAX_TIMEOUT_SECONDS:
        raise ValueError(f"timeout_seconds must be an integer between 1 and {MAX_TIMEOUT_SECONDS}")

    execute = runner or subprocess.run
    completed = execute(
        [program, *args],
        cwd=str(cwd),
        shell=False,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    stdout = (completed.stdout or "")[:MAX_OUTPUT_CHARS]
    stderr = (completed.stderr or "")[:MAX_OUTPUT_CHARS]
    return {
        "returncode": int(completed.returncode),
        "stdout": stdout,
        "stderr": stderr,
        "timed_out": False,
        "truncated": len(completed.stdout or "") > MAX_OUTPUT_CHARS or len(completed.stderr or "") > MAX_OUTPUT_CHARS,
    }
