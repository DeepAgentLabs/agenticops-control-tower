"""Read-only console, version policy and authorization acceptance tests."""

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
from fastapi.testclient import TestClient  # noqa: E402

from agenticops_control_tower.api import ControlTowerAPI  # noqa: E402
from agenticops_control_tower.api.http import create_app  # noqa: E402
from agenticops_control_tower.discovery import CapabilityDiscoveryService  # noqa: E402
from agenticops_control_tower.models import AgentRegistrationPayload  # noqa: E402
from agenticops_control_tower.registry import AgentRegistry  # noqa: E402


@pytest.fixture
def console_client() -> TestClient:
    api = ControlTowerAPI(AgentRegistry(), CapabilityDiscoveryService())
    for agent_id, version in [
        ("old", "0.4.9"),
        ("current", "0.5.0"),
        ("new", "0.10.0"),
        ("prerelease", "0.5.0rc1"),
        ("invalid", "development"),
        ("missing", None),
    ]:
        api.register(
            AgentRegistrationPayload(
                agent_id=agent_id,
                name=agent_id,
                environment="staging",
                runtime="python",
                framework="custom",
                capabilities={"agenticlens": version} if version else {},
            )
        )
    return TestClient(create_app(api, read_token="reader", write_token="writer"))


def test_public_shell_has_no_inventory_and_assets_are_served(console_client: TestClient) -> None:
    response = console_client.get("/console")
    assert response.status_code == 200
    assert response.url.path == "/console/"
    assert "Fleet inventory" in response.text
    assert "default-src 'self'" in response.headers["content-security-policy"]
    assert response.headers["cache-control"] == "no-store"
    assert "0.4.9" not in response.text
    assert console_client.get("/console/assets/console.css").status_code == 200
    script = console_client.get("/console/assets/console.js")
    assert script.status_code == 200
    assert 'method: "GET"' in script.text
    assert "localStorage" not in script.text
    assert console_client.get("/console/assets/../../api/http.py").status_code == 404


@pytest.mark.parametrize(
    "path",
    [
        "/agents",
        "/status",
        "/capabilities",
        "/agents/old",
        "/versions?capability=agenticlens&minimum_version=0.5.0",
        "/agents/old/evidence",
    ],
)
def test_console_reads_require_existing_authorization(
    console_client: TestClient,
    path: str,
) -> None:
    assert console_client.get(path).status_code == 401
    assert console_client.get(path, headers={"Authorization": "Bearer wrong"}).status_code == 401
    for token in ["reader", "writer"]:
        assert (
            console_client.get(path, headers={"Authorization": f"Bearer {token}"}).status_code
            == 200
        )


def test_version_policy_uses_pep440_and_preserves_missing_unknown(
    console_client: TestClient,
) -> None:
    headers = {"Authorization": "Bearer reader"}
    response = console_client.get(
        "/versions?capability=agenticlens&minimum_version=0.5.0&environment=staging",
        headers=headers,
    )
    results = {row["agent_id"]: row["assessment"] for row in response.json()}
    assert results == {
        "old": "outdated",
        "current": "meets_minimum",
        "new": "meets_minimum",
        "prerelease": "outdated",
        "invalid": "unknown",
        "missing": "missing",
    }
    assert (
        console_client.get(
            "/versions?capability=agenticlens&minimum_version=0.5.0&environment=production",
            headers=headers,
        ).json()
        == []
    )
    for query in [
        "capability=agenticlens&minimum_version=garbage",
        "capability=&minimum_version=1",
    ]:
        assert console_client.get(f"/versions?{query}", headers=headers).status_code == 422
    assert console_client.post("/agents/old/heartbeat", json={}, headers=headers).status_code == 403


def test_evidence_readiness_is_honest_and_checks_agent(console_client: TestClient) -> None:
    headers = {"Authorization": "Bearer reader"}
    evidence = console_client.get("/agents/old/evidence", headers=headers).json()
    assert evidence["availability"] == "unavailable"
    assert "not collected or persisted" in evidence["reason"]
    assert console_client.get("/agents/absent/evidence", headers=headers).status_code == 404
