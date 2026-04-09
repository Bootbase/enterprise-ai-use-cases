from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class Phase(StrEnum):
    PREFLIGHT = "preflight"
    RESEARCH_NEW_RUNNING = "research_new_running"
    RESEARCH_NEW_VERIFYING = "research_new_verifying"
    RESEARCH_NEW_GIT = "research_new_git"
    RESEARCH_COMPLETE_RUNNING = "research_complete_running"
    RESEARCH_COMPLETE_VERIFYING = "research_complete_verifying"
    RESEARCH_COMPLETE_GIT = "research_complete_git"
    WAITING_FOR_LIMIT_RESET = "waiting_for_limit_reset"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(slots=True)
class GitState:
    branch: str | None = None
    upstream: str | None = None
    push_remote: str | None = None
    last_commit: str | None = None


@dataclass(slots=True)
class ArtifactState:
    research_new_folder: str | None = None
    logs_dir: str | None = None


@dataclass(slots=True)
class TimestampState:
    started_at: str | None = None
    updated_at: str | None = None


@dataclass(slots=True)
class RunState:
    version: int
    run_id: str
    root: str
    session_name: str
    current_phase: Phase
    topic_id: str | None = None
    last_command: str | None = None
    resume_phase: Phase | None = None
    session_started: bool = False
    sleep_hours: int = 4
    limit_retries: int = 0
    waiting_until: str | None = None
    git: GitState = field(default_factory=GitState)
    artifacts: ArtifactState = field(default_factory=ArtifactState)
    timestamps: TimestampState = field(default_factory=TimestampState)
    failure_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["current_phase"] = self.current_phase.value
        payload["resume_phase"] = self.resume_phase.value if self.resume_phase else None
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RunState":
        git_payload = payload.get("git") or {}
        artifact_payload = payload.get("artifacts") or {}
        timestamp_payload = payload.get("timestamps") or {}
        return cls(
            version=int(payload.get("version", 1)),
            run_id=str(payload["run_id"]),
            root=str(payload["root"]),
            session_name=str(payload["session_name"]),
            current_phase=Phase(payload["current_phase"]),
            topic_id=payload.get("topic_id"),
            last_command=payload.get("last_command"),
            resume_phase=Phase(payload["resume_phase"]) if payload.get("resume_phase") else None,
            session_started=bool(payload.get("session_started", False)),
            sleep_hours=int(payload.get("sleep_hours", 4)),
            limit_retries=int(payload.get("limit_retries", 0)),
            waiting_until=payload.get("waiting_until"),
            git=GitState(**git_payload),
            artifacts=ArtifactState(**artifact_payload),
            timestamps=TimestampState(**timestamp_payload),
            failure_message=payload.get("failure_message"),
        )


@dataclass(slots=True)
class LimitHit:
    kind: str
    matched_text: str
    reset_at: str | None = None


@dataclass(slots=True)
class ClaudeRunResult:
    exit_code: int
    rendered_text: str
    raw_output: str
    stderr_text: str
    limit_hit: LimitHit | None = None


@dataclass(slots=True)
class VerificationResult:
    topic_id: str
    use_case_dir: str
