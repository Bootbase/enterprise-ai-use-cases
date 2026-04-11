from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from research_runner.verification import find_next_topic_needing_detail, verify_research_complete, verify_research_new


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


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


class VerificationTests(unittest.TestCase):
    def test_verify_research_new(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            _write(root / "README.md", "| UC-024 | Title | Workflow Automation | Cross | High | `research` |\n")
            _write(
                root / "docs/use-cases/workflow-automation/UC-024-test/index.md",
                _index_md("research"),
            )
            result = verify_research_new(root, "UC-024")
            self.assertEqual(result.topic_id, "UC-024")

    def test_verify_research_new_from_use_cases_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            _write(root / "docs/use-cases/README.md", "| UC-024 | Title | Workflow Automation | Cross | research | `workflow-automation/UC-024-test/` |\n")
            _write(
                root / "docs/use-cases/workflow-automation/UC-024-test/index.md",
                _index_md("research"),
            )
            result = verify_research_new(root, "UC-024")
            self.assertEqual(result.topic_id, "UC-024")

    def test_verify_research_complete_from_plain_status_row(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            _write(root / "docs/use-cases/README.md", "| UC-024 | Title | Workflow Automation | Cross | detailed | `workflow-automation/UC-024-test/` |\n")
            base = root / "docs/use-cases/workflow-automation/UC-024-test"
            _write(base / "index.md", _index_md("detailed"))
            for name in ("solution-design.md", "implementation-guide.md", "evaluation.md", "references.md"):
                _write(base / name, _detail_md(name))
            result = verify_research_complete(root, "UC-024")
            self.assertEqual(result.topic_id, "UC-024")

    def test_verify_research_complete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            _write(root / "README.md", "| UC-024 | Title | Workflow Automation | Cross | High | `detailed` |\n")
            base = root / "docs/use-cases/workflow-automation/UC-024-test"
            _write(base / "index.md", _index_md("detailed"))
            for name in ("solution-design.md", "implementation-guide.md", "evaluation.md", "references.md"):
                _write(base / name, _detail_md(name))
            result = verify_research_complete(root, "UC-024")
            self.assertEqual(result.topic_id, "UC-024")

    def test_verify_research_complete_allows_curly_braces_in_inline_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            _write(
                root / "docs/use-cases/README.md",
                "| UC-024 | Title | Workflow Automation | Cross | detailed | `workflow-automation/UC-024-test/` |\n",
            )
            base = root / "docs/use-cases/workflow-automation/UC-024-test"
            _write(base / "index.md", _index_md("detailed"))
            for name in ("solution-design.md", "implementation-guide.md", "evaluation.md", "references.md"):
                content = _detail_md(name)
                if name == "implementation-guide.md":
                    content = content.replace(
                        "## Integration Notes\n\nBody.",
                        "## Integration Notes\n\nCall `/repos/{owner}/{repo}/actions/runs` to list runs.",
                    )
                _write(base / name, content)
            result = verify_research_complete(root, "UC-024")
            self.assertEqual(result.topic_id, "UC-024")

    def test_verify_research_complete_rejects_curly_braces_in_prose(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            _write(
                root / "docs/use-cases/README.md",
                "| UC-024 | Title | Workflow Automation | Cross | detailed | `workflow-automation/UC-024-test/` |\n",
            )
            base = root / "docs/use-cases/workflow-automation/UC-024-test"
            _write(base / "index.md", _index_md("detailed"))
            for name in ("solution-design.md", "implementation-guide.md", "evaluation.md", "references.md"):
                content = _detail_md(name)
                if name == "implementation-guide.md":
                    content = content.replace(
                        "## Integration Notes\n\nBody.",
                        "## Integration Notes\n\nFill in the {owner placeholder} before shipping.",
                    )
                _write(base / name, content)
            with self.assertRaises(RuntimeError) as ctx:
                verify_research_complete(root, "UC-024")
            self.assertIn("{owner placeholder}", str(ctx.exception))

    def test_verify_research_complete_allows_placeholder_url_in_inline_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            _write(
                root / "docs/use-cases/README.md",
                "| UC-024 | Title | Workflow Automation | Cross | detailed | `workflow-automation/UC-024-test/` |\n",
            )
            base = root / "docs/use-cases/workflow-automation/UC-024-test"
            _write(base / "index.md", _index_md("detailed"))
            for name in ("solution-design.md", "implementation-guide.md", "evaluation.md", "references.md"):
                content = _detail_md(name)
                if name == "implementation-guide.md":
                    content = content.replace(
                        "## Integration Notes\n\nBody.",
                        "## Integration Notes\n\nDocument the endpoint `https://api.github.com/repos/{owner}/{repo}/actions/runs`.",
                    )
                _write(base / name, content)
            result = verify_research_complete(root, "UC-024")
            self.assertEqual(result.topic_id, "UC-024")

    def test_verify_research_complete_rejects_placeholder_url_in_prose(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            _write(
                root / "docs/use-cases/README.md",
                "| UC-024 | Title | Workflow Automation | Cross | detailed | `workflow-automation/UC-024-test/` |\n",
            )
            base = root / "docs/use-cases/workflow-automation/UC-024-test"
            _write(base / "index.md", _index_md("detailed"))
            for name in ("solution-design.md", "implementation-guide.md", "evaluation.md", "references.md"):
                content = _detail_md(name)
                if name == "implementation-guide.md":
                    content = content.replace(
                        "## Integration Notes\n\nBody.",
                        "## Integration Notes\n\nSee [the docs](https://example.com/api) for details.",
                    )
                _write(base / name, content)
            with self.assertRaises(RuntimeError) as ctx:
                verify_research_complete(root, "UC-024")
            self.assertIn("placeholder URL", str(ctx.exception))

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
