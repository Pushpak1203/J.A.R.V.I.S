import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from Backend.ToolRegistry import ToolRegistry


class ToolRegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.workspace = self.root / "Documents"
        self.workspace.mkdir()
        self.registry = ToolRegistry([self.workspace])

    def tearDown(self):
        self.temp.cleanup()

    def test_list_directory_and_read_file(self):
        target = self.workspace / "note.txt"
        target.write_text("hello", encoding="utf-8")
        listing = self.registry.run("list_directory", {"path": str(self.workspace)})
        reading = self.registry.run("read_file", {"path": str(target)})
        self.assertTrue(listing.success)
        self.assertTrue(reading.success)
        self.assertEqual(reading.data, "hello")

    def test_read_outside_workspace_is_blocked(self):
        result = self.registry.run("read_file", {"path": str(self.root / "outside.txt")})
        self.assertFalse(result.success)
        self.assertIn("Blocked by policy", result.message)

    def test_create_file(self):
        target = self.workspace / "new.txt"
        result = self.registry.run("create_file", {"path": str(target), "content": "new"})
        self.assertTrue(result.success)
        self.assertEqual(target.read_text(encoding="utf-8"), "new")

    def test_existing_file_requires_confirmation_before_replacement(self):
        target = self.workspace / "existing.txt"
        target.write_text("old", encoding="utf-8")
        cancelled = self.registry.run("create_file", {"path": str(target), "content": "new"})
        self.assertFalse(cancelled.success)
        self.assertEqual(target.read_text(encoding="utf-8"), "old")
        approved = self.registry.run("create_file", {"path": str(target), "content": "new"}, confirm=lambda *_: True)
        self.assertTrue(approved.success)
        self.assertEqual(target.read_text(encoding="utf-8"), "new")

    def test_delete_requires_confirmation(self):
        target = self.workspace / "delete.txt"
        target.write_text("x", encoding="utf-8")
        result = self.registry.run("delete_file", {"path": str(target)})
        self.assertFalse(result.success)
        self.assertTrue(target.exists())
        approved = self.registry.run("delete_file", {"path": str(target)}, confirm=lambda *_: True)
        self.assertTrue(approved.success)
        self.assertFalse(target.exists())

    def test_unknown_tool_is_blocked(self):
        result = self.registry.run("execute_arbitrary_code", {"code": "print(1)"})
        self.assertFalse(result.success)
        self.assertIn("Blocked by policy", result.message)

    def test_launch_app_uses_argument_list_and_allowlist(self):
        popen = Mock(return_value=Mock(pid=123))
        registry = ToolRegistry([self.workspace], popen=popen)
        result = registry.run("launch_app", {"app": "notepad"})
        self.assertTrue(result.success)
        popen.assert_called_once_with(["notepad.exe"], shell=False, close_fds=True)
        blocked = registry.run("launch_app", {"app": "untrusted app"})
        self.assertFalse(blocked.success)

    def test_browser_rejects_javascript_url(self):
        opener = Mock()
        registry = ToolRegistry([self.workspace], open_url=opener)
        result = registry.run("open_url", {"url": "javascript:alert(1)"})
        self.assertFalse(result.success)
        opener.assert_not_called()

    def test_terminal_tool_is_not_yet_implemented(self):
        result = self.registry.run("run_command", {"command": "whoami"}, confirm=lambda *_: True)
        self.assertFalse(result.success)
        self.assertIn("not implemented yet", result.message)


if __name__ == "__main__":
    unittest.main()
