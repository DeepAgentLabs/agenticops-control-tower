"""In-memory scaffold for registration and heartbeat flows."""

from __future__ import annotations

from agenticops_control_tower.models import AgentRecord, HeartbeatPayload


class AgentRegistry:
    """Very small in-memory registry to anchor the scaffold tests."""

    def __init__(self) -> None:
        self._agents: dict[str, AgentRecord] = {}

    def register(self, agent: AgentRecord) -> AgentRecord:
        self._agents[agent.agent_id] = agent
        return agent

    def heartbeat(self, agent_id: str, heartbeat: HeartbeatPayload) -> AgentRecord:
        agent = self._agents[agent_id]
        agent.status = heartbeat.status
        agent.last_seen = heartbeat.last_seen
        agent.capabilities = heartbeat.capabilities
        return agent

    def list_agents(self) -> list[AgentRecord]:
        return list(self._agents.values())

    def get(self, agent_id: str) -> AgentRecord:
        return self._agents[agent_id]
