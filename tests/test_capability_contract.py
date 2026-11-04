"""Candidate negotiation and real Python/Node HTTP clients, including durable readback."""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
uvicorn = pytest.importorskip("uvicorn")

from fastapi.testclient import TestClient  # noqa: E402
from jsonschema import Draft202012Validator  # noqa: E402

from agenticops_control_tower.api.http import create_app  # noqa: E402


def test_contract_authorization_schemas_and_detached_response() -> None:
    client = TestClient(create_app(read_token="reader", write_token="writer"))
    assert client.get("/contracts/capabilities").status_code == 401
    response = client.get("/contracts/capabilities", headers={"Authorization": "Bearer reader"})
    assert response.status_code == 200
    contract = response.json()
    assert contract["contract_version"] == "tower.capabilities.v1"
    assert contract["maturity"] == "candidate"
    for schema in contract["schemas"].values():
        Draft202012Validator.check_schema(schema)
    registration = {
        "agent_id": "worker",
        "name": "worker",
        "environment": "test",
        "runtime": "custom",
        "framework": "custom",
    }
    Draft202012Validator(contract["schemas"]["registration"]).validate(registration)
    headers = {"Authorization": "Bearer writer"}
    record = client.post("/agents/register", json=registration, headers=headers).json()
    Draft202012Validator(contract["schemas"]["agent"]).validate(record)
    assert (
        client.post(
            "/agents/worker/heartbeat", json={"status": "invalid"}, headers=headers
        ).status_code
        == 422
    )
    assert client.post("/agents/missing/heartbeat", json={}, headers=headers).status_code == 404


def test_python_and_node_runtime_roundtrip(tmp_path: Path) -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js required for the second runtime")
    database = str(tmp_path / "registry.sqlite")
    app = create_app(
        database_path=database,
        read_token="reader",
        write_token="writer",
        detection_interval_seconds=0,
    )
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, log_level="error"))
    thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
    thread.start()
    try:
        deadline = time.monotonic() + 10
        while not server.started:
            if not thread.is_alive() or time.monotonic() >= deadline:
                pytest.fail("HTTP server did not start")
            time.sleep(0.01)
        env = dict(
            os.environ,
            AGENTICOPS_API_URL=f"http://127.0.0.1:{port}",
            AGENTICOPS_WRITE_TOKEN="writer",
        )
        examples = Path(__file__).resolve().parents[1] / "examples" / "runtimes"
        for command in (
            [sys.executable, str(examples / "python_worker.py")],
            [node, str(examples / "node_worker.mjs")],
        ):
            result = subprocess.run(
                command, env=env, check=True, capture_output=True, text=True, timeout=20
            )
            assert json.loads(result.stdout)["heartbeat_count"] == 1
    finally:
        server.should_exit = True
        thread.join(timeout=10)
        sock.close()
    assert not thread.is_alive()
    restarted = TestClient(create_app(database_path=database, read_token="reader"))
    headers = {"Authorization": "Bearer reader"}
    records = restarted.get("/agents", headers=headers).json()
    assert [(a["runtime"], a["status"]) for a in records] == [
        ("nodejs", "degraded"),
        ("cpython", "healthy"),
    ]
    assert restarted.get("/capabilities", headers=headers).json() == {"custom.worker": ["1.0"]}


def test_candidate_contract_snapshot() -> None:
    """Changes to the candidate baseline require an explicit compatibility review."""
    from agenticops_control_tower.models.contract import CapabilityContract

    baseline = Path(__file__).parent / "fixtures" / "capability-contract-v1.json"
    assert CapabilityContract().model_dump() == json.loads(baseline.read_text())
