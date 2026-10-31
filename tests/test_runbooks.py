"""Phase 9 runbooks: approval binding, bounded steps, compensation and verification."""

import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from agenticops_control_tower.api import ControlTowerAPI
from agenticops_control_tower.api.http import create_app
from agenticops_control_tower.cli.main import main
from agenticops_control_tower.config.models import Operator
from agenticops_control_tower.discovery import CapabilityDiscoveryService
from agenticops_control_tower.errors import AgentNotFoundError
from agenticops_control_tower.evidence import EvidenceIngestError, EvidenceStore
from agenticops_control_tower.incidents import IncidentError, IncidentService
from agenticops_control_tower.models import AgentRegistrationPayload, EvidenceIngestRequest
from agenticops_control_tower.registry import AgentRegistry
from agenticops_control_tower.runbooks import (
    STAGING_DEPENDENCY_RECOVERY,
    CatalogError,
    RunbookCatalog,
    RunbookError,
    RunbookService,
)
from agenticops_control_tower.runbooks.models import (
    RunbookDefinition,
    RunbookPreviewRequest,
    RunbookStep,
    RunbookValidationRequest,
)
from agenticops_control_tower.runbooks.staging import StagingRunbookRuntime
from test_incidents import APPROVER, READER, WRITER, evidence

RUNBOOK = dict(runbook_id="staging.dependency_recovery", version="1.0.0")
REQUEST = RunbookPreviewRequest(**RUNBOOK, parameters={"dependency": "search"})


def register(registry, environment="staging"):
    registry.register(
        AgentRegistrationPayload(
            agent_id="staging",
            name="staging",
            environment=environment,
            runtime="fixture",
            framework="custom",
        )
    )


@pytest.fixture
def tower(tmp_path):
    path = str(tmp_path / "tower.sqlite")
    registry = AgentRegistry(path)
    register(registry)
    store = EvidenceStore(registry, path)
    runtime = StagingRunbookRuntime(str(tmp_path / "runtime.sqlite"), "staging", "search")
    runtime.fail()
    incidents = IncidentService(registry, store, path)
    runbooks = RunbookService(incidents, connectors={"staging": runtime})
    api = ControlTowerAPI(
        registry,
        CapabilityDiscoveryService(),
        evidence_store=store,
        incident_service=incidents,
        runbook_service=runbooks,
    )
    return api, runtime, path


def investigated(api):
    record = evidence(api.evidence)
    incident = api.incidents.detect("staging", record.record_id, WRITER)
    return api.incidents.investigate(incident.incident_id, WRITER)


def approved(api, request=REQUEST):
    incident = investigated(api)
    execution = api.runbooks.preview(incident.incident_id, request, WRITER)
    api.runbooks.decide(execution.execution_id, execution.preview_digest, True, APPROVER)
    return execution


def recovered(api, run_id="recovery", status="succeeded"):
    lens = evidence(api.evidence, status=status, run_id=run_id)
    evals = evidence(api.evidence, "agentic-evals", status, run_id)
    return lens.record_id, evals.record_id


def outcomes(execution):
    return [(s.step_id, s.outcome, s.rollback) for s in execution.steps]


# Definitions and catalog ---------------------------------------------------------


def test_catalog_versions_are_immutable_and_bounded():
    catalog = RunbookCatalog()
    assert [d.runbook_id for d in catalog.list()] == ["staging.dependency_recovery"]
    assert catalog.install(STAGING_DEPENDENCY_RECOVERY).digest() == (
        STAGING_DEPENDENCY_RECOVERY.digest()
    )
    changed = STAGING_DEPENDENCY_RECOVERY.model_copy(update={"title": "Different"})
    with pytest.raises(CatalogError):
        catalog.install(changed)
    with pytest.raises(CatalogError):
        catalog.get("staging.dependency_recovery", "9.9.9")
    step = dict(step_id="a", action="a.b", description="d")
    base = dict(
        runbook_id="x",
        version="1.0.0",
        title="t",
        description="d",
        environments=["staging"],
        impact="i",
        rollback="r",
    )
    with pytest.raises(ValidationError):
        RunbookDefinition(**base, steps=[RunbookStep(**step), RunbookStep(**step)])
    with pytest.raises(ValidationError, match="exceeds"):
        RunbookDefinition(
            **base,
            steps=[
                RunbookStep(**{**step, "step_id": f"s{i}"}, timeout_seconds=30, max_attempts=3)
                for i in range(2)
            ],
        )
    with pytest.raises(ValidationError):
        RunbookDefinition(
            **base, steps=[RunbookStep(**step)], parameters={"Bad-Name": {"description": "x"}}
        )
    with pytest.raises(ValidationError):
        RunbookStep(**{**step, "action": "rm -rf /"})


def test_recommendations_only_offer_installed_runbooks_with_unmet_reasons(tower):
    api, _, _ = tower
    record = evidence(api.evidence)
    incident = api.incidents.detect("staging", record.record_id, WRITER)
    [early] = api.runbooks.recommend(incident.incident_id, READER)
    assert not early.eligible and early.unmet == ["incident.investigated"]
    api.incidents.investigate(incident.incident_id, WRITER)
    [ready] = api.runbooks.recommend(incident.incident_id, READER)
    assert ready.eligible and ready.validation == "unvalidated"
    assert ready.definition_digest == STAGING_DEPENDENCY_RECOVERY.digest()
    api.runbooks.connectors.clear()
    [missing] = api.runbooks.recommend(incident.incident_id, READER)
    assert missing.unmet == ["connector.installed"]
    with pytest.raises(RunbookError, match="prerequisites"):
        api.runbooks.preview(incident.incident_id, REQUEST, WRITER)


def test_contradictory_investigation_and_production_are_not_eligible(tower):
    api, _, _ = tower
    record = evidence(api.evidence)
    evidence(api.evidence, status="succeeded", run_id="failure")
    incident = api.incidents.detect("staging", record.record_id, WRITER)
    api.incidents.investigate(incident.incident_id, WRITER)
    register(api.incidents.registry, "production")
    [rec] = api.runbooks.recommend(incident.incident_id, WRITER)
    assert "investigation.not_contradictory" in rec.unmet
    assert any("production" in reason for reason in rec.unmet)


# Preview and approval -------------------------------------------------------------


@pytest.mark.parametrize(
    "parameters",
    [{}, {"dependency": "other"}, {"dependency": "../x"}, {"dependency": "search", "extra": "x"}],
)
def test_preview_rejects_undeclared_or_unsupported_parameters(tower, parameters):
    api, runtime, _ = tower
    incident = investigated(api)
    request = RunbookPreviewRequest(**RUNBOOK, parameters=parameters)
    with pytest.raises(RunbookError):
        api.runbooks.preview(incident.incident_id, request, WRITER)
    with pytest.raises(CatalogError, match="Unknown runbook"):
        api.runbooks.preview(
            incident.incident_id, REQUEST.model_copy(update={"version": "2.0.0"}), WRITER
        )
    assert runtime.receipts() == []


def test_preview_closes_legacy_plan_and_investigation(tower):
    api, _, _ = tower
    incident = investigated(api)
    execution = api.runbooks.preview(incident.incident_id, REQUEST, WRITER)
    stored = api.incidents.get(incident.incident_id, READER)
    assert stored.runbook_execution_id == execution.execution_id
    assert stored.events[-1].event == "runbook.previewed"
    with pytest.raises(IncidentError):
        api.incidents.investigate(incident.incident_id, WRITER)
    with pytest.raises(IncidentError):
        api.incidents.preview(incident.incident_id, "search", 300, WRITER)
    with pytest.raises(RunbookError, match="live or dispatched"):
        api.runbooks.preview(incident.incident_id, REQUEST, WRITER)


@pytest.mark.parametrize(
    "failure", ["denied", "revoked", "digest", "self", "writer", "expired", "scope", "cancelled"]
)
def test_rejected_or_withdrawn_approval_never_dispatches(tower, failure):
    api, runtime, path = tower
    incident = investigated(api)
    execution = api.runbooks.preview(incident.incident_id, REQUEST, WRITER)
    eid, digest = execution.execution_id, execution.preview_digest
    if failure == "denied":
        api.runbooks.decide(eid, digest, False, APPROVER)
    elif failure == "revoked":
        api.runbooks.decide(eid, digest, True, APPROVER)
        api.runbooks.revoke(eid, APPROVER)
    elif failure == "cancelled":
        api.runbooks.decide(eid, digest, True, APPROVER)
        assert api.runbooks.cancel(eid, WRITER).status == "cancelled"
    elif failure == "expired":
        api.runbooks.decide(eid, digest, True, APPROVER)
        with sqlite3.connect(path) as db:
            stored = api.runbooks._load(db, eid)
            stored.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
            api.runbooks._save(db, stored)
    else:
        approver = {
            "digest": APPROVER,
            "self": Operator(operator_id="operator", role="approver"),
            "writer": WRITER,
            "scope": Operator(operator_id="human", role="approver", agent_ids=["other"]),
        }[failure]
        with pytest.raises(RunbookError):
            api.runbooks.decide(eid, "0" * 64 if failure == "digest" else digest, True, approver)
    with pytest.raises(RunbookError):
        api.runbooks.execute(eid, digest, WRITER)
    assert runtime.receipts() == []
    assert api.incidents.get(incident.incident_id, READER).state == "open"


def test_denied_preview_can_be_replaced_by_a_new_exact_preview(tower):
    api, _, _ = tower
    incident = investigated(api)
    first = api.runbooks.preview(incident.incident_id, REQUEST, WRITER)
    api.runbooks.decide(first.execution_id, first.preview_digest, False, APPROVER)
    [rec] = api.runbooks.recommend(incident.incident_id, READER)
    assert rec.eligible
    second = api.runbooks.preview(incident.incident_id, REQUEST, WRITER)
    assert second.preview_digest != first.preview_digest
    with pytest.raises(RunbookError):
        api.runbooks.decide(second.execution_id, first.preview_digest, True, APPROVER)
    assert [e.status for e in api.runbooks.list(incident.incident_id, READER)] == [
        "denied",
        "pending",
    ]


@pytest.mark.parametrize("change", ["environment", "connector", "unsupported", "catalog"])
def test_changed_scope_or_unavailable_connector_blocks_dispatch(tower, change):
    api, runtime, _ = tower
    execution = approved(api)
    if change == "environment":
        register(api.incidents.registry, "production")
    elif change == "connector":
        api.runbooks.connectors.clear()
    elif change == "unsupported":
        runtime.dependency = "other"
    else:
        api.runbooks.catalog = RunbookCatalog([])
    with pytest.raises(RunbookError, match="changed"):
        api.runbooks.execute(execution.execution_id, execution.preview_digest, WRITER)
    assert runtime.receipts() == []


def test_role_and_scope_checks_apply_to_every_transition(tower):
    api, _, _ = tower
    incident = investigated(api)
    with pytest.raises(RunbookError):
        api.runbooks.preview(incident.incident_id, REQUEST, READER)
    with pytest.raises(RunbookError):
        api.runbooks.preview(incident.incident_id, REQUEST, APPROVER)
    execution = api.runbooks.preview(incident.incident_id, REQUEST, WRITER)
    api.runbooks.decide(execution.execution_id, execution.preview_digest, True, APPROVER)
    outsider = Operator(operator_id="outsider", role="writer", agent_ids=["other"])
    for call in (
        lambda: api.runbooks.get(execution.execution_id, outsider),
        lambda: api.runbooks.execute(execution.execution_id, execution.preview_digest, APPROVER),
        lambda: api.runbooks.execute(execution.execution_id, execution.preview_digest, outsider),
        lambda: api.runbooks.cancel(execution.execution_id, READER),
        lambda: api.runbooks.revoke(execution.execution_id, WRITER),
    ):
        with pytest.raises(RunbookError):
            call()


# Execution outcomes ---------------------------------------------------------------


def test_successful_recovery_requires_fresh_evidence_and_probe(tower):
    api, runtime, _ = tower
    execution = approved(api)
    done = api.runbooks.execute(execution.execution_id, execution.preview_digest, WRITER)
    assert done.status == "awaiting_verification"
    assert outcomes(done) == [
        ("drain", "succeeded", "not_needed"),
        ("restore", "succeeded", "not_declared"),
        ("resume", "succeeded", "not_declared"),
    ]
    assert [k for k, _ in runtime.receipts()] == [
        f"{execution.execution_id}:{s}" for s in ("drain", "restore", "resume")
    ]
    incident = api.incidents.get(execution.incident_id, READER)
    assert (incident.state, incident.outcome) == ("awaiting_verification", "succeeded")
    resolved = api.runbooks.verify(execution.execution_id, *recovered(api), WRITER)
    assert resolved.status == "resolved"
    assert resolved.verification["probe"] is True
    assert api.incidents.get(execution.incident_id, READER).state == "resolved"
    with pytest.raises(RunbookError, match="not awaiting"):
        api.runbooks.verify(execution.execution_id, *recovered(api, "again"), WRITER)


@pytest.mark.parametrize("failure", ["lens", "probe", "same_run", "stale", "unknown_id"])
def test_failed_recovery_escalates(tower, failure):
    api, runtime, path = tower
    execution = approved(api)
    api.runbooks.execute(execution.execution_id, execution.preview_digest, WRITER)
    if failure == "unknown_id":
        with pytest.raises(EvidenceIngestError):
            api.runbooks.verify(execution.execution_id, "missing", "missing", WRITER)
        assert api.runbooks.get(execution.execution_id, READER).status == ("awaiting_verification")
        return
    if failure == "probe":
        runtime.fail()
    if failure == "stale":
        with sqlite3.connect(path) as db:
            stored = api.runbooks._load(db, execution.execution_id)
            stored.started_at = datetime.now(timezone.utc) + timedelta(minutes=1)
            api.runbooks._save(db, stored)
    ids = recovered(
        api,
        run_id="failure" if failure == "same_run" else "recovery",
        status="failed" if failure == "lens" else "succeeded",
    )
    result = api.runbooks.verify(execution.execution_id, *ids, WRITER)
    assert result.status == "escalated"
    assert api.incidents.get(execution.incident_id, READER).state == "escalated"


def test_clean_failure_retries_within_the_step_limit(tower):
    api, runtime, _ = tower
    runtime.inject("dependency.restore", "failed")
    execution = approved(api)
    done = api.runbooks.execute(execution.execution_id, execution.preview_digest, WRITER)
    assert done.status == "awaiting_verification"
    assert done.steps[1].attempts == 2
    assert [e.event for e in done.events].count("runbook.step.restore.retrying") == 1


def test_exhausted_clean_failures_compensate_completed_steps(tower):
    api, runtime, _ = tower
    runtime.inject("dependency.restore", "failed", "failed")
    execution = approved(api)
    done = api.runbooks.execute(execution.execution_id, execution.preview_digest, WRITER)
    assert done.status == "escalated"
    assert outcomes(done) == [
        ("drain", "succeeded", "succeeded"),
        ("restore", "failed", "not_declared"),
        ("resume", "skipped", "not_declared"),
    ]
    assert runtime.state() == {"available": False, "drained": False}
    incident = api.incidents.get(execution.incident_id, READER)
    assert (incident.state, incident.outcome) == ("escalated", "failed")
    with pytest.raises(RunbookError):
        api.runbooks.verify(execution.execution_id, *recovered(api), WRITER)


@pytest.mark.parametrize(
    ("fault", "outcome"),
    [("partial_failure", "partial_failure"), ("raise", "unknown"), ("hang", "timed_out")],
)
def test_unknown_outcomes_stop_without_retry_or_rollback(tower, fault, outcome):
    api, runtime, _ = tower
    quick = STAGING_DEPENDENCY_RECOVERY.model_copy(
        update={
            "version": "1.0.1",
            "steps": [
                s.model_copy(update={"timeout_seconds": 1})
                for s in STAGING_DEPENDENCY_RECOVERY.steps
            ],
        }
    )
    api.runbooks.catalog.install(quick)
    runtime.hang_seconds = 1.5
    runtime.inject("dependency.restore", fault)
    execution = approved(api, REQUEST.model_copy(update={"version": "1.0.1"}))
    done = api.runbooks.execute(execution.execution_id, execution.preview_digest, WRITER)
    assert done.status == "reconciliation_required"
    assert outcomes(done) == [
        ("drain", "succeeded", "not_needed"),
        ("restore", outcome, "not_declared"),
        ("resume", "skipped", "not_declared"),
    ]
    assert done.steps[1].attempts == 1
    incident = api.incidents.get(execution.incident_id, READER)
    assert (incident.state, incident.outcome) == ("escalated", "partial_failure")
    assert runtime.state()["drained"] is True


def test_failed_rollback_requires_reconciliation(tower):
    api, runtime, _ = tower
    runtime.inject("dependency.restore", "failed", "failed")
    runtime.inject("traffic.resume", "partial_failure")
    execution = approved(api)
    done = api.runbooks.execute(execution.execution_id, execution.preview_digest, WRITER)
    assert done.status == "reconciliation_required"
    assert done.steps[0].rollback == "partial_failure"


def test_repeated_and_concurrent_execute_dispatch_once(tower):
    api, runtime, _ = tower
    execution = approved(api)
    with ThreadPoolExecutor(4) as pool:
        results = list(
            pool.map(
                lambda _: _attempt(api, execution),
                range(4),
            )
        )
    assert results.count("awaiting_verification") == 1
    assert results.count("rejected") == 3
    assert len(runtime.receipts()) == 3
    with pytest.raises(RunbookError):
        api.runbooks.execute(execution.execution_id, execution.preview_digest, WRITER)


def _attempt(api, execution):
    try:
        return api.runbooks.execute(execution.execution_id, execution.preview_digest, WRITER).status
    except RunbookError:
        return "rejected"


def test_cancellation_stops_before_the_next_step_and_compensates(tower):
    api, runtime, _ = tower
    execution = approved(api)
    original = runtime.run

    def cancel_during_drain(key, action, parameters):
        result = original(key, action, parameters)
        if action == "traffic.drain" and not key.endswith(":rollback"):
            api.runbooks.cancel(execution.execution_id, APPROVER)
        return result

    runtime.run = cancel_during_drain
    done = api.runbooks.execute(execution.execution_id, execution.preview_digest, WRITER)
    assert done.status == "cancelled"
    assert done.cancel_requested_by == "human"
    assert outcomes(done) == [
        ("drain", "succeeded", "succeeded"),
        ("restore", "skipped", "not_declared"),
        ("resume", "skipped", "not_declared"),
    ]
    assert runtime.state() == {"available": False, "drained": False}
    assert api.incidents.get(execution.incident_id, READER).state == "escalated"
    with pytest.raises(RunbookError):
        api.runbooks.cancel(execution.execution_id, WRITER)


def test_interrupted_execution_is_reconciled_after_its_lease_without_replay(tower):
    api, runtime, path = tower
    execution = approved(api)
    api.runbooks._claim(execution.execution_id, execution.preview_digest, WRITER)
    with pytest.raises(RunbookError, match="lease"):
        api.runbooks.reconcile(execution.execution_id, WRITER)
    with pytest.raises(RunbookError):
        api.runbooks.execute(execution.execution_id, execution.preview_digest, WRITER)
    # A new process sees the durable claim after the lease elapses.
    restarted = RunbookService(
        IncidentService(api.incidents.registry, api.evidence, path),
        connectors={"staging": runtime},
    )
    with sqlite3.connect(path) as db:
        stored = restarted._load(db, execution.execution_id)
        stored.lease_expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        restarted._save(db, stored)
    done = restarted.reconcile(execution.execution_id, WRITER)
    assert done.status == "reconciliation_required"
    assert {s.outcome for s in done.steps} == {"skipped"}
    assert runtime.receipts() == []
    incident = api.incidents.get(execution.incident_id, READER)
    assert (incident.state, incident.outcome) == ("escalated", "unknown")
    assert incident.events[-1].event == "runbook.reconciliation_required"


def test_incident_view_joins_runbook_history(tower):
    api, _, _ = tower
    execution = approved(api)
    api.runbooks.execute(execution.execution_id, execution.preview_digest, WRITER)
    view = api.operations.incident_view(execution.incident_id, READER)
    assert [r.execution_id for r in view["runbooks"]] == [execution.execution_id]
    events = [e["event"] for e in view["timeline"]]
    assert "runbook.step.restore.succeeded" in events
    assert events.index("runbook.claimed") < events.index("runbook.awaiting_verification")


# Chaos and Evals validation -------------------------------------------------------


def chaos(store, run_id="validation", completed=True):
    now = datetime.now(timezone.utc)
    return store.ingest(
        EvidenceIngestRequest.model_validate(
            dict(
                link=dict(
                    agent_id="staging",
                    source="agentic-chaos",
                    source_version="0.9.0",
                    artifact_type="chaos_report",
                    artifact_ref="chaos:" + run_id + str(completed),
                    run_id=run_id,
                    observed_at=now.isoformat(),
                ),
                artifact=dict(
                    id="exp-" + run_id,
                    name="dependency outage",
                    start_time=now.isoformat(),
                    end_time=now.isoformat() if completed else None,
                    chaos_events=[{"type": "tool_failure"}],
                ),
            )
        )
    ).record


def test_validation_records_completed_chaos_and_passing_same_run_evals(tower):
    api, _, _ = tower
    report = chaos(api.evidence)
    gate = evidence(api.evidence, "agentic-evals", "succeeded", "validation")
    request = RunbookValidationRequest(
        agent_id="staging", chaos_evidence_id=report.record_id, evals_evidence_id=gate.record_id
    )
    with pytest.raises(RunbookError):
        api.runbooks.record_validation(**RUNBOOK, request=request, operator=READER)
    validation = api.runbooks.record_validation(**RUNBOOK, request=request, operator=WRITER)
    assert validation.definition_digest == STAGING_DEPENDENCY_RECOVERY.digest()
    incident = investigated(api)
    [rec] = api.runbooks.recommend(incident.incident_id, READER)
    assert rec.validation == "validated"
    assert rec.validation_ids == [validation.validation_id]


@pytest.mark.parametrize("problem", ["incomplete", "other_run", "failed_gate", "swapped"])
def test_validation_rejects_unsupported_evidence(tower, problem):
    api, _, _ = tower
    report = chaos(api.evidence, completed=problem != "incomplete")
    gate = evidence(
        api.evidence,
        "agentic-evals",
        "failed" if problem == "failed_gate" else "succeeded",
        "other" if problem == "other_run" else "validation",
    )
    ids = (
        (gate.record_id, report.record_id)
        if problem == "swapped"
        else (report.record_id, gate.record_id)
    )
    request = RunbookValidationRequest(
        agent_id="staging", chaos_evidence_id=ids[0], evals_evidence_id=ids[1]
    )
    with pytest.raises(RunbookError):
        api.runbooks.record_validation(**RUNBOOK, request=request, operator=WRITER)
    assert api.runbooks.validations(**RUNBOOK) == []


# HTTP, CLI and durability ----------------------------------------------------------


@pytest.fixture
def client(tower):
    api, runtime, _ = tower
    return (
        TestClient(
            create_app(
                api,
                read_token="r",
                write_token="w",
                approval_token="a",
                detection_interval_seconds=0,
            )
        ),
        api,
        runtime,
    )


def auth(token):
    return {"Authorization": "Bearer " + token}


def test_http_runbook_flow_with_separate_roles(client):
    http, api, runtime = client
    incident = investigated(api)
    base = f"/incidents/{incident.incident_id}"
    assert http.get("/runbooks", headers=auth("r")).json()[0]["version"] == "1.0.0"
    assert http.get(base + "/runbooks", headers=auth("r")).json()[0]["eligible"] is True
    body = REQUEST.model_dump()
    assert http.post(base + "/runbooks/preview", json=body, headers=auth("r")).status_code == 409
    assert http.post(base + "/runbooks/preview", json=body, headers=auth("a")).status_code == 409
    preview = http.post(base + "/runbooks/preview", json=body, headers=auth("w")).json()
    path = "/runbook-executions/" + preview["execution_id"]
    digest = {"preview_digest": preview["preview_digest"]}
    approval = {**digest, "approved": True}
    assert http.post(path + "/approval", json=approval, headers=auth("w")).status_code == 409
    assert http.post(path + "/execute", json=digest, headers=auth("w")).status_code == 409
    assert http.post(path + "/approval", json=approval, headers=auth("a")).json()["status"] == (
        "approved"
    )
    assert http.post(path + "/execute", json=digest, headers=auth("a")).status_code == 409
    executed = http.post(path + "/execute", json=digest, headers=auth("w")).json()
    assert executed["status"] == "awaiting_verification"
    assert http.post(path + "/execute", json=digest, headers=auth("w")).status_code == 409
    lens, evals = recovered(api)
    verified = http.post(
        path + "/verify",
        json={"lens_evidence_id": lens, "evals_evidence_id": evals},
        headers=auth("w"),
    ).json()
    assert verified["status"] == "resolved"
    assert http.get(path, headers=auth("r")).json()["status"] == "resolved"
    history = http.get(base + "/runbook-executions", headers=auth("r")).json()
    assert [h["execution_id"] for h in history] == [preview["execution_id"]]
    assert http.get(base + "/view", headers=auth("r")).json()["runbooks"][0]["status"] == (
        "resolved"
    )
    assert http.post(path + "/unknown", headers=auth("w")).status_code == 404
    assert http.post(path + "/reconcile", headers=auth("w")).status_code == 409
    assert http.get("/runbooks", headers={}).status_code == 401
    assert http.get(path, headers={}).status_code in (401, 403)
    assert len(runtime.receipts()) == 3


def test_http_validation_routes(client):
    http, api, _ = client
    report = chaos(api.evidence)
    gate = evidence(api.evidence, "agentic-evals", "succeeded", "validation")
    body = {
        "agent_id": "staging",
        "chaos_evidence_id": report.record_id,
        "evals_evidence_id": gate.record_id,
    }
    route = "/runbooks/staging.dependency_recovery/1.0.0/validations"
    assert http.post(route, json=body, headers=auth("r")).status_code == 409
    assert http.post(route, json=body, headers=auth("w")).status_code == 200
    assert len(http.get(route, headers=auth("r")).json()) == 1
    missing = "/runbooks/staging.dependency_recovery/9.0.0/validations"
    assert http.get(missing, headers=auth("r")).status_code == 404
    assert http.post(missing, json=body, headers=auth("w")).status_code == 404


def test_cli_runbook_commands(client, tmp_path, capsys):
    http, api, _ = client
    incident = investigated(api)
    preview_file = tmp_path / "preview.json"
    preview_file.write_text(REQUEST.model_dump_json())
    assert main(["--token", "r", "runbooks", "catalog"], client=http) == 0
    assert json.loads(capsys.readouterr().out)[0]["runbook_id"] == RUNBOOK["runbook_id"]
    assert main(["--token", "r", "runbooks", "recommend", incident.incident_id], client=http) == 0
    capsys.readouterr()
    command = ["--token", "w", "runbooks", "preview", incident.incident_id, str(preview_file)]
    assert main(command, client=http) == 0
    preview = json.loads(capsys.readouterr().out)
    eid = preview["execution_id"]
    approval = tmp_path / "approval.json"
    approval.write_text(json.dumps({"preview_digest": preview["preview_digest"], "approved": True}))
    assert main(["--token", "a", "runbooks", "approval", eid, str(approval)], client=http) == 0
    execute = tmp_path / "execute.json"
    execute.write_text(json.dumps({"preview_digest": preview["preview_digest"]}))
    assert main(["--token", "w", "runbooks", "execute", eid, str(execute)], client=http) == 0
    capsys.readouterr()
    lens, evals = recovered(api, status="failed")
    verify = tmp_path / "verify.json"
    verify.write_text(json.dumps({"lens_evidence_id": lens, "evals_evidence_id": evals}))
    assert main(["--token", "w", "runbooks", "verify", eid, str(verify)], client=http) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "escalated"
    assert main(["--token", "r", "runbooks", "get", eid], client=http) == 0
    assert main(["--token", "r", "runbooks", "history", incident.incident_id], client=http) == 0
    capsys.readouterr()
    assert main(["--token", "r", "runbooks", "validations", *RUNBOOK.values()], client=http) == 0
    assert json.loads(capsys.readouterr().out) == []


def test_cli_snapshot_mode_rejects_runbooks(tmp_path):
    with pytest.raises(SystemExit):
        main(["--snapshot", str(tmp_path / "missing.json"), "runbooks", "catalog"])


def test_executions_survive_restart(tower):
    api, runtime, path = tower
    execution = approved(api)
    restarted = RunbookService(
        IncidentService(api.incidents.registry, api.evidence, path),
        connectors={"staging": runtime},
    )
    stored = restarted.get(execution.execution_id, READER)
    assert stored.status == "approved"
    done = restarted.execute(execution.execution_id, execution.preview_digest, WRITER)
    assert done.status == "awaiting_verification"


def test_api_rejects_runbook_service_over_other_incident_storage(tower):
    api, _, _ = tower
    other = RunbookService(IncidentService(api.incidents.registry, api.evidence))
    with pytest.raises(ValueError, match="share"):
        ControlTowerAPI(
            api.incidents.registry,
            CapabilityDiscoveryService(),
            evidence_store=api.evidence,
            incident_service=api.incidents,
            runbook_service=other,
        )


def test_connectors_install_only_for_registered_deployments(tower):
    api, runtime, _ = tower
    api.runbooks.connectors.clear()
    with pytest.raises(AgentNotFoundError):
        api.runbooks.install("unknown", runtime)
    api.runbooks.install("staging", runtime)
    assert api.runbooks.connectors == {"staging": runtime}
    with pytest.raises(RunbookError, match="Unknown runbook execution"):
        api.runbooks.get("missing", READER)


def test_legacy_reconcile_cannot_override_a_running_runbook(tower):
    api, runtime, _ = tower
    execution = approved(api)
    api.runbooks._claim(execution.execution_id, execution.preview_digest, WRITER)
    with pytest.raises(IncidentError, match="execution lease"):
        api.incidents.reconcile(execution.incident_id, WRITER)
    assert api.runbooks.get(execution.execution_id, READER).status == "running"
    assert api.incidents.get(execution.incident_id, READER).state == "executing"


def test_parameter_values_are_length_bounded_and_previews_need_open_incidents(tower):
    from agenticops_control_tower.runbooks.models import ParameterSpec

    spec = ParameterSpec(description="x", pattern=r"^.*$", max_length=5)
    assert spec.accepts("abcde") and not spec.accepts("abcdef")
    api, _, _ = tower
    lax = STAGING_DEPENDENCY_RECOVERY.model_copy(
        update={"version": "1.1.0", "prerequisites": ["connector.installed"]}
    )
    api.runbooks.catalog.install(lax)
    incident = investigated(api)
    with api.incidents._transaction() as db:
        stored = api.incidents._load(db, incident.incident_id)
        stored.state = "escalated"
        api.incidents._save(db, stored)
    with pytest.raises(RunbookError, match="incident.open"):
        api.runbooks.preview(
            incident.incident_id, REQUEST.model_copy(update={"version": "1.1.0"}), WRITER
        )


def test_http_preview_returns_404_for_unknown_versions(client):
    http, api, _ = client
    incident = investigated(api)
    body = REQUEST.model_copy(update={"version": "9.0.0"}).model_dump()
    route = f"/incidents/{incident.incident_id}/runbooks/preview"
    assert http.post(route, json=body, headers=auth("w")).status_code == 404
