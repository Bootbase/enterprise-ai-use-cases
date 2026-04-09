from __future__ import annotations

import re
from datetime import datetime, timedelta

from .models import LimitHit


PIPE_LIMIT_RE = re.compile(r"(Claude AI usage limit reached)\|(?P<epoch>\d+)", re.IGNORECASE)
RESET_RE = re.compile(
    r"(?P<kind>5-hour|weekly|opus weekly|usage)\s+limit reached.*?resets?\s+(?P<reset>[A-Za-z0-9,: ]+)",
    re.IGNORECASE,
)
LIMIT_TERMS = (
    "5-hour limit reached",
    "weekly limit reached",
    "usage limit reached",
)


def _normalize_kind(value: str) -> str:
    lowered = value.lower()
    if "5-hour" in lowered:
        return "five_hour"
    if "weekly" in lowered:
        return "weekly"
    return "usage"


def parse_reset_text(reset_text: str, now: datetime | None = None) -> datetime | None:
    current = now or datetime.now().astimezone()
    normalized = " ".join(reset_text.replace("∙", " ").strip().split())
    if not normalized:
        return None

    month_day_formats = ("%Y %b %d, %I%p", "%Y %b %d, %I:%M%p", "%Y %b %d, %I %p")
    for fmt in month_day_formats:
        candidate_text = f"{current.year} {normalized}"
        try:
            parsed = datetime.strptime(candidate_text, fmt)
        except ValueError:
            continue
        candidate = current.replace(
            year=parsed.year,
            month=parsed.month,
            day=parsed.day,
            hour=parsed.hour,
            minute=parsed.minute,
            second=0,
            microsecond=0,
        )
        if candidate < current:
            candidate = candidate.replace(year=current.year + 1)
        return candidate

    for fmt in ("%I%p", "%I:%M%p", "%I %p"):
        try:
            parsed = datetime.strptime(normalized, fmt)
        except ValueError:
            continue
        candidate = current.replace(hour=parsed.hour, minute=parsed.minute, second=0, microsecond=0)
        if candidate < current:
            candidate = candidate + timedelta(days=1)
        return candidate
    return None


def detect_limit_hit(text: str, now: datetime | None = None) -> LimitHit | None:
    pipe_match = PIPE_LIMIT_RE.search(text)
    if pipe_match:
        reset_dt = datetime.fromtimestamp(int(pipe_match.group("epoch")), tz=datetime.now().astimezone().tzinfo)
        return LimitHit(kind="usage", matched_text=pipe_match.group(0), reset_at=reset_dt.astimezone().isoformat())

    reset_match = RESET_RE.search(text)
    if reset_match:
        reset_dt = parse_reset_text(reset_match.group("reset"), now=now)
        return LimitHit(
            kind=_normalize_kind(reset_match.group("kind")),
            matched_text=reset_match.group(0),
            reset_at=reset_dt.astimezone().isoformat() if reset_dt else None,
        )

    lowered = text.lower()
    for term in LIMIT_TERMS:
        if term in lowered:
            return LimitHit(kind=_normalize_kind(term), matched_text=term, reset_at=None)
    return None
