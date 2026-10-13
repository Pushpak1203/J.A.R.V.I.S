import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from Backend.CommandRunner import run_approved_command, validate_command
from Backend.ToolRegistry import ToolRegistry


class CommandRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.workspace = self.root / "Projects"
        self.workspace.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def test_python_version_command_is_mapped_to_current_interpreter(self):
        import sys
        executable, args = validate_command("python", ["--version"])
        self.assertEqual(executable, sys.executable)
        self.assertEqual(args, ["--version"])

    def test_shell_and_arbitrary_python_are_rejected(self):
        for program, args in [
            ("cmd.exe", ["/c", "whoami"]),
            ("python", ["-c", "print('unsafe')"]),
            ("python", ["malicious.py"]),
            ("git", ["push", "origin", "main"]),
            ("git", ["status", "--porcelain=v1", "--untracked-files=all"]),
        ]:
            with self.subTest(program=program, args=args), self.assertRaises(PermissionError):
                validate_command(program, args)

    def test_runner_uses_shell_false_and_bounded_timeout(self):
        completed = Mock(returncode=0, stdout="ok", stderr="")
        runner = Mock(return_value=completed)
        result = run_approved_command(
            {"program": "python", "args": ["--version"], "cwd": str(self.workspace), "timeout_seconds": 10},
            allowed_roots=[self.workspace],
            runner=runner,
        )
        self.assertEqual(result["returncode"], 0)
        self.assertEqual(result["stdout"], "ok")
        kwargs = runner.call_args.kwargs
        self.assertFalse(kwargs["shell"])
        self.assertEqual(kwargs["timeout"], 10)

    def test_timeout_is_reported_as_structured_failure(self):
        runner = Mock(side_effect=subprocess.TimeoutExpired(cmd=["python"], timeout=1, output="partial"))
        result = run_approved_command(
            {"program": "python", "args": ["--version"], "cwd": str(self.workspace), "timeout_seconds": 1},
            allowed_roots=[self.workspace],
            runner=runner,
        )
        self.assertTrue(result["timed_out"])
        self.assertEqual(result["returncode"], -1)

    def test_working_directory_must_be_approved(self):
        with self.assertRaises(PermissionError):
            run_approved_command(
                {"program": "python", "args": ["--version"], "cwd": str(self.root), "timeout_seconds": 1},
                allowed_roots=[self.workspace],
                runner=Mock(),
            )

    def test_registry_requires_confirmation_and_rejects_before_prompt(self):
        registry = ToolRegistry([self.workspace])
        runner = Mock(return_value=Mock(returncode=0, stdout="Python 3.10", stderr=""))
        # The registry does not expose an arbitrary runner parameter. An unsafe
        # command must be rejected before the confirmation callback is invoked.
        confirm = Mock(return_value=True)
        result = registry.run(
            "run_command",
            {"program": "python", "args": ["-c", "print(1)"], "cwd": str(self.workspace)},
            confirm=confirm,
        )
        self.assertFalse(result.success)
        confirm.assert_not_called()

    def test_registry_never_runs_command_without_confirmation(self):
        registry = ToolRegistry([self.workspace])
        result = registry.run(
            "run_command",
            {"program": "python", "args": ["--version"], "cwd": str(self.workspace)},
        )
        self.assertFalse(result.success)
        self.assertTrue(result.requires_confirmation)


if __name__ == "__main__":
    unittest.main()
