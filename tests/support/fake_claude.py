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


def _upsert_readme_row(root: Path, topic_id: str, status: str) -> None:
    readme_path = os.environ.get("FAKE_CLAUDE_README_PATH", "README.md")
    readme = root / readme_path
    readme.parent.mkdir(parents=True, exist_ok=True)
    existing = readme.read_text(encoding="utf-8") if readme.exists() else ""
    lines = existing.splitlines()
    target_prefix = f"| {topic_id} "
    replacement = f"| {topic_id} | Title | Workflow Automation | Cross | High | `{status}` |"
    replaced = False
    updated: list[str] = []
    for line in lines:
        if line.startswith(target_prefix):
            updated.append(replacement)
            replaced = True
        else:
            updated.append(line)
    if not replaced:
        updated.append(replacement)
    readme.write_text("\n".join(updated).rstrip() + "\n", encoding="utf-8")


def _index_md(status: str) -> str:
    return (
        "---\n"
        'layout: "use-case"\n'
        f'status: "{status}"\n'
        "---\n\n"
        "## Problem Statement\n\nBody.\n\n"
        "## Business Case\n\n| A | B | C |\n|---|---|---|\n| x | y | z |\n\n"
        "## Current Workflow\n\n1. One\n\n"
        "## Target State\n\nBody.\n\n"
        "## Stakeholders\n\n| A | B |\n|---|---|\n| x | y |\n\n"
        "## Constraints\n\n| A | B |\n|---|---|\n| x | y |\n\n"
        "## Evidence Base\n\n| A | B | C |\n|---|---|---|\n| x | y | z |\n\n"
        "## Scope Boundaries\n\n### In Scope\n\n- One\n\n### Out of Scope\n\n- Two\n"
    )


def _detail_md(name: str) -> str:
    sections = {
        "solution-design.md": (
            "## What This Design Covers\n\nBody.\n\n"
            "## Recommended Operating Model\n\nBody.\n\n"
            "## Architecture\n\n### System Diagram\n\n```text\nok\n```\n\n"
            "## End-to-End Flow\n\nBody.\n\n"
            "## AI Responsibilities and Boundaries\n\nBody.\n\n"
            "## Integration Seams\n\nBody.\n\n"
            "## Control Model\n\nBody.\n\n"
            "## Reference Technology Stack\n\nBody.\n\n"
            "## Key Design Decisions\n\nBody.\n"
        ),
        "implementation-guide.md": (
            "## Build Goal\n\nBody.\n\n"
            "## Reference Stack\n\nBody.\n\n"
            "## Delivery Plan\n\nBody.\n\n"
            "## Core Contracts\n\nBody.\n\n"
            "## Orchestration Outline\n\nBody.\n\n"
            "## Prompt And Guardrail Pattern\n\nBody.\n\n"
            "## Integration Notes\n\nBody.\n\n"
            "## Evaluation Harness\n\nBody.\n\n"
            "## Deployment Notes\n\nBody.\n"
        ),
        "evaluation.md": (
            "## Decision Summary\n\nBody.\n\n"
            "## Published Evidence\n\nBody.\n\n"
            "## Assumptions And Scenario Model\n\nBody.\n\n"
            "## Expected Economics\n\nBody.\n\n"
            "## Quality, Risk, And Failure Modes\n\nBody.\n\n"
            "## Rollout KPI Set\n\nBody.\n\n"
            "## Open Questions\n\n- One\n"
        ),
        "references.md": (
            "## Source Quality Notes\n\nBody.\n\n"
            "## Source Register\n\nBody.\n\n"
            "## Claim Map\n\nBody.\n"
        ),
    }
    return f'---\nlayout: "use-case-detail"\nstatus: "detailed"\n---\n\n{sections[name]}'


def _ensure_research_new(root: Path, topic_id: str) -> None:
    folder = root / f"docs/use-cases/workflow-automation/{topic_id}-example"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "index.md").write_text(_index_md("research"), encoding="utf-8")
    _upsert_readme_row(root, topic_id, "research")


def _ensure_research_complete(root: Path, topic_id: str) -> None:
    folder = root / f"docs/use-cases/workflow-automation/{topic_id}-example"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "index.md").write_text(_index_md("detailed"), encoding="utf-8")
    for name in ("solution-design.md", "implementation-guide.md", "evaluation.md", "references.md"):
        (folder / name).write_text(_detail_md(name), encoding="utf-8")
    _upsert_readme_row(root, topic_id, "detailed")


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
        _emit("5-hour limit reached \u2219 resets 12pm")
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
