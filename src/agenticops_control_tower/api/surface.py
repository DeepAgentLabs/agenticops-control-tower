"""Read-only scaffold API over the registry."""

from __future__ import annotations

from agenticops_control_tower.discovery import CapabilityDiscoveryService
from agenticops_control_tower.models import AgentRecord
from agenticops_control_tower.registry import AgentRegistry


class ControlTowerAPI:
    """Small facade that mirrors the v0.1 roadmap surface."""

    def __init__(
        self,
        registry: AgentRegistry,
        discovery: CapabilityDiscoveryService,
    ) -> None:
        self._registry = registry
        self._discovery = discovery

    def list_agents(self) -> list[AgentRecord]:
        return self._registry.list_agents()

    def get_agent(self, agent_id: str) -> AgentRecord:
        return self._registry.get(agent_id)

    def list_capabilities(self, agent_id: str) -> dict[str, str]:
        return self._discovery.list_capabilities(self._registry.get(agent_id))
