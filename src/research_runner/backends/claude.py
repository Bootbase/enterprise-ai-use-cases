from __future__ import annotations

import json
import os
import queue
import re
import shutil
import subprocess
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from ..console import info
from ..models import AgentRunResult, LimitHit
from .base import AgentBackend


# ---------------------------------------------------------------------------
# Limit detection (Claude-specific)
# ---------------------------------------------------------------------------

PIPE_LIMIT_RE = re.compile(r"(Claude AI usage limit reached)\|(?P<epoch>\d+)", re.IGNORECASE)
RESET_RE = re.compile(
    r"(?P<kind>5-hour|weekly|opus weekly|usage)\s+limit reached.*?resets?\s+(?P<reset>[A-Za-z0-9,: ]+)",
    re.IGNORECASE,
)
LIMIT_TERMS = (
    "5-hour limit reached",
    "weekly limit reached",
    "usage limit reached",
)


def _normalize_kind(value: str) -> str:
    lowered = value.lower()
    if "5-hour" in lowered:
        return "five_hour"
    if "weekly" in lowered:
        return "weekly"
    return "usage"


def parse_reset_text(reset_text: str, now: datetime | None = None) -> datetime | None:
    current = now or datetime.now().astimezone()
    normalized = " ".join(reset_text.replace("\u2219", " ").strip().split())
    if not normalized:
        return None

    month_day_formats = ("%Y %b %d, %I%p", "%Y %b %d, %I:%M%p", "%Y %b %d, %I %p")
    for fmt in month_day_formats:
        candidate_text = f"{current.year} {normalized}"
        try:
            parsed = datetime.strptime(candidate_text, fmt)
        except ValueError:
            continue
        candidate = current.replace(
            year=parsed.year,
            month=parsed.month,
            day=parsed.day,
            hour=parsed.hour,
            minute=parsed.minute,
            second=0,
            microsecond=0,
        )
        if candidate < current:
            candidate = candidate.replace(year=current.year + 1)
        return candidate

    for fmt in ("%I%p", "%I:%M%p", "%I %p"):
        try:
            parsed = datetime.strptime(normalized, fmt)
        except ValueError:
            continue
        candidate = current.replace(hour=parsed.hour, minute=parsed.minute, second=0, microsecond=0)
        if candidate < current:
            candidate = candidate + timedelta(days=1)
        return candidate
    return None


def detect_limit_hit(text: str, now: datetime | None = None) -> LimitHit | None:
    pipe_match = PIPE_LIMIT_RE.search(text)
    if pipe_match:
        reset_dt = datetime.fromtimestamp(int(pipe_match.group("epoch")), tz=datetime.now().astimezone().tzinfo)
        return LimitHit(kind="usage", matched_text=pipe_match.group(0), reset_at=reset_dt.astimezone().isoformat())

    reset_match = RESET_RE.search(text)
    if reset_match:
        reset_dt = parse_reset_text(reset_match.group("reset"), now=now)
        return LimitHit(
            kind=_normalize_kind(reset_match.group("kind")),
            matched_text=reset_match.group(0),
            reset_at=reset_dt.astimezone().isoformat() if reset_dt else None,
        )

    lowered = text.lower()
    for term in LIMIT_TERMS:
        if term in lowered:
            return LimitHit(kind=_normalize_kind(term), matched_text=term, reset_at=None)
    return None


# ---------------------------------------------------------------------------
# Stream parsing helpers
# ---------------------------------------------------------------------------

def _reader(stream: Any, stream_name: str, target_queue: queue.Queue[tuple[str, str]]) -> None:
    try:
        for line in iter(stream.readline, ""):
            target_queue.put((stream_name, line))
    finally:
        target_queue.put((stream_name, ""))


def _tool_start_message(tool_name: str) -> str:
    if tool_name == "TodoWrite":
        return "Updating todo list..."
    if tool_name == "Write":
        return "Writing file..."
    return f"Running {tool_name}..."


def _render_tool_start(payload: dict[str, Any]) -> str:
    if payload.get("type") != "stream_event":
        return ""
    event = payload.get("event")
    if not isinstance(event, dict) or event.get("type") != "content_block_start":
        return ""
    content_block = event.get("content_block")
    if not isinstance(content_block, dict) or content_block.get("type") != "tool_use":
        return ""
    tool_name = content_block.get("name")
    if not isinstance(tool_name, str) or not tool_name:
        return ""
    return _tool_start_message(tool_name)


def _render_message(payload: dict[str, Any]) -> str:
    if payload.get("type") not in {"assistant", "user"}:
        return ""
    message = payload.get("message")
    if not isinstance(message, dict):
        return ""
    content_blocks = message.get("content")
    if not isinstance(content_blocks, list):
        return ""

    rendered_parts: list[str] = []
    for block in content_blocks:
        if not isinstance(block, dict):
            continue
        block_type = block.get("type")
        if block_type == "text":
            text = block.get("text")
            if isinstance(text, str) and text.strip():
                rendered_parts.append(text.strip())
            continue
        if block_type == "tool_result":
            content = block.get("content")
            if isinstance(content, str) and content.strip():
                rendered_parts.append(content.strip())
            continue
    return "\n".join(rendered_parts)


def _render_line(raw_line: str) -> str:
    stripped = raw_line.strip()
    if not stripped:
        return ""
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return stripped
    if not isinstance(payload, dict):
        return ""
    tool_start = _render_tool_start(payload)
    if tool_start:
        return tool_start
    return _render_message(payload)


def _extract_session_id(raw_line: str) -> str | None:
    stripped = raw_line.strip()
    if not stripped:
        return None
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return None
    session_id = payload.get("session_id")
    return session_id if isinstance(session_id, str) and session_id else None


def _log_event(log_path: Path, stream_name: str, raw_line: str, rendered_line: str) -> None:
    event = {
        "timestamp": datetime.now().astimezone().isoformat(),
        "stream": stream_name,
        "raw": raw_line.rstrip("\n"),
        "rendered": rendered_line,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=True) + "\n")


def _child_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("ANTHROPIC_API_KEY", None)
    return env


# ---------------------------------------------------------------------------
# Claude backend
# ---------------------------------------------------------------------------

class ClaudeBackend(AgentBackend):
    """Backend that drives the local ``claude`` CLI."""

    default_bin: str = "claude"

    @property
    def name(self) -> str:
        return "claude"

    @property
    def supports_sessions(self) -> bool:
        return True

    def preflight(self, root: Path) -> None:
        if shutil.which(self.agent_bin) is None and not Path(self.agent_bin).exists():
            raise RuntimeError(f"Claude binary not found: {self.agent_bin}")

        completed = subprocess.run(
            [self.agent_bin, "auth", "status", "--text"],
            cwd=root,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                completed.stderr.strip() or completed.stdout.strip() or "Failed to read Claude auth status"
            )
        login_method: str | None = None
        for line in completed.stdout.splitlines():
            if line.lower().startswith("login method:"):
                login_method = line.split(":", 1)[1].strip()
                break
        if not login_method or not login_method.startswith("Claude "):
            raise RuntimeError(f"Unsupported Claude auth mode: {login_method or 'unknown'}")

    def build_prompt(self, root: Path, skill_name: str, args: str | None = None) -> str:
        if args:
            return f"/{skill_name} {args}"
        return f"/{skill_name}"

    def run(
        self,
        *,
        root: Path,
        command: str,
        log_path: Path,
        session_name: str,
        session_id: str | None = None,
        resume: bool = False,
    ) -> AgentRunResult:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        args = [
            self.agent_bin,
            "--dangerously-skip-permissions",
            "--effort",
            "max",
            "--verbose",
            "--print",
            "--output-format",
            "stream-json",
            "--include-partial-messages",
        ]
        if resume:
            if not session_id:
                raise RuntimeError("Claude session_id is required to resume in print mode")
            args.extend(["--resume", session_id])
        else:
            args.extend(["--name", session_name])
        args.append(command)

        info(f"Executing: {' '.join(args[:-1])} {command}")
        process = subprocess.Popen(
            args,
            cwd=root,
            text=True,
            encoding="utf-8",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=1,
            env=_child_env(),
        )

        assert process.stdout is not None
        assert process.stderr is not None

        q: queue.Queue[tuple[str, str]] = queue.Queue()
        threads = [
            threading.Thread(target=_reader, args=(process.stdout, "stdout", q), daemon=True),
            threading.Thread(target=_reader, args=(process.stderr, "stderr", q), daemon=True),
        ]
        for thread in threads:
            thread.start()

        raw_lines: list[str] = []
        rendered_lines: list[str] = []
        stderr_lines: list[str] = []
        closed = {"stdout": False, "stderr": False}
        limit_hit: LimitHit | None = None
        observed_session_id: str | None = session_id

        while not all(closed.values()):
            stream_name, line = q.get()
            if line == "":
                closed[stream_name] = True
                continue
            raw_lines.append(line)
            rendered = _render_line(line)
            observed_from_line = _extract_session_id(line)
            if observed_from_line:
                observed_session_id = observed_from_line
            _log_event(log_path, stream_name, line, rendered)

            if stream_name == "stderr":
                stderr_lines.append(line.rstrip("\n"))

            candidate_text = "\n".join(part for part in (line, rendered) if part)
            if not limit_hit:
                limit_hit = detect_limit_hit(candidate_text)

            if rendered:
                print(rendered)
                rendered_lines.append(rendered)
            elif stream_name == "stderr":
                print(line.rstrip("\n"))

        return_code = process.wait()
        return AgentRunResult(
            exit_code=return_code,
            rendered_text="\n".join(rendered_lines),
            raw_output="".join(raw_lines),
            stderr_text="\n".join(stderr_lines),
            session_id=observed_session_id,
            limit_hit=limit_hit,
        )

    def recover_session_id(self, log_path: Path) -> str | None:
        if not log_path.exists():
            return None
        for line in reversed(log_path.read_text(encoding="utf-8").splitlines()):
            try:
                payload = json.loads(line)
            except Exception:
                continue
            outer_session_id = payload.get("session_id")
            if isinstance(outer_session_id, str) and outer_session_id:
                return outer_session_id
            for field_name in ("raw", "rendered"):
                field_value = payload.get(field_name)
                if not isinstance(field_value, str) or not field_value.strip():
                    continue
                try:
                    embedded = json.loads(field_value)
                except Exception:
                    continue
                embedded_session_id = embedded.get("session_id")
                if isinstance(embedded_session_id, str) and embedded_session_id:
                    return embedded_session_id
        return None

    def extract_log_texts(self, log_path: Path) -> list[str]:
        if not log_path.exists():
            return []
        texts: list[str] = []
        for line in log_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except Exception:
                continue
            for key in ("rendered", "raw"):
                value = payload.get(key)
                if isinstance(value, str):
                    texts.append(value)
        return texts
