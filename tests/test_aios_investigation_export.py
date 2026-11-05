from datetime import datetime, timedelta, timezone

import pytest

from agenticops_control_tower.incidents.export import export_investigation_report
from agenticops_control_tower.incidents.models import Incident, Investigation, TimelineEvent
from agenticops_control_tower.models.evidence import EvidenceLink, EvidenceRecord, EvidenceSummary
from aios08_helpers import assert_schema

NOW = datetime(2026, 11, 4, 18, tzinfo=timezone.utc)


def native(state="open"):
    record = EvidenceRecord(
        record_id="e-1",
        ingested_at=NOW,
        ingested_by="private-operator",
        summary=EvidenceSummary(
            link=EvidenceLink(
                agent_id="agent-1",
                source="agenticlens",
                source_version="0.14.0",
                artifact_type="run",
                artifact_ref="run-source",
                observed_at=NOW,
                run_id="run-1",
                spec_version="0.4-draft",
            ),
            availability="available",
            details={"secret": "private"},
        ),
    )
    investigation = Investigation(
        finding="secret private finding",
        certainty="observed_failure",
        citations=[record.record_id],
        missing=["secret missing input"],
        timeline=[record],
    )
    return Incident(
        incident_id="incident-1",
        agent_id="agent-1",
        detection=record,
        state=state,
        investigation=investigation,
    )


def test_report_cites_native_evidence_and_omits_private_text():
    doc = export_investigation_report(native(), created_at=NOW)
    assert_schema(doc)
    assert doc["summary"]["certainty"] == "observed"
    assert doc["summary"]["evidence_ids"] == ["record:e-1"]
    assert doc["incident"]["status"] == "investigating"
    assert doc["source"]["artifact_id"] == "incident-1"
    assert "secret" not in str(doc) and "private" not in str(doc)


def test_closure_does_not_imply_recovery_but_native_verification_is_preserved():
    incident = native("resolved")
    doc = export_investigation_report(incident, created_at=NOW)
    assert_schema(doc)
    assert doc["recovery"]["status"] == "unknown"
    incident.events.append(
        TimelineEvent(at=NOW, event="verification.resolved", operator_id="private", detail="secret")
    )
    doc = export_investigation_report(incident, created_at=NOW)
    assert_schema(doc)
    assert doc["recovery"] == {"status": "verified", "evidence_ids": ["event:0"]}
    assert "secret" not in str(doc) and "private" not in str(doc)


def test_unsupported_citations_and_future_observations_fail():
    incident = native()
    incident.investigation.citations = ["unavailable"]
    with pytest.raises(ValueError, match="not supplied"):
        export_investigation_report(incident, created_at=NOW)
    with pytest.raises(ValueError, match="observed before"):
        export_investigation_report(native(), created_at=NOW - timedelta(seconds=1))


def test_latest_verification_and_conflicting_identity_are_preserved():
    incident = native("resolved")
    incident.events = [
        TimelineEvent(at=NOW, event="verification.resolved", operator_id="operator"),
        TimelineEvent(at=NOW, event="verification.escalated", operator_id="operator"),
    ]
    doc = export_investigation_report(incident, created_at=NOW)
    assert_schema(doc)
    assert doc["recovery"] == {"status": "failed", "evidence_ids": ["event:1"]}
    conflicting = incident.detection.model_copy(update={"ingested_by": "other"})
    incident.investigation.timeline = [conflicting]
    with pytest.raises(ValueError, match="Conflicting"):
        export_investigation_report(incident, created_at=NOW)
