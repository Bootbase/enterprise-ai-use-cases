from __future__ import annotations

import re
from pathlib import Path


FRONTMATTER_RE = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)


def resolve_skill_prompt(root: Path, skill_name: str, args: str | None = None) -> str:
    """Read a SKILL.md file and return its content as a prompt.

    Strips YAML front matter so the returned string is pure instructions.
    Appends ``args`` at the end when provided.
    """
    skill_path = root / ".agents" / "skills" / skill_name / "SKILL.md"
    if not skill_path.exists():
        raise FileNotFoundError(f"Skill file not found: {skill_path}")

    content = skill_path.read_text(encoding="utf-8")
    content = FRONTMATTER_RE.sub("", content, count=1).strip()

    if args:
        content += f"\n\nArguments: {args}"

    return content
