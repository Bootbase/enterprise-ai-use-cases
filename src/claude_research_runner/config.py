from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .models import WorkflowMode


@dataclass(slots=True)
class AppConfig:
    root: Path
    claude_bin: str
    sleep_hours: int
    max_runtime_hours: float
    session_name: str
    state_path: Path
    logs_dir: Path
    baselines_dir: Path
    no_push: bool
    workflow_mode: WorkflowMode
    git_remote: str | None = None


def build_session_name(explicit_name: str | None) -> tuple[str, str]:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if explicit_name:
        return run_id, explicit_name
    return run_id, f"claude-research-runner-{run_id}"


def build_config(
    root: str | None,
    claude_bin: str,
    sleep_hours: int,
    session_name: str | None,
    git_remote: str | None,
    no_push: bool,
    state_path: str | None = None,
    max_runtime_hours: float = 24,
    workflow_mode: str = WorkflowMode.NEW_AND_COMPLETE.value,
) -> AppConfig:
    resolved_root = Path(root or ".").resolve()
    _, effective_session_name = build_session_name(session_name)
    effective_state_path = Path(state_path).resolve() if state_path else resolved_root / ".claude-research-runner" / "state.json"
    logs_dir = effective_state_path.parent / "logs"
    return AppConfig(
        root=resolved_root,
        claude_bin=claude_bin,
        sleep_hours=sleep_hours,
        max_runtime_hours=max_runtime_hours,
        session_name=effective_session_name,
        state_path=effective_state_path,
        logs_dir=logs_dir,
        baselines_dir=effective_state_path.parent / "baselines",
        no_push=no_push,
        workflow_mode=WorkflowMode(workflow_mode),
        git_remote=git_remote,
    )
