"""Thin JSON artifact readers. No sibling runtime logic or imports required."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from agenticops_control_tower.adapters.evals_contract import validate_evals_artifact
from agenticops_control_tower.models.evidence import EvidenceLink, EvidenceSummary


class _Span(BaseModel):
    span_id: str = Field(min_length=1)
    name: str
    span_type: str
    tool_name: str | None = None
    status: Literal["running", "succeeded", "failed"] = "running"
    error_type: str | None = None


class _Run(BaseModel):
    schema_version: Literal["1.0"]
    run_id: str = Field(min_length=1)
    application_name: str
    status: Literal["running", "succeeded", "failed"]
    trace_id: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    task_success: bool | None = None
    error_type: str | None = None
    spans: list[_Span] = Field(default_factory=list)


class _DiagnosisTotals(BaseModel):
    total_diagnoses: int = Field(ge=0)
    unrecovered: int = Field(ge=0)
    highest_severity: Literal["low", "medium", "high", "critical"] | None = None
    categories: dict[str, int] = Field(default_factory=dict)
    failed_spans: int = Field(default=0, ge=0)


class _Attribution(BaseModel):
    status: Literal["attributed", "recovered", "unattributed", "no_failure"]
    faulty_span_id: str | None = None
    faulty_step: str | None = None
    faulty_agent: str | None = None
    category: str | None = None
    confidence: float = Field(default=0.0, ge=0, le=1)


class _Diagnosis(BaseModel):
    """AgenticLens 0.7.0+ `DiagnosisReport`; diagnoses, evidence and timeline stay in Lens."""

    schema_version: Literal["1.0", "1.1"]
    taxonomy_version: str
    engine_version: str
    run_id: str = Field(min_length=1)
    trace_id: str
    application_name: str
    run_status: Literal["running", "succeeded", "failed"]
    task_success: bool | None = None
    summary: _DiagnosisTotals
    attribution: _Attribution


class _JudgeTotals(BaseModel):
    """Evals 0.9.0+ `summary.judge`: what the judges cost and whether they answered."""

    judge_scores: int = Field(default=0, ge=0)
    unavailable_scores: int = Field(default=0, ge=0)
    unavailable_cases: list[str] = Field(default_factory=list)
    total_cost_usd: float | None = Field(default=None, ge=0)
    min_agreement: float | None = Field(default=None, ge=0, le=1)


class _LiveTotals(BaseModel):
    """Evals 0.9.0+ `summary.live`: target outages, kept apart from wrong answers."""

    retried_cases: int = Field(default=0, ge=0)
    timed_out_cases: int = Field(default=0, ge=0)
    error_cases: int = Field(default=0, ge=0)
    timed_out_case_ids: list[str] = Field(default_factory=list)
    error_case_ids: list[str] = Field(default_factory=list)


class _EvaluationTotals(BaseModel):
    total_cases: int = Field(ge=0)
    passed_cases: int = Field(ge=0)
    failed_cases: int = Field(ge=0)
    pass_rate: float = Field(ge=0, le=1)
    average_score: float = Field(ge=0, le=1)
    # Absent before Evals 0.9.0; projected as null rather than assumed healthy.
    judge: _JudgeTotals | None = None
    live: _LiveTotals | None = None


class _Evaluation(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    suite_name: str
    suite_version: str
    created_at: datetime | None = None
    summary: _EvaluationTotals


class _Gate(BaseModel):
    passed: bool
    reasons: list[str]
    observed: dict[str, float | int | None]


class _Decision(BaseModel):
    decision_id: str | None = Field(default=None, min_length=1)
    trigger_details: dict[str, Any] | None = None
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


ARTIFACT_TYPES: dict[str, str] = {
    "agenticlens": "run",
    "agentic-evals": "evaluation_report",
    "agentic-sidecar": "decision",
    "agentic-chaos": "chaos_report",
}
"""Default native artifact type per source."""

ACCEPTED_ARTIFACT_TYPES: dict[str, tuple[str, ...]] = {
    **{source: (artifact_type,) for source, artifact_type in ARTIFACT_TYPES.items()},
    "agenticlens": ("run", "diagnosis_report", "execution_bundle"),
}
"""Every native artifact type Tower reads per source."""


def artifact_type_for(source: str, artifact: dict[str, Any] | None) -> str:
    """The native type of `artifact`: Lens diagnosis reports carry `engine_version`."""
    if source == "agenticlens" and isinstance(artifact, dict) and "manifest" in artifact:
        return "execution_bundle"
    if source == "agenticlens" and isinstance(artifact, dict) and "engine_version" in artifact:
        return "diagnosis_report"
    return ARTIFACT_TYPES[source]


def _run_details(run: _Run) -> dict[str, Any]:
    """Keep correlation fields; span payloads, inputs and error messages stay in Lens."""
    details = run.model_dump(mode="json", exclude={"spans"})
    details["span_count"] = len(run.spans)
    details["tool_names"] = sorted({span.tool_name for span in run.spans if span.tool_name})
    details["failed_spans"] = [
        span.model_dump(mode="json", exclude={"status"})
        for span in run.spans
        if span.status == "failed"
    ]
    return details


def _diagnostic(error: ValidationError) -> str:
    """Name the first failing native field without echoing producer values."""
    first = error.errors(include_input=False)[0]
    location = ".".join(str(part) for part in first["loc"]) or "artifact"
    extra = f" (+{error.error_count() - 1} more)" if error.error_count() > 1 else ""
    return f"{location}: {first['msg']}{extra}"


def summarize_evidence(
    link: EvidenceLink,
    artifact: dict[str, Any] | None,
    *,
    gate: dict[str, Any] | None = None,
    trusted_lens_keys: dict[str, bytes] | None = None,
) -> EvidenceSummary:
    """Project validated producer fields, or return an honest unavailable result.

    `gate` must be an existing Evals GateDecision associated with this report;
    this reader does not run evaluators or recompute release policy.
    """
    if artifact is None:
        return EvidenceSummary(link=link, availability="unavailable", reason="No artifact supplied")
    if link.artifact_type not in ACCEPTED_ARTIFACT_TYPES[link.source]:
        return EvidenceSummary(link=link, availability="unavailable", reason="Source/type mismatch")
    if link.source == "agenticlens" and link.artifact_type == "execution_bundle":
        from agenticops_control_tower.adapters.lens_execution import summarize_execution

        if not link.run_id or link.spec_version not in (None, "0.4-draft"):
            return EvidenceSummary(
                link=link,
                availability="unavailable",
                reason="Execution evidence requires run_id and supported AIOS version",
            )
        execution_details = summarize_execution(
            artifact, trusted_keys=trusted_lens_keys or {}, expected_run_id=link.run_id
        )
        verified = execution_details["verification"]["status"] == "verified"
        return EvidenceSummary(
            link=link,
            availability="available" if verified else "unavailable",
            reason=None if verified else "Execution evidence is not verified",
            details=execution_details,
        )
    if link.spec_version is not None:
        return EvidenceSummary(
            link=link,
            availability="unavailable",
            reason="AIOS artifact ingestion is not implemented; native producer artifacts only",
        )
    try:
        details: dict[str, Any]
        if link.source == "agenticlens" and link.artifact_type == "diagnosis_report":
            diagnosis = _Diagnosis.model_validate(artifact)
            if link.run_id is not None and link.run_id != diagnosis.run_id:
                return EvidenceSummary(
                    link=link, availability="unavailable", reason="Run ID mismatch"
                )
            details = diagnosis.model_dump(mode="json")
        elif link.source == "agenticlens":
            run = _Run.model_validate(artifact)
            if link.run_id is not None and link.run_id != run.run_id:
                return EvidenceSummary(
                    link=link, availability="unavailable", reason="Run ID mismatch"
                )
            details = _run_details(run)
        elif link.source == "agentic-evals":
            validate_evals_artifact(artifact, "evaluation_report")
            if gate is not None:
                validate_evals_artifact(gate, "gate_decision")
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
    except ValidationError as exc:
        return EvidenceSummary(
            link=link,
            availability="unavailable",
            reason=f"Invalid or unsupported producer artifact: {_diagnostic(exc)}",
        )
    except ValueError as exc:
        return EvidenceSummary(link=link, availability="unavailable", reason=str(exc))
    return EvidenceSummary(link=link, availability="available", details=details)
