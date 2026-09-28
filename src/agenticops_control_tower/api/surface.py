"""Scaffold API over the registry: the v0.1 registration/heartbeat writes
plus the read-only inventory and capability surface."""

from __future__ import annotations

from agenticops_control_tower.discovery import CapabilityDiscoveryService
from agenticops_control_tower.models import (
    AgentRecord,
    AgentRegistrationPayload,
    AgentStatus,
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

    def register_agent(
        self,
        registration: AgentRegistrationPayload,
    ) -> AgentRecord:
        return self._registry.register(registration)

    def record_heartbeat(
        self,
        agent_id: str,
        heartbeat: HeartbeatPayload,
    ) -> AgentRecord:
        return self._registry.heartbeat(agent_id, heartbeat)

    def list_agents(
        self,
        status: AgentStatus | None = None,
        environment: str | None = None,
        capability: str | None = None,
        missing_capability: str | None = None,
    ) -> list[AgentRecord]:
        agents = self._registry.list_agents()

        if status is not None:
            agents = [agent for agent in agents if agent.status is status]

        if environment is not None:
            agents = [
                agent for agent in agents if agent.environment == environment
            ]

        if capability is not None:
            agents = [
                agent for agent in agents if capability in agent.capabilities
            ]

        if missing_capability is not None:
            agents = [
                agent
                for agent in agents
                if missing_capability not in agent.capabilities
            ]

        return agents

    def get_status(self) -> FleetStatusSummary:
        return self._status_service.summarize_fleet(
            self._registry.list_agents()
        )

    def get_agent(self, agent_id: str) -> AgentRecord:
        return self._registry.get(agent_id)

    def get_agent_capabilities(self, agent_id: str) -> dict[str, str]:
        return self._discovery.list_agent_capabilities(
            self._registry.get(agent_id)
        )

    def list_capabilities(self) -> list[CapabilityInventoryRecord]:
        return self._discovery.list_capabilities(
            self._registry.list_agents()
        )

    def list_all_capabilities(self) -> dict[str, list[str]]:
        """Aggregate capability versions seen across every registered agent."""
        inventory = self._discovery.list_capabilities(self._registry.list_agents())

        return {item.capability: item.versions for item in inventory}
