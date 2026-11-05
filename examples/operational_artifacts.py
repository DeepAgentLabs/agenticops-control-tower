"""Offline native-to-AIOS projection; grants no authority or stable conformance."""

import json
from datetime import datetime, timezone

from agenticops_control_tower.incidents.export import export_investigation_report
from agenticops_control_tower.incidents.models import Incident
from agenticops_control_tower.models.evidence import EvidenceLink, EvidenceRecord, EvidenceSummary

at = datetime(2026, 11, 4, 18, tzinfo=timezone.utc)
link = EvidenceLink(
    agent_id="agent-1",
    source="agenticlens",
    source_version="0.14.0",
    artifact_type="run",
    artifact_ref="run-1",
    observed_at=at,
)
evidence = EvidenceRecord(
    record_id="e-1",
    ingested_at=at,
    ingested_by="operator",
    summary=EvidenceSummary(link=link, availability="available"),
)
incident = Incident(incident_id="incident-1", agent_id="agent-1", detection=evidence)
print(json.dumps(export_investigation_report(incident, created_at=at), indent=2))
