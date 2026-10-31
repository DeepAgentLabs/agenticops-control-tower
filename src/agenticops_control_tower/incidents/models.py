"""Tower-local incident and exact-preview approval contracts (not AIOS schemas)."""

from typing import Literal

from pydantic import AwareDatetime, Field

from agenticops_control_tower.config.models import Contract
from agenticops_control_tower.models.evidence import EvidenceRecord


class DetectionRequest(Contract):
    agent_id: str = Field(min_length=1)
    evidence_id: str = Field(min_length=1)


class Investigation(Contract):
    finding: str
    certainty: Literal["observed_failure", "hypothesis", "contradictory"]
    citations: list[str]
    missing: list[str]
    timeline: list[EvidenceRecord]


class RecoveryPlan(Contract):
    runbook: Literal["staging.restore_dependency.v1"] = "staging.restore_dependency.v1"
    agent_id: str
    environment: Literal["staging"] = "staging"
    dependency: str = Field(min_length=1, max_length=100)
    timeout_seconds: int = Field(default=5, ge=1, le=30)
    max_attempts: Literal[1] = 1
    prerequisites: list[str] = Field(
        default_factory=lambda: [
            "Explicitly installed bounded staging connector",
            "Failed native Lens run",
        ]
    )
    impact: str = "Restore one allowlisted staging dependency; no fleet changes"
    rollback: str = "Connector reports partial failure; reconcile manually before another action"
    recovery: str = "Successful probe plus fresh same-run Lens success and passing Evals gate"


class TimelineEvent(Contract):
    at: AwareDatetime
    event: str
    operator_id: str
    detail: str = ""


class Incident(Contract):
    incident_id: str
    agent_id: str
    detection: EvidenceRecord
    state: Literal["open", "executing", "awaiting_verification", "resolved", "escalated"] = "open"
    investigation: Investigation | None = None
    plan: RecoveryPlan | None = None
    # Set once a versioned runbook is previewed; the single-action plan is then closed.
    runbook_execution_id: str | None = None
    preview_digest: str | None = None
    expires_at: AwareDatetime | None = None
    approval: Literal["pending", "approved", "denied", "revoked", "consumed"] = "pending"
    proposed_by: str | None = None
    approved_by: str | None = None
    execution_started_at: AwareDatetime | None = None
    outcome: Literal["succeeded", "failed", "partial_failure", "unknown"] | None = None
    events: list[TimelineEvent] = Field(default_factory=list)


class PlanRequest(Contract):
    dependency: str = Field(min_length=1, max_length=100)
    expires_in_seconds: int = Field(default=300, ge=1, le=3600)


class DecisionRequest(Contract):
    preview_digest: str
    approved: bool


class ExecuteRequest(Contract):
    preview_digest: str


class VerificationRequest(Contract):
    lens_evidence_id: str
    evals_evidence_id: str
