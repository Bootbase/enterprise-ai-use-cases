from __future__ import annotations

import re


TOPIC_ID_RE = re.compile(r"\bUC-\d{3}\b")


def extract_topic_ids(text: str) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for match in TOPIC_ID_RE.finditer(text):
        topic_id = match.group(0)
        if topic_id not in seen:
            ordered.append(topic_id)
            seen.add(topic_id)
    return ordered

