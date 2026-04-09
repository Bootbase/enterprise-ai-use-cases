from __future__ import annotations

import re
from pathlib import Path

from .models import VerificationResult


STATUS_ROW_RE = re.compile(r"\|\s*\*\*Status\*\*\s*\|\s*`(?P<status>[^`]+)`")


def find_use_case_dirs(root: Path, topic_id: str) -> list[Path]:
    matches = sorted(path.parent for path in root.glob(f"use-cases/*/{topic_id}-*/use-case.md"))
    return matches


def readme_row(root: Path, topic_id: str) -> str | None:
    readme = root / "README.md"
    if not readme.exists():
        return None
    for line in readme.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"| {topic_id} "):
            return line
    return None


def use_case_status(use_case_md: Path) -> str | None:
    content = use_case_md.read_text(encoding="utf-8")
    match = STATUS_ROW_RE.search(content)
    if not match:
        return None
    return match.group("status")


def verify_research_new(root: Path, topic_id: str) -> VerificationResult:
    row = readme_row(root, topic_id)
    if row is None:
        raise RuntimeError(f"{topic_id} is missing from README.md")
    if "`research`" not in row:
        raise RuntimeError(f"{topic_id} row in README.md is not marked as research")

    matches = find_use_case_dirs(root, topic_id)
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one use case directory for {topic_id}, found {len(matches)}")

    use_case_md = matches[0] / "use-case.md"
    if not use_case_md.exists():
        raise RuntimeError(f"{use_case_md} does not exist")

    status = use_case_status(use_case_md)
    if status != "research":
        raise RuntimeError(f"{use_case_md} is not marked as research")

    return VerificationResult(topic_id=topic_id, use_case_dir=str(matches[0].relative_to(root)))


def verify_research_complete(root: Path, topic_id: str) -> VerificationResult:
    row = readme_row(root, topic_id)
    if row is None or "`detailed`" not in row:
        raise RuntimeError(f"{topic_id} row in README.md is not marked as detailed")

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

    use_case_md = use_case_dir / "use-case.md"
    status = use_case_status(use_case_md)
    if status != "detailed":
        raise RuntimeError(f"{use_case_md} is not marked as detailed")

    return VerificationResult(topic_id=topic_id, use_case_dir=str(use_case_dir.relative_to(root)))
