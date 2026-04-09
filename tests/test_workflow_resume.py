from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from claude_research_runner.app import _recover_session_id_from_log, run_workflow
from claude_research_runner.config import build_config
from claude_research_runner.models import ClaudeRunResult, LimitHit, Phase
from claude_research_runner.state import load_state


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
    def test_recover_session_id_from_realistic_log_event(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = Path(tmp_dir) / "research-new.ndjson"
            outer_event = {
                "timestamp": "2026-04-09T18:16:31.038943+02:00",
                "stream": "stdout",
                "raw": (
                    "{\"type\":\"stream_event\",\"event\":{\"type\":\"content_block_stop\",\"index\":0},"
                    "\"session_id\":\"fdbbf8c0-bd59-4a71-bed7-5440da411e26\","
                    "\"parent_tool_use_id\":null,\"uuid\":\"d95d0340-fde2-40aa-878d-1e59fd0da836\"}"
                ),
                "rendered": "",
            }
            log_path.write_text(json.dumps(outer_event) + "\n", encoding="utf-8")
            self.assertEqual(
                _recover_session_id_from_log(log_path),
                "fdbbf8c0-bd59-4a71-bed7-5440da411e26",
            )

    def _run_workflow(self, *, dirty_readme: bool) -> tuple[int, Path]:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir) / "repo"
            remote = Path(tmp_dir) / "remote.git"
            root.mkdir()
            _run(root, "git", "init", "-b", "main")
            _run(root, "git", "config", "user.name", "Test User")
            _run(root, "git", "config", "user.email", "test@example.com")
            _run(root, "git", "init", "--bare", str(remote))
            _run(root, "git", "remote", "add", "origin", str(remote))
            initial_readme = "preexisting note\n" if dirty_readme else ""
            (root / "README.md").write_text(initial_readme, encoding="utf-8")
            _run(root, "git", "add", "README.md")
            _run(root, "git", "commit", "-m", "init")
            _run(root, "git", "push", "-u", "origin", "main")
            if dirty_readme:
                (root / "README.md").write_text("preexisting note\nuser draft change\n", encoding="utf-8")

            fake_claude = Path(__file__).parent / "support" / "fake_claude.py"
            config = build_config(
                root=str(root),
                claude_bin="python3",
                sleep_hours=0,
                max_runtime_hours=24,
                session_name="runner-test",
                git_remote="origin",
                no_push=False,
            )

            original = os.environ.copy()
            os.environ["FAKE_CLAUDE_TOPIC_ID"] = "UC-024"

            try:
                with patch("claude_research_runner.app._read_claude_auth_status", return_value="Login method: Claude Max Account\n"):
                    with patch(
                        "claude_research_runner.app._runtime_limit_reached",
                        side_effect=lambda _config, state: state.current_phase == Phase.COMPLETED,
                    ):
                        with patch("claude_research_runner.app.run_claude") as mocked_run:

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
                                rendered = completed.stdout.strip()
                                payload = json.dumps({"rendered": rendered, "raw": rendered}) + "\n"
                                kwargs["log_path"].write_text(payload, encoding="utf-8")
                                return ClaudeRunResult(
                                    exit_code=completed.returncode,
                                    rendered_text=completed.stdout,
                                    raw_output=completed.stdout,
                                    stderr_text=completed.stderr,
                                    limit_hit=None,
                                )

                            mocked_run.side_effect = _side_effect
                            exit_code = run_workflow(config)

                if dirty_readme:
                    committed_readme = _run(root, "git", "show", "HEAD:README.md")
                    self.assertNotIn("user draft change", committed_readme)
                    self.assertIn("UC-024", committed_readme)
                    working_readme = (root / "README.md").read_text(encoding="utf-8")
                    self.assertIn("user draft change", working_readme)
                    self.assertIn("UC-024", working_readme)

                state_path = root / ".claude-research-runner" / "state.json"
                self.assertTrue(state_path.exists())
                copied_state_dir = Path(tmp_dir) / "state-copy"
                copied_state_dir.mkdir(parents=True, exist_ok=True)
                copied_state_path = copied_state_dir / "state.json"
                copied_state_path.write_text(state_path.read_text(encoding="utf-8"), encoding="utf-8")
                return exit_code, copied_state_path
            finally:
                os.environ.clear()
                os.environ.update(original)

    def test_end_to_end_success(self) -> None:
        exit_code, _ = self._run_workflow(dirty_readme=False)
        self.assertEqual(exit_code, 0)

    def test_end_to_end_with_dirty_readme(self) -> None:
        exit_code, _ = self._run_workflow(dirty_readme=True)
        self.assertEqual(exit_code, 0)

    def test_stops_on_weekly_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir) / "repo"
            root.mkdir()
            _run(root, "git", "init", "-b", "main")
            _run(root, "git", "config", "user.name", "Test User")
            _run(root, "git", "config", "user.email", "test@example.com")
            (root / "README.md").write_text("", encoding="utf-8")
            _run(root, "git", "add", "README.md")
            _run(root, "git", "commit", "-m", "init")

            config = build_config(
                root=str(root),
                claude_bin="python3",
                sleep_hours=0,
                max_runtime_hours=24,
                session_name="runner-test",
                git_remote=None,
                no_push=True,
            )

            with patch("claude_research_runner.app._read_claude_auth_status", return_value="Login method: Claude Max Account\n"):
                with patch(
                    "claude_research_runner.app.run_claude",
                    return_value=ClaudeRunResult(
                        exit_code=0,
                        rendered_text="weekly limit reached",
                        raw_output="weekly limit reached",
                        stderr_text="",
                        limit_hit=LimitHit(kind="weekly", matched_text="weekly limit reached"),
                    ),
                ):
                    exit_code = run_workflow(config)

            self.assertEqual(exit_code, 0)
            state = load_state(root / ".claude-research-runner" / "state.json")
            self.assertIsNotNone(state)
            assert state is not None
            self.assertEqual(state.current_phase, Phase.STOPPED)
            self.assertIn("weekly", state.stop_reason or "")

    def test_starts_second_cycle_before_user_interrupt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir) / "repo"
            root.mkdir()
            _run(root, "git", "init", "-b", "main")
            _run(root, "git", "config", "user.name", "Test User")
            _run(root, "git", "config", "user.email", "test@example.com")
            (root / "README.md").write_text("", encoding="utf-8")
            _run(root, "git", "add", "README.md")
            _run(root, "git", "commit", "-m", "init")

            fake_claude = Path(__file__).parent / "support" / "fake_claude.py"
            config = build_config(
                root=str(root),
                claude_bin="python3",
                sleep_hours=0,
                max_runtime_hours=24,
                session_name="runner-test",
                git_remote=None,
                no_push=True,
            )

            calls = 0
            current_topic_id = "UC-024"
            next_topic_number = 24

            def _side_effect(**kwargs):
                nonlocal calls, current_topic_id, next_topic_number
                calls += 1
                if calls == 3:
                    raise KeyboardInterrupt

                prompt = kwargs["command_text"]
                if prompt == "/research-new":
                    current_topic_id = f"UC-{next_topic_number:03d}"
                    next_topic_number += 1

                env = os.environ.copy()
                env["FAKE_CLAUDE_TOPIC_ID"] = current_topic_id
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
                rendered = completed.stdout.strip()
                payload = json.dumps({"rendered": rendered, "raw": rendered}) + "\n"
                kwargs["log_path"].write_text(payload, encoding="utf-8")
                return ClaudeRunResult(
                    exit_code=completed.returncode,
                    rendered_text=completed.stdout,
                    raw_output=completed.stdout,
                    stderr_text=completed.stderr,
                    limit_hit=None,
                )

            with patch("claude_research_runner.app._read_claude_auth_status", return_value="Login method: Claude Max Account\n"):
                with patch("claude_research_runner.app.run_claude", side_effect=_side_effect):
                    exit_code = run_workflow(config)

            self.assertEqual(exit_code, 130)
            self.assertEqual(calls, 3)
            state = load_state(root / ".claude-research-runner" / "state.json")
            self.assertIsNotNone(state)
            assert state is not None
            self.assertEqual(state.current_phase, Phase.STOPPED)
            self.assertEqual(state.stop_reason, "Stopped by user")


if __name__ == "__main__":
    unittest.main()
