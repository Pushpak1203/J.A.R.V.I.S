"""Small, policy-enforced desktop tool registry for J.A.R.V.I.S.

Only registered tools can run. This module deliberately avoids shell=True and
keeps terminal execution out of the initial registry until its allowlist and
UI confirmation flow are implemented.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping
import os
import shutil
import subprocess
import webbrowser

from Backend.Safety import evaluate_tool_request, resolve_user_path, validate_url
from Backend.CommandRunner import run_approved_command


@dataclass(frozen=True)
class ToolResult:
    success: bool
    message: str
    data: Any = None
    requires_confirmation: bool = False


ConfirmCallback = Callable[[str, Mapping[str, Any]], bool]


class ToolRegistry:
    """Execute a limited set of validated tools after policy evaluation."""

    APP_ALLOWLIST = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "paint": "mspaint.exe",
        "file explorer": "explorer.exe",
    }
    MAX_READ_BYTES = 1_000_000
    MAX_DIRECTORY_ITEMS = 200
    MAX_SEARCH_RESULTS = 200

    def __init__(
        self,
        allowed_roots: Iterable[str | Path] | None = None,
        *,
        popen: Callable[..., Any] | None = None,
        open_url: Callable[[str], Any] | None = None,
    ) -> None:
        self.allowed_roots = tuple(allowed_roots) if allowed_roots is not None else None
        self._popen = popen or subprocess.Popen
        self._open_url = open_url or webbrowser.open

    def run(
        self,
        tool_name: str,
        arguments: Mapping[str, Any] | None = None,
        *,
        confirm: ConfirmCallback | None = None,
    ) -> ToolResult:
        args = dict(arguments or {})
        decision = evaluate_tool_request(tool_name, args, allowed_roots=self.allowed_roots)
        if not decision.allowed:
            return ToolResult(False, f"Blocked by policy: {decision.reason}")
        if decision.requires_confirmation:
            if confirm is None or not confirm(tool_name, args):
                return ToolResult(False, "Action cancelled: explicit confirmation was not granted.", requires_confirmation=True)
        handlers = {
            "launch_app": self._launch_app,
            "open_url": self._open_url_tool,
            "list_directory": self._list_directory,
            "search_files": self._search_files,
            "read_file": self._read_file,
            "create_file": self._create_file,
            "write_file": self._write_file,
            "delete_file": self._delete_file,
            "move_file": self._move_file,
            "run_command": self._run_command,
        }
        handler = handlers.get(tool_name)
        if handler is None:
            return ToolResult(False, f"Tool is policy-listed but not implemented yet: {tool_name}")
        try:
            return handler(args)
        except (OSError, ValueError, PermissionError, shutil.Error) as exc:
            return ToolResult(False, f"{tool_name} failed: {exc}")

    def _run_command(self, args: Mapping[str, Any]) -> ToolResult:
        try:
            result = run_approved_command(dict(args), allowed_roots=self.allowed_roots)
        except (OSError, ValueError, PermissionError) as exc:
            return ToolResult(False, f"Command rejected or failed validation: {exc}")
        return_code = result["returncode"]
        summary = "Command completed." if return_code == 0 else f"Command exited with code {return_code}."
        if result["timed_out"]:
            summary = "Command timed out."
        return ToolResult(
            return_code == 0 and not result["timed_out"],
            summary,
            data=result,
        )

    def _path(self, value: Any) -> Path:
        return resolve_user_path(value, self.allowed_roots)

    def _launch_app(self, args: Mapping[str, Any]) -> ToolResult:
        app = str(args.get("app", "")).strip().lower()
        executable = self.APP_ALLOWLIST.get(app)
        if executable is None:
            return ToolResult(False, f"Application is not allowlisted: {app}")
        try:
            process = self._popen([executable], shell=False, close_fds=True)
        except FileNotFoundError:
            return ToolResult(False, f"Application executable was not found: {executable}")
        return ToolResult(True, f"Started {app}.", data={"pid": getattr(process, "pid", None)})

    def _open_url_tool(self, args: Mapping[str, Any]) -> ToolResult:
        url = validate_url(args.get("url"))
        opened = self._open_url(url)
        if opened is False:
            return ToolResult(False, "The browser did not accept the URL.")
        return ToolResult(True, "Opened URL in the default browser.", data={"url": url})

    def _list_directory(self, args: Mapping[str, Any]) -> ToolResult:
        path = self._path(args.get("path"))
        if not path.is_dir():
            return ToolResult(False, "The requested path is not a directory.")
        items = []
        with os.scandir(path) as entries:
            for entry in entries:
                if len(items) >= self.MAX_DIRECTORY_ITEMS:
                    break
                try:
                    items.append({"name": entry.name, "is_dir": entry.is_dir(follow_symlinks=False)})
                except OSError:
                    continue
        return ToolResult(True, f"Listed {len(items)} item(s).", data=items)

    def _search_files(self, args: Mapping[str, Any]) -> ToolResult:
        root = self._path(args.get("path"))
        query = str(args.get("query", "")).strip().casefold()
        if not query:
            return ToolResult(False, "A non-empty search query is required.")
        if not root.is_dir():
            return ToolResult(False, "The search root is not a directory.")
        matches = []
        for current, dirs, files in os.walk(root, followlinks=False):
            dirs[:] = [d for d in dirs if not (Path(current) / d).is_symlink()]
            for name in files:
                if query in name.casefold():
                    matches.append(str(Path(current) / name))
                    if len(matches) >= self.MAX_SEARCH_RESULTS:
                        return ToolResult(True, f"Search capped at {len(matches)} result(s).", data=matches)
        return ToolResult(True, f"Found {len(matches)} matching file(s).", data=matches)

    def _read_file(self, args: Mapping[str, Any]) -> ToolResult:
        path = self._path(args.get("path"))
        if not path.is_file():
            return ToolResult(False, "The requested path is not a file.")
        if path.stat().st_size > self.MAX_READ_BYTES:
            return ToolResult(False, f"File exceeds the {self.MAX_READ_BYTES}-byte read limit.")
        return ToolResult(True, f"Read {path.name}.", data=path.read_text(encoding="utf-8"))

    def _create_file(self, args: Mapping[str, Any]) -> ToolResult:
        path = self._path(args.get("path"))
        content = args.get("content", "")
        if not isinstance(content, str):
            return ToolResult(False, "File content must be text.")
        if path.exists() and not path.is_file():
            return ToolResult(False, "The target exists and is not a regular file.")
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            path.write_text(content, encoding="utf-8")
            return ToolResult(True, f"Replaced {path.name} after confirmation.")
        # Exclusive create prevents silently replacing a file created in a race.
        with path.open("x", encoding="utf-8") as handle:
            handle.write(content)
        return ToolResult(True, f"Created {path.name}.")

    def _write_file(self, args: Mapping[str, Any]) -> ToolResult:
        path = self._path(args.get("path"))
        content = args.get("content")
        if not isinstance(content, str):
            return ToolResult(False, "File content must be text.")
        if not path.is_file():
            return ToolResult(False, "write_file only modifies an existing regular file.")
        path.write_text(content, encoding="utf-8")
        return ToolResult(True, f"Updated {path.name} after confirmation.")

    def _delete_file(self, args: Mapping[str, Any]) -> ToolResult:
        path = self._path(args.get("path"))
        if not path.is_file() or path.is_symlink():
            return ToolResult(False, "Only regular files can be deleted by this tool.")
        path.unlink()
        return ToolResult(True, f"Deleted {path.name} after confirmation.")

    def _move_file(self, args: Mapping[str, Any]) -> ToolResult:
        source = self._path(args.get("source"))
        destination = self._path(args.get("destination"))
        if not source.is_file() or source.is_symlink():
            return ToolResult(False, "Only regular files can be moved by this tool.")
        if destination.exists():
            return ToolResult(False, "Destination already exists; refusing to overwrite.")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))
        return ToolResult(True, f"Moved {source.name} to {destination.name}.")
