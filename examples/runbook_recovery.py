"""Versioned runbook recovery through real HTTP routes; no siblings or network required.

Run: uv run python examples/runbook_recovery.py
Pass --fail-step to exhaust a clean-failure retry and observe compensation, or
--fail-verification to observe escalation after a successful runbook.
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from fastapi.testclient import TestClient

from agenticops_control_tower.api import ControlTowerAPI
from agenticops_control_tower.api.http import create_app
from agenticops_control_tower.discovery import CapabilityDiscoveryService
from agenticops_control_tower.evidence import EvidenceStore
from agenticops_control_tower.incidents import IncidentService
from agenticops_control_tower.registry import AgentRegistry
from agenticops_control_tower.runbooks import RunbookService
from agenticops_control_tower.runbooks.staging import StagingRunbookRuntime


def walkthrough(directory: Path, fail_step: bool = False, fail_verification: bool = False):
    database = str(directory / "tower.db")
    registry = AgentRegistry(database)
    store = EvidenceStore(registry, database)
    incidents = IncidentService(registry, store, database)
    runtime = StagingRunbookRuntime(str(directory / "runtime.db"), "staging", "search")
    api = ControlTowerAPI(
        registry,
        CapabilityDiscoveryService(),
        evidence_store=store,
        incident_service=incidents,
        runbook_service=RunbookService(incidents, connectors={"staging": runtime}),
    )
    client = TestClient(
        create_app(
            api,
            read_token="demo-reader",
            write_token="demo-writer",
            approval_token="demo-human",
            detection_interval_seconds=0,
        )
    )
    writer = {"Authorization": "Bearer demo-writer"}
    human = {"Authorization": "Bearer demo-human"}

    def call(method, path, payload=None, headers=writer):
        response = client.request(method, path, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

    def push(source, run_id, ok):
        now = datetime.now(timezone.utc).isoformat()
        if source == "agenticlens":
            artifact = dict(
                schema_version="1.0",
                run_id=run_id,
                application_name="dependency fixture",
                status="succeeded" if ok else "failed",
                task_success=ok,
                error_type=None if ok else "ConnectionError",
                spans=[],
            )
            extra = {}
        else:
            artifact = dict(
                schema_version="1.0",
                suite_name="dependency recovery",
                suite_version="1",
                cases=[],
                created_at=now,
                summary=dict(
                    total_cases=1,
                    passed_cases=int(ok),
                    failed_cases=int(not ok),
                    pass_rate=float(ok),
                    average_score=float(ok),
                    average_latency_ms=0,
                ),
            )
            extra = {"gate": dict(passed=ok, reasons=[], observed={})}
        link = dict(
            agent_id="staging",
            source=source,
            source_version="0.11.0" if source == "agenticlens" else "0.10.0",
            artifact_type="run" if source == "agenticlens" else "evaluation_report",
            artifact_ref=f"{source}:{run_id}",
            run_id=run_id,
            observed_at=now,
        )
        result = call("POST", "/evidence", dict(link=link, artifact=artifact, **extra))
        return result["record"]["record_id"]

    call(
        "POST",
        "/agents/register",
        dict(
            agent_id="staging",
            name="dependency fixture",
            environment="staging",
            runtime="sqlite-staging-fixture",
            framework="custom",
        ),
    )
    runtime.fail()
    failed_id = push("agenticlens", "failed-" + uuid4().hex, False)
    incident = call("POST", "/incidents/detect", dict(agent_id="staging", evidence_id=failed_id))
    base = "/incidents/" + incident["incident_id"]
    call("POST", base + "/investigate")
    [recommendation] = call("GET", base + "/runbooks")
    preview = call(
        "POST",
        base + "/runbooks/preview",
        dict(
            runbook_id=recommendation["runbook_id"],
            version=recommendation["version"],
            parameters={"dependency": "search"},
        ),
    )
    execution = "/runbook-executions/" + preview["execution_id"]
    digest = dict(preview_digest=preview["preview_digest"])
    call("POST", execution + "/approval", {**digest, "approved": True}, human)
    if fail_step:
        runtime.inject("dependency.restore", "failed", "failed")
    result = call("POST", execution + "/execute", digest)
    if result["status"] == "awaiting_verification":
        if fail_verification:
            runtime.fail()
        run_id = "recovery-" + uuid4().hex
        healthy = runtime.probe("staging", {"dependency": "search"})
        result = call(
            "POST",
            execution + "/verify",
            dict(
                lens_evidence_id=push("agenticlens", run_id, healthy),
                evals_evidence_id=push("agentic-evals", run_id, healthy),
            ),
        )
    view = call("GET", base + "/view")
    return dict(
        runbook=f"{result['runbook_id']}@{result['version']}",
        status=result["status"],
        incident=view["incident"]["state"],
        steps=[
            dict(step=s["step_id"], outcome=s["outcome"], rollback=s["rollback"])
            for s in result["steps"]
        ],
        runtime=runtime.state(),
        timeline=[e["event"] for e in view["timeline"] if e["event"].startswith("runbook.")],
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fail-step", action="store_true")
    parser.add_argument("--fail-verification", action="store_true")
    args = parser.parse_args()
    with TemporaryDirectory() as directory:
        print(
            json.dumps(
                walkthrough(Path(directory), args.fail_step, args.fail_verification), indent=2
            )
        )
