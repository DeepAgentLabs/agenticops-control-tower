"""Capability discovery helpers for the v0.1 control-plane surface.

The real implementation will likely combine explicit agent-reported metadata
with adapter-assisted discovery. For now this module only exposes a normalized
view over an agent's reported capabilities.
"""

from __future__ import annotations

from agenticops_control_tower.models import AgentRecord, CapabilityInventoryRecord


class CapabilityDiscoveryService:
    """Normalize per-agent and cross-agent capability inventory."""

    def list_agent_capabilities(self, agent: AgentRecord) -> dict[str, str]:
        return dict(sorted(agent.capabilities.items()))

    def list_capabilities(
        self,
        agents: list[AgentRecord],
    ) -> list[CapabilityInventoryRecord]:
        capability_index: dict[str, dict[str, set[str]]] = {}

        for agent in agents:
            for capability, version in agent.capabilities.items():
                versions = capability_index.setdefault(capability, {})
                agent_ids = versions.setdefault(version, set())
                agent_ids.add(agent.agent_id)

        inventory: list[CapabilityInventoryRecord] = []
        for capability in sorted(capability_index):
            version_map = capability_index[capability]
            sorted_versions = sorted(version_map)
            sorted_agent_ids = sorted(
                agent_id
                for per_version_agents in version_map.values()
                for agent_id in per_version_agents
            )
            inventory.append(
                CapabilityInventoryRecord(
                    capability=capability,
                    versions=sorted_versions,
                    agent_ids=sorted_agent_ids,
                )
            )

        return inventory
