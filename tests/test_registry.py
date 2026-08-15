from agenticops_control_tower.api import ControlTowerAPI
from agenticops_control_tower.discovery import CapabilityDiscoveryService
from agenticops_control_tower.models import AgentRecord, AgentStatus, HeartbeatPayload
from agenticops_control_tower.registry import AgentRegistry


def test_registry_and_discovery_flow() -> None:
    registry = AgentRegistry()
    discovery = CapabilityDiscoveryService()
    api = ControlTowerAPI(registry=registry, discovery=discovery)

    registry.register(
        AgentRecord(
            agent_id="payment-agent",
            name="payment-agent",
            environment="staging",
            runtime="local-python",
            framework="langgraph",
        )
    )

    registry.heartbeat(
        "payment-agent",
        HeartbeatPayload(
            status=AgentStatus.HEALTHY,
            capabilities={
                "agenticlens": "0.8.1",
                "agentic-sidecar": "0.4.0",
            },
        ),
    )

    agent = api.get_agent("payment-agent")
    assert agent.status is AgentStatus.HEALTHY
    assert api.list_capabilities("payment-agent") == {
        "agentic-sidecar": "0.4.0",
        "agenticlens": "0.8.1",
    }
