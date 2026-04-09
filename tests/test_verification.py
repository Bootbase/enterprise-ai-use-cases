from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from claude_research_runner.verification import verify_research_complete, verify_research_new


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class VerificationTests(unittest.TestCase):
    def test_verify_research_new(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            _write(root / "README.md", "| UC-024 | [Title](foo) | Workflow Automation | Cross | High | `research` |\n")
            _write(
                root / "use-cases/workflow-automation/UC-024-test/use-case.md",
                "| **Status**       | `research`                   |\n",
            )
            result = verify_research_new(root, "UC-024")
            self.assertEqual(result.topic_id, "UC-024")

    def test_verify_research_complete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            _write(root / "README.md", "| UC-024 | [Title](foo) | Workflow Automation | Cross | High | `detailed` |\n")
            base = root / "use-cases/workflow-automation/UC-024-test"
            _write(base / "use-case.md", "| **Status**       | `detailed`                   |\n")
            for name in ("solution-design.md", "implementation-guide.md", "evaluation.md", "references.md"):
                _write(base / name, "# ok\n")
            result = verify_research_complete(root, "UC-024")
            self.assertEqual(result.topic_id, "UC-024")


if __name__ == "__main__":
    unittest.main()

