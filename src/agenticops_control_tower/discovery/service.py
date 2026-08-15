"""Capability discovery scaffold.

The real implementation will likely combine explicit agent-reported metadata
with adapter-assisted discovery. For now this module only exposes a normalized
view over an agent's reported capabilities.
"""

from __future__ import annotations

from agenticops_control_tower.models import AgentRecord


class CapabilityDiscoveryService:
    """Scaffold normalization for capability inventory."""

    def list_capabilities(self, agent: AgentRecord) -> dict[str, str]:
        return dict(sorted(agent.capabilities.items()))
