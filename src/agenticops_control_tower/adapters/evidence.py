"""Thin JSON artifact readers. No sibling runtime logic or imports required."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from agenticops_control_tower.models.evidence import EvidenceLink, EvidenceSummary


class _Run(BaseModel):
    schema_version: Literal["1.0"]
    run_id: str = Field(min_length=1)
    application_name: str
    status: Literal["running", "succeeded", "failed"]


class _EvaluationTotals(BaseModel):
    total_cases: int = Field(ge=0)
    passed_cases: int = Field(ge=0)
    failed_cases: int = Field(ge=0)
    pass_rate: float = Field(ge=0, le=1)
    average_score: float = Field(ge=0, le=1)


class _Evaluation(BaseModel):
    schema_version: Literal["1.0"]
    suite_name: str
    suite_version: str
    created_at: datetime
    summary: _EvaluationTotals


class _Gate(BaseModel):
    passed: bool
    reasons: list[str]
    observed: dict[str, float | int | None]


class _Decision(BaseModel):
    status: Literal["ALLOW", "WARN", "BLOCK", "CHALLENGE", "REPLAN", "PAUSE", "ESCALATE"]
    risk: Literal["LOW", "MEDIUM", "HIGH"] | None
    reason: str
    decision_point: str | None = None
    escalation_required: bool = False
    causal_link: str | None = None


class _Chaos(BaseModel):
    id: str = Field(min_length=1)
    name: str
    start_time: datetime
    end_time: datetime | None = None
    chaos_events: list[dict[str, Any]]


_ARTIFACT_TYPES = {
    "agenticlens": "run",
    "agentic-evals": "evaluation_report",
    "agentic-sidecar": "decision",
    "agentic-chaos": "chaos_report",
}


def summarize_evidence(
    link: EvidenceLink,
    artifact: dict[str, Any] | None,
    *,
    gate: dict[str, Any] | None = None,
) -> EvidenceSummary:
    """Project validated producer fields, or return an honest unavailable result.

    `gate` must be an existing Evals GateDecision associated with this report;
    this reader does not run evaluators or recompute release policy.
    """
    if artifact is None:
        return EvidenceSummary(link=link, availability="unavailable", reason="No artifact supplied")
    if link.artifact_type != _ARTIFACT_TYPES[link.source]:
        return EvidenceSummary(link=link, availability="unavailable", reason="Source/type mismatch")
    if link.spec_version is not None:
        return EvidenceSummary(
            link=link,
            availability="unavailable",
            reason="AIOS artifact ingestion is not implemented; native producer artifacts only",
        )
    try:
        details: dict[str, Any]
        if link.source == "agenticlens":
            run = _Run.model_validate(artifact)
            if link.run_id is not None and link.run_id != run.run_id:
                return EvidenceSummary(
                    link=link, availability="unavailable", reason="Run ID mismatch"
                )
            details = run.model_dump(mode="json")
        elif link.source == "agentic-evals":
            report = _Evaluation.model_validate(artifact)
            details = report.model_dump(mode="json")
            details["gate"] = _Gate.model_validate(gate).model_dump() if gate is not None else None
        elif link.source == "agentic-sidecar":
            details = _Decision.model_validate(artifact).model_dump(mode="json")
        else:
            chaos = _Chaos.model_validate(artifact)
            details = {
                "id": chaos.id,
                "name": chaos.name,
                "start_time": chaos.start_time.isoformat(),
                "end_time": chaos.end_time.isoformat() if chaos.end_time else None,
                "event_count": len(chaos.chaos_events),
                "completed": chaos.end_time is not None,
            }
    except ValidationError:
        return EvidenceSummary(
            link=link,
            availability="unavailable",
            reason="Invalid or unsupported producer artifact",
        )
    return EvidenceSummary(link=link, availability="available", details=details)
