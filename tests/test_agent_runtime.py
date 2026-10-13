import json
import tempfile
import unittest
from pathlib import Path

from Backend.AgentRuntime import AgentRuntime
from Backend.ToolRegistry import ToolRegistry


class FakeModel:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = 0

    def complete(self, messages):
        self.calls += 1
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


class AgentRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.workspace = self.root / "Documents"
        self.workspace.mkdir()
        self.tools = ToolRegistry([self.workspace])

    def tearDown(self):
        self.temp.cleanup()

    def test_final_response(self):
        model = FakeModel(['{"type":"final","response":"Ready."}'])
        result = AgentRuntime(model, self.tools).run("Hello")
        self.assertTrue(result.success)
        self.assertEqual(result.text, "Ready.")
        self.assertEqual(result.steps, 1)

    def test_model_tool_call_then_final(self):
        target = self.workspace / "note.txt"
        model = FakeModel([
            json.dumps({"type": "tool_call", "tool": "create_file", "arguments": {"path": str(target), "content": "created"}}),
            json.dumps({"type": "final", "response": "Created and verified."}),
        ])
        result = AgentRuntime(model, self.tools).run("Create note.txt")
        self.assertTrue(result.success)
        self.assertEqual(target.read_text(encoding="utf-8"), "created")
        self.assertEqual(model.calls, 2)

    def test_unknown_tool_fails_closed(self):
        model = FakeModel([
            json.dumps({"type": "tool_call", "tool": "run_arbitrary_shell", "arguments": {"command": "whoami"}}),
            json.dumps({"type": "final", "response": "The request was blocked."}),
        ])
        result = AgentRuntime(model, self.tools).run("Run a shell command")
        self.assertTrue(result.success)
        self.assertIn("blocked", result.text.lower())

    def test_malformed_json_fails_without_executing_tools(self):
        model = FakeModel(["not json"])
        result = AgentRuntime(model, self.tools).run("Do something")
        self.assertFalse(result.success)
        self.assertIn("planning failed", result.text.lower())

    def test_extra_plan_fields_are_rejected(self):
        model = FakeModel(['{"type":"final","response":"No","shell":"dangerous"}'])
        result = AgentRuntime(model, self.tools).run("Do something")
        self.assertFalse(result.success)

    def test_empty_input_is_rejected_without_model_call(self):
        model = FakeModel([])
        result = AgentRuntime(model, self.tools).run("  ")
        self.assertFalse(result.success)
        self.assertEqual(model.calls, 0)

    def test_cancelled_confirmation_stops_the_agent(self):
        target = self.workspace / "existing.txt"
        target.write_text("original", encoding="utf-8")
        model = FakeModel([
            json.dumps({"type": "tool_call", "tool": "create_file", "arguments": {"path": str(target), "content": "overwrite"}}),
        ])
        result = AgentRuntime(model, self.tools).run("Replace the file", confirm=lambda *_: False)
        self.assertFalse(result.success)
        self.assertEqual(target.read_text(encoding="utf-8"), "original")
        self.assertEqual(model.calls, 1)

    def test_step_limit_is_enforced(self):
        repeated = json.dumps({"type": "tool_call", "tool": "list_directory", "arguments": {"path": str(self.workspace)}})
        model = FakeModel([repeated, repeated, repeated])
        result = AgentRuntime(model, self.tools, max_steps=2).run("List the folder")
        self.assertFalse(result.success)
        self.assertEqual(result.steps, 2)
        self.assertEqual(model.calls, 2)

    def test_model_exception_does_not_leak_exception_message(self):
        model = FakeModel([RuntimeError("secret-token-should-not-be-shown")])
        result = AgentRuntime(model, self.tools).run("Hello")
        self.assertFalse(result.success)
        self.assertNotIn("secret-token", result.text)


if __name__ == "__main__":
    unittest.main()
