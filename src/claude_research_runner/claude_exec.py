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
