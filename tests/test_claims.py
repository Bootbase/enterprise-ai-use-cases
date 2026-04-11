from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from research_runner.app import _load_or_create_state
from research_runner.backends.claude import ClaudeBackend
from research_runner.backends.codex import CodexBackend
from research_runner.claims import (
    acquire_claim,
    list_claimed_topics,
    read_claim,
    release_claim,
)
from research_runner.config import build_config
from research_runner.models import Phase, WorkflowMode
from research_runner.state import save_state
from research_runner.verification import find_next_topic_needing_detail


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _index_md(status: str) -> str:
    return (
        "---\n"
        'layout: "use-case"\n'
        f'status: "{status}"\n'
        "---\n\nbody\n"
    )


class ClaimsTests(unittest.TestCase):
    def test_acquire_creates_claim_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            claims_dir = Path(tmp_dir) / "claims"
            self.assertTrue(acquire_claim(claims_dir, "UC-123", "claude"))
            payload = read_claim(claims_dir, "UC-123")
            assert payload is not None
            self.assertEqual(payload["instance_id"], "claude")
            self.assertEqual(payload["topic_id"], "UC-123")

    def test_acquire_is_idempotent_for_same_instance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            claims_dir = Path(tmp_dir) / "claims"
            self.assertTrue(acquire_claim(claims_dir, "UC-123", "claude"))
            # The second acquire from the same instance should still report success
            # so resume after a crash works.
            self.assertTrue(acquire_claim(claims_dir, "UC-123", "claude"))

    def test_acquire_blocks_foreign_instance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            claims_dir = Path(tmp_dir) / "claims"
            self.assertTrue(acquire_claim(claims_dir, "UC-123", "claude"))
            self.assertFalse(acquire_claim(claims_dir, "UC-123", "codex"))

    def test_release_only_removes_own_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            claims_dir = Path(tmp_dir) / "claims"
            acquire_claim(claims_dir, "UC-123", "claude")
            # A peer cannot release someone else's claim.
            self.assertFalse(release_claim(claims_dir, "UC-123", "codex"))
            self.assertIsNotNone(read_claim(claims_dir, "UC-123"))
            # The owner can release it.
            self.assertTrue(release_claim(claims_dir, "UC-123", "claude"))
            self.assertIsNone(read_claim(claims_dir, "UC-123"))

    def test_release_returns_false_when_no_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            claims_dir = Path(tmp_dir) / "claims"
            self.assertFalse(release_claim(claims_dir, "UC-123", "claude"))

    def test_list_excludes_own_instance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            claims_dir = Path(tmp_dir) / "claims"
            acquire_claim(claims_dir, "UC-001", "claude")
            acquire_claim(claims_dir, "UC-002", "codex")
            self.assertEqual(
                list_claimed_topics(claims_dir, exclude_instance="claude"),
                {"UC-002"},
            )
            self.assertEqual(
                list_claimed_topics(claims_dir, exclude_instance="codex"),
                {"UC-001"},
            )
            self.assertEqual(
                list_claimed_topics(claims_dir),
                {"UC-001", "UC-002"},
            )

    def test_list_handles_missing_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            self.assertEqual(list_claimed_topics(Path(tmp_dir) / "nope"), set())

    def test_corrupt_claim_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            claims_dir = Path(tmp_dir) / "claims"
            claims_dir.mkdir()
            (claims_dir / "UC-123.json").write_text("not-json", encoding="utf-8")
            # A corrupt claim file should not be reported as owned.
            self.assertEqual(list_claimed_topics(claims_dir), set())


class FindNextTopicExclusionTests(unittest.TestCase):
    def test_excluded_ids_are_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            for topic_id in ("UC-021", "UC-022", "UC-023"):
                _write(
                    root / f"docs/use-cases/workflow-automation/{topic_id}-test/index.md",
                    _index_md("research"),
                )
            self.assertEqual(
                find_next_topic_needing_detail(root, excluded_ids={"UC-021"}).topic_id,
                "UC-022",
            )
            self.assertEqual(
                find_next_topic_needing_detail(
                    root, excluded_ids={"UC-021", "UC-022"}
                ).topic_id,
                "UC-023",
            )
            self.assertIsNone(
                find_next_topic_needing_detail(
                    root, excluded_ids={"UC-021", "UC-022", "UC-023"}
                )
            )


class PerInstanceConfigTests(unittest.TestCase):
    def test_state_path_is_namespaced_per_instance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            claude_config = build_config(
                root=tmp_dir,
                backend=ClaudeBackend(agent_bin="claude"),
                sleep_hours=0,
                session_name="x",
                git_remote=None,
                no_push=True,
            )
            codex_config = build_config(
                root=tmp_dir,
                backend=CodexBackend(agent_bin="codex"),
                sleep_hours=0,
                session_name="x",
                git_remote=None,
                no_push=True,
            )
            self.assertEqual(claude_config.instance_id, "claude")
            self.assertEqual(codex_config.instance_id, "codex")
            self.assertNotEqual(claude_config.state_path, codex_config.state_path)
            self.assertNotEqual(claude_config.logs_dir, codex_config.logs_dir)
            self.assertNotEqual(claude_config.baselines_dir, codex_config.baselines_dir)
            # Claims dir is shared so the lock is visible across instances.
            self.assertEqual(claude_config.claims_dir, codex_config.claims_dir)

    def test_explicit_instance_id_overrides_backend_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config = build_config(
                root=tmp_dir,
                backend=ClaudeBackend(agent_bin="claude"),
                sleep_hours=0,
                session_name="x",
                git_remote=None,
                no_push=True,
                instance_id="claude-mobile",
            )
            self.assertEqual(config.instance_id, "claude-mobile")
            self.assertTrue(config.state_path.name.endswith("state-claude-mobile.json"))


class ResumeDefaultsTests(unittest.TestCase):
    def _build_config(self, root: Path):
        return build_config(
            root=str(root),
            backend=ClaudeBackend(agent_bin="claude"),
            sleep_hours=0,
            session_name="x",
            git_remote=None,
            no_push=True,
            workflow_mode=WorkflowMode.DETAIL_NEXT.value,
        )

    def _seed_state(self, config, phase: Phase, topic_id: str | None = None) -> None:
        from research_runner.models import RunState

        config.state_path.parent.mkdir(parents=True, exist_ok=True)
        state = RunState(
            version=1,
            run_id="seed",
            root=str(config.root),
            session_name=config.session_name,
            current_phase=phase,
            workflow_mode=config.workflow_mode,
            topic_id=topic_id,
        )
        save_state(config.state_path, state)

    def test_no_state_file_starts_fresh(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config = self._build_config(Path(tmp_dir))
            state, resumed = _load_or_create_state(config)
            self.assertFalse(resumed)
            self.assertEqual(state.current_phase, Phase.PREFLIGHT)

    def test_resumes_in_place_for_non_terminal_phase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config = self._build_config(Path(tmp_dir))
            self._seed_state(config, Phase.RESEARCH_COMPLETE_RUNNING, topic_id="UC-123")
            state, resumed = _load_or_create_state(config)
            self.assertTrue(resumed)
            self.assertEqual(state.current_phase, Phase.RESEARCH_COMPLETE_RUNNING)
            self.assertEqual(state.topic_id, "UC-123")
            # The claim was re-acquired during resume.
            payload = read_claim(config.claims_dir, "UC-123")
            self.assertIsNotNone(payload)

    def test_resumes_with_fresh_cycle_after_completed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config = self._build_config(Path(tmp_dir))
            self._seed_state(config, Phase.COMPLETED, topic_id="UC-123")
            state, resumed = _load_or_create_state(config)
            self.assertFalse(resumed)
            self.assertEqual(state.current_phase, Phase.PREFLIGHT)
            self.assertIsNone(state.topic_id)

    def test_resumes_with_fresh_cycle_after_stopped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config = self._build_config(Path(tmp_dir))
            self._seed_state(config, Phase.STOPPED, topic_id="UC-123")
            state, resumed = _load_or_create_state(config)
            self.assertFalse(resumed)
            self.assertEqual(state.current_phase, Phase.PREFLIGHT)

    def test_resumes_with_fresh_cycle_after_failed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config = self._build_config(Path(tmp_dir))
            self._seed_state(config, Phase.FAILED, topic_id="UC-123")
            state, resumed = _load_or_create_state(config)
            self.assertFalse(resumed)
            self.assertEqual(state.current_phase, Phase.PREFLIGHT)

    def test_resume_fails_when_topic_is_claimed_by_peer(self) -> None:
        from research_runner.app import RunnerError

        with tempfile.TemporaryDirectory() as tmp_dir:
            config = self._build_config(Path(tmp_dir))
            self._seed_state(config, Phase.RESEARCH_COMPLETE_RUNNING, topic_id="UC-123")
            # A peer instance grabbed the topic between runs.
            acquire_claim(config.claims_dir, "UC-123", "codex")
            with self.assertRaises(RunnerError) as ctx:
                _load_or_create_state(config)
            self.assertIn("UC-123", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
