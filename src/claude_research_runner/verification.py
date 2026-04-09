from __future__ import annotations

import re
from pathlib import Path

from .models import VerificationResult


STATUS_ROW_RE = re.compile(r"\|\s*\*\*Status\*\*\s*\|\s*`(?P<status>[^`]+)`")
TOPIC_ID_RE = re.compile(r"^(?P<topic_id>UC-\d+)-")
INDEX_READMES = ("README.md", "use-cases/README.md")


def find_use_case_dirs(root: Path, topic_id: str) -> list[Path]:
    matches = sorted(path.parent for path in root.glob(f"use-cases/*/{topic_id}-*/use-case.md"))
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


def use_case_status(use_case_md: Path) -> str | None:
    content = use_case_md.read_text(encoding="utf-8")
    match = STATUS_ROW_RE.search(content)
    if not match:
        return None
    return match.group("status")


def topic_id_from_use_case_dir(use_case_dir: Path) -> str | None:
    match = TOPIC_ID_RE.match(use_case_dir.name)
    if not match:
        return None
    return match.group("topic_id")


def find_next_topic_needing_detail(root: Path) -> VerificationResult | None:
    candidates: list[tuple[int, str, str]] = []
    for use_case_md in root.glob("use-cases/*/UC-*/use-case.md"):
        status = use_case_status(use_case_md)
        if status == "detailed":
            continue
        topic_id = topic_id_from_use_case_dir(use_case_md.parent)
        if topic_id is None:
            continue
        candidates.append((int(topic_id.split("-", 1)[1]), topic_id, str(use_case_md.parent.relative_to(root))))

    if not candidates:
        return None

    _, topic_id, use_case_dir = min(candidates)
    return VerificationResult(topic_id=topic_id, use_case_dir=use_case_dir)


def verify_research_new(root: Path, topic_id: str) -> VerificationResult:
    row = readme_row(root, topic_id)
    if row is None:
        raise RuntimeError(f"{topic_id} is missing from the repository index files")
    if "`research`" not in row:
        raise RuntimeError(f"{topic_id} row in the repository index files is not marked as research")

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

    use_case_md = use_case_dir / "use-case.md"
    status = use_case_status(use_case_md)
    if status != "detailed":
        raise RuntimeError(f"{use_case_md} is not marked as detailed")

    return VerificationResult(topic_id=topic_id, use_case_dir=str(use_case_dir.relative_to(root)))
