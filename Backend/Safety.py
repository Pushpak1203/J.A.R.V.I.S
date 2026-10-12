"""Policy checks for J.A.R.V.I.S desktop tool execution.

This module is deliberately dependency-free. It does not execute tools; it
returns a decision that the orchestrator must enforce before dispatch.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Any
from urllib.parse import urlparse


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    requires_confirmation: bool
    reason: str


# Unknown tools fail closed. Add tools here only after implementing and testing
# their argument validation and execution behavior.
_AUTONOMOUS_TOOLS = {
    "launch_app",
    "open_url",
    "list_directory",
    "search_files",
    "read_file",
    "create_file",
    "volume_up",
    "volume_down",
    "mute_audio",
}
_CONFIRM_TOOLS = {
    "write_file",
    "move_file",
    "delete_file",
    "run_command",
    "change_system_setting",
    "install_software",
    "shutdown",
    "restart",
    "send_message",
    "purchase",
    "close_app",
}
_PATH_FIELDS = {
    "list_directory": ("path",),
    "search_files": ("path",),
    "read_file": ("path",),
    "create_file": ("path",),
    "write_file": ("path",),
    "delete_file": ("path",),
    "move_file": ("source", "destination"),
}


def default_allowed_roots(home: Path | None = None) -> tuple[Path, ...]:
    """Return user-owned working folders; never include Windows/system roots."""
    home = (home or Path.home()).resolve()
    candidates = (home / "Desktop", home / "Documents", home / "Downloads", home / "Projects")
    return tuple(path.resolve() for path in candidates)


def resolve_user_path(value: str | Path, allowed_roots: Iterable[str | Path] | None = None) -> Path:
    """Resolve a path and reject traversal or paths outside approved roots.

    Callers should pass explicit roots for tests or workspace-specific setups.
    Existing symlinks are resolved before containment is checked.
    """
    if not isinstance(value, (str, Path)) or not str(value).strip():
        raise ValueError("A non-empty filesystem path is required")
    candidate = Path(value).expanduser().resolve(strict=False)
    roots = tuple(Path(root).expanduser().resolve(strict=False) for root in (allowed_roots or default_allowed_roots()))
    for root in roots:
        try:
            candidate.relative_to(root)
            return candidate
        except ValueError:
            continue
    raise PermissionError(f"Path is outside the approved working folders: {candidate}")


def validate_url(value: str) -> str:
    """Allow ordinary HTTP(S) URLs only; reject script and local-file schemes."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("A non-empty URL is required")
    url = value.strip()
    parsed = urlparse(url)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        raise PermissionError("Only absolute http:// and https:// URLs may be opened")
    if parsed.username or parsed.password:
        raise PermissionError("URLs containing embedded credentials are not allowed")
    return url


def evaluate_tool_request(
    tool_name: str,
    arguments: Mapping[str, Any] | None = None,
    *,
    allowed_roots: Iterable[str | Path] | None = None,
) -> PolicyDecision:
    """Return an allow/confirmation decision; never execute the requested action."""
    args: Mapping[str, Any] = arguments or {}
    if tool_name not in _AUTONOMOUS_TOOLS and tool_name not in _CONFIRM_TOOLS:
        return PolicyDecision(False, False, f"Unknown tool is blocked: {tool_name}")

    if tool_name == "open_url":
        try:
            validate_url(args.get("url"))
        except (ValueError, PermissionError) as exc:
            return PolicyDecision(False, False, str(exc))

    for field in _PATH_FIELDS.get(tool_name, ()):
        try:
            resolve_user_path(args.get(field), allowed_roots)
        except (ValueError, PermissionError, OSError) as exc:
            return PolicyDecision(False, False, f"Invalid {field}: {exc}")

    if tool_name == "create_file":
        path = resolve_user_path(args["path"], allowed_roots)
        if path.exists():
            return PolicyDecision(True, True, "The target already exists; confirm before replacing it")

    if tool_name in _CONFIRM_TOOLS:
        return PolicyDecision(True, True, f"{tool_name} requires explicit user confirmation")

    return PolicyDecision(True, False, "Allowed by the autonomous low-risk tool policy")
