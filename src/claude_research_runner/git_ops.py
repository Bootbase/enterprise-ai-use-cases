from __future__ import annotations

import subprocess
from pathlib import Path


class GitError(RuntimeError):
    pass


def _run_git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )
    if check and completed.returncode != 0:
        raise GitError(completed.stderr.strip() or completed.stdout.strip() or f"git {' '.join(args)} failed")
    return completed


def ensure_repo_root(root: Path) -> None:
    repo_root = _run_git(root, "rev-parse", "--show-toplevel").stdout.strip()
    if Path(repo_root).resolve() != root.resolve():
        raise GitError(f"{root} is not the repository root ({repo_root})")


def current_branch(root: Path) -> str:
    return _run_git(root, "branch", "--show-current").stdout.strip()


def upstream_ref(root: Path) -> str | None:
    completed = _run_git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}", check=False)
    if completed.returncode != 0:
        return None
    return completed.stdout.strip() or None


def dirty_paths(root: Path, *paths: str) -> list[str]:
    completed = _run_git(root, "status", "--porcelain", "--", *paths, check=False)
    lines = [line.rstrip() for line in completed.stdout.splitlines() if line.strip()]
    return lines


def stage_paths(root: Path, paths: list[str]) -> None:
    _run_git(root, "add", "--", *paths)


def has_staged_changes(root: Path) -> bool:
    completed = _run_git(root, "diff", "--cached", "--quiet", check=False)
    return completed.returncode == 1


def has_path_changes(root: Path, paths: list[str]) -> bool:
    return bool(dirty_paths(root, *paths))


def commit(root: Path, message: str) -> str | None:
    if not has_staged_changes(root):
        return None
    _run_git(root, "commit", "-m", message)
    return _run_git(root, "rev-parse", "HEAD").stdout.strip()


def push(root: Path, remote: str, branch: str) -> None:
    _run_git(root, "push", remote, branch)

