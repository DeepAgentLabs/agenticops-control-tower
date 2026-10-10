"""Scaffold API over the registry: the v0.1 registration/heartbeat writes
plus the read-only inventory and capability surface."""

from __future__ import annotations

from typing import Any

from packaging.version import InvalidVersion, Version

from agenticops_control_tower.adapters.evidence import summarize_evidence
from agenticops_control_tower.discovery import CapabilityDiscoveryService
from agenticops_control_tower.models import (
    AgentRecord,
    AgentRegistrationPayload,
    AgentStatus,
    CapabilityInventoryRecord,
    FleetStatusSummary,
    HeartbeatPayload,
)
from agenticops_control_tower.models.evidence import EvidenceLink, EvidenceSummary
from agenticops_control_tower.models.version import VersionAssessment
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

    def register(self, agent: AgentRegistrationPayload | AgentRecord) -> AgentRecord:
        return self._registry.register(AgentRegistrationPayload.model_validate(agent.model_dump()))

    def heartbeat(self, agent_id: str, heartbeat: HeartbeatPayload) -> AgentRecord:
        return self._registry.heartbeat(agent_id, heartbeat)

    def list_agents(
        self,
        *,
        status: AgentStatus | None = None,
        environment: str | None = None,
        capability: str | None = None,
        missing_capability: str | None = None,
    ) -> list[AgentRecord]:
        return [
            agent
            for agent in self._registry.list_agents()
            if (status is None or agent.status == status)
            and (environment is None or agent.environment == environment)
            and (capability is None or capability in agent.capabilities)
            and (missing_capability is None or missing_capability not in agent.capabilities)
        ]

    register_agent = register
    record_heartbeat = heartbeat

    def get_status(self, *, environment: str | None = None) -> FleetStatusSummary:
        return self._status_service.summarize_fleet(self.list_agents(environment=environment))

    def get_agent(self, agent_id: str) -> AgentRecord:
        return self._registry.get(agent_id)

    def get_agent_capabilities(self, agent_id: str) -> dict[str, str]:
        return self._discovery.list_agent_capabilities(self._registry.get(agent_id))

    def list_capabilities(self) -> list[CapabilityInventoryRecord]:
        return self._discovery.list_capabilities(self.list_agents())

    def list_all_capabilities(self) -> dict[str, list[str]]:
        """Aggregate capability versions seen across every registered agent."""
        aggregated: dict[str, set[str]] = {}
        for agent in self._registry.list_agents():
            for name, version in self._discovery.list_agent_capabilities(agent).items():
                aggregated.setdefault(name, set()).add(version)
        return {name: sorted(versions) for name, versions in sorted(aggregated.items())}

    def summarize_evidence(
        self,
        link: EvidenceLink,
        artifact: dict[str, Any] | None,
        *,
        gate: dict[str, Any] | None = None,
    ) -> EvidenceSummary:
        """Read attributed evidence without changing inventory or health.

        Unknown deployment IDs raise AgentNotFoundError. Missing or invalid
        artifacts return unavailable. No evidence is persisted by this method.
        """
        self._registry.get(link.agent_id)
        return summarize_evidence(link, artifact, gate=gate)

    def assess_versions(
        self, capability: str, minimum_version: str, *, environment: str | None = None
    ) -> list[VersionAssessment]:
        """Compare PEP 440 versions with an explicit operator minimum."""
        minimum = Version(minimum_version)
        results: list[VersionAssessment] = []
        for agent in self.list_agents(environment=environment):
            installed = agent.capabilities.get(capability)
            result = VersionAssessment(
                agent_id=agent.agent_id,
                capability=capability,
                installed_version=installed,
                minimum_version=minimum_version,
                assessment="missing",
            )
            if installed is not None:
                try:
                    result.assessment = (
                        "outdated" if Version(installed) < minimum else "meets_minimum"
                    )
                except InvalidVersion:
                    result.assessment = "unknown"
                    result.reason = "Reported version is not a valid PEP 440 version"
            results.append(result)
        return results
