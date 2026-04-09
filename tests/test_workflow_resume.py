from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from claude_research_runner.app import run_workflow
from claude_research_runner.config import build_config


def _run(cwd: Path, *args: str) -> str:
    completed = subprocess.run(
        list(args),
        cwd=cwd,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=True,
    )
    return completed.stdout.strip()


class WorkflowResumeTests(unittest.TestCase):
    def test_end_to_end_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir) / "repo"
            remote = Path(tmp_dir) / "remote.git"
            root.mkdir()
            _run(root, "git", "init", "-b", "main")
            _run(root, "git", "config", "user.name", "Test User")
            _run(root, "git", "config", "user.email", "test@example.com")
            _run(root, "git", "init", "--bare", str(remote))
            _run(root, "git", "remote", "add", "origin", str(remote))
            (root / "README.md").write_text("", encoding="utf-8")
            _run(root, "git", "add", "README.md")
            _run(root, "git", "commit", "-m", "init")
            _run(root, "git", "push", "-u", "origin", "main")

            fake_claude = Path(__file__).parent / "support" / "fake_claude.py"
            config = build_config(
                root=str(root),
                claude_bin="python3",
                sleep_hours=0,
                session_name="runner-test",
                git_remote="origin",
                no_push=False,
            )

            original = os.environ.copy()
            os.environ["FAKE_CLAUDE_TOPIC_ID"] = "UC-024"

            try:
                with patch("claude_research_runner.app._read_claude_auth_status", return_value="Login method: Claude Max Account\n"):
                    with patch("claude_research_runner.app.run_claude") as mocked_run:
                        from claude_research_runner.models import ClaudeRunResult

                        def _side_effect(**kwargs):
                            prompt = kwargs["command_text"]
                            env = os.environ.copy()
                            completed = subprocess.run(
                                ["python3", str(fake_claude), "--dangerously-skip-permissions", prompt],
                                cwd=root,
                                text=True,
                                encoding="utf-8",
                                capture_output=True,
                                env=env,
                                check=False,
                            )
                            kwargs["log_path"].parent.mkdir(parents=True, exist_ok=True)
                            kwargs["log_path"].write_text(
                                '{"rendered": "%s", "raw": "%s"}\n'
                                % (completed.stdout.strip().replace('"', '\\"'), completed.stdout.strip().replace('"', '\\"')),
                                encoding="utf-8",
                            )
                            return ClaudeRunResult(
                                exit_code=completed.returncode,
                                rendered_text=completed.stdout,
                                raw_output=completed.stdout,
                                stderr_text=completed.stderr,
                                limit_hit=None,
                            )

                        mocked_run.side_effect = _side_effect
                        exit_code = run_workflow(config)
                self.assertEqual(exit_code, 0)
                state_path = root / ".claude-research-runner" / "state.json"
                self.assertTrue(state_path.exists())
            finally:
                os.environ.clear()
                os.environ.update(original)


if __name__ == "__main__":
    unittest.main()
