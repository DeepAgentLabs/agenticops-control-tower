"""Control-plane API over the v0.2 in-memory registry."""

from __future__ import annotations

from agenticops_control_tower.discovery import CapabilityDiscoveryService
from agenticops_control_tower.models import (
    AgentRecord,
    AgentRegistrationPayload,
    AgentStatus,
    AgentStatusSummary,
    CapabilityInventoryRecord,
    FleetStatusSummary,
    HeartbeatPayload,
)
from agenticops_control_tower.registry import AgentRegistry
from agenticops_control_tower.status import StatusService


class ControlTowerAPI:
    """Small facade that mirrors the roadmap's initial control-plane surface."""

    def __init__(
        self,
        registry: AgentRegistry,
        discovery: CapabilityDiscoveryService,
        status_service: StatusService | None = None,
    ) -> None:
        self._registry = registry
        self._discovery = discovery
        self._status_service = status_service or StatusService(discovery)

    def register_agent(self, registration: AgentRegistrationPayload) -> AgentRecord:
        return self._registry.register(registration)

    def record_heartbeat(self, agent_id: str, heartbeat: HeartbeatPayload) -> AgentRecord:
        return self._registry.heartbeat(agent_id, heartbeat)

    def list_agents(
        self,
        *,
        status: AgentStatus | None = None,
        environment: str | None = None,
        capability: str | None = None,
        missing_capability: str | None = None,
    ) -> list[AgentRecord]:
        agents = self._registry.list_agents()
        if status is not None:
            agents = [agent for agent in agents if agent.status is status]
        if environment is not None:
            agents = [agent for agent in agents if agent.environment == environment]
        if capability is not None:
            agents = [agent for agent in agents if capability in agent.capabilities]
        if missing_capability is not None:
            agents = [agent for agent in agents if missing_capability not in agent.capabilities]
        return agents

    def get_agent(self, agent_id: str) -> AgentRecord:
        return self._registry.get(agent_id)

    def list_capabilities(self) -> list[CapabilityInventoryRecord]:
        return self._discovery.list_capabilities(self._registry.list_agents())

    def get_agent_capabilities(self, agent_id: str) -> dict[str, str]:
        return self._discovery.list_agent_capabilities(self._registry.get(agent_id))

    def get_status(self, agent_id: str | None = None) -> FleetStatusSummary | AgentStatusSummary:
        if agent_id is not None:
            return self._status_service.summarize_agent(self._registry.get(agent_id))
        return self._status_service.summarize_fleet(self._registry.list_agents())
