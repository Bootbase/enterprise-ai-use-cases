from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .backends.base import AgentBackend
from .models import WorkflowMode


@dataclass(slots=True)
class AppConfig:
    root: Path
    backend: AgentBackend
    sleep_hours: int
    max_runtime_hours: float
    session_name: str
    instance_id: str
    state_path: Path
    logs_dir: Path
    baselines_dir: Path
    claims_dir: Path
    no_push: bool
    workflow_mode: WorkflowMode
    git_remote: str | None = None


def build_session_name(explicit_name: str | None) -> tuple[str, str]:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if explicit_name:
        return run_id, explicit_name
    return run_id, f"research-runner-{run_id}"


def build_config(
    root: str | None,
    backend: AgentBackend,
    sleep_hours: int,
    session_name: str | None,
    git_remote: str | None,
    no_push: bool,
    state_path: str | None = None,
    max_runtime_hours: float = 24,
    workflow_mode: str = WorkflowMode.NEW_AND_COMPLETE.value,
    instance_id: str | None = None,
) -> AppConfig:
    resolved_root = Path(root or ".").resolve()
    _, effective_session_name = build_session_name(session_name)
    effective_instance_id = (instance_id or backend.name).strip() or backend.name
    if state_path:
        effective_state_path = Path(state_path).resolve()
        base_dir = effective_state_path.parent
    else:
        base_dir = resolved_root / ".research-runner"
        effective_state_path = base_dir / f"state-{effective_instance_id}.json"
    logs_dir = base_dir / "logs" / effective_instance_id
    baselines_dir = base_dir / "baselines" / effective_instance_id
    claims_dir = base_dir / "claims"
    return AppConfig(
        root=resolved_root,
        backend=backend,
        sleep_hours=sleep_hours,
        max_runtime_hours=max_runtime_hours,
        session_name=effective_session_name,
        instance_id=effective_instance_id,
        state_path=effective_state_path,
        logs_dir=logs_dir,
        baselines_dir=baselines_dir,
        claims_dir=claims_dir,
        no_push=no_push,
        workflow_mode=WorkflowMode(workflow_mode),
        git_remote=git_remote,
    )
