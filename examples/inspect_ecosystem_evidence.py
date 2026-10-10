"""Run with `uv run python examples/inspect_ecosystem_evidence.py` from Tower."""

from datetime import datetime, timezone

from agenticops_control_tower.models import AgentRegistrationPayload
from agenticops_control_tower.models.evidence import EvidenceLink
from agenticops_control_tower.snapshot import create_api

api = create_api()
api.register_agent(
    AgentRegistrationPayload(
        agent_id="payment-agent",
        name="Payments",
        environment="staging",
        runtime="custom",
        framework="custom",
        status="healthy",
    )
)
link = EvidenceLink(
    agent_id="payment-agent",
    source="agentic-sidecar",
    source_version="0.6.0",
    artifact_type="decision",
    artifact_ref="decision:payment-run:tool-1",
    observed_at=datetime.now(timezone.utc),
    run_id="payment-run",
)
# An existing producer decision, not a decision computed by Tower.
result = api.summarize_evidence(
    link,
    {
        "status": "BLOCK",
        "risk": "HIGH",
        "reason": "Producer policy denied this action",
    },
)
print(result.model_dump_json(indent=2))
assert api.get_status().healthy_agents == 1
