from __future__ import annotations

import json
import unittest

from claude_research_runner.claude_exec import _render_line


class ClaudeExecRenderTests(unittest.TestCase):
    def test_renders_todo_tool_start_as_progress_message(self) -> None:
        payload = {
            "type": "stream_event",
            "event": {
                "type": "content_block_start",
                "index": 0,
                "content_block": {
                    "type": "tool_use",
                    "id": "toolu_123",
                    "name": "TodoWrite",
                    "input": {},
                    "caller": {"type": "direct"},
                },
            },
        }
        self.assertEqual(_render_line(json.dumps(payload)), "Updating todo list...")

    def test_renders_write_tool_start_as_progress_message(self) -> None:
        payload = {
            "type": "stream_event",
            "event": {
                "type": "content_block_start",
                "index": 0,
                "content_block": {
                    "type": "tool_use",
                    "id": "toolu_123",
                    "name": "Write",
                    "input": {},
                    "caller": {"type": "direct"},
                },
            },
        }
        self.assertEqual(_render_line(json.dumps(payload)), "Writing file...")

    def test_ignores_nested_todo_metadata_on_tool_result(self) -> None:
        payload = {
            "type": "user",
            "message": {
                "role": "user",
                "content": [
                    {
                        "tool_use_id": "toolu_123",
                        "type": "tool_result",
                        "content": (
                            "Todos have been modified successfully. Ensure that you continue "
                            "to use the todo list to track your progress. Please proceed with "
                            "the current tasks if applicable"
                        ),
                    }
                ],
            },
            "tool_use_result": {
                "oldTodos": [{"content": "Write evaluation.md", "status": "pending"}],
                "newTodos": [{"content": "Write evaluation.md", "status": "in_progress"}],
            },
        }
        self.assertEqual(
            _render_line(json.dumps(payload)),
            (
                "Todos have been modified successfully. Ensure that you continue to use "
                "the todo list to track your progress. Please proceed with the current "
                "tasks if applicable"
            ),
        )

    def test_ignores_embedded_file_content_on_write_result(self) -> None:
        payload = {
            "type": "user",
            "message": {
                "role": "user",
                "content": [
                    {
                        "tool_use_id": "toolu_123",
                        "type": "tool_result",
                        "content": "File created successfully at: /tmp/evaluation.md",
                    }
                ],
            },
            "tool_use_result": {
                "type": "create",
                "filePath": "/tmp/evaluation.md",
                "content": "# Large file body that should not be printed",
            },
        }
        self.assertEqual(
            _render_line(json.dumps(payload)),
            "File created successfully at: /tmp/evaluation.md",
        )


if __name__ == "__main__":
    unittest.main()
