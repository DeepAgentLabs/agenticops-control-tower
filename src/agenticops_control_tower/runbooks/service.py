"""Approved, bounded, durable runbook execution; recovery needs verified evidence.

Storage shares the incident transaction so execution and incident timelines change
together. Every step is claimed and committed before dispatch, so a crash cannot
replay a step: interrupted executions become `reconciliation_required`.
"""

from __future__ import annotations

import builtins
import json
import sqlite3
from collections.abc import Callable, Mapping
from datetime import timedelta
from hashlib import sha256
from queue import Empty, Queue
from threading import BoundedSemaphore, Thread
from typing import Literal, TypeVar
from uuid import uuid4

from agenticops_control_tower.config.models import Operator
from agenticops_control_tower.incidents.models import Incident
from agenticops_control_tower.incidents.service import IncidentError, IncidentService, utcnow
from agenticops_control_tower.runbooks.catalog import CatalogError, RunbookCatalog
from agenticops_control_tower.runbooks.connectors import RunbookConnector
from agenticops_control_tower.runbooks.models import (
    RunbookDefinition,
    RunbookEvent,
    RunbookExecution,
    RunbookPreviewRequest,
    RunbookRecommendation,
    RunbookValidation,
    RunbookValidationRequest,
    StepResult,
)

_DISPATCH_SLOTS = BoundedSemaphore(16)
LEASE_SLACK_SECONDS = 30
PROBE_TIMEOUT_SECONDS = 5
T = TypeVar("T")
Dispatch = Literal["succeeded", "failed", "partial_failure", "timed_out", "unknown"]


class RunbookError(IncidentError):
    """Unauthorized, unsupported or out-of-order runbook transition."""


def _bounded(
    call: Callable[[], T], timeout: float
) -> tuple[Literal["ok", "raised", "timeout", "busy"], T | None]:
    """Wait at most `timeout` seconds; a late callback may still finish in its thread."""
    if not _DISPATCH_SLOTS.acquire(blocking=False):
        return "busy", None
    queue: Queue[tuple[Literal["ok", "raised"], T | None]] = Queue(maxsize=1)

    def target() -> None:
        try:
            try:
                queue.put(("ok", call()))
            except Exception:
                # Connector exception text may contain credentials; never record it.
                queue.put(("raised", None))
        finally:
            _DISPATCH_SLOTS.release()

    Thread(target=target, daemon=True).start()
    try:
        return queue.get(timeout=timeout)
    except Empty:
        return "timeout", None


class RunbookService:
    def __init__(
        self,
        incidents: IncidentService,
        catalog: RunbookCatalog | None = None,
        connectors: dict[str, RunbookConnector] | None = None,
    ) -> None:
        self.incidents = incidents
        self.catalog = catalog or RunbookCatalog()
        self.connectors = dict(connectors or {})
        with incidents._transaction() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS tower_runbook_executions "
                "(id TEXT PRIMARY KEY, incident_id TEXT NOT NULL, body TEXT NOT NULL)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS tower_runbook_validations "
                "(id TEXT PRIMARY KEY, runbook_id TEXT NOT NULL, version TEXT NOT NULL, "
                "body TEXT NOT NULL)"
            )

    def install(self, agent_id: str, connector: RunbookConnector) -> None:
        """Trusted host wiring; payloads can never choose a connector."""
        self.incidents.registry.get(agent_id)
        self.connectors[agent_id] = connector

    # Storage -----------------------------------------------------------------

    @staticmethod
    def _save(db: sqlite3.Connection, execution: RunbookExecution) -> None:
        db.execute(
            "INSERT OR REPLACE INTO tower_runbook_executions VALUES (?, ?, ?)",
            (execution.execution_id, execution.incident_id, execution.model_dump_json()),
        )

    @staticmethod
    def _load(db: sqlite3.Connection, execution_id: str) -> RunbookExecution:
        row = db.execute(
            "SELECT body FROM tower_runbook_executions WHERE id=?", (execution_id,)
        ).fetchone()
        if row is None:
            raise RunbookError("Unknown runbook execution")
        return RunbookExecution.model_validate_json(row[0])

    @staticmethod
    def _event(
        execution: RunbookExecution,
        incident: Incident | None,
        event: str,
        operator: Operator,
        detail: str = "",
    ) -> None:
        at = utcnow()
        execution.events.append(
            RunbookEvent(at=at, event=event, operator_id=operator.operator_id, detail=detail)
        )
        if incident is not None:
            IncidentService._event(incident, event, operator, f"{execution.execution_id} {detail}")

    def _authorize(self, operator: Operator, agent_id: str, *roles: str) -> None:
        if (roles and operator.role not in roles) or (
            operator.agent_ids is not None and agent_id not in operator.agent_ids
        ):
            raise RunbookError("Operator role or deployment scope does not authorize operation")

    # Catalog, recommendations and validation ------------------------------------

    def definitions(self) -> builtins.list[RunbookDefinition]:
        return self.catalog.list()

    def _unmet(self, definition: RunbookDefinition, incident: Incident) -> builtins.list[str]:
        agent = self.incidents.registry.get(incident.agent_id)
        unmet = []
        if agent.environment not in definition.environments:
            unmet.append(f"environment {agent.environment!r} not in {definition.environments}")
        checks = {
            "incident.open": incident.state == "open"
            and incident.plan is None
            and incident.runbook_execution_id is None,
            "incident.investigated": incident.investigation is not None,
            "investigation.not_contradictory": incident.investigation is None
            or incident.investigation.certainty != "contradictory",
            "connector.installed": incident.agent_id in self.connectors,
        }
        unmet += [p for p in definition.prerequisites if not checks[p]]
        return unmet

    def recommend(
        self, incident_id: str, operator: Operator
    ) -> builtins.list[RunbookRecommendation]:
        """Only installed catalog entries; the copilot cannot invent executable steps."""
        incident = self.incidents.get(incident_id, operator)
        environment = self.incidents.registry.get(incident.agent_id).environment
        results = []
        if incident.runbook_execution_id is not None:
            with self.incidents._transaction() as db:
                if self._replaceable(db, incident.runbook_execution_id):
                    incident = incident.model_copy(update={"runbook_execution_id": None})
        for definition in self.catalog.list():
            unmet = self._unmet(definition, incident)
            validations = [
                v.validation_id
                for v in self.validations(definition.runbook_id, definition.version)
                if v.definition_digest == definition.digest() and v.environment == environment
            ]
            results.append(
                RunbookRecommendation(
                    runbook_id=definition.runbook_id,
                    version=definition.version,
                    definition_digest=definition.digest(),
                    title=definition.title,
                    eligible=not unmet,
                    unmet=unmet,
                    parameters=definition.parameters,
                    validation="validated" if validations else "unvalidated",
                    validation_ids=validations,
                )
            )
        return results

    def validations(self, runbook_id: str, version: str) -> builtins.list[RunbookValidation]:
        with self.incidents._transaction() as db:
            return [
                RunbookValidation.model_validate_json(row[0])
                for row in db.execute(
                    "SELECT body FROM tower_runbook_validations "
                    "WHERE runbook_id=? AND version=? ORDER BY id",
                    (runbook_id, version),
                )
            ]

    def record_validation(
        self,
        runbook_id: str,
        version: str,
        request: RunbookValidationRequest,
        operator: Operator,
    ) -> RunbookValidation:
        """Attach an existing completed Chaos report and passing same-run Evals gate."""
        self._authorize(operator, request.agent_id, "writer")
        definition = self.catalog.get(runbook_id, version)
        agent = self.incidents.registry.get(request.agent_id)
        if agent.environment not in definition.environments:
            raise RunbookError("Validation deployment is outside the runbook environments")
        chaos = self.incidents.evidence.get_record(request.agent_id, request.chaos_evidence_id)
        evals = self.incidents.evidence.get_record(request.agent_id, request.evals_evidence_id)
        run_id = chaos.summary.link.run_id
        if (
            chaos.summary.link.source != "agentic-chaos"
            or chaos.summary.availability != "available"
            or chaos.summary.details.get("completed") is not True
            or evals.summary.link.source != "agentic-evals"
            or evals.summary.availability != "available"
            or (evals.summary.details.get("gate") or {}).get("passed") is not True
            or not run_id
            or evals.summary.link.run_id != run_id
        ):
            raise RunbookError(
                "Validation requires a completed Chaos report and passing Evals gate "
                "linked to the same run"
            )
        validation = RunbookValidation(
            validation_id=str(uuid4()),
            runbook_id=runbook_id,
            version=version,
            definition_digest=definition.digest(),
            agent_id=request.agent_id,
            environment=agent.environment,
            chaos_evidence_id=chaos.record_id,
            evals_evidence_id=evals.record_id,
            run_id=run_id,
            recorded_by=operator.operator_id,
            recorded_at=utcnow(),
        )
        with self.incidents._transaction() as db:
            db.execute(
                "INSERT INTO tower_runbook_validations VALUES (?, ?, ?, ?)",
                (validation.validation_id, runbook_id, version, validation.model_dump_json()),
            )
        return validation

    # Preview and approval ------------------------------------------------------

    def _replaceable(self, db: sqlite3.Connection, execution_id: str) -> bool:
        """A never-dispatched preview that can no longer be approved or executed."""
        previous = self._load(db, execution_id)
        return previous.started_at is None and (
            previous.status in ("denied", "revoked", "cancelled")
            or (previous.status in ("pending", "approved") and previous.expires_at <= utcnow())
        )

    def _supports(
        self,
        connector: RunbookConnector,
        agent_id: str,
        definition: RunbookDefinition,
        parameters: Mapping[str, str],
    ) -> bool:
        actions = {s.action for s in definition.steps} | {
            s.rollback_action for s in definition.steps if s.rollback_action
        }
        try:
            return all(connector.supports(agent_id, a, dict(parameters)) for a in sorted(actions))
        except Exception:
            return False

    def preview(
        self, incident_id: str, request: RunbookPreviewRequest, operator: Operator
    ) -> RunbookExecution:
        # Unknown versions raise CatalogError so HTTP can return 404.
        definition = self.catalog.get(request.runbook_id, request.version)
        if set(request.parameters) != set(definition.parameters) or not all(
            spec.accepts(request.parameters[name]) for name, spec in definition.parameters.items()
        ):
            raise RunbookError("Parameters must exactly match the runbook's declared parameters")
        with self.incidents._transaction() as db:
            incident = IncidentService._load(db, incident_id)
            self._authorize(operator, incident.agent_id, "writer")
            if incident.runbook_execution_id is not None:
                if not self._replaceable(db, incident.runbook_execution_id):
                    raise RunbookError("Incident already has a live or dispatched runbook")
                incident.runbook_execution_id = None
            unmet = self._unmet(definition, incident)
            # Claim requires an open incident, whatever the definition declares.
            if (incident.state != "open" or incident.plan is not None) and (
                "incident.open" not in unmet
            ):
                unmet.append("incident.open")
            connector = self.connectors.get(incident.agent_id)
            if unmet or connector is None:
                raise RunbookError("Runbook prerequisites unmet: " + "; ".join(unmet))
            if not self._supports(connector, incident.agent_id, definition, request.parameters):
                raise RunbookError("Installed connector does not support every runbook action")
            agent = self.incidents.registry.get(incident.agent_id)
            execution_id = str(uuid4())
            expires_at = utcnow() + timedelta(seconds=request.expires_in_seconds)
            digest = sha256(
                "\0".join(
                    (
                        execution_id,
                        incident.incident_id,
                        incident.agent_id,
                        agent.environment,
                        definition.digest(),
                        json.dumps(request.parameters, sort_keys=True),
                        expires_at.isoformat(),
                    )
                ).encode()
            ).hexdigest()
            execution = RunbookExecution(
                execution_id=execution_id,
                incident_id=incident.incident_id,
                agent_id=incident.agent_id,
                environment=agent.environment,
                runbook_id=definition.runbook_id,
                version=definition.version,
                definition=definition,
                definition_digest=definition.digest(),
                parameters=dict(request.parameters),
                preview_digest=digest,
                expires_at=expires_at,
                proposed_by=operator.operator_id,
                steps=[
                    StepResult(
                        step_id=s.step_id,
                        action=s.action,
                        rollback="not_declared" if s.rollback_action is None else "not_needed",
                    )
                    for s in definition.steps
                ],
                evidence_ids=list(
                    incident.investigation.citations if incident.investigation else []
                ),
            )
            incident.runbook_execution_id = execution_id
            self._event(
                execution,
                incident,
                "runbook.previewed",
                operator,
                f"{definition.runbook_id}@{definition.version} {digest}",
            )
            self._save(db, execution)
            IncidentService._save(db, incident)
            return execution

    def get(self, execution_id: str, operator: Operator) -> RunbookExecution:
        with self.incidents._transaction() as db:
            execution = self._load(db, execution_id)
        self._authorize(operator, execution.agent_id)
        return execution

    def list(self, incident_id: str, operator: Operator) -> builtins.list[RunbookExecution]:
        incident = self.incidents.get(incident_id, operator)
        with self.incidents._transaction() as db:
            return [
                RunbookExecution.model_validate_json(row[0])
                for row in db.execute(
                    "SELECT body FROM tower_runbook_executions WHERE incident_id=? ORDER BY rowid",
                    (incident.incident_id,),
                )
            ]

    def decide(
        self, execution_id: str, digest: str, approved: bool, operator: Operator
    ) -> RunbookExecution:
        with self.incidents._transaction() as db:
            execution = self._load(db, execution_id)
            self._authorize(operator, execution.agent_id, "approver")
            if (
                execution.status != "pending"
                or digest != execution.preview_digest
                or execution.expires_at <= utcnow()
                or execution.proposed_by == operator.operator_id
            ):
                raise RunbookError("Approval does not match a live pending runbook preview")
            incident = IncidentService._load(db, execution.incident_id)
            execution.status = "approved" if approved else "denied"
            execution.approved_by = operator.operator_id if approved else None
            self._event(execution, incident, "runbook." + execution.status, operator, digest)
            self._save(db, execution)
            IncidentService._save(db, incident)
            return execution

    def revoke(self, execution_id: str, operator: Operator) -> RunbookExecution:
        with self.incidents._transaction() as db:
            execution = self._load(db, execution_id)
            self._authorize(operator, execution.agent_id, "approver")
            if execution.status not in ("pending", "approved"):
                raise RunbookError("Only unclaimed runbook approvals can be revoked")
            incident = IncidentService._load(db, execution.incident_id)
            execution.status = "revoked"
            self._event(execution, incident, "runbook.revoked", operator)
            self._save(db, execution)
            IncidentService._save(db, incident)
            return execution

    def cancel(self, execution_id: str, operator: Operator) -> RunbookExecution:
        """Writers or approvers stop further steps; a running step is never interrupted."""
        with self.incidents._transaction() as db:
            execution = self._load(db, execution_id)
            self._authorize(operator, execution.agent_id, "writer", "approver")
            incident = IncidentService._load(db, execution.incident_id)
            if execution.status in ("pending", "approved"):
                execution.status = "cancelled"
                self._event(execution, incident, "runbook.cancelled", operator, "Not dispatched")
            elif execution.status == "running" and execution.cancel_requested_by is None:
                execution.cancel_requested_by = operator.operator_id
                self._event(execution, incident, "runbook.cancel_requested", operator)
            else:
                raise RunbookError("Runbook is not pending, approved or running")
            self._save(db, execution)
            IncidentService._save(db, incident)
            return execution

    # Execution ---------------------------------------------------------------

    def execute(self, execution_id: str, digest: str, operator: Operator) -> RunbookExecution:
        connector = self._claim(execution_id, digest, operator)
        return self._run(execution_id, connector, operator)

    def _claim(self, execution_id: str, digest: str, operator: Operator) -> RunbookConnector:
        with self.incidents._transaction() as db:
            execution = self._load(db, execution_id)
            self._authorize(operator, execution.agent_id, "writer")
            incident = IncidentService._load(db, execution.incident_id)
            if (
                execution.status != "approved"
                or digest != execution.preview_digest
                or execution.expires_at <= utcnow()
                or incident.state != "open"
                or incident.runbook_execution_id != execution_id
            ):
                raise RunbookError("Missing, expired, changed or consumed runbook approval")
            agent = self.incidents.registry.get(execution.agent_id)
            try:
                installed = self.catalog.get(execution.runbook_id, execution.version).digest()
            except CatalogError:
                installed = ""
            connector = self.connectors.get(execution.agent_id)
            if (
                agent.environment != execution.environment
                or execution.environment not in execution.definition.environments
                or installed != execution.definition_digest
                or connector is None
                or not self._supports(
                    connector, execution.agent_id, execution.definition, execution.parameters
                )
            ):
                raise RunbookError("Target scope, runbook version or connector changed")
            now = utcnow()
            execution.status = "running"
            execution.executed_by = operator.operator_id
            execution.started_at = now
            execution.lease_expires_at = now + timedelta(
                seconds=execution.definition.budget_seconds() + LEASE_SLACK_SECONDS
            )
            incident.state = "executing"
            incident.execution_started_at = now
            incident.outcome = "unknown"
            self._event(execution, incident, "runbook.claimed", operator)
            self._save(db, execution)
            IncidentService._save(db, incident)
        # Commit before dispatch: a process crash cannot cause an automatic replay.
        return connector

    @staticmethod
    def _dispatch(
        connector: RunbookConnector,
        key: str,
        action: str,
        params: dict[str, str],
        timeout: int,
    ) -> Dispatch:
        status, outcome = _bounded(lambda: connector.run(key, action, dict(params)), timeout)
        if status == "busy":
            return "failed"  # No call was made, so nothing changed.
        if status == "timeout":
            return "timed_out"
        if status == "ok" and outcome in ("succeeded", "failed", "partial_failure"):
            return outcome
        return "unknown"

    def _run(
        self, execution_id: str, connector: RunbookConnector, operator: Operator
    ) -> RunbookExecution:
        with self.incidents._transaction() as db:
            definition = self._load(db, execution_id).definition
        stopped: str | None = None
        for index, step in enumerate(definition.steps):
            with self.incidents._transaction() as db:
                execution = self._load(db, execution_id)
                if execution.status != "running":
                    raise RunbookError("Execution lease was reconciled by another operator")
                if execution.cancel_requested_by is not None:
                    stopped = "cancelled"
                    break
            outcome: Dispatch = "failed"
            for attempt in range(1, step.max_attempts + 1):
                with self.incidents._transaction() as db:
                    execution = self._load(db, execution_id)
                    incident = IncidentService._load(db, execution.incident_id)
                    result = execution.steps[index]
                    result.attempts = attempt
                    result.outcome = "unknown"
                    result.started_at = result.started_at or utcnow()
                    self._event(
                        execution,
                        incident,
                        f"runbook.step.{step.step_id}.claimed",
                        operator,
                        f"attempt {attempt}/{step.max_attempts}",
                    )
                    self._save(db, execution)
                    IncidentService._save(db, incident)
                outcome = self._dispatch(
                    connector,
                    f"{execution_id}:{step.step_id}",
                    step.action,
                    execution.parameters,
                    step.timeout_seconds,
                )
                if outcome != "failed" or attempt == step.max_attempts:
                    break
                with self.incidents._transaction() as db:
                    execution = self._load(db, execution_id)
                    incident = IncidentService._load(db, execution.incident_id)
                    self._event(
                        execution,
                        incident,
                        f"runbook.step.{step.step_id}.retrying",
                        operator,
                        "Connector reported a clean failure",
                    )
                    self._save(db, execution)
                    IncidentService._save(db, incident)
            with self.incidents._transaction() as db:
                execution = self._load(db, execution_id)
                incident = IncidentService._load(db, execution.incident_id)
                result = execution.steps[index]
                result.outcome = outcome
                result.finished_at = utcnow()
                result.detail = {
                    "timed_out": "Step deadline elapsed; the call may still complete",
                    "unknown": "Connector raised or returned an unsupported outcome",
                    "partial_failure": "Connector reported partial failure",
                }.get(outcome, "")
                self._event(
                    execution,
                    incident,
                    f"runbook.step.{step.step_id}.{outcome}",
                    operator,
                    result.detail,
                )
                self._save(db, execution)
                IncidentService._save(db, incident)
            if outcome != "succeeded":
                stopped = "failed" if outcome == "failed" else "unknown"
                break
        if stopped in ("failed", "cancelled"):
            self._compensate(execution_id, connector, operator)
        return self._finish(execution_id, stopped, operator)

    def _compensate(
        self, execution_id: str, connector: RunbookConnector, operator: Operator
    ) -> None:
        """Run declared rollback actions for succeeded steps, newest first."""
        with self.incidents._transaction() as db:
            execution = self._load(db, execution_id)
        for index in reversed(range(len(execution.steps))):
            step = execution.definition.steps[index]
            if execution.steps[index].outcome != "succeeded" or step.rollback_action is None:
                continue
            outcome = self._dispatch(
                connector,
                f"{execution_id}:{step.step_id}:rollback",
                step.rollback_action,
                execution.parameters,
                step.rollback_timeout_seconds,
            )
            with self.incidents._transaction() as db:
                stored = self._load(db, execution_id)
                incident = IncidentService._load(db, stored.incident_id)
                stored.steps[index].rollback = (
                    "partial_failure" if outcome == "unknown" else outcome
                )
                self._event(
                    stored, incident, f"runbook.step.{step.step_id}.rollback.{outcome}", operator
                )
                self._save(db, stored)
                IncidentService._save(db, incident)

    def _finish(
        self, execution_id: str, stopped: str | None, operator: Operator
    ) -> RunbookExecution:
        with self.incidents._transaction() as db:
            execution = self._load(db, execution_id)
            incident = IncidentService._load(db, execution.incident_id)
            for result in execution.steps:
                if result.outcome == "pending":
                    result.outcome = "skipped"
            rollback_clean = all(
                r.rollback in ("not_declared", "not_needed", "succeeded") for r in execution.steps
            )
            if stopped is None:
                execution.status = "awaiting_verification"
                incident.state = "awaiting_verification"
                incident.outcome = "succeeded"
            else:
                execution.status = (
                    ("cancelled" if stopped == "cancelled" else "escalated")
                    if stopped != "unknown" and rollback_clean
                    else "reconciliation_required"
                )
                incident.state = "escalated"
                incident.outcome = "failed" if stopped != "unknown" else "partial_failure"
            self._event(
                execution,
                incident,
                "runbook." + execution.status,
                operator,
                "Recovery requires verification"
                if stopped is None
                else "Reconcile runtime manually before another action"
                if execution.status == "reconciliation_required"
                else "Completed steps with declared rollback were compensated",
            )
            self._save(db, execution)
            IncidentService._save(db, incident)
            return execution

    def reconcile(self, execution_id: str, operator: Operator) -> RunbookExecution:
        """Escalate an interrupted execution after its lease, without replaying a step."""
        with self.incidents._transaction() as db:
            execution = self._load(db, execution_id)
            self._authorize(operator, execution.agent_id, "writer")
            if execution.status != "running":
                raise RunbookError("Only an interrupted running runbook requires reconciliation")
            if execution.lease_expires_at is None or execution.lease_expires_at > utcnow():
                raise RunbookError("Runbook is still within its execution lease")
            incident = IncidentService._load(db, execution.incident_id)
            for result in execution.steps:
                if result.outcome == "pending":
                    result.outcome = "skipped"
            execution.status = "reconciliation_required"
            incident.state = "escalated"
            incident.outcome = "unknown"
            self._event(
                execution,
                incident,
                "runbook.reconciliation_required",
                operator,
                "Interrupted; claimed steps are unknown and will not replay",
            )
            self._save(db, execution)
            IncidentService._save(db, incident)
            return execution

    # Verification -------------------------------------------------------------

    def verify(
        self, execution_id: str, lens_id: str, evals_id: str, operator: Operator
    ) -> RunbookExecution:
        execution = self.get(execution_id, operator)
        self._authorize(operator, execution.agent_id, "writer")
        if execution.status != "awaiting_verification":
            raise RunbookError("Runbook is not awaiting verification")
        incident = self.incidents.get(execution.incident_id, operator)
        valid = self.incidents.recovery_evidence(
            incident,
            lens_id,
            evals_id,
            execution.started_at,
            execution.definition.recovery.freshness_seconds,
        )
        connector = self.connectors.get(execution.agent_id)
        probe = False
        if connector is not None:
            status, value = _bounded(
                lambda: connector.probe(execution.agent_id, dict(execution.parameters)),
                PROBE_TIMEOUT_SECONDS,
            )
            probe = status == "ok" and value is True
        with self.incidents._transaction() as db:
            execution = self._load(db, execution_id)
            incident = IncidentService._load(db, execution.incident_id)
            if execution.status != "awaiting_verification":
                raise RunbookError("Verification already completed")
            resolved = valid and probe
            execution.status = "resolved" if resolved else "escalated"
            incident.state = execution.status
            execution.verification = {
                "lens_evidence_id": lens_id,
                "evals_evidence_id": evals_id,
                "probe": probe,
                "evidence_criteria": valid,
            }
            execution.evidence_ids += [lens_id, evals_id]
            self._event(
                execution,
                incident,
                "runbook.verification." + execution.status,
                operator,
                f"Lens={lens_id}; Evals={evals_id}; probe={probe}; criteria={valid}",
            )
            self._save(db, execution)
            IncidentService._save(db, incident)
            return execution
