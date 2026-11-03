"""Push-based execution evidence: optional Lens verification and durable redaction."""

import builtins
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agenticops_control_tower.adapters.evidence import summarize_evidence
from agenticops_control_tower.api.http import create_app
from agenticops_control_tower.evidence import EvidenceStore
from agenticops_control_tower.evidence.posture import native_tallies
from agenticops_control_tower.models import AgentRegistrationPayload, EvidenceIngestRequest
from agenticops_control_tower.registry import AgentRegistry

KEY = b"execution-demo-key-at-least-32-bytes"
FIXTURE = Path(__file__).parent / "fixtures" / "lens-execution-bundle.json"


@pytest.fixture
def lens(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).parents[2] / "agenticlens" / "src"))
    pytest.importorskip("agenticlens.integrity.execution")


def request():
    return EvidenceIngestRequest.model_validate(
        {
            "link": {
                "agent_id": "payments",
                "source": "agenticlens",
                "source_version": "unreleased",
                "artifact_type": "execution_bundle",
                "artifact_ref": "local:capture",
                "observed_at": datetime.now(timezone.utc),
                "run_id": "run-evidence",
                "spec_version": "0.4-draft",
            },
            "artifact": json.loads(FIXTURE.read_text()),
        }
    )


def registry(path):
    result = AgentRegistry(str(path))
    result.register(
        AgentRegistrationPayload(
            agent_id="payments",
            name="Payments",
            environment="staging",
            runtime="python",
            framework="custom",
            status="healthy",
        )
    )
    return result


def test_durable_verification_and_causal_links(lens, tmp_path):
    path = tmp_path / "tower.db"
    agents = registry(path)
    store = EvidenceStore(agents, str(path), trusted_lens_keys={"test": KEY})
    stored = store.ingest(request()).record
    assert stored.summary.availability == "available"
    assert stored.summary.details["verification"]["status"] == "verified"
    assert stored.summary.details["causal_links"][0]["decision_id"] == "decision-1"
    assert "private" not in stored.model_dump_json()
    reread = EvidenceStore(agents, str(path)).get_record("payments", stored.record_id)
    assert reread == stored
    assert native_tallies("agenticlens", [stored])["verification_counts"]["verified"] == 1
    assert agents.get("payments").status.value == "healthy"


def test_unknown_and_failed_stay_distinct(lens):
    observation = request()
    unknown = summarize_evidence(observation.link, observation.artifact)
    assert unknown.availability == "unavailable"
    assert unknown.details["verification"]["status"] == "unknown"
    observation.artifact["artifact"]["events"].pop()
    failed = summarize_evidence(
        observation.link, observation.artifact, trusted_lens_keys={"test": KEY}
    )
    assert failed.details["verification"]["status"] == "failed"
    assert failed.details["causal_links"] == []


def test_optional_dependency_absent(monkeypatch):
    original = builtins.__import__

    def blocked(name, *args, **kwargs):
        if name.startswith("agenticlens"):
            raise ImportError("not installed")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked)
    observation = request()
    summary = summarize_evidence(observation.link, observation.artifact)
    assert summary.details["verification"]["status"] == "unknown"
    assert summary.availability == "unavailable"


def test_http_uses_host_trust_and_existing_auth(lens, tmp_path):
    application = create_app(
        database_path=str(tmp_path / "http.db"),
        read_token="reader",
        write_token="writer",
        detection_interval_seconds=0,
        trusted_lens_keys={"test": KEY},
    )
    with TestClient(application) as client:
        agent = {
            "agent_id": "payments",
            "name": "Payments",
            "environment": "staging",
            "runtime": "python",
            "framework": "custom",
            "status": "healthy",
        }
        assert client.post(
            "/agents/register", json=agent, headers={"Authorization": "Bearer writer"}
        ).status_code in (200, 201)
        body = request().model_dump(mode="json")
        denied = client.post("/evidence", json=body, headers={"Authorization": "Bearer reader"})
        assert denied.status_code == 403
        accepted = client.post("/evidence", json=body, headers={"Authorization": "Bearer writer"})
        assert accepted.status_code in (200, 201), accepted.text
        assert (
            accepted.json()["record"]["summary"]["details"]["verification"]["status"] == "verified"
        )


def test_host_trust_store_from_environment(lens, monkeypatch, tmp_path):
    keys = tmp_path / "keys.json"
    keys.write_text(json.dumps({"test": KEY.hex()}))
    monkeypatch.setenv("AGENTICOPS_LENS_TRUST_STORE", str(keys))
    app = create_app(detection_interval_seconds=0)
    assert app is not None
    keys.write_text("invalid")
    with pytest.raises(ValueError, match="Invalid host Lens trust store"):
        create_app(detection_interval_seconds=0)
