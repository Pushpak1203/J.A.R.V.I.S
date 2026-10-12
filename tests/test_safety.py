import tempfile
import unittest
from pathlib import Path

from Backend.Safety import evaluate_tool_request, resolve_user_path, validate_url


class SafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.workspace = self.root / "Documents"
        self.workspace.mkdir()
        self.roots = [self.workspace]

    def tearDown(self):
        self.temp.cleanup()

    def test_allows_path_inside_workspace(self):
        result = resolve_user_path(self.workspace / "notes.txt", self.roots)
        self.assertEqual(result, self.workspace / "notes.txt")

    def test_rejects_path_traversal_outside_workspace(self):
        with self.assertRaises(PermissionError):
            resolve_user_path(self.workspace / ".." / "secret.txt", self.roots)

    def test_rejects_unapproved_tool(self):
        decision = evaluate_tool_request("format_drive", {})
        self.assertFalse(decision.allowed)
        self.assertFalse(decision.requires_confirmation)

    def test_read_and_list_can_run_without_confirmation(self):
        decision = evaluate_tool_request("list_directory", {"path": str(self.workspace)}, allowed_roots=self.roots)
        self.assertTrue(decision.allowed)
        self.assertFalse(decision.requires_confirmation)

    def test_delete_requires_confirmation(self):
        target = self.workspace / "old.txt"
        target.write_text("test", encoding="utf-8")
        decision = evaluate_tool_request("delete_file", {"path": str(target)}, allowed_roots=self.roots)
        self.assertTrue(decision.allowed)
        self.assertTrue(decision.requires_confirmation)

    def test_create_file_outside_workspace_is_blocked(self):
        decision = evaluate_tool_request("create_file", {"path": str(self.root / "outside.txt")}, allowed_roots=self.roots)
        self.assertFalse(decision.allowed)

    def test_existing_create_target_requires_confirmation(self):
        target = self.workspace / "existing.txt"
        target.write_text("original", encoding="utf-8")
        decision = evaluate_tool_request("create_file", {"path": str(target)}, allowed_roots=self.roots)
        self.assertTrue(decision.allowed)
        self.assertTrue(decision.requires_confirmation)

    def test_only_http_and_https_urls_are_allowed(self):
        self.assertEqual(validate_url("https://example.com/path"), "https://example.com/path")
        for url in ("javascript:alert(1)", "file:///C:/Windows/win.ini", "data:text/plain,hi"):
            with self.subTest(url=url), self.assertRaises(PermissionError):
                validate_url(url)

    def test_url_embedded_credentials_are_blocked(self):
        with self.assertRaises(PermissionError):
            validate_url("https://user:pass@example.com")


if __name__ == "__main__":
    unittest.main()
