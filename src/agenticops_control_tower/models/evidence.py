"""Control Tower-local evidence links; these are not normative AIOS objects."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

EvidenceSource = Literal["agenticlens", "agentic-evals", "agentic-sidecar", "agentic-chaos"]


class EvidenceLink(BaseModel):
    """Explicit attribution of a producer artifact to a registered deployment."""

    contract_version: Literal["1.0"] = "1.0"
    agent_id: str = Field(min_length=1)
    source: EvidenceSource
    source_version: str = Field(min_length=1)
    artifact_type: Literal["run", "evaluation_report", "decision", "chaos_report"]
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
