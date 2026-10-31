"""Scaffold API over the registry: the v0.1 registration/heartbeat writes
plus the read-only inventory and capability surface."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from packaging.version import InvalidVersion, Version

from agenticops_control_tower.adapters.evidence import summarize_evidence
from agenticops_control_tower.bulk import BulkService
from agenticops_control_tower.config.service import ConfigurationService
from agenticops_control_tower.discovery import CapabilityDiscoveryService
from agenticops_control_tower.evidence import (
    DEFAULT_STALE_AFTER_SECONDS,
    EvidenceStore,
    PostureService,
)
from agenticops_control_tower.incidents import IncidentService
from agenticops_control_tower.models import (
    AgentRecord,
    AgentRegistrationPayload,
    AgentStatus,
    CapabilityInventoryRecord,
    FleetStatusSummary,
    HeartbeatPayload,
)
from agenticops_control_tower.models.evidence import (
    AgentEvidencePosture,
    EvidenceIngestRequest,
    EvidenceIngestResult,
    EvidenceLink,
    EvidenceRecord,
    EvidenceSource,
    EvidenceSummary,
    FleetEvidencePosture,
)
from agenticops_control_tower.models.version import VersionAssessment
from agenticops_control_tower.operations import OperationsService
from agenticops_control_tower.registry import AgentRegistry
from agenticops_control_tower.runbooks import RunbookService
from agenticops_control_tower.status import StatusService


class ControlTowerAPI:
    """Small facade that mirrors the roadmap's initial control-plane surface."""

    def __init__(
        self,
        registry: AgentRegistry,
        discovery: CapabilityDiscoveryService,
        status_service: StatusService | None = None,
        configuration_service: ConfigurationService | None = None,
        evidence_store: EvidenceStore | None = None,
        incident_service: IncidentService | None = None,
        runbook_service: RunbookService | None = None,
    ) -> None:
        self.config = configuration_service or ConfigurationService(registry)
        self.bulk = BulkService(self.config)
        self.evidence = evidence_store or EvidenceStore(registry)
        self.incidents = incident_service or IncidentService(registry, self.evidence)
        if runbook_service is not None and runbook_service.incidents is not self.incidents:
            raise ValueError("Runbook service must share the API's incident service")
        self.runbooks = runbook_service or RunbookService(self.incidents)
        self._posture = PostureService(self.evidence)
        self._registry = registry
        self._discovery = discovery
        self._status_service = status_service or StatusService(discovery)
        self.operations = OperationsService(self)

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
        artifacts return unavailable. Nothing is persisted; use ingest_evidence
        to record history and posture.
        """
        self._registry.get(link.agent_id)
        return summarize_evidence(link, artifact, gate=gate)

    def ingest_evidence(
        self, request: EvidenceIngestRequest, *, ingested_by: str = "python"
    ) -> EvidenceIngestResult:
        """Persist an attributed projection; retries of one observation are idempotent."""
        return self.evidence.ingest(request, ingested_by=ingested_by)

    def evidence_history(
        self,
        agent_id: str,
        *,
        source: EvidenceSource | None = None,
        limit: int | None = 50,
    ) -> list[EvidenceRecord]:
        return self.evidence.history(agent_id, source=source, limit=limit)

    def agent_posture(
        self,
        agent_id: str,
        *,
        stale_after_seconds: int = DEFAULT_STALE_AFTER_SECONDS,
        now: datetime | None = None,
    ) -> AgentEvidencePosture:
        """Per-source evidence posture; reported health is included, never derived."""
        return self._posture.agent(
            self._registry.get(agent_id), now=now, stale_after_seconds=stale_after_seconds
        )

    def fleet_posture(
        self,
        *,
        environment: str | None = None,
        stale_after_seconds: int = DEFAULT_STALE_AFTER_SECONDS,
        now: datetime | None = None,
    ) -> FleetEvidencePosture:
        return self._posture.fleet(
            self.list_agents(environment=environment),
            environment=environment,
            now=now,
            stale_after_seconds=stale_after_seconds,
        )

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
