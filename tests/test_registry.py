from datetime import datetime, timezone
from pathlib import Path

from agenticops_control_tower.api import ControlTowerAPI
from agenticops_control_tower.discovery import CapabilityDiscoveryService
from agenticops_control_tower.errors import AgentNotFoundError
from agenticops_control_tower.models import (
    AgentRegistrationPayload,
    AgentStatus,
    FleetStatusSummary,
    HeartbeatPayload,
)
from agenticops_control_tower.registry import AgentRegistry
from agenticops_control_tower.snapshot import load_snapshot
from agenticops_control_tower.status import StatusService


def test_registry_and_discovery_flow() -> None:
    registry = AgentRegistry()
    discovery = CapabilityDiscoveryService()
    api = ControlTowerAPI(registry=registry, discovery=discovery)
    registered_at = datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc)
    last_seen = datetime(2026, 8, 15, 12, 5, tzinfo=timezone.utc)

    api.register_agent(
        AgentRegistrationPayload(
            agent_id="payment-agent",
            name="payment-agent",
            environment="staging",
            runtime="local-python",
            framework="langgraph",
            capabilities={"agenticlens": "0.8.1"},
            runtime_metadata={"python_version": "3.12"},
            package_metadata={"build_sha": "abc123"},
            registered_at=registered_at,
        )
    )

    api.record_heartbeat(
        "payment-agent",
        HeartbeatPayload(
            status=AgentStatus.HEALTHY,
            last_seen=last_seen,
            capabilities={
                "agentic-sidecar": "0.4.0",
            },
            runtime_metadata={"host": "devbox-01"},
            package_metadata={"release_channel": "staging"},
        ),
    )

    agent = api.get_agent("payment-agent")
    assert agent.status is AgentStatus.HEALTHY
    assert agent.last_seen == last_seen
    assert agent.registered_at == registered_at
    assert agent.heartbeat_count == 1
    assert api.get_agent_capabilities("payment-agent") == {
        "agentic-sidecar": "0.4.0",
        "agenticlens": "0.8.1",
    }
    assert agent.runtime_metadata == {
        "host": "devbox-01",
        "python_version": "3.12",
    }
    assert agent.package_metadata == {
        "build_sha": "abc123",
        "release_channel": "staging",
    }


def test_capability_inventory_is_aggregated_across_agents() -> None:
    registry = AgentRegistry()
    discovery = CapabilityDiscoveryService()
    api = ControlTowerAPI(registry=registry, discovery=discovery)

    api.register_agent(
        AgentRegistrationPayload(
            agent_id="payment-agent",
            name="payment-agent",
            environment="production",
            runtime="aws-lambda",
            framework="langgraph",
            capabilities={
                "agenticlens": "0.8.1",
                "deep-agentic-core-mcp": "0.2.0",
            },
        )
    )
    api.register_agent(
        AgentRegistrationPayload(
            agent_id="support-agent",
            name="support-agent",
            environment="production",
            runtime="docker",
            framework="openai-agents",
            capabilities={
                "agenticlens": "0.8.2",
                "agentic-sidecar": "0.4.0",
            },
        )
    )

    capabilities = api.list_capabilities()

    assert [capability.capability for capability in capabilities] == [
        "agentic-sidecar",
        "agenticlens",
        "deep-agentic-core-mcp",
    ]
    assert capabilities[1].versions == ["0.8.1", "0.8.2"]
    assert capabilities[1].agent_ids == ["payment-agent", "support-agent"]


def test_status_summary_and_filters_share_the_same_control_model() -> None:
    registry = AgentRegistry()
    discovery = CapabilityDiscoveryService()
    api = ControlTowerAPI(
        registry=registry,
        discovery=discovery,
        status_service=StatusService(discovery),
    )

    api.register_agent(
        AgentRegistrationPayload(
            agent_id="healthy-agent",
            name="healthy-agent",
            environment="production",
            runtime="docker",
            framework="langgraph",
            capabilities={"agenticlens": "0.8.1", "agentic-sidecar": "0.4.0"},
        )
    )
    api.register_agent(
        AgentRegistrationPayload(
            agent_id="unhealthy-agent",
            name="unhealthy-agent",
            environment="staging",
            runtime="local-python",
            framework="openai-agents",
            capabilities={"agenticlens": "0.8.2"},
        )
    )
    api.record_heartbeat(
        "healthy-agent",
        HeartbeatPayload(
            status=AgentStatus.HEALTHY,
        ),
    )
    api.record_heartbeat(
        "unhealthy-agent",
        HeartbeatPayload(
            status=AgentStatus.UNHEALTHY,
        ),
    )

    unhealthy_agents = api.list_agents(status=AgentStatus.UNHEALTHY)
    production_agents = api.list_agents(environment="production")
    lens_agents = api.list_agents(capability="agenticlens")
    missing_sidecar = api.list_agents(missing_capability="agentic-sidecar")
    status_summary = api.get_status()
    assert isinstance(status_summary, FleetStatusSummary)

    assert [agent.agent_id for agent in unhealthy_agents] == ["unhealthy-agent"]
    assert [agent.agent_id for agent in production_agents] == ["healthy-agent"]
    assert [agent.agent_id for agent in lens_agents] == [
        "healthy-agent",
        "unhealthy-agent",
    ]
    assert [agent.agent_id for agent in missing_sidecar] == ["unhealthy-agent"]
    assert status_summary.total_agents == 2
    assert status_summary.healthy_agents == 1
    assert status_summary.unhealthy_agents == 1
    assert {capability.capability for capability in status_summary.capabilities} == {
        "agenticlens",
        "agentic-sidecar",
    }


def test_unknown_agent_raises_domain_error() -> None:
    registry = AgentRegistry()
    discovery = CapabilityDiscoveryService()
    api = ControlTowerAPI(registry=registry, discovery=discovery)

    try:
        api.get_agent("missing-agent")
    except AgentNotFoundError as exc:
        assert exc.agent_id == "missing-agent"
    else:
        raise AssertionError("Expected AgentNotFoundError")


def test_snapshot_uses_capture_time_when_event_times_are_missing(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "fleet.json"
    snapshot_path.write_text(
        """
        {
          "captured_at": "2026-08-15T12:00:00Z",
          "registrations": [
            {
              "agent_id": "payment-agent",
              "name": "payment-agent",
              "environment": "production",
              "runtime": "aws-lambda",
              "framework": "langgraph"
            }
          ],
          "heartbeats": [
            {
              "agent_id": "payment-agent",
              "heartbeat": {
                "status": "healthy"
              }
            }
          ]
        }
        """.strip()
    )

    api = load_snapshot(snapshot_path)
    agent = api.get_agent("payment-agent")

    assert agent.registered_at.isoformat() == "2026-08-15T12:00:00+00:00"
    assert agent.last_seen is not None
    assert agent.last_seen.isoformat() == "2026-08-15T12:00:00+00:00"
