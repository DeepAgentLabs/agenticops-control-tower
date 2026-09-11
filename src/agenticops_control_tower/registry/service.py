"""In-memory registry for v0.1 registration and heartbeat flows."""

from __future__ import annotations

from agenticops_control_tower.errors import AgentNotFoundError
from agenticops_control_tower.models import AgentRecord, AgentRegistrationPayload, HeartbeatPayload


class AgentRegistry:
    """Small runtime-agnostic in-memory registry for known agents."""

    def __init__(self) -> None:
        self._agents: dict[str, AgentRecord] = {}

    def register(self, registration: AgentRegistrationPayload) -> AgentRecord:
        agent = AgentRecord(
            agent_id=registration.agent_id,
            name=registration.name,
            environment=registration.environment,
            runtime=registration.runtime,
            framework=registration.framework,
            status=registration.status,
            capabilities=dict(sorted(registration.capabilities.items())),
            runtime_metadata=dict(sorted(registration.runtime_metadata.items())),
            package_metadata=dict(sorted(registration.package_metadata.items())),
            registered_at=registration.registered_at,
            last_seen=registration.registered_at,
        )
        self._agents[agent.agent_id] = agent
        return agent

    def heartbeat(self, agent_id: str, heartbeat: HeartbeatPayload) -> AgentRecord:
        agent = self.get(agent_id)
        agent.status = heartbeat.status
        agent.last_seen = heartbeat.last_seen
        agent.capabilities.update(heartbeat.capabilities)
        agent.runtime_metadata.update(heartbeat.runtime_metadata)
        agent.package_metadata.update(heartbeat.package_metadata)
        agent.capabilities = dict(sorted(agent.capabilities.items()))
        agent.runtime_metadata = dict(sorted(agent.runtime_metadata.items()))
        agent.package_metadata = dict(sorted(agent.package_metadata.items()))
        agent.heartbeat_count += 1
        return agent

    def list_agents(self) -> list[AgentRecord]:
        return [self._agents[agent_id] for agent_id in sorted(self._agents)]

    def get(self, agent_id: str) -> AgentRecord:
        try:
            return self._agents[agent_id]
        except KeyError as exc:
            raise AgentNotFoundError(agent_id) from exc
