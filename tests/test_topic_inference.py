from __future__ import annotations

import unittest

from claude_research_runner.topic_inference import extract_topic_ids


class TopicInferenceTests(unittest.TestCase):
    def test_extracts_unique_ids_in_order(self) -> None:
        text = "Created UC-024 and later referenced UC-024 again before mentioning UC-031."
        self.assertEqual(extract_topic_ids(text), ["UC-024", "UC-031"])


if __name__ == "__main__":
    unittest.main()

