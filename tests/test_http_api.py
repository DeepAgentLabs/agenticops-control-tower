"""Tests for the optional HTTP API (`api` extra). Skips automatically if
`fastapi`/`httpx` aren't installed, matching the sibling-repo pattern for
optional-extra tests (see e.g. agentic-chaos's agenticlens integration test).
"""

from __future__ import annotations

import pytest

fastapi = pytest.importorskip("fastapi")
httpx = pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from agenticops_control_tower.api.http import create_app  # noqa: E402


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def test_register_then_list_and_get(client: TestClient) -> None:
    payload = {
        "agent_id": "payment-agent",
        "name": "payment-agent",
        "environment": "staging",
        "runtime": "local-python",
        "framework": "langgraph",
    }
    response = client.post("/agents/register", json=payload)
    assert response.status_code == 201
    assert response.json()["agent_id"] == "payment-agent"

    listed = client.get("/agents")
    assert listed.status_code == 200
    assert [a["agent_id"] for a in listed.json()] == ["payment-agent"]

    fetched = client.get("/agents/payment-agent")
    assert fetched.status_code == 200
    assert fetched.json()["status"] == "unknown"


def test_heartbeat_updates_status_and_capabilities(client: TestClient) -> None:
    client.post(
        "/agents/register",
        json={
            "agent_id": "fraud-agent",
            "name": "fraud-agent",
            "environment": "production",
            "runtime": "kubernetes",
            "framework": "crewai",
        },
    )

    response = client.post(
        "/agents/fraud-agent/heartbeat",
        json={
            "status": "healthy",
            "capabilities": {"agenticlens": "0.8.1", "agentic-sidecar": "0.4.0"},
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

    capabilities = client.get("/capabilities")
    assert capabilities.status_code == 200
    assert capabilities.json() == {
        "agentic-sidecar": ["0.4.0"],
        "agenticlens": ["0.8.1"],
    }


def test_unknown_agent_returns_404(client: TestClient) -> None:
    assert client.get("/agents/does-not-exist").status_code == 404
    assert (
        client.post("/agents/does-not-exist/heartbeat", json={"status": "healthy"}).status_code
        == 404
    )


def test_capabilities_aggregate_across_agents(client: TestClient) -> None:
    for agent_id, version in [("agent-a", "0.8.0"), ("agent-b", "0.8.1")]:
        client.post(
            "/agents/register",
            json={
                "agent_id": agent_id,
                "name": agent_id,
                "environment": "staging",
                "runtime": "local-python",
                "framework": "custom",
            },
        )
        client.post(
            f"/agents/{agent_id}/heartbeat",
            json={"status": "healthy", "capabilities": {"agenticlens": version}},
        )

    response = client.get("/capabilities")
    assert response.json() == {"agenticlens": ["0.8.0", "0.8.1"]}
