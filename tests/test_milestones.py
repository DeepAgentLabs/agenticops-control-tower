"""Milestone acceptance: durability, authorization and shared fleet views."""

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agenticops_control_tower.api.http import create_app
from agenticops_control_tower.cli.main import main
from agenticops_control_tower.models import AgentRegistrationPayload, HeartbeatPayload
from agenticops_control_tower.registry import AgentRegistry

PAYLOAD = dict(
    agent_id="a", name="Agent A", environment="staging", runtime="custom", framework="custom"
)


def test_restart_and_concurrent_heartbeats(tmp_path: Path) -> None:
    path = tmp_path / "registry.sqlite"
    registry = AgentRegistry(path)
    registry.register(AgentRegistrationPayload(**PAYLOAD))
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(
            pool.map(
                lambda _: AgentRegistry(path).heartbeat("a", HeartbeatPayload(status="healthy")),
                range(20),
            )
        )
    restored = AgentRegistry(path).get("a")
    assert restored.heartbeat_count == 20
    assert restored.status == "healthy"
    restored.name = "changed"
    assert registry.get("a").name == "Agent A"
    client = TestClient(create_app(database_path=str(path)))
    assert client.get("/status").json()["healthy_agents"] == 1


def test_reader_writer_authorization(tmp_path: Path) -> None:
    client = TestClient(
        create_app(database_path=str(tmp_path / "db"), read_token="reader", write_token="writer")
    )
    for path in ("/agents", "/agents/a", "/capabilities", "/status"):
        assert client.get(path).status_code == 401
    assert client.post("/agents/register", json=PAYLOAD).status_code == 401
    reader = {"Authorization": "Bearer reader"}
    writer = {"Authorization": "Bearer writer"}
    assert client.post("/agents/register", json=PAYLOAD, headers=reader).status_code == 403
    assert client.post("/agents/register", json=PAYLOAD, headers=writer).status_code == 201
    assert client.get("/agents", headers=reader).status_code == 200
    assert client.post("/agents/a/heartbeat", json={}, headers=reader).status_code == 403
    assert (
        client.post("/agents/a/heartbeat", json={"status": "healthy"}, headers=writer).status_code
        == 200
    )
    assert client.get("/status", headers={"Authorization": "Bearer invalid"}).status_code == 401
    assert client.get("/status", headers=writer).json()["healthy_agents"] == 1
    assert (
        TestClient(create_app(read_token="reader"))
        .post("/agents/register", json=PAYLOAD, headers=reader)
        .status_code
        == 403
    )


def test_cli_status_filters_and_snapshot(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    client = TestClient(create_app(read_token="reader", write_token="writer"))
    client.post("/agents/register", json=PAYLOAD, headers={"Authorization": "Bearer writer"})
    main(["--token", "reader", "status"], client=client)
    assert json.loads(capsys.readouterr().out)["unknown_agents"] == 1
    main(["--token", "reader", "agents", "list", "--environment", "production"], client=client)
    assert json.loads(capsys.readouterr().out) == []
    main(["agents", "list", "--missing-capability", "lens"], client=client)
    assert len(json.loads(capsys.readouterr().out)) == 1
    assert client.get("/agents?status=invalid").status_code == 422
    snapshot = tmp_path / "fleet.json"
    snapshot.write_text(
        json.dumps({"captured_at": "2026-10-10T12:00:00Z", "registrations": [PAYLOAD]})
    )
    main(["--snapshot", str(snapshot), "status"])
    assert json.loads(capsys.readouterr().out)["total_agents"] == 1
    with pytest.raises(SystemExit):
        main(["--snapshot", str(snapshot), "agents", "register", "unused"])


@pytest.mark.parametrize("example", list(Path("examples").glob("sample_agent_registration*.json")))
def test_registration_examples(example: Path) -> None:
    response = TestClient(create_app()).post(
        "/agents/register", json=json.loads(example.read_text())
    )
    assert response.status_code == 201
