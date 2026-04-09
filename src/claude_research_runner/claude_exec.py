from __future__ import annotations

import json
import os
import queue
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from .console import info
from .limit_detection import detect_limit_hit
from .models import ClaudeRunResult, LimitHit


def _reader(stream: Any, stream_name: str, target_queue: queue.Queue[tuple[str, str]]) -> None:
    try:
        for line in iter(stream.readline, ""):
            target_queue.put((stream_name, line))
    finally:
        target_queue.put((stream_name, ""))


def _walk_text(payload: Any) -> list[str]:
    texts: list[str] = []
    if isinstance(payload, dict):
        if payload.get("type") == "text" and isinstance(payload.get("text"), str):
            texts.append(payload["text"])
        elif isinstance(payload.get("content"), str):
            texts.append(payload["content"])
        for value in payload.values():
            texts.extend(_walk_text(value))
    elif isinstance(payload, list):
        for item in payload:
            texts.extend(_walk_text(item))
    return texts


def _render_line(raw_line: str) -> str:
    stripped = raw_line.strip()
    if not stripped:
        return ""
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return stripped
    texts = [segment.strip() for segment in _walk_text(payload) if segment.strip()]
    return "\n".join(texts)


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


def run_claude(
    *,
    claude_bin: str,
    root: Path,
    session_name: str,
    session_id: str | None,
    command_text: str,
    log_path: Path,
    resume_session: bool,
) -> ClaudeRunResult:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    args = [
        claude_bin,
        "--dangerously-skip-permissions",
        "--effort",
        "max",
        "--verbose",
        "--print",
        "--output-format",
        "stream-json",
        "--include-partial-messages",
    ]
    if resume_session:
        if not session_id:
            raise RuntimeError("Claude session_id is required to resume in print mode")
        args.extend(["--resume", session_id])
    else:
        args.extend(["--name", session_name])
    args.append(command_text)

    info(f"Executing: {' '.join(args[:-1])} {command_text}")
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
    return ClaudeRunResult(
        exit_code=return_code,
        rendered_text="\n".join(rendered_lines),
        raw_output="".join(raw_lines),
        stderr_text="\n".join(stderr_lines),
        session_id=observed_session_id,
        limit_hit=limit_hit,
    )
