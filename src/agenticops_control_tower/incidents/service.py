"""Durable incident transitions; claim execution before touching a runtime."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from threading import RLock
from uuid import uuid4

from agenticops_control_tower.adapters.containment import SidecarContainmentAdapter
from agenticops_control_tower.config.models import Operator
from agenticops_control_tower.evidence.store import EvidenceStore, as_utc
from agenticops_control_tower.incidents.connectors import RecoveryConnector
from agenticops_control_tower.incidents.models import (
    Incident,
    Investigation,
    RecoveryPlan,
    TimelineEvent,
)
from agenticops_control_tower.models.evidence import EvidenceRecord
from agenticops_control_tower.registry import AgentRegistry


class IncidentError(ValueError):
    """Unauthorized or unsupported incident transition."""


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class IncidentService:
    def __init__(
        self,
        registry: AgentRegistry,
        evidence: EvidenceStore,
        database_path: str | None = None,
        connectors: dict[str, RecoveryConnector] | None = None,
        containment: dict[str, SidecarContainmentAdapter] | None = None,
    ) -> None:
        self.registry = registry
        self.evidence = evidence
        self.connectors = dict(connectors or {})
        self.containment = dict(containment or {})
        self._path = database_path
        self._memory = sqlite3.connect(":memory:", check_same_thread=False)
        self._lock = RLock()
        with self._transaction() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS tower_incidents "
                "(id TEXT PRIMARY KEY, detection_id TEXT UNIQUE, body TEXT NOT NULL)"
            )

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            db = sqlite3.connect(self._path) if self._path else self._memory
            try:
                db.execute("BEGIN IMMEDIATE")
                yield db
                db.commit()
            except BaseException:
                db.rollback()
                raise
            finally:
                if self._path:
                    db.close()

    @staticmethod
    def _authorize(operator: Operator, agent_id: str, role: str | None = None) -> None:
        if (role is not None and operator.role != role) or (
            operator.agent_ids is not None and agent_id not in operator.agent_ids
        ):
            raise IncidentError("Operator role or deployment scope does not authorize operation")

    @staticmethod
    def _event(incident: Incident, event: str, operator: Operator, detail: str = "") -> None:
        incident.events.append(
            TimelineEvent(at=utcnow(), event=event, operator_id=operator.operator_id, detail=detail)
        )

    @staticmethod
    def _save(db: sqlite3.Connection, incident: Incident) -> None:
        db.execute(
            "INSERT OR REPLACE INTO tower_incidents VALUES (?, ?, ?)",
            (incident.incident_id, incident.detection.record_id, incident.model_dump_json()),
        )

    @staticmethod
    def _load(db: sqlite3.Connection, incident_id: str) -> Incident:
        row = db.execute("SELECT body FROM tower_incidents WHERE id=?", (incident_id,)).fetchone()
        if row is None:
            raise IncidentError("Unknown incident")
        return Incident.model_validate_json(row[0])

    def _record(self, agent_id: str, record_id: str) -> EvidenceRecord:
        # Exact lookup avoids silently excluding evidence beyond a history page.
        return self.evidence.get_record(agent_id, record_id)

    def get(self, incident_id: str, operator: Operator) -> Incident:
        with self._transaction() as db:
            incident = self._load(db, incident_id)
            self._authorize(operator, incident.agent_id)
            return incident

    def list(self, operator: Operator) -> list[Incident]:
        with self._transaction() as db:
            incidents = [
                Incident.model_validate_json(row[0])
                for row in db.execute("SELECT body FROM tower_incidents ORDER BY id")
            ]
            return [
                i
                for i in incidents
                if operator.agent_ids is None or i.agent_id in operator.agent_ids
            ]

    def detect(self, agent_id: str, evidence_id: str, operator: Operator) -> Incident:
        self._authorize(operator, agent_id, "writer")
        record = self._record(agent_id, evidence_id)
        with self._transaction() as db:
            return self._detect(db, record, operator)

    def _detect(
        self, db: sqlite3.Connection, record: EvidenceRecord, operator: Operator
    ) -> Incident:
        """Create from a trusted stored projection in the caller's atomic transaction."""
        agent_id, evidence_id = record.summary.link.agent_id, record.record_id
        self._authorize(operator, agent_id, "writer")
        summary = record.summary
        if (
            summary.link.source != "agenticlens"
            or summary.link.artifact_type != "run"
            or summary.availability != "available"
            or summary.details.get("status") != "failed"
        ):
            raise IncidentError("Detection requires an available failed native Lens run")
        row = db.execute(
            "SELECT body FROM tower_incidents WHERE detection_id=?", (evidence_id,)
        ).fetchone()
        if row:
            return Incident.model_validate_json(row[0])
        incident = Incident(incident_id=str(uuid4()), agent_id=agent_id, detection=record)
        self._event(incident, "detected", operator, evidence_id)
        self._save(db, incident)
        return incident

    def investigate(self, incident_id: str, operator: Operator) -> Incident:
        with self._transaction() as db:
            incident = self._load(db, incident_id)
            self._authorize(operator, incident.agent_id, "writer")
            if (
                incident.state != "open"
                or incident.plan is not None
                or incident.runbook_execution_id is not None
            ):
                raise IncidentError("Investigation is closed once a plan is previewed")
            run_id = incident.detection.summary.details.get("run_id")
            records = self.evidence.history(incident.agent_id, limit=500)
            linked = [
                r
                for r in records
                if r.record_id == incident.detection.record_id
                or (run_id and r.summary.link.run_id == run_id)
            ]
            if not any(r.record_id == incident.detection.record_id for r in linked):
                linked.append(incident.detection)
            linked.sort(key=lambda r: (as_utc(r.summary.link.observed_at), r.record_id))
            contradictory = any(
                r.summary.availability == "available"
                and r.summary.link.source == "agenticlens"
                and r.summary.details.get("status") == "succeeded"
                for r in linked
            )
            error = incident.detection.summary.details.get("error_type")
            incident.investigation = Investigation(
                finding=(
                    "Contradictory run outcomes; cause remains unconfirmed"
                    if contradictory
                    else "Native Lens records a failed run; dependency cause is a hypothesis"
                ),
                certainty="contradictory"
                if contradictory
                else "hypothesis"
                if error
                else "observed_failure",
                citations=[r.record_id for r in linked],
                timeline=linked,
                missing=[
                    "Prompt version unavailable in native Lens run",
                    "Deployment change history unavailable",
                    "Independent causal confirmation unavailable",
                ],
            )
            self._event(incident, "investigated", operator)
            self._save(db, incident)
            return incident

    def preview(
        self, incident_id: str, dependency: str, expires_in_seconds: int, operator: Operator
    ) -> Incident:
        if not 1 <= expires_in_seconds <= 3600:
            raise IncidentError("Expiry must be between 1 and 3600 seconds")
        with self._transaction() as db:
            incident = self._load(db, incident_id)
            self._authorize(operator, incident.agent_id, "writer")
            agent = self.registry.get(incident.agent_id)
            connector = self.connectors.get(incident.agent_id)
            if (
                incident.state != "open"
                or incident.plan is not None
                or incident.runbook_execution_id is not None
                or incident.investigation is None
                or incident.investigation.certainty == "contradictory"
                or agent.environment != "staging"
                or connector is None
                or not connector.supports(incident.agent_id, dependency)
            ):
                raise IncidentError(
                    "Runbook prerequisites or allowlisted staging connector missing"
                )
            incident.plan = RecoveryPlan(agent_id=incident.agent_id, dependency=dependency)
            incident.expires_at = utcnow() + timedelta(seconds=expires_in_seconds)
            incident.proposed_by = operator.operator_id
            incident.preview_digest = sha256(
                (
                    incident.incident_id
                    + incident.plan.model_dump_json()
                    + incident.expires_at.isoformat()
                ).encode()
            ).hexdigest()
            self._event(incident, "previewed", operator, incident.preview_digest)
            self._save(db, incident)
            return incident

    def decide(self, incident_id: str, digest: str, approved: bool, operator: Operator) -> Incident:
        with self._transaction() as db:
            incident = self._load(db, incident_id)
            self._authorize(operator, incident.agent_id, "approver")
            if (
                incident.approval != "pending"
                or incident.plan is None
                or digest != incident.preview_digest
                or incident.expires_at is None
                or incident.expires_at <= utcnow()
                or incident.proposed_by == operator.operator_id
            ):
                raise IncidentError("Approval does not match a live pending preview")
            incident.approval = "approved" if approved else "denied"
            incident.approved_by = operator.operator_id if approved else None
            self._event(incident, incident.approval, operator, digest)
            self._save(db, incident)
            return incident

    def revoke(self, incident_id: str, operator: Operator) -> Incident:
        with self._transaction() as db:
            incident = self._load(db, incident_id)
            self._authorize(operator, incident.agent_id, "approver")
            if incident.approval not in ("pending", "approved"):
                raise IncidentError("Approval cannot be revoked")
            incident.approval = "revoked"
            self._event(incident, "revoked", operator)
            self._save(db, incident)
            return incident

    def execute(self, incident_id: str, digest: str, operator: Operator) -> Incident:
        with self._transaction() as db:
            incident = self._load(db, incident_id)
            self._authorize(operator, incident.agent_id, "writer")
            if (
                incident.state != "open"
                or incident.approval != "approved"
                or digest != incident.preview_digest
                or incident.expires_at is None
                or incident.expires_at <= utcnow()
                or incident.plan is None
                or self.registry.get(incident.agent_id).environment != "staging"
            ):
                raise IncidentError("Missing, expired, changed or consumed approval")
            connector = self.connectors.get(incident.agent_id)
            if connector is None or not connector.supports(
                incident.agent_id, incident.plan.dependency
            ):
                raise IncidentError("Connector unavailable or target changed")
            incident.state = "executing"
            incident.approval = "consumed"
            incident.execution_started_at = utcnow()
            incident.outcome = "unknown"
            self._event(incident, "execution.claimed", operator)
            self._save(db, incident)
        # Commit before dispatch: a process crash cannot cause an automatic replay.
        try:
            outcome = connector.execute(incident_id, incident.plan)
            if outcome not in ("succeeded", "failed", "partial_failure"):
                outcome = "partial_failure"
        except Exception:
            outcome = "partial_failure"
        with self._transaction() as db:
            incident = self._load(db, incident_id)
            incident.outcome = outcome
            incident.state = "awaiting_verification" if outcome == "succeeded" else "escalated"
            self._event(
                incident,
                "execution." + outcome,
                operator,
                "Reconcile runtime manually on partial or unknown execution",
            )
            self._save(db, incident)
            return incident

    def recovery_evidence(
        self,
        incident: Incident,
        lens_id: str,
        evals_id: str,
        start: datetime | None,
        freshness_seconds: int = 300,
    ) -> bool:
        """Shared recovery criteria: fresh same-run Lens success and passing Evals gate.

        Unknown record IDs raise; stale, mismatched, failed or future evidence is False.
        """
        lens = self._record(incident.agent_id, lens_id)
        evals = self._record(incident.agent_id, evals_id)
        now = utcnow()
        fresh = start is not None and all(
            start < as_utc(r.summary.link.observed_at) <= now
            and start < as_utc(r.ingested_at) <= now
            and now - as_utc(r.summary.link.observed_at) <= timedelta(seconds=freshness_seconds)
            and r.summary.availability == "available"
            for r in (lens, evals)
        )
        run_id = lens.summary.details.get("run_id")
        valid = (
            fresh
            and lens.summary.link.source == "agenticlens"
            and lens.summary.link.artifact_type == "run"
            and lens.summary.details.get("status") == "succeeded"
            and lens.summary.details.get("task_success") is True
            and bool(run_id)
            and run_id != incident.detection.summary.details.get("run_id")
            and evals.summary.link.run_id == run_id
            and evals.summary.link.source == "agentic-evals"
            and (evals.summary.details.get("gate") or {}).get("passed") is True
        )
        contradictory = any(
            r.summary.link.run_id == run_id
            and r.summary.link.source == "agenticlens"
            and r.summary.availability == "available"
            and r.summary.details.get("status") == "failed"
            for r in self.evidence.history(incident.agent_id, limit=500)
        )
        return bool(valid and not contradictory)

    def verify(self, incident_id: str, lens_id: str, evals_id: str, operator: Operator) -> Incident:
        # The bounded probe runs outside the storage transaction.
        incident = self.get(incident_id, operator)
        self._authorize(operator, incident.agent_id, "writer")
        if incident.state != "awaiting_verification" or incident.plan is None:
            raise IncidentError("Incident is not awaiting verification")
        valid = self.recovery_evidence(
            incident, lens_id, evals_id, incident.execution_started_at
        )
        connector = self.connectors.get(incident.agent_id)
        try:
            probe = connector is not None and connector.probe(incident.plan)
        except Exception:
            probe = False
        with self._transaction() as db:
            incident = self._load(db, incident_id)
            if incident.state != "awaiting_verification":
                raise IncidentError("Verification already completed")
            incident.state = "resolved" if valid and probe else "escalated"
            self._event(
                incident,
                "verification." + incident.state,
                operator,
                f"Lens={lens_id}; Evals={evals_id}; probe={probe}; criteria={bool(valid)}",
            )
            self._save(db, incident)
            return incident

    def control(self, incident_id: str, action: str, operator: Operator) -> Incident:
        """Human writer stop/restart; stop does not depend on model approval."""
        if action not in ("stop", "restart"):
            raise IncidentError("Unsupported runtime control")
        incident = self.get(incident_id, operator)
        self._authorize(operator, incident.agent_id, "writer")
        adapter = self.containment.get(incident.agent_id)
        with self._transaction() as db:
            incident = self._load(db, incident_id)
            self._event(incident, "control." + action + ".requested", operator)
            self._save(db, incident)
        outcome = "unsupported" if adapter is None else "acknowledged"
        try:
            receipt = adapter.control(action, operator.operator_id) if adapter else None
            if receipt is not None:
                reported = receipt.get("outcome")
                outcome = (
                    reported
                    if reported in ("acknowledged", "failed", "unsupported", "incomplete")
                    else "failed"
                )
        except Exception:
            receipt = None
            outcome = "failed"
        with self._transaction() as db:
            incident = self._load(db, incident_id)
            self._event(
                incident,
                "control." + action + "." + outcome,
                operator,
                json.dumps(receipt) if receipt else "No confirmed runtime acknowledgement",
            )
            self._save(db, incident)
            return incident

    def reconcile(self, incident_id: str, operator: Operator) -> Incident:
        """Escalate an interrupted execution without replaying its runtime action."""
        with self._transaction() as db:
            incident = self._load(db, incident_id)
            self._authorize(operator, incident.agent_id, "writer")
            if incident.state != "executing":
                raise IncidentError("Only unknown interrupted execution requires reconciliation")
            incident.state = "escalated"
            self._event(
                incident,
                "execution.reconciliation_required",
                operator,
                "Host must reconcile runtime; action remains consumed and cannot replay",
            )
            self._save(db, incident)
            return incident
