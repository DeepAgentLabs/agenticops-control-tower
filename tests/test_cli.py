"""CLI tests against an in-process ASGI app -- no real server/socket needed.
Skips automatically if `httpx`/`fastapi` aren't installed (`api` extra)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("httpx")
pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from agenticops_control_tower.api.http import create_app  # noqa: E402
from agenticops_control_tower.cli.main import main  # noqa: E402


@pytest.fixture
def api_client() -> TestClient:
    # FastAPI's TestClient (not a bare httpx.Client(transport=ASGITransport))
    # -- it behaves like an httpx.Client (same .get()/.post()/.is_error
    # surface main()'s handlers rely on) but handles the sync/ASGI bridging
    # itself, which a hand-built ASGITransport can't in this httpx version
    # (sync Client.close()/. __enter__() call transport methods ASGITransport
    # no longer implements -- it's async-only here).
    return TestClient(create_app())


def _write_json(tmp_path: Path, name: str, payload: dict) -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(payload))
    return path


def test_register_list_and_get(
    tmp_path: Path, api_client: TestClient, capsys: pytest.CaptureFixture[str]
) -> None:
    payload_file = _write_json(
        tmp_path,
        "agent.json",
        {
            "agent_id": "payment-agent",
            "name": "payment-agent",
            "environment": "staging",
            "runtime": "local-python",
            "framework": "langgraph",
        },
    )

    exit_code = main(["agents", "register", str(payload_file)], client=api_client)
    assert exit_code == 0
    registered = json.loads(capsys.readouterr().out)
    assert registered["agent_id"] == "payment-agent"

    exit_code = main(["agents", "list"], client=api_client)
    assert exit_code == 0
    listed = json.loads(capsys.readouterr().out)
    assert [a["agent_id"] for a in listed] == ["payment-agent"]

    exit_code = main(["agents", "get", "payment-agent"], client=api_client)
    assert exit_code == 0
    fetched = json.loads(capsys.readouterr().out)
    assert fetched["agent_id"] == "payment-agent"


def test_heartbeat_and_capabilities(
    tmp_path: Path, api_client: TestClient, capsys: pytest.CaptureFixture[str]
) -> None:
    agent_file = _write_json(
        tmp_path,
        "agent.json",
        {
            "agent_id": "fraud-agent",
            "name": "fraud-agent",
            "environment": "production",
            "runtime": "kubernetes",
            "framework": "crewai",
        },
    )
    main(["agents", "register", str(agent_file)], client=api_client)
    capsys.readouterr()

    heartbeat_file = _write_json(
        tmp_path,
        "heartbeat.json",
        {"status": "healthy", "capabilities": {"agenticlens": "0.8.1"}},
    )
    exit_code = main(["agents", "heartbeat", "fraud-agent", str(heartbeat_file)], client=api_client)
    assert exit_code == 0
    updated = json.loads(capsys.readouterr().out)
    assert updated["status"] == "healthy"

    exit_code = main(["capabilities", "list"], client=api_client)
    assert exit_code == 0
    capabilities = json.loads(capsys.readouterr().out)
    assert capabilities == {"agenticlens": ["0.8.1"]}


def test_get_unknown_agent_exits_nonzero(api_client: TestClient) -> None:
    with pytest.raises(SystemExit):
        main(["agents", "get", "does-not-exist"], client=api_client)


def test_missing_client_dependency_without_extra(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without a caller-supplied client, a missing `httpx` (no `api` extra
    installed) should fail with a clear message, not an ImportError
    traceback. `sys.modules["httpx"] = None` is the standard trick to make
    `import httpx` raise ImportError even though it's already imported and
    cached for the rest of this test session."""
    import sys

    monkeypatch.setitem(sys.modules, "httpx", None)

    with pytest.raises(SystemExit, match=r"\[api\]"):
        main(["agents", "list"])
