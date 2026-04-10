from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from ..models import AgentRunResult


class AgentBackend(ABC):
    """Abstract base for agent CLI backends (Claude, Codex, etc.)."""

    default_bin: str = ""

    def __init__(self, agent_bin: str) -> None:
        self.agent_bin = agent_bin

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable backend name."""

    @property
    def supports_sessions(self) -> bool:
        """Whether this backend supports session resume."""
        return False

    @abstractmethod
    def preflight(self, root: Path) -> None:
        """Verify the agent binary is available and authenticated.

        Raises ``RuntimeError`` on failure.
        """

    @abstractmethod
    def build_prompt(self, root: Path, skill_name: str, args: str | None = None) -> str:
        """Build the command/prompt string to send to the agent for a given skill."""

    @abstractmethod
    def run(
        self,
        *,
        root: Path,
        command: str,
        log_path: Path,
        session_name: str,
        session_id: str | None = None,
        resume: bool = False,
    ) -> AgentRunResult:
        """Execute a command and return the result."""

    def recover_session_id(self, log_path: Path) -> str | None:
        """Try to recover a session/conversation ID from a previous log file."""
        return None

    @abstractmethod
    def extract_log_texts(self, log_path: Path) -> list[str]:
        """Extract rendered text segments from a log file for topic ID inference."""
