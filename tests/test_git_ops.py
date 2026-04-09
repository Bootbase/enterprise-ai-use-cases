from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from claude_research_runner.git_ops import commit, current_branch, ensure_repo_root, has_path_changes, push, stage_paths, upstream_ref


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


class GitOpsTests(unittest.TestCase):
    def test_commit_and_push(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir) / "repo"
            remote = Path(tmp_dir) / "remote.git"
            root.mkdir()
            _run(root, "git", "init", "-b", "main")
            _run(root, "git", "config", "user.name", "Test User")
            _run(root, "git", "config", "user.email", "test@example.com")
            _run(root, "git", "init", "--bare", str(remote))
            _run(root, "git", "remote", "add", "origin", str(remote))
            (root / "README.md").write_text("hello\n", encoding="utf-8")
            _run(root, "git", "add", "README.md")
            _run(root, "git", "commit", "-m", "init")
            _run(root, "git", "push", "-u", "origin", "main")

            ensure_repo_root(root)
            self.assertEqual(current_branch(root), "main")
            self.assertEqual(upstream_ref(root), "origin/main")

            (root / "README.md").write_text("changed\n", encoding="utf-8")
            self.assertTrue(has_path_changes(root, ["README.md"]))
            stage_paths(root, ["README.md"])
            sha = commit(root, "update")
            self.assertIsNotNone(sha)
            push(root, "origin", "main")


if __name__ == "__main__":
    unittest.main()

