from __future__ import annotations

from .base import AgentBackend
from .claude import ClaudeBackend
from .codex import CodexBackend

BACKENDS: dict[str, type[AgentBackend]] = {
    "claude": ClaudeBackend,
    "codex": CodexBackend,
}


def get_backend(name: str, agent_bin: str | None = None) -> AgentBackend:
    backend_cls = BACKENDS.get(name)
    if backend_cls is None:
        raise ValueError(f"Unknown backend: {name!r}. Available: {', '.join(BACKENDS)}")
    return backend_cls(agent_bin=agent_bin or backend_cls.default_bin)


__all__ = ["AgentBackend", "ClaudeBackend", "CodexBackend", "BACKENDS", "get_backend"]
