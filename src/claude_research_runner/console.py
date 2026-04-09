from __future__ import annotations

from datetime import datetime


def _stamp() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S%z")


def banner(message: str) -> None:
    print(f"\n== {message} ==")


def info(message: str) -> None:
    print(f"[{_stamp()}] {message}")


def warn(message: str) -> None:
    print(f"[{_stamp()}] WARNING: {message}")


def error(message: str) -> None:
    print(f"[{_stamp()}] ERROR: {message}")

