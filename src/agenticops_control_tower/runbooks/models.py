"""Tower-local versioned runbook contracts (not AIOS schemas).

Definitions are host-installed data. Callers choose a catalog entry and supply
bounded string parameters; they never supply commands, endpoints, credentials or steps.
"""

from __future__ import annotations

import re
from hashlib import sha256
from typing import Literal

from pydantic import AwareDatetime, Field, field_validator, model_validator

from agenticops_control_tower.config.models import Contract

_IDENTIFIER = r"^[a-z][a-z0-9_.-]{0,99}$"
_VERSION = r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$"
MAX_RUNBOOK_SECONDS = 120

Prerequisite = Literal[
    "incident.open",
    "incident.investigated",
    "investigation.not_contradictory",
    "connector.installed",
]
DEFAULT_PREREQUISITES: tuple[Prerequisite, ...] = (
    "incident.open",
    "incident.investigated",
    "investigation.not_contradictory",
    "connector.installed",
)
StepOutcome = Literal[
    "pending", "succeeded", "failed", "partial_failure", "timed_out", "unknown", "skipped"
]
RollbackOutcome = Literal[
    "not_declared", "not_needed", "succeeded", "failed", "partial_failure", "timed_out"
]


class ParameterSpec(Contract):
    """Bounded string parameter; connectors still apply their own allowlists."""

    description: str = Field(min_length=1, max_length=500)
    pattern: str = Field(default=r"^[A-Za-z0-9_.-]{1,100}$", max_length=200)
    allowed: list[str] | None = Field(default=None, min_length=1, max_length=100)
    max_length: int = Field(default=100, ge=1, le=1000)

    @field_validator("pattern")
    @classmethod
    def compiles(cls, value: str) -> str:
        re.compile(value)
        return value

    def accepts(self, value: str) -> bool:
        return (
            len(value) <= self.max_length
            and bool(re.fullmatch(self.pattern, value))
            and (self.allowed is None or value in self.allowed)
        )


class RunbookStep(Contract):
    step_id: str = Field(pattern=_IDENTIFIER)
    action: str = Field(pattern=_IDENTIFIER)
    description: str = Field(min_length=1, max_length=500)
    timeout_seconds: int = Field(default=5, ge=1, le=30)
    # Retries apply only to a connector-reported clean failure (no side effects).
    max_attempts: int = Field(default=1, ge=1, le=3)
    rollback_action: str | None = Field(default=None, pattern=_IDENTIFIER)
    rollback_timeout_seconds: int = Field(default=5, ge=1, le=30)


class RecoveryCriteria(Contract):
    """Fixed evidence criteria; Tower never computes Lens or Evals outcomes."""

    connector_probe: Literal[True] = True
    lens_run_succeeded: Literal[True] = True
    evals_gate_passed: Literal[True] = True
    freshness_seconds: int = Field(default=300, ge=1, le=3600)


class RunbookDefinition(Contract):
    runbook_id: str = Field(pattern=_IDENTIFIER)
    version: str = Field(pattern=_VERSION)
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=2000)
    environments: list[str] = Field(min_length=1, max_length=20)
    prerequisites: list[Prerequisite] = Field(
        default_factory=lambda: list(DEFAULT_PREREQUISITES), max_length=4
    )
    parameters: dict[str, ParameterSpec] = Field(default_factory=dict, max_length=20)
    steps: list[RunbookStep] = Field(min_length=1, max_length=10)
    impact: str = Field(min_length=1, max_length=1000)
    rollback: str = Field(min_length=1, max_length=1000)
    recovery: RecoveryCriteria = Field(default_factory=RecoveryCriteria)

    @model_validator(mode="after")
    def bounded(self) -> RunbookDefinition:
        if len({s.step_id for s in self.steps}) != len(self.steps):
            raise ValueError("Step IDs must be unique")
        for name in self.parameters:
            if not re.fullmatch(r"[a-z][a-z0-9_]{0,49}", name):
                raise ValueError("Parameter names must be lowercase identifiers")
        if self.budget_seconds() > MAX_RUNBOOK_SECONDS:
            raise ValueError(f"Worst-case runbook duration exceeds {MAX_RUNBOOK_SECONDS} seconds")
        return self

    def budget_seconds(self) -> int:
        """Worst-case connector time: every attempt plus every declared rollback."""
        return sum(
            s.timeout_seconds * s.max_attempts
            + (s.rollback_timeout_seconds if s.rollback_action else 0)
            for s in self.steps
        )

    def digest(self) -> str:
        return sha256(self.model_dump_json().encode()).hexdigest()


class RunbookRecommendation(Contract):
    runbook_id: str
    version: str
    definition_digest: str
    title: str
    eligible: bool
    unmet: list[str]
    parameters: dict[str, ParameterSpec]
    validation: Literal["validated", "unvalidated"]
    validation_ids: list[str]


class RunbookValidation(Contract):
    """Recorded Chaos scenario and Evals result; both engines stay in their packages."""

    validation_id: str
    runbook_id: str
    version: str
    definition_digest: str
    agent_id: str
    environment: str
    chaos_evidence_id: str
    evals_evidence_id: str
    run_id: str
    recorded_by: str
    recorded_at: AwareDatetime


class StepResult(Contract):
    step_id: str
    action: str
    attempts: int = 0
    outcome: StepOutcome = "pending"
    rollback: RollbackOutcome = "not_declared"
    started_at: AwareDatetime | None = None
    finished_at: AwareDatetime | None = None
    detail: str = ""


class RunbookEvent(Contract):
    at: AwareDatetime
    event: str
    operator_id: str
    detail: str = ""


ExecutionStatus = Literal[
    "pending",
    "approved",
    "denied",
    "revoked",
    "running",
    "awaiting_verification",
    "resolved",
    "escalated",
    "cancelled",
    "reconciliation_required",
]


class RunbookExecution(Contract):
    execution_id: str
    incident_id: str
    agent_id: str
    environment: str
    runbook_id: str
    version: str
    definition: RunbookDefinition
    definition_digest: str
    parameters: dict[str, str]
    preview_digest: str
    expires_at: AwareDatetime
    status: ExecutionStatus = "pending"
    proposed_by: str
    approved_by: str | None = None
    executed_by: str | None = None
    cancel_requested_by: str | None = None
    started_at: AwareDatetime | None = None
    lease_expires_at: AwareDatetime | None = None
    steps: list[StepResult]
    evidence_ids: list[str] = Field(default_factory=list)
    verification: dict[str, str | bool] = Field(default_factory=dict)
    events: list[RunbookEvent] = Field(default_factory=list)
    reconciliation: str = (
        "Steps are not atomic. Clean failures and cancellation compensate completed steps "
        "with declared rollback actions in reverse order. Partial, timed-out or unknown "
        "outcomes stop the runbook without automatic rollback and require host "
        "reconciliation; Tower never replays a dispatched step."
    )


class RunbookPreviewRequest(Contract):
    runbook_id: str = Field(min_length=1, max_length=100)
    version: str = Field(pattern=_VERSION)
    parameters: dict[str, str] = Field(default_factory=dict, max_length=20)
    expires_in_seconds: int = Field(default=300, ge=1, le=3600)


class RunbookDecisionRequest(Contract):
    preview_digest: str = Field(min_length=64, max_length=64)
    approved: bool


class RunbookExecuteRequest(Contract):
    preview_digest: str = Field(min_length=64, max_length=64)


class RunbookVerificationRequest(Contract):
    lens_evidence_id: str = Field(min_length=1)
    evals_evidence_id: str = Field(min_length=1)


class RunbookValidationRequest(Contract):
    agent_id: str = Field(min_length=1)
    chaos_evidence_id: str = Field(min_length=1)
    evals_evidence_id: str = Field(min_length=1)
