"""Control Tower-local evidence links; these are not normative AIOS objects."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, get_args

from pydantic import BaseModel, Field

from .agent import AgentStatus

EvidenceSource = Literal["agenticlens", "agentic-evals", "agentic-sidecar", "agentic-chaos"]
EVIDENCE_SOURCES: tuple[EvidenceSource, ...] = get_args(EvidenceSource)
EvidenceFreshness = Literal["fresh", "stale", "missing"]


class EvidenceLink(BaseModel):
    """Explicit attribution of a producer artifact to a registered deployment."""

    contract_version: Literal["1.0"] = "1.0"
    agent_id: str = Field(min_length=1)
    source: EvidenceSource
    source_version: str = Field(min_length=1)
    artifact_type: Literal[
        "run",
        "diagnosis_report",
        "execution_bundle",
        "evaluation_report",
        "decision",
        "chaos_report",
    ]
    artifact_ref: str = Field(min_length=1)
    observed_at: datetime
    run_id: str | None = None
    runtime_agent_id: str | None = None
    spec_version: str | None = None


class EvidenceSummary(BaseModel):
    """Source-specific outcomes, kept separate from fleet health."""

    link: EvidenceLink
    availability: Literal["available", "unavailable"]
    reason: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class EvidenceIngestRequest(BaseModel):
    """A native producer artifact pushed to Tower with explicit attribution."""

    link: EvidenceLink
    artifact: dict[str, Any] | None = None
    gate: dict[str, Any] | None = None


class EvidenceRecord(BaseModel):
    """A persisted projection; Tower never stores the raw producer artifact."""

    record_id: str
    ingested_at: datetime
    ingested_by: str
    summary: EvidenceSummary


class EvidenceIngestResult(BaseModel):
    """`created` is false when the same attributed observation was already stored."""

    record: EvidenceRecord
    created: bool


class SourcePosture(BaseModel):
    """Latest and recent evidence from one producer for one deployment."""

    source: EvidenceSource
    freshness: EvidenceFreshness
    reason: str | None = None
    latest: EvidenceRecord | None = None
    recent_records: int = 0
    recent_unavailable: int = 0
    summary: dict[str, Any] = Field(default_factory=dict)


class AgentEvidencePosture(BaseModel):
    """Evidence posture for one deployment; reported health is shown, never derived."""

    agent_id: str
    environment: str
    reported_health: AgentStatus
    evaluated_at: datetime
    stale_after_seconds: int
    sources: list[SourcePosture]


class FleetSourcePosture(BaseModel):
    """Per-producer evidence coverage across deployments."""

    source: EvidenceSource
    fresh_agents: list[str] = Field(default_factory=list)
    stale_agents: list[str] = Field(default_factory=list)
    missing_agents: list[str] = Field(default_factory=list)
    latest_unavailable_agents: list[str] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)


class FleetEvidencePosture(BaseModel):
    """Fleet-wide evidence posture, independent of the fleet health rollup."""

    evaluated_at: datetime
    environment: str | None = None
    stale_after_seconds: int
    total_agents: int
    sources: list[FleetSourcePosture]
