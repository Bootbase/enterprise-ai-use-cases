from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def _emit(text: str) -> None:
    payload = {
        "type": "assistant",
        "message": {
            "content": [
                {"type": "text", "text": text},
            ]
        },
    }
    print(json.dumps(payload), flush=True)


def _ensure_research_new(root: Path, topic_id: str) -> None:
    folder = root / f"use-cases/workflow-automation/{topic_id}-example"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "use-case.md").write_text("| **Status**       | `research`                   |\n", encoding="utf-8")
    (root / "README.md").write_text(
        f"| {topic_id} | [Title](foo) | Workflow Automation | Cross | High | `research` |\n",
        encoding="utf-8",
    )


def _ensure_research_complete(root: Path, topic_id: str) -> None:
    folder = root / f"use-cases/workflow-automation/{topic_id}-example"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "use-case.md").write_text("| **Status**       | `detailed`                   |\n", encoding="utf-8")
    for name in ("solution-design.md", "implementation-guide.md", "evaluation.md", "references.md"):
        (folder / name).write_text("# ok\n", encoding="utf-8")
    (root / "README.md").write_text(
        f"| {topic_id} | [Title](foo) | Workflow Automation | Cross | High | `detailed` |\n",
        encoding="utf-8",
    )


def main() -> int:
    args = sys.argv[1:]
    prompt = args[-1]
    root = Path.cwd()
    topic_id = os.environ.get("FAKE_CLAUDE_TOPIC_ID", "UC-024")
    scenario = os.environ.get("FAKE_CLAUDE_SCENARIO", "success")
    state_file = root / ".fake-claude-state"
    attempt = int(state_file.read_text(encoding="utf-8")) if state_file.exists() else 0
    state_file.write_text(str(attempt + 1), encoding="utf-8")

    if scenario == "limit-then-success" and attempt == 0:
        _emit("5-hour limit reached ∙ resets 12pm")
        return 0

    if prompt == "/research-new":
        _ensure_research_new(root, topic_id)
        _emit(f"Created new use case {topic_id}")
        return 0

    if prompt.startswith("/research-complete"):
        _ensure_research_complete(root, topic_id)
        _emit(f"Completed use case {topic_id}")
        return 0

    _emit(f"Unhandled prompt: {prompt}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
