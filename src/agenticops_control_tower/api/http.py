"""Optional authenticated HTTP surface over the shared control model."""

from __future__ import annotations

import os
from secrets import compare_digest

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles

from agenticops_control_tower import __version__
from agenticops_control_tower.api.surface import ControlTowerAPI
from agenticops_control_tower.console.app import ASSET_DIRECTORY
from agenticops_control_tower.discovery import CapabilityDiscoveryService
from agenticops_control_tower.errors import AgentNotFoundError
from agenticops_control_tower.models import (
    AgentRecord,
    AgentRegistrationPayload,
    AgentStatus,
    FleetStatusSummary,
    HeartbeatPayload,
)
from agenticops_control_tower.models.version import VersionAssessment
from agenticops_control_tower.registry import AgentRegistry


def create_app(
    api: ControlTowerAPI | None = None,
    *,
    database_path: str | None = None,
    read_token: str | None = None,
    write_token: str | None = None,
) -> FastAPI:
    """Configure SQLite and reader/writer bearer tokens via arguments or environment.

    With no tokens configured, local development access is anonymous.
    Reader-only configuration rejects writes. Writer tokens also permit reads.
    """
    database_path = database_path or os.environ.get("AGENTICOPS_DATABASE")
    read_token = read_token or os.environ.get("AGENTICOPS_READ_TOKEN")
    write_token = write_token or os.environ.get("AGENTICOPS_WRITE_TOKEN")
    control_api = api or ControlTowerAPI(AgentRegistry(database_path), CapabilityDiscoveryService())
    app = FastAPI(title="AgenticOps Control Tower", version=__version__)
    bearer = HTTPBearer(auto_error=False)

    def authorize(credentials: HTTPAuthorizationCredentials | None, *, write: bool) -> None:
        if not read_token and not write_token:
            return
        if credentials is None:
            raise HTTPException(
                401, "Bearer token required", headers={"WWW-Authenticate": "Bearer"}
            )
        token = credentials.credentials
        is_writer = bool(write_token and compare_digest(token.encode(), write_token.encode()))
        is_reader = bool(read_token and compare_digest(token.encode(), read_token.encode()))
        if not is_writer and not is_reader:
            raise HTTPException(401, "Invalid bearer token", headers={"WWW-Authenticate": "Bearer"})
        if write and not is_writer:
            raise HTTPException(403, "Writer token required")

    def read_access(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> None:
        authorize(credentials, write=False)

    def write_access(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> None:
        authorize(credentials, write=True)

    @app.post(
        "/agents/register",
        response_model=AgentRecord,
        status_code=201,
        dependencies=[Depends(write_access)],
    )
    def register_agent(agent: AgentRegistrationPayload) -> AgentRecord:
        return control_api.register(agent)

    @app.post(
        "/agents/{agent_id}/heartbeat",
        response_model=AgentRecord,
        dependencies=[Depends(write_access)],
    )
    def send_heartbeat(agent_id: str, payload: HeartbeatPayload) -> AgentRecord:
        try:
            return control_api.heartbeat(agent_id, payload)
        except AgentNotFoundError as exc:
            raise HTTPException(404, f"unknown agent: {agent_id}") from exc

    @app.get("/agents", response_model=list[AgentRecord], dependencies=[Depends(read_access)])
    def list_agents(
        status: AgentStatus | None = None,
        environment: str | None = None,
        capability: str | None = None,
        missing_capability: str | None = None,
    ) -> list[AgentRecord]:
        return control_api.list_agents(
            status=status,
            environment=environment,
            capability=capability,
            missing_capability=missing_capability,
        )

    @app.get("/agents/{agent_id}", response_model=AgentRecord, dependencies=[Depends(read_access)])
    def get_agent(agent_id: str) -> AgentRecord:
        try:
            return control_api.get_agent(agent_id)
        except AgentNotFoundError as exc:
            raise HTTPException(404, f"unknown agent: {agent_id}") from exc

    @app.get("/capabilities", dependencies=[Depends(read_access)])
    def list_capabilities() -> dict[str, list[str]]:
        return control_api.list_all_capabilities()

    @app.get("/status", response_model=FleetStatusSummary, dependencies=[Depends(read_access)])
    def get_status(environment: str | None = None) -> FleetStatusSummary:
        return control_api.get_status(environment=environment)

    @app.get(
        "/versions", response_model=list[VersionAssessment], dependencies=[Depends(read_access)]
    )
    def versions(
        capability: str = Query(min_length=1),
        minimum_version: str = Query(min_length=1),
        environment: str | None = None,
    ) -> list[VersionAssessment]:
        try:
            return control_api.assess_versions(capability, minimum_version, environment=environment)
        except ValueError as exc:
            raise HTTPException(422, "Minimum version must be a valid PEP 440 version") from exc

    @app.get("/agents/{agent_id}/evidence", dependencies=[Depends(read_access)])
    def evidence_readiness(agent_id: str) -> dict[str, str]:
        try:
            control_api.get_agent(agent_id)
        except AgentNotFoundError as exc:
            raise HTTPException(404, f"unknown agent: {agent_id}") from exc
        return {
            "agent_id": agent_id,
            "availability": "unavailable",
            "reason": "Evidence is not collected or persisted by this service. "
            "Native artifact readers are available through the Python API.",
        }

    @app.get("/console", include_in_schema=False)
    def console_redirect() -> RedirectResponse:
        return RedirectResponse("./console/")

    @app.get("/console/", include_in_schema=False)
    def console() -> FileResponse:
        # The public shell contains no inventory. Data reads use bearer authorization.
        return FileResponse(
            ASSET_DIRECTORY / "index.html",
            headers={
                "Cache-Control": "no-store",
                "Content-Security-Policy": "default-src 'self'; script-src 'self'; "
                "style-src 'self'; connect-src 'self'; object-src 'none'; "
                "base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
                "Referrer-Policy": "no-referrer",
                "X-Content-Type-Options": "nosniff",
            },
        )

    app.mount("/console/assets", StaticFiles(directory=ASSET_DIRECTORY), name="console-assets")
    return app
