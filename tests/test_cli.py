import json
from pathlib import Path

import pytest

from agenticops_control_tower.cli.main import main


def test_cli_agents_list_filters_by_status(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    snapshot_path = _write_snapshot(tmp_path)

    exit_code = main(
        [
            "--snapshot",
            str(snapshot_path),
            "agents",
            "list",
            "--status",
            "healthy",
            "--format",
            "json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert [agent["agent_id"] for agent in payload] == ["payment-agent"]


def test_cli_status_reports_fleet_rollup(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    snapshot_path = _write_snapshot(tmp_path)

    exit_code = main(
        [
            "--snapshot",
            str(snapshot_path),
            "status",
            "--format",
            "json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["total_agents"] == 2
    assert payload["healthy_agents"] == 1
    assert payload["unhealthy_agents"] == 1
    assert payload["capability_count"] == 3


def test_cli_agents_list_renders_default_table(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    snapshot_path = _write_snapshot(tmp_path)

    exit_code = main(
        [
            "--snapshot",
            str(snapshot_path),
            "agents",
            "list",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "AGENT ID" in captured.out
    assert "payment-agent" in captured.out
    assert "support-agent" in captured.out


def test_cli_agent_get_renders_default_detail_table(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    snapshot_path = _write_snapshot(tmp_path)

    exit_code = main(
        [
            "--snapshot",
            str(snapshot_path),
            "agents",
            "get",
            "payment-agent",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Agent ID: payment-agent" in captured.out
    assert "Capabilities:" in captured.out
    assert "agenticlens: 0.8.1" in captured.out


def test_cli_capabilities_list_renders_default_table(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    snapshot_path = _write_snapshot(tmp_path)

    exit_code = main(
        [
            "--snapshot",
            str(snapshot_path),
            "capabilities",
            "list",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "CAPABILITY" in captured.out
    assert "agenticlens" in captured.out
    assert "deep-agentic-core-mcp" in captured.out


def test_cli_status_renders_default_fleet_table(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    snapshot_path = _write_snapshot(tmp_path)

    exit_code = main(
        [
            "--snapshot",
            str(snapshot_path),
            "status",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Total Agents: 2" in captured.out
    assert "Capability Coverage:" in captured.out
    assert "agenticlens" in captured.out


def test_cli_status_agent_renders_default_detail_table(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    snapshot_path = _write_snapshot(tmp_path)

    exit_code = main(
        [
            "--snapshot",
            str(snapshot_path),
            "status",
            "support-agent",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Agent ID: support-agent" in captured.out
    assert "Status: unhealthy" in captured.out
    assert "Capability Count: 1" in captured.out


def test_cli_unknown_agent_returns_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    snapshot_path = _write_snapshot(tmp_path)

    exit_code = main(
        [
            "--snapshot",
            str(snapshot_path),
            "agents",
            "get",
            "missing-agent",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "missing-agent" in captured.err


def _write_snapshot(tmp_path: Path) -> Path:
    snapshot = {
        "registrations": [
            {
                "agent_id": "payment-agent",
                "name": "payment-agent",
                "environment": "production",
                "runtime": "aws-lambda",
                "framework": "langgraph",
                "capabilities": {
                    "agenticlens": "0.8.1",
                    "agentic-sidecar": "0.4.0",
                },
            },
            {
                "agent_id": "support-agent",
                "name": "support-agent",
                "environment": "staging",
                "runtime": "docker",
                "framework": "openai-agents",
                "capabilities": {
                    "agenticlens": "0.8.2",
                },
            },
        ],
        "heartbeats": [
            {
                "agent_id": "payment-agent",
                "heartbeat": {
                    "status": "healthy",
                    "capabilities": {
                        "deep-agentic-core-mcp": "0.2.0",
                    },
                },
            },
            {
                "agent_id": "support-agent",
                "heartbeat": {
                    "status": "unhealthy",
                },
            },
        ],
    }
    snapshot_path = tmp_path / "fleet.json"
    snapshot_path.write_text(json.dumps(snapshot))
    return snapshot_path
