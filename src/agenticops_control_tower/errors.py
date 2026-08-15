"""Domain errors for control-plane operations."""

from __future__ import annotations


class AgenticOpsControlTowerError(Exception):
    """Base exception for control-plane domain errors."""


class AgentNotFoundError(AgenticOpsControlTowerError):
    """Raised when an agent lookup references an unknown agent id."""

    def __init__(self, agent_id: str) -> None:
        super().__init__(f"Agent '{agent_id}' is not registered")
        self.agent_id = agent_id
