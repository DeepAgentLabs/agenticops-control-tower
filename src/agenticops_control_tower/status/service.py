"""Shared health and inventory rollups for the v0.2 operator surface."""

from __future__ import annotations

from agenticops_control_tower.discovery import CapabilityDiscoveryService
from agenticops_control_tower.models import (
    AgentRecord,
    AgentStatus,
    AgentStatusSummary,
    CapabilityCoverageRecord,
    FleetStatusSummary,
)


class StatusService:
    """Compute consistent status summaries for API and CLI consumers."""

    def __init__(self, discovery: CapabilityDiscoveryService) -> None:
        self._discovery = discovery

    def summarize_agent(self, agent: AgentRecord) -> AgentStatusSummary:
        return AgentStatusSummary(
            agent_id=agent.agent_id,
            name=agent.name,
            environment=agent.environment,
            runtime=agent.runtime,
            framework=agent.framework,
            status=agent.status,
            last_seen=agent.last_seen.isoformat() if agent.last_seen is not None else None,
            heartbeat_count=agent.heartbeat_count,
            capability_count=len(agent.capabilities),
            capabilities=dict(sorted(agent.capabilities.items())),
        )

    def summarize_fleet(self, agents: list[AgentRecord]) -> FleetStatusSummary:
        status_buckets = {
            status.value: sorted(agent.agent_id for agent in agents if agent.status is status)
            for status in AgentStatus
        }
        capability_inventory = self._discovery.list_capabilities(agents)
        capability_coverage = [
            self._build_coverage_record(
                capability.capability,
                capability.versions,
                capability.agent_ids,
                agents,
            )
            for capability in capability_inventory
        ]
        return FleetStatusSummary(
            total_agents=len(agents),
            healthy_agents=len(status_buckets[AgentStatus.HEALTHY.value]),
            degraded_agents=len(status_buckets[AgentStatus.DEGRADED.value]),
            unhealthy_agents=len(status_buckets[AgentStatus.UNHEALTHY.value]),
            unknown_agents=len(status_buckets[AgentStatus.UNKNOWN.value]),
            capability_count=len(capability_coverage),
            status_buckets=status_buckets,
            capabilities=capability_coverage,
        )

    def _build_coverage_record(
        self,
        capability: str,
        versions: list[str],
        installed_agent_ids: list[str],
        agents: list[AgentRecord],
    ) -> CapabilityCoverageRecord:
        all_agent_ids = sorted(agent.agent_id for agent in agents)
        missing_agent_ids = sorted(
            agent_id for agent_id in all_agent_ids if agent_id not in installed_agent_ids
        )
        return CapabilityCoverageRecord(
            capability=capability,
            installed_agents=len(installed_agent_ids),
            missing_agents=len(missing_agent_ids),
            versions=versions,
            agent_ids=installed_agent_ids,
            missing_agent_ids=missing_agent_ids,
        )
