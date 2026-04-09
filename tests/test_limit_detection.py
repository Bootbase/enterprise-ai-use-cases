from __future__ import annotations

import unittest
from datetime import datetime

from claude_research_runner.limit_detection import detect_limit_hit, parse_reset_text


class LimitDetectionTests(unittest.TestCase):
    def test_detects_pipe_format(self) -> None:
        hit = detect_limit_hit("Claude AI usage limit reached|1760004000")
        self.assertIsNotNone(hit)
        assert hit is not None
        self.assertEqual(hit.kind, "usage")
        self.assertIsNotNone(hit.reset_at)

    def test_detects_human_readable_limit(self) -> None:
        hit = detect_limit_hit("5-hour limit reached ∙ resets 12pm")
        self.assertIsNotNone(hit)
        assert hit is not None
        self.assertEqual(hit.kind, "five_hour")

    def test_parse_short_time_rolls_forward(self) -> None:
        now = datetime(2026, 4, 9, 13, 0).astimezone()
        parsed = parse_reset_text("12pm", now=now)
        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertGreater(parsed, now)


if __name__ == "__main__":
    unittest.main()

