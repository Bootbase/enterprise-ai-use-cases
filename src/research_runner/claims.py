"""Cross-process topic ownership for the research runner.

When multiple runner instances share a repository, they must avoid working on
the same use case. Each instance writes a small JSON file under
``.research-runner/claims/UC-XXX.json`` to advertise that it owns the topic.

The acquire path uses ``os.O_CREAT | os.O_EXCL`` so the create-or-fail step is
atomic on local filesystems, which is enough to prevent two runners from
believing they hold the same claim. Reads of foreign claims are advisory and
only used to filter the candidate list before the atomic acquire attempt.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _claim_path(claims_dir: Path, topic_id: str) -> Path:
    return claims_dir / f"{topic_id}.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_claim(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, json.JSONDecodeError):
        return None


def read_claim(claims_dir: Path, topic_id: str) -> dict[str, Any] | None:
    """Return the claim payload for a topic, or None if no claim exists."""
    return _read_claim(_claim_path(claims_dir, topic_id))


def list_claimed_topics(claims_dir: Path, *, exclude_instance: str | None = None) -> set[str]:
    """List topic IDs that currently have a claim file.

    When ``exclude_instance`` is provided, claims owned by that instance are
    omitted from the result so a runner does not exclude its own work.
    """
    if not claims_dir.exists():
        return set()
    claimed: set[str] = set()
    for path in sorted(claims_dir.glob("UC-*.json")):
        data = _read_claim(path)
        if data is None:
            continue
        if exclude_instance is not None and data.get("instance_id") == exclude_instance:
            continue
        claimed.add(path.stem)
    return claimed


def acquire_claim(claims_dir: Path, topic_id: str, instance_id: str) -> bool:
    """Atomically claim ``topic_id`` for ``instance_id``.

    Returns ``True`` if the caller now owns the claim — either because it was
    freshly created or because the existing claim already belongs to the same
    instance. Returns ``False`` if a foreign instance currently owns it.
    """
    claims_dir.mkdir(parents=True, exist_ok=True)
    path = _claim_path(claims_dir, topic_id)

    payload = {
        "topic_id": topic_id,
        "instance_id": instance_id,
        "pid": os.getpid(),
        "acquired_at": _now_iso(),
    }
    serialized = json.dumps(payload, indent=2, sort_keys=True) + "\n"

    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    except FileExistsError:
        existing = _read_claim(path)
        if existing is not None and existing.get("instance_id") == instance_id:
            return True
        return False

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(serialized)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return True


def release_claim(claims_dir: Path, topic_id: str, instance_id: str) -> bool:
    """Remove the claim for ``topic_id`` if it belongs to ``instance_id``.

    Returns ``True`` if a claim was removed, ``False`` otherwise. Foreign
    claims are left untouched so a runaway instance cannot delete a peer's
    lock.
    """
    path = _claim_path(claims_dir, topic_id)
    existing = _read_claim(path)
    if existing is None:
        return False
    if existing.get("instance_id") != instance_id:
        return False
    try:
        path.unlink()
    except FileNotFoundError:
        return False
    return True
