"""Evaluate pushed telemetry; persist deduplicated alerts without executing recovery."""

from __future__ import annotations

import builtins
import sqlite3
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import TYPE_CHECKING, Any

from agenticops_control_tower.config.models import Operator
from agenticops_control_tower.evidence.store import as_utc
from agenticops_control_tower.incidents import IncidentError, IncidentService
from agenticops_control_tower.incidents.models import TimelineEvent
from agenticops_control_tower.models import AgentRecord
from agenticops_control_tower.models.evidence import EVIDENCE_SOURCES, EvidenceRecord
from agenticops_control_tower.operations.models import Alert, DetectionPolicy

if TYPE_CHECKING:
    from agenticops_control_tower.api.surface import ControlTowerAPI


class OperationsService:
    def __init__(self, api: ControlTowerAPI, policy: DetectionPolicy | None = None) -> None:
        self.api = api
        self.policy = policy or DetectionPolicy()
        # Share the incident transaction/connection so in-memory and durable modes agree.
        with self.api.incidents._transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS tower_alerts (id TEXT PRIMARY KEY, body TEXT)")
            db.execute(
                "CREATE TABLE IF NOT EXISTS tower_detection_scans "
                "(agent_id TEXT PRIMARY KEY, at TEXT NOT NULL)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS tower_alert_audit "
                "(seq INTEGER PRIMARY KEY, agent_id TEXT NOT NULL, body TEXT NOT NULL)"
            )

    @staticmethod
    def _save(db: sqlite3.Connection, alert: Alert) -> None:
        db.execute(
            "INSERT OR REPLACE INTO tower_alerts VALUES (?, ?)",
            (alert.alert_id, alert.model_dump_json()),
        )

    @staticmethod
    def _audit(
        db: sqlite3.Connection, alert: Alert, event: str, operator: Operator, at: datetime
    ) -> None:
        record = TimelineEvent(
            at=at, event=event, operator_id=operator.operator_id, detail=alert.alert_id
        )
        db.execute(
            "INSERT INTO tower_alert_audit(agent_id, body) VALUES (?, ?)",
            (alert.agent_id, record.model_dump_json()),
        )

    def list(
        self, operator: Operator, *, environment: str | None = None, active_only: bool = False
    ) -> builtins.list[Alert]:
        with self.api.incidents._transaction() as db:
            alerts = [
                Alert.model_validate_json(row[0])
                for row in db.execute("SELECT body FROM tower_alerts ORDER BY id")
            ]
        return [
            a
            for a in alerts
            if (operator.agent_ids is None or a.agent_id in operator.agent_ids)
            and (environment is None or a.environment == environment)
            and (not active_only or a.cleared_at is None)
        ]

    def acknowledge(self, alert_id: str, operator: Operator) -> Alert:
        with self.api.incidents._transaction() as db:
            row = db.execute("SELECT body FROM tower_alerts WHERE id=?", (alert_id,)).fetchone()
            if row is None:
                raise IncidentError("Unknown alert")
            alert = Alert.model_validate_json(row[0])
            IncidentService._authorize(operator, alert.agent_id, "writer")
            if alert.acknowledged_at is None:
                alert.acknowledged_by = operator.operator_id
                alert.acknowledged_at = datetime.now(timezone.utc)
                self._save(db, alert)
                self._audit(db, alert, "alert.acknowledged", operator, alert.acknowledged_at)
            return alert

    def evaluate(self, operator: Operator, *, now: datetime | None = None) -> builtins.list[Alert]:
        if operator.role != "writer":
            raise IncidentError("Detection requires writer authority")
        now = as_utc(now or datetime.now(timezone.utc))
        for agent in self.api.list_agents():
            if operator.agent_ids is not None and agent.agent_id not in operator.agent_ids:
                continue
            candidates: list[Alert] = []
            failures: dict[str, EvidenceRecord] = {}

            def add(
                rule: Any,
                source: str,
                message: str,
                evidence_id: str | None = None,
                run_id: str | None = None,
                *,
                agent: AgentRecord = agent,
                candidates: list[Alert] = candidates,
            ) -> None:
                identity = "\0".join(
                    (agent.agent_id, agent.environment, rule, source, evidence_id or "")
                )
                candidates.append(
                    Alert(
                        alert_id=sha256(identity.encode()).hexdigest(),
                        agent_id=agent.agent_id,
                        environment=agent.environment,
                        rule=rule,
                        source=source,
                        severity="critical" if rule == "lens.failed" else "warning",
                        message=message,
                        evidence_id=evidence_id,
                        correlation_key=sha256(
                            "\0".join(
                                (agent.environment, source, run_id or agent.agent_id)
                            ).encode()
                        ).hexdigest(),
                        first_seen=now,
                        last_seen=now,
                    )
                )

            heartbeat = as_utc(agent.last_seen or agent.registered_at)
            if now - heartbeat > timedelta(seconds=self.policy.heartbeat_after_seconds):
                add(
                    "heartbeat.stale",
                    "registry",
                    "Heartbeat overdue; reported health unchanged",
                )
            for source in EVIDENCE_SOURCES:
                records = self.api.evidence.history(agent.agent_id, source=source, limit=1)
                if not records:
                    if source in agent.capabilities:
                        add(
                            "evidence.missing",
                            source,
                            "Installed capability has no pushed evidence",
                        )
                    continue
                record = records[0]
                summary = record.summary
                age = (now - as_utc(summary.link.observed_at)).total_seconds()
                if age > self.policy.stale_after_seconds:
                    add("evidence.stale", source, "Latest producer evidence is stale")
                elif (
                    age >= 0
                    and source == "agenticlens"
                    and summary.availability == "available"
                    and summary.link.artifact_type == "run"
                    and summary.details.get("status") == "failed"
                ):
                    failures[record.record_id] = record
                    add(
                        "lens.failed",
                        source,
                        "Fresh native Lens failure; cause unconfirmed",
                        record.record_id,
                        summary.details.get("run_id") or summary.link.run_id,
                    )
            # Storage transactions never hold locks while reading other services.
            with self.api.incidents._transaction() as db:
                scan = db.execute(
                    "SELECT at FROM tower_detection_scans WHERE agent_id=?", (agent.agent_id,)
                ).fetchone()
                if scan and datetime.fromisoformat(scan[0]) > now:
                    continue
                db.execute(
                    "INSERT OR REPLACE INTO tower_detection_scans VALUES (?, ?)",
                    (agent.agent_id, now.isoformat()),
                )
                active = {a.alert_id for a in candidates}
                for row in db.execute("SELECT body FROM tower_alerts").fetchall():
                    previous = Alert.model_validate_json(row[0])
                    if (
                        previous.agent_id == agent.agent_id
                        and previous.cleared_at is None
                        and previous.alert_id not in active
                    ):
                        previous.cleared_at = now
                        self._save(db, previous)
                        self._audit(db, previous, "alert.cleared", operator, now)
                for alert in candidates:
                    if alert.rule == "lens.failed" and alert.evidence_id is not None:
                        alert.incident_id = self.api.incidents._detect(
                            db, failures[alert.evidence_id], operator
                        ).incident_id
                    row = db.execute(
                        "SELECT body FROM tower_alerts WHERE id=?", (alert.alert_id,)
                    ).fetchone()
                    event = "alert.created"
                    if row:
                        previous = Alert.model_validate_json(row[0])
                        event = "alert.reopened" if previous.cleared_at else ""
                        if previous.cleared_at is None:
                            alert.first_seen = previous.first_seen
                            alert.acknowledged_by = previous.acknowledged_by
                            alert.acknowledged_at = previous.acknowledged_at
                    self._save(db, alert)
                    if event:
                        self._audit(db, alert, event, operator, now)
        return self.list(operator)

    def incident_view(self, incident_id: str, operator: Operator) -> dict[str, Any]:
        incident = self.api.incidents.get(incident_id, operator)
        agent = self.api.get_agent(incident.agent_id)
        native_run_id = incident.detection.summary.details.get("run_id")
        run_id = (
            native_run_id
            if isinstance(native_run_id, str)
            else incident.detection.summary.link.run_id
        )
        linked, evidence_truncated = (
            self.api.evidence.run_history(agent.agent_id, run_id, limit=100)
            if run_id
            else ([], False)
        )
        if not any(r.record_id == incident.detection.record_id for r in linked):
            linked.append(incident.detection)
        timeline: list[dict[str, Any]] = [
            dict(
                at=e.at,
                event=e.event,
                operator_id=e.operator_id,
                detail=e.detail,
                source="incident",
            )
            for e in incident.events
        ]
        timeline += [
            dict(
                at=a.recorded_at,
                event=a.event,
                operator_id=a.operator_id,
                detail=a.detail,
                source="configuration",
                action_id=a.action_id,
            )
            for a in self.api.config.audit(agent.agent_id)
        ]
        with self.api.incidents._transaction() as db:
            alert_events = [
                TimelineEvent.model_validate_json(row[0])
                for row in db.execute(
                    "SELECT body FROM tower_alert_audit WHERE agent_id=? ORDER BY seq",
                    (agent.agent_id,),
                )
            ]
        timeline += [
            dict(at=e.at, event=e.event, operator_id=e.operator_id, detail=e.detail, source="alert")
            for e in alert_events
        ]
        timeline += [
            dict(
                at=r.summary.link.observed_at,
                event="evidence.observed",
                operator_id=r.ingested_by,
                detail=r.record_id,
                source=r.summary.link.source,
            )
            for r in linked
        ]
        runbooks = self.api.runbooks.list(incident_id, operator)
        timeline.sort(key=lambda e: (as_utc(e["at"]), e["source"], e["event"]))
        return dict(
            incident=incident,
            agent=agent,
            posture=self.api.agent_posture(agent.agent_id),
            evidence=linked,
            evidence_truncated=evidence_truncated,
            evidence_limit=100,
            runbooks=runbooks,
            timeline=timeline,
            lens_integrity="not_verified",
            lens_coverage="not_assessed",
            correlation="Explicit same-run links within deployment; not proof of causality",
            change_scope="All retained deployment configuration/bulk audit events",
        )
