"""Project a held native incident into an AIOS 0.8-draft investigation report."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from agenticops_control_tower import __version__
from agenticops_control_tower.incidents._aios import identifier, timestamp
from agenticops_control_tower.incidents.models import Incident


def export_investigation_report(incident: Incident, *, created_at: datetime) -> dict[str, Any]:
    """Emit public ids/states and redacted summaries without recomputing outcomes.

    Native timeline details, operator ids, findings and missing-input text are
    withheld. The supplied Incident must come from an authorized native reader;
    validation or this projection never authenticates it. A native verification
    event is cited separately from incident closure.
    """
    created = timestamp(created_at)
    identifier(incident.incident_id)
    identifier(incident.agent_id)
    records = {incident.detection.record_id: incident.detection}
    investigation = incident.investigation
    if investigation:
        for record in investigation.timeline:
            if record.record_id in records and records[record.record_id] != record:
                raise ValueError("Conflicting native evidence records share an identity")
            records[record.record_id] = record
    evidence: list[dict[str, Any]] = []
    timeline: list[dict[str, Any]] = []
    for key, record in records.items():
        link = record.summary.link
        identifier(key)
        observed = timestamp(link.observed_at)
        if link.agent_id != incident.agent_id or link.observed_at > created_at:
            raise ValueError(
                "Incident evidence must be attributable and observed before report creation"
            )
        evidence.append(
            {
                "id": f"record:{key}",
                "producer": link.source,
                "artifact_id": link.artifact_ref,
                "format": link.spec_version or f"{link.source}.{link.artifact_type}",
                "object_id": link.run_id,
            }
            if link.run_id
            else {
                "id": f"record:{key}",
                "producer": link.source,
                "artifact_id": link.artifact_ref,
                "format": link.spec_version or f"{link.source}.{link.artifact_type}",
            }
        )
        timeline.append(
            {"id": f"observation:{key}", "occurred_at": observed, "evidence_ids": [f"record:{key}"]}
        )
    citations = (
        list(dict.fromkeys(investigation.citations))
        if investigation
        else [incident.detection.record_id]
    )
    if not set(citations) <= records.keys():
        raise ValueError("Native investigation cites evidence that was not supplied")
    citations = [f"record:{key}" for key in citations]
    certainty = {
        "observed_failure": "observed",
        "hypothesis": "hypothesis",
        "contradictory": "contradictory",
    }.get(investigation.certainty if investigation else "observed_failure", "inconclusive")
    if certainty in {"observed", "contradictory"} and not citations:
        raise ValueError("Observed/contradictory claims need source evidence citations")
    verification: list[str] = []
    failed_verification: list[str] = []
    for position, event in enumerate(incident.events):
        event_time = timestamp(event.at)
        if event.at > created_at:
            raise ValueError("Native events cannot follow report creation")
        key = f"event:{position}"
        evidence.append(
            {
                "id": key,
                "producer": "agenticops-control-tower",
                "artifact_id": incident.incident_id,
                "format": "tower.incident",
                "object_id": f"events/{position}",
            }
        )
        timeline.append(
            {"id": f"timeline:{position}", "occurred_at": event_time, "evidence_ids": [key]}
        )
        if event.event == "verification.resolved":
            verification = [key]
            failed_verification = []
        elif event.event == "verification.escalated":
            failed_verification = [key]
            verification = []
    recovery = (
        "verified"
        if incident.state == "resolved" and verification
        else "failed"
        if failed_verification
        else "pending"
        if incident.state in {"executing", "awaiting_verification"}
        else "unknown"
    )
    detected_at = timestamp(incident.detection.ingested_at)
    if incident.detection.ingested_at > created_at:
        raise ValueError("Detection cannot follow report creation")
    return {
        "spec_version": "0.8-draft",
        "artifact_type": "investigation_report",
        "id": f"tower:investigation:{incident.incident_id}",
        "created_at": created,
        "producer": {"name": "agenticops-control-tower", "version": __version__},
        "source": {
            "id": "native-incident",
            "producer": "agenticops-control-tower",
            "artifact_id": incident.incident_id,
            "format": "tower.incident",
        },
        "incident": {
            "id": incident.incident_id,
            "status": "investigating"
            if incident.state in {"executing", "awaiting_verification"}
            or (incident.state == "open" and investigation is not None)
            else incident.state,
            "native_state": incident.state,
            "detected_at": detected_at,
            "affected_targets": [
                {
                    "id": "affected-agent",
                    "producer": "agenticops-control-tower",
                    "artifact_id": incident.agent_id,
                    "format": "tower.agent",
                }
            ],
        },
        "summary": {
            "statement": f"Native incident {incident.state}; detailed text withheld.",
            "certainty": certainty,
            "evidence_ids": citations,
        },
        "evidence": evidence,
        "timeline_entries": timeline,
        "findings": [
            {
                "id": "finding:0",
                "statement": "Native investigation finding; detailed text withheld.",
                "certainty": certainty,
                "evidence_ids": citations,
            }
        ]
        if investigation
        else [],
        "missing_evidence_items": [
            f"Redacted missing input {i + 1}" for i in range(len(investigation.missing))
        ]
        if investigation
        else ["Investigation not yet available"],
        "recovery": {
            "status": recovery,
            "evidence_ids": verification
            if recovery == "verified"
            else failed_verification
            if recovery == "failed"
            else [],
        },
        "attributes": {"text_redacted": True},
    }
