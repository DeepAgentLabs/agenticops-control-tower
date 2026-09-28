"""HTTP-reachable surface over `ControlTowerAPI` (v0.1's "read-only API").

Optional: requires the `api` extra (`pip install agenticops-control-tower[api]`).
The base package stays free of a web-framework dependency -- this module is
only imported when a caller explicitly asks for the HTTP app (e.g. via the
CLI's `serve` command, or a test importing `create_app` directly).

Implements the roadmap's "Suggested initial surface" from ROADMAP.md's v0.1
section: `POST /agents/register`, `POST /agents/{id}/heartbeat`,
`GET /agents`, `GET /agents/{id}`, `GET /capabilities`.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from agenticops_control_tower.api.surface import ControlTowerAPI
from agenticops_control_tower.discovery import CapabilityDiscoveryService
from agenticops_control_tower.errors import AgentNotFoundError
from agenticops_control_tower.models import (
    AgentRecord,
    AgentRegistrationPayload,
    HeartbeatPayload,
)
from agenticops_control_tower.registry import AgentRegistry


def create_app(api: ControlTowerAPI | None = None) -> FastAPI:
    """Build the FastAPI app.

    Pass `api` to share state with an existing registry/discovery pair (used
    by tests to inspect state set up before the app was created); otherwise a
    fresh in-memory `ControlTowerAPI` backs the app for its process lifetime
    -- there is no persistence across restarts (see ROADMAP_AUDIT.md).
    """
    control_api = api or ControlTowerAPI(
        registry=AgentRegistry(), discovery=CapabilityDiscoveryService()
    )
    app = FastAPI(
        title="AgenticOps Control Tower",
        description=(
            "Agent registry, heartbeat, and capability discovery API "
            "(v0.1 scaffold -- in-memory, no persistence, no auth)."
        ),
        version="0.1.0",
    )

    @app.post("/agents/register", response_model=AgentRecord, status_code=201)
    def register_agent(agent: AgentRegistrationPayload) -> AgentRecord:
        return control_api.register_agent(agent)

    @app.post("/agents/{agent_id}/heartbeat", response_model=AgentRecord)
    def send_heartbeat(agent_id: str, payload: HeartbeatPayload) -> AgentRecord:
        try:
            return control_api.record_heartbeat(agent_id, payload)
        except AgentNotFoundError as exc:
            raise HTTPException(status_code=404, detail=f"unknown agent: {agent_id}") from exc

    @app.get("/agents", response_model=list[AgentRecord])
    def list_agents() -> list[AgentRecord]:
        return control_api.list_agents()

    @app.get("/agents/{agent_id}", response_model=AgentRecord)
    def get_agent(agent_id: str) -> AgentRecord:
        try:
            return control_api.get_agent(agent_id)
        except AgentNotFoundError as exc:
            raise HTTPException(status_code=404, detail=f"unknown agent: {agent_id}") from exc

    @app.get("/capabilities")
    def list_capabilities() -> dict[str, list[str]]:
        return control_api.list_all_capabilities()

    return app
