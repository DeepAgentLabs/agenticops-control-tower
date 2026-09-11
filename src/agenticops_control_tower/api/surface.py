"""Scaffold API over the registry: the v0.1 registration/heartbeat writes
plus the read-only inventory and capability surface."""

from __future__ import annotations

from agenticops_control_tower.discovery import CapabilityDiscoveryService
from agenticops_control_tower.models import AgentRecord, HeartbeatPayload
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

    def register(self, agent: AgentRecord) -> AgentRecord:
        return self._registry.register(agent)

    def heartbeat(self, agent_id: str, heartbeat: HeartbeatPayload) -> AgentRecord:
        return self._registry.heartbeat(agent_id, heartbeat)

    def list_agents(self) -> list[AgentRecord]:
        return self._registry.list_agents()

    def get_agent(self, agent_id: str) -> AgentRecord:
        return self._registry.get(agent_id)

    def list_capabilities(self, agent_id: str) -> dict[str, str]:
        return self._discovery.list_capabilities(self._registry.get(agent_id))

    def list_all_capabilities(self) -> dict[str, list[str]]:
        """Aggregate capability versions seen across every registered agent."""
        aggregated: dict[str, set[str]] = {}
        for agent in self._registry.list_agents():
            for name, version in self._discovery.list_capabilities(agent).items():
                aggregated.setdefault(name, set()).add(version)
        return {name: sorted(versions) for name, versions in sorted(aggregated.items())}
