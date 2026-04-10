from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from research_runner.verification import find_next_topic_needing_detail, verify_research_complete, verify_research_new


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _index_md(status: str) -> str:
    return f'---\nstatus: "{status}"\n---\n'


class VerificationTests(unittest.TestCase):
    def test_verify_research_new(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            _write(root / "README.md", "| UC-024 | [Title](foo) | Workflow Automation | Cross | High | `research` |\n")
            _write(
                root / "docs/use-cases/workflow-automation/UC-024-test/index.md",
                _index_md("research"),
            )
            result = verify_research_new(root, "UC-024")
            self.assertEqual(result.topic_id, "UC-024")

    def test_verify_research_new_from_use_cases_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            _write(root / "docs/use-cases/README.md", "| UC-024 | [Title](foo) | Workflow Automation | Cross | High | `research` |\n")
            _write(
                root / "docs/use-cases/workflow-automation/UC-024-test/index.md",
                _index_md("research"),
            )
            result = verify_research_new(root, "UC-024")
            self.assertEqual(result.topic_id, "UC-024")

    def test_verify_research_complete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            _write(root / "README.md", "| UC-024 | [Title](foo) | Workflow Automation | Cross | High | `detailed` |\n")
            base = root / "docs/use-cases/workflow-automation/UC-024-test"
            _write(base / "index.md", _index_md("detailed"))
            for name in ("solution-design.md", "implementation-guide.md", "evaluation.md", "references.md"):
                _write(base / name, "# ok\n")
            result = verify_research_complete(root, "UC-024")
            self.assertEqual(result.topic_id, "UC-024")

    def test_find_next_topic_needing_detail_returns_lowest_non_detailed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            _write(
                root / "docs/use-cases/workflow-automation/UC-022-test/index.md",
                _index_md("research"),
            )
            _write(
                root / "docs/use-cases/workflow-automation/UC-021-test/index.md",
                _index_md("research"),
            )
            _write(
                root / "docs/use-cases/workflow-automation/UC-020-test/index.md",
                _index_md("detailed"),
            )
            result = find_next_topic_needing_detail(root)
            self.assertIsNotNone(result)
            assert result is not None
            self.assertEqual(result.topic_id, "UC-021")

    def test_find_next_topic_needing_detail_returns_none_when_all_detailed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            _write(
                root / "docs/use-cases/workflow-automation/UC-021-test/index.md",
                _index_md("detailed"),
            )
            self.assertIsNone(find_next_topic_needing_detail(root))


if __name__ == "__main__":
    unittest.main()
