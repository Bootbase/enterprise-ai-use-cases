from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from research_runner.app import _recover_session_id_from_log, run_workflow
from research_runner.backends.claude import ClaudeBackend
from research_runner.config import build_config
from research_runner.models import AgentRunResult, LimitHit, Phase, WorkflowMode
from research_runner.state import load_state


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
            backend = ClaudeBackend(agent_bin="claude")
            config_stub = type("Stub", (), {"backend": backend})()
            self.assertEqual(
                _recover_session_id_from_log(config_stub, log_path),
                "fdbbf8c0-bd59-4a71-bed7-5440da411e26",
            )

    def _run_workflow(
        self,
        *,
        dirty_readme: bool,
        readme_path: str = "README.md",
        workflow_mode: WorkflowMode = WorkflowMode.NEW_AND_COMPLETE,
        topic_id: str = "UC-024",
    ) -> tuple[int, Path]:
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
            (root / readme_path).parent.mkdir(parents=True, exist_ok=True)
            (root / readme_path).write_text(initial_readme, encoding="utf-8")
            _run(root, "git", "add", readme_path)
            _run(root, "git", "commit", "-m", "init")
            _run(root, "git", "push", "-u", "origin", "main")
            if dirty_readme:
                (root / readme_path).write_text("preexisting note\nuser draft change\n", encoding="utf-8")

            fake_claude = Path(__file__).parent / "support" / "fake_claude.py"
            backend = ClaudeBackend(agent_bin="python3")
            config = build_config(
                root=str(root),
                backend=backend,
                sleep_hours=0,
                max_runtime_hours=24,
                session_name="runner-test",
                git_remote="origin",
                no_push=False,
                workflow_mode=workflow_mode.value,
            )

            original = os.environ.copy()
            os.environ["FAKE_CLAUDE_TOPIC_ID"] = topic_id
            os.environ["FAKE_CLAUDE_README_PATH"] = readme_path

            try:
                with patch.object(ClaudeBackend, "preflight"):
                    with patch(
                        "research_runner.app._runtime_limit_reached",
                        side_effect=lambda _config, state: state.current_phase == Phase.COMPLETED,
                    ):
                        with patch.object(ClaudeBackend, "run") as mocked_run:

                            def _side_effect(**kwargs):
                                prompt = kwargs["command"]
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
                                return AgentRunResult(
                                    exit_code=completed.returncode,
                                    rendered_text=completed.stdout,
                                    raw_output=completed.stdout,
                                    stderr_text=completed.stderr,
                                    limit_hit=None,
                                )

                            mocked_run.side_effect = _side_effect
                            exit_code = run_workflow(config)

                if dirty_readme:
                    committed_readme = _run(root, "git", "show", f"HEAD:{readme_path}")
                    self.assertNotIn("user draft change", committed_readme)
                    self.assertIn("UC-024", committed_readme)
                    working_readme = (root / readme_path).read_text(encoding="utf-8")
                    self.assertIn("user draft change", working_readme)
                    self.assertIn("UC-024", working_readme)

                state_path = root / ".research-runner" / "state.json"
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

    def test_end_to_end_with_use_cases_readme_only(self) -> None:
        exit_code, _ = self._run_workflow(dirty_readme=False, readme_path="docs/use-cases/README.md")
        self.assertEqual(exit_code, 0)

    def test_end_to_end_detail_next_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir) / "repo"
            remote = Path(tmp_dir) / "remote.git"
            root.mkdir()
            _run(root, "git", "init", "-b", "main")
            _run(root, "git", "config", "user.name", "Test User")
            _run(root, "git", "config", "user.email", "test@example.com")
            _run(root, "git", "init", "--bare", str(remote))
            _run(root, "git", "remote", "add", "origin", str(remote))
            (root / "README.md").write_text("| UC-021 | [Title](foo) | Workflow Automation | Cross | High | `research` |\n", encoding="utf-8")
            base = root / "docs/use-cases/workflow-automation/UC-021-example"
            base.mkdir(parents=True, exist_ok=True)
            (base / "index.md").write_text('---\nstatus: "research"\n---\n', encoding="utf-8")
            _run(root, "git", "add", "README.md", "docs/use-cases/workflow-automation/UC-021-example/index.md")
            _run(root, "git", "commit", "-m", "init")
            _run(root, "git", "push", "-u", "origin", "main")

            fake_claude = Path(__file__).parent / "support" / "fake_claude.py"
            backend = ClaudeBackend(agent_bin="python3")
            config = build_config(
                root=str(root),
                backend=backend,
                sleep_hours=0,
                max_runtime_hours=24,
                session_name="runner-test",
                git_remote="origin",
                no_push=False,
                workflow_mode=WorkflowMode.DETAIL_NEXT.value,
            )

            with patch.object(ClaudeBackend, "preflight"):
                with patch(
                    "research_runner.app._runtime_limit_reached",
                    side_effect=lambda _config, state: state.current_phase == Phase.COMPLETED,
                ):
                    with patch.object(ClaudeBackend, "run") as mocked_run:

                        def _side_effect(**kwargs):
                            prompt = kwargs["command"]
                            env = os.environ.copy()
                            env["FAKE_CLAUDE_TOPIC_ID"] = prompt.rsplit(" ", 1)[-1]
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
                            return AgentRunResult(
                                exit_code=completed.returncode,
                                rendered_text=completed.stdout,
                                raw_output=completed.stdout,
                                stderr_text=completed.stderr,
                                limit_hit=None,
                            )

                        mocked_run.side_effect = _side_effect
                        exit_code = run_workflow(config)

            self.assertEqual(exit_code, 0)
            committed_readme = _run(root, "git", "show", "HEAD:README.md")
            self.assertIn("`detailed`", committed_readme)
            self.assertTrue((base / "solution-design.md").exists())

    def test_detail_next_stops_when_nothing_remains(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir) / "repo"
            root.mkdir()
            _run(root, "git", "init", "-b", "main")
            _run(root, "git", "config", "user.name", "Test User")
            _run(root, "git", "config", "user.email", "test@example.com")
            (root / "README.md").write_text("", encoding="utf-8")
            detailed_dir = root / "docs/use-cases/workflow-automation/UC-021-example"
            detailed_dir.mkdir(parents=True, exist_ok=True)
            (detailed_dir / "index.md").write_text('---\nstatus: "detailed"\n---\n', encoding="utf-8")
            _run(root, "git", "add", "README.md", "docs/use-cases/workflow-automation/UC-021-example/index.md")
            _run(root, "git", "commit", "-m", "init")

            backend = ClaudeBackend(agent_bin="python3")
            config = build_config(
                root=str(root),
                backend=backend,
                sleep_hours=0,
                max_runtime_hours=24,
                session_name="runner-test",
                git_remote=None,
                no_push=True,
                workflow_mode=WorkflowMode.DETAIL_NEXT.value,
            )

            with patch.object(ClaudeBackend, "preflight"):
                exit_code = run_workflow(config)

            self.assertEqual(exit_code, 0)
            state = load_state(root / ".research-runner" / "state.json")
            self.assertIsNotNone(state)
            assert state is not None
            self.assertEqual(state.current_phase, Phase.STOPPED)
            self.assertEqual(state.stop_reason, "No use cases remain that are not detailed")

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

            backend = ClaudeBackend(agent_bin="python3")
            config = build_config(
                root=str(root),
                backend=backend,
                sleep_hours=0,
                max_runtime_hours=24,
                session_name="runner-test",
                git_remote=None,
                no_push=True,
                workflow_mode=WorkflowMode.NEW_AND_COMPLETE.value,
            )

            with patch.object(ClaudeBackend, "preflight"):
                with patch.object(
                    ClaudeBackend,
                    "run",
                    return_value=AgentRunResult(
                        exit_code=0,
                        rendered_text="weekly limit reached",
                        raw_output="weekly limit reached",
                        stderr_text="",
                        limit_hit=LimitHit(kind="weekly", matched_text="weekly limit reached"),
                    ),
                ):
                    exit_code = run_workflow(config)

            self.assertEqual(exit_code, 0)
            state = load_state(root / ".research-runner" / "state.json")
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
            backend = ClaudeBackend(agent_bin="python3")
            config = build_config(
                root=str(root),
                backend=backend,
                sleep_hours=0,
                max_runtime_hours=24,
                session_name="runner-test",
                git_remote=None,
                no_push=True,
                workflow_mode=WorkflowMode.NEW_AND_COMPLETE.value,
            )

            calls = 0
            current_topic_id = "UC-024"
            next_topic_number = 24

            def _side_effect(**kwargs):
                nonlocal calls, current_topic_id, next_topic_number
                calls += 1
                if calls == 3:
                    raise KeyboardInterrupt

                prompt = kwargs["command"]
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
                return AgentRunResult(
                    exit_code=completed.returncode,
                    rendered_text=completed.stdout,
                    raw_output=completed.stdout,
                    stderr_text=completed.stderr,
                    limit_hit=None,
                )

            with patch.object(ClaudeBackend, "preflight"):
                with patch.object(ClaudeBackend, "run", side_effect=_side_effect):
                    exit_code = run_workflow(config)

            self.assertEqual(exit_code, 130)
            self.assertEqual(calls, 3)
            state = load_state(root / ".research-runner" / "state.json")
            self.assertIsNotNone(state)
            assert state is not None
            self.assertEqual(state.current_phase, Phase.STOPPED)
            self.assertEqual(state.stop_reason, "Stopped by user")

    def test_detail_next_starts_second_existing_cycle_before_user_interrupt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir) / "repo"
            root.mkdir()
            _run(root, "git", "init", "-b", "main")
            _run(root, "git", "config", "user.name", "Test User")
            _run(root, "git", "config", "user.email", "test@example.com")
            (root / "README.md").write_text(
                (
                    "| UC-021 | [Title](foo) | Workflow Automation | Cross | High | `research` |\n"
                    "| UC-022 | [Title](bar) | Workflow Automation | Cross | High | `research` |\n"
                ),
                encoding="utf-8",
            )
            for topic_id in ("UC-021", "UC-022"):
                use_case_dir = root / f"docs/use-cases/workflow-automation/{topic_id}-example"
                use_case_dir.mkdir(parents=True, exist_ok=True)
                (use_case_dir / "index.md").write_text(
                    '---\nstatus: "research"\n---\n',
                    encoding="utf-8",
                )
            _run(root, "git", "add", "README.md", "docs")
            _run(root, "git", "commit", "-m", "init")

            fake_claude = Path(__file__).parent / "support" / "fake_claude.py"
            backend = ClaudeBackend(agent_bin="python3")
            config = build_config(
                root=str(root),
                backend=backend,
                sleep_hours=0,
                max_runtime_hours=24,
                session_name="runner-test",
                git_remote=None,
                no_push=True,
                workflow_mode=WorkflowMode.DETAIL_NEXT.value,
            )

            calls = 0

            def _side_effect(**kwargs):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise KeyboardInterrupt

                prompt = kwargs["command"]
                env = os.environ.copy()
                env["FAKE_CLAUDE_TOPIC_ID"] = prompt.rsplit(" ", 1)[-1]
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
                return AgentRunResult(
                    exit_code=completed.returncode,
                    rendered_text=completed.stdout,
                    raw_output=completed.stdout,
                    stderr_text=completed.stderr,
                    limit_hit=None,
                )

            with patch.object(ClaudeBackend, "preflight"):
                with patch.object(ClaudeBackend, "run", side_effect=_side_effect):
                    exit_code = run_workflow(config)

            self.assertEqual(exit_code, 130)
            self.assertEqual(calls, 2)
            state = load_state(root / ".research-runner" / "state.json")
            self.assertIsNotNone(state)
            assert state is not None
            self.assertEqual(state.current_phase, Phase.STOPPED)
            self.assertEqual(state.stop_reason, "Stopped by user")
            self.assertEqual(state.topic_id, "UC-022")


if __name__ == "__main__":
    unittest.main()
