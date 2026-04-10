from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from .models import Phase, RunState, WorkflowMode


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def default_state(root: Path, session_name: str, sleep_hours: int, workflow_mode: WorkflowMode) -> RunState:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    state = RunState(
        version=1,
        run_id=run_id,
        root=str(root),
        session_name=session_name,
        current_phase=Phase.PREFLIGHT,
        sleep_hours=sleep_hours,
        workflow_mode=workflow_mode,
    )
    state.timestamps.started_at = now_iso()
    state.timestamps.updated_at = state.timestamps.started_at
    state.artifacts.logs_dir = str(root / ".research-runner" / "logs")
    return state


def load_state(path: Path) -> RunState | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return RunState.from_dict(payload)


def save_state(path: Path, state: RunState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    state.timestamps.updated_at = now_iso()
    path.write_text(json.dumps(state.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def update_state(state: RunState, **changes: object) -> RunState:
    return replace(state, **changes)
