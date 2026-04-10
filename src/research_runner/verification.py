from __future__ import annotations

import re
from pathlib import Path

from .models import VerificationResult


FRONTMATTER_STATUS_RE = re.compile(r'^status:\s*["\']?(?P<status>[^"\']+?)["\']?\s*$', re.MULTILINE)
FRONTMATTER_LAYOUT_RE = re.compile(r'^layout:\s*["\']?(?P<layout>[^"\']+?)["\']?\s*$', re.MULTILINE)
TOPIC_ID_RE = re.compile(r"^(?P<topic_id>UC-\d+)-")
README_STATUS_RE = re.compile(r"\|\s*(research|detailed)\s*\|", re.IGNORECASE)
INDEX_READMES = ("docs/use-cases/README.md", "README.md")
CODE_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
PLACEHOLDER_RE = re.compile(r"\{[A-Za-z][A-Za-z0-9 ,._/+():-]{1,120}\}")

USE_CASE_GLOB = "docs/use-cases/*/UC-*"
USE_CASE_INDEX = "index.md"

REQUIRED_HEADINGS: dict[str, tuple[str, ...]] = {
    "index.md": (
        "## Problem Statement",
        "## Business Case",
        "## Current Workflow",
        "## Target State",
        "## Stakeholders",
        "## Constraints",
        "## Evidence Base",
        "## Scope Boundaries",
    ),
    "solution-design.md": (
        "## What This Design Covers",
        "## Recommended Operating Model",
        "## Architecture",
        "## End-to-End Flow",
        "## AI Responsibilities and Boundaries",
        "## Integration Seams",
        "## Control Model",
        "## Reference Technology Stack",
        "## Key Design Decisions",
    ),
    "implementation-guide.md": (
        "## Build Goal",
        "## Reference Stack",
        "## Delivery Plan",
        "## Core Contracts",
        "## Orchestration Outline",
        "## Prompt And Guardrail Pattern",
        "## Integration Notes",
        "## Evaluation Harness",
        "## Deployment Notes",
    ),
    "evaluation.md": (
        "## Decision Summary",
        "## Published Evidence",
        "## Assumptions And Scenario Model",
        "## Expected Economics",
        "## Quality, Risk, And Failure Modes",
        "## Rollout KPI Set",
        "## Open Questions",
    ),
    "references.md": (
        "## Source Quality Notes",
        "## Source Register",
        "## Claim Map",
    ),
}

EXPECTED_LAYOUTS = {
    "index.md": "use-case",
    "solution-design.md": "use-case-detail",
    "implementation-guide.md": "use-case-detail",
    "evaluation.md": "use-case-detail",
    "references.md": "use-case-detail",
}


def _extract_frontmatter_status(content: str) -> str | None:
    if not content.startswith("---"):
        return None
    end = content.find("---", 3)
    if end == -1:
        return None
    frontmatter = content[: end + 3]
    match = FRONTMATTER_STATUS_RE.search(frontmatter)
    if not match:
        return None
    return match.group("status")


def _extract_frontmatter_layout(content: str) -> str | None:
    if not content.startswith("---"):
        return None
    end = content.find("---", 3)
    if end == -1:
        return None
    frontmatter = content[: end + 3]
    match = FRONTMATTER_LAYOUT_RE.search(frontmatter)
    if not match:
        return None
    return match.group("layout")


def _content_without_code_fences(content: str) -> str:
    return CODE_FENCE_RE.sub("", content)


def _validate_markdown_file(
    path: Path,
    *,
    check_headings: bool = True,
    check_placeholders: bool = True,
) -> None:
    content = path.read_text(encoding="utf-8")
    layout = _extract_frontmatter_layout(content)
    expected_layout = EXPECTED_LAYOUTS.get(path.name)
    if expected_layout and layout != expected_layout:
        raise RuntimeError(f"{path} is missing expected layout '{expected_layout}'")

    if check_headings:
        for heading in REQUIRED_HEADINGS.get(path.name, ()):
            if heading not in content:
                raise RuntimeError(f"{path} is missing required heading: {heading}")

    if check_placeholders:
        stripped = _content_without_code_fences(content)
        placeholder_match = PLACEHOLDER_RE.search(stripped)
        if placeholder_match:
            raise RuntimeError(f"{path} still contains template placeholder text: {placeholder_match.group(0)}")


def find_use_case_dirs(root: Path, topic_id: str) -> list[Path]:
    matches = sorted(path.parent for path in root.glob(f"docs/use-cases/*/{topic_id}-*/{USE_CASE_INDEX}"))
    return matches


def readme_row(root: Path, topic_id: str) -> str | None:
    for relative_path in INDEX_READMES:
        readme = root / relative_path
        if not readme.exists():
            continue
        for line in readme.read_text(encoding="utf-8").splitlines():
            if line.startswith(f"| {topic_id} "):
                return line
    return None


def readme_row_has_status(row: str, status: str) -> bool:
    if f"`{status}`" in row:
        return True
    match = README_STATUS_RE.search(row)
    return bool(match and match.group(1).lower() == status.lower())


def use_case_status(index_md: Path) -> str | None:
    content = index_md.read_text(encoding="utf-8")
    return _extract_frontmatter_status(content)


def topic_id_from_use_case_dir(use_case_dir: Path) -> str | None:
    match = TOPIC_ID_RE.match(use_case_dir.name)
    if not match:
        return None
    return match.group("topic_id")


def find_next_topic_needing_detail(root: Path) -> VerificationResult | None:
    candidates: list[tuple[int, str, str]] = []
    for index_md in root.glob(f"docs/use-cases/*/UC-*/{USE_CASE_INDEX}"):
        status = use_case_status(index_md)
        if status == "detailed":
            continue
        topic_id = topic_id_from_use_case_dir(index_md.parent)
        if topic_id is None:
            continue
        candidates.append((int(topic_id.split("-", 1)[1]), topic_id, str(index_md.parent.relative_to(root))))

    if not candidates:
        return None

    _, topic_id, use_case_dir = min(candidates)
    return VerificationResult(topic_id=topic_id, use_case_dir=use_case_dir)


def verify_research_new(root: Path, topic_id: str) -> VerificationResult:
    row = readme_row(root, topic_id)
    if row is None:
        raise RuntimeError(f"{topic_id} is missing from the repository index files")
    if not readme_row_has_status(row, "research"):
        raise RuntimeError(f"{topic_id} row in the repository index files is not marked as research")

    matches = find_use_case_dirs(root, topic_id)
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one use case directory for {topic_id}, found {len(matches)}")

    index_md = matches[0] / USE_CASE_INDEX
    if not index_md.exists():
        raise RuntimeError(f"{index_md} does not exist")

    status = use_case_status(index_md)
    if status != "research":
        raise RuntimeError(f"{index_md} is not marked as research")

    _validate_markdown_file(index_md)

    return VerificationResult(topic_id=topic_id, use_case_dir=str(matches[0].relative_to(root)))


def verify_research_complete(root: Path, topic_id: str) -> VerificationResult:
    row = readme_row(root, topic_id)
    if row is None or not readme_row_has_status(row, "detailed"):
        raise RuntimeError(f"{topic_id} row in the repository index files is not marked as detailed")

    matches = find_use_case_dirs(root, topic_id)
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one use case directory for {topic_id}, found {len(matches)}")

    use_case_dir = matches[0]
    expected = [
        "solution-design.md",
        "implementation-guide.md",
        "evaluation.md",
        "references.md",
    ]
    missing = [name for name in expected if not (use_case_dir / name).exists()]
    if missing:
        raise RuntimeError(f"{topic_id} is missing expected files: {', '.join(missing)}")

    index_md = use_case_dir / USE_CASE_INDEX
    status = use_case_status(index_md)
    if status != "detailed":
        raise RuntimeError(f"{index_md} is not marked as detailed")

    _validate_markdown_file(index_md, check_headings=False)
    for name in expected:
        _validate_markdown_file(use_case_dir / name)

    return VerificationResult(topic_id=topic_id, use_case_dir=str(use_case_dir.relative_to(root)))
