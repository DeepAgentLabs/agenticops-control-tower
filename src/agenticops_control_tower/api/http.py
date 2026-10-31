"""Optional authenticated HTTP surface over the shared control model."""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from secrets import compare_digest

from fastapi import Depends, FastAPI, HTTPException, Query, Response
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles

from agenticops_control_tower import __version__
from agenticops_control_tower.api.limits import BodySizeLimit
from agenticops_control_tower.api.surface import ControlTowerAPI
from agenticops_control_tower.bulk import BulkRequest
from agenticops_control_tower.config.models import ActionRequest, ApprovalRequest, Operator
from agenticops_control_tower.config.service import ConfigurationError, ConfigurationService
from agenticops_control_tower.console.app import ASSET_DIRECTORY
from agenticops_control_tower.discovery import CapabilityDiscoveryService
from agenticops_control_tower.errors import AgentNotFoundError
from agenticops_control_tower.evidence import (
    DEFAULT_STALE_AFTER_SECONDS,
    MAX_HISTORY_LIMIT,
    MAX_STALE_AFTER_SECONDS,
    EvidenceIngestError,
    EvidenceStore,
)
from agenticops_control_tower.incidents import IncidentError, IncidentService
from agenticops_control_tower.incidents.models import (
    DecisionRequest,
    DetectionRequest,
    ExecuteRequest,
    PlanRequest,
    VerificationRequest,
)
from agenticops_control_tower.models import (
    AgentEvidencePosture,
    AgentRecord,
    AgentRegistrationPayload,
    AgentStatus,
    EvidenceIngestRequest,
    EvidenceIngestResult,
    EvidenceRecord,
    FleetEvidencePosture,
    FleetStatusSummary,
    HeartbeatPayload,
)
from agenticops_control_tower.models.evidence import EvidenceSource
from agenticops_control_tower.models.version import VersionAssessment
from agenticops_control_tower.registry import AgentRegistry
from agenticops_control_tower.runbooks import CatalogError
from agenticops_control_tower.runbooks.models import (
    RunbookDecisionRequest,
    RunbookExecuteRequest,
    RunbookPreviewRequest,
    RunbookValidationRequest,
    RunbookVerificationRequest,
)

MAX_EVIDENCE_BYTES = 1024 * 1024


def create_app(
    api: ControlTowerAPI | None = None,
    *,
    database_path: str | None = None,
    read_token: str | None = None,
    write_token: str | None = None,
    approval_token: str | None = None,
    detection_interval_seconds: float = 30,
) -> FastAPI:
    """Configure SQLite and reader/writer bearer tokens via arguments or environment.

    With no tokens configured, local development access is anonymous.
    Reader-only configuration rejects writes. Writer tokens also permit reads.
    """
    database_path = database_path or os.environ.get("AGENTICOPS_DATABASE")
    read_token = read_token or os.environ.get("AGENTICOPS_READ_TOKEN")
    write_token = write_token or os.environ.get("AGENTICOPS_WRITE_TOKEN")
    approval_token = approval_token or os.environ.get("AGENTICOPS_APPROVAL_TOKEN")
    if approval_token and approval_token in (read_token, write_token):
        raise ValueError("Approval token must differ from reader and writer tokens")
    if api is None:
        registry = AgentRegistry(database_path)
        evidence = EvidenceStore(registry, database_path)
        api = ControlTowerAPI(
            registry,
            CapabilityDiscoveryService(),
            configuration_service=ConfigurationService(registry, database_path),
            evidence_store=evidence,
            incident_service=IncidentService(registry, evidence, database_path),
        )
    control_api = api
    if detection_interval_seconds < 0:
        raise ValueError("Detection interval cannot be negative")

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        stop = asyncio.Event()

        async def poll() -> None:
            import logging

            detector = Operator(operator_id="tower-detector", role="writer")
            while not stop.is_set():
                try:
                    await asyncio.to_thread(control_api.operations.evaluate, detector)
                except Exception:
                    logging.getLogger(__name__).exception("Live detection scan failed")
                with suppress(asyncio.TimeoutError):
                    await asyncio.wait_for(stop.wait(), timeout=detection_interval_seconds)

        task = asyncio.create_task(poll()) if detection_interval_seconds else None
        try:
            yield
        finally:
            stop.set()
            if task:
                await task

    app = FastAPI(title="AgenticOps Control Tower", version=__version__, lifespan=lifespan)
    # Enforced in ASGI middleware so oversized or unsized bodies are never buffered.
    app.add_middleware(
        BodySizeLimit, paths=frozenset({"/evidence", "/bulk/preview"}), max_bytes=MAX_EVIDENCE_BYTES
    )
    bearer = HTTPBearer(auto_error=False)

    def authorize(credentials: HTTPAuthorizationCredentials | None, *, write: bool) -> None:
        if not read_token and not write_token and not approval_token:
            return
        if credentials is None:
            raise HTTPException(
                401, "Bearer token required", headers={"WWW-Authenticate": "Bearer"}
            )
        token = credentials.credentials
        is_writer = bool(write_token and compare_digest(token.encode(), write_token.encode()))
        is_reader = bool(read_token and compare_digest(token.encode(), read_token.encode()))
        is_approver = bool(
            approval_token and compare_digest(token.encode(), approval_token.encode())
        )
        if not is_writer and not is_reader and not is_approver:
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

    stale_after = Query(DEFAULT_STALE_AFTER_SECONDS, ge=1, le=MAX_STALE_AFTER_SECONDS)

    @app.post(
        "/evidence",
        response_model=EvidenceIngestResult,
        status_code=201,
        dependencies=[Depends(write_access)],
    )
    def ingest_evidence(payload: EvidenceIngestRequest, response: Response) -> EvidenceIngestResult:
        ingested_by = (
            "http-writer" if (read_token or write_token or approval_token) else "anonymous"
        )
        try:
            result = control_api.ingest_evidence(payload, ingested_by=ingested_by)
        except AgentNotFoundError as exc:
            raise HTTPException(404, f"unknown agent: {payload.link.agent_id}") from exc
        except EvidenceIngestError as exc:
            raise HTTPException(422, str(exc)) from exc
        if not result.created:
            response.status_code = 200
        return result

    @app.get(
        "/agents/{agent_id}/evidence",
        response_model=AgentEvidencePosture,
        dependencies=[Depends(read_access)],
    )
    def agent_evidence_posture(
        agent_id: str, stale_after_seconds: int = stale_after
    ) -> AgentEvidencePosture:
        try:
            return control_api.agent_posture(agent_id, stale_after_seconds=stale_after_seconds)
        except AgentNotFoundError as exc:
            raise HTTPException(404, f"unknown agent: {agent_id}") from exc

    @app.get(
        "/agents/{agent_id}/evidence/history",
        response_model=list[EvidenceRecord],
        dependencies=[Depends(read_access)],
    )
    def agent_evidence_history(
        agent_id: str,
        source: EvidenceSource | None = None,
        limit: int = Query(50, ge=1, le=MAX_HISTORY_LIMIT),
    ) -> list[EvidenceRecord]:
        try:
            return control_api.evidence_history(agent_id, source=source, limit=limit)
        except AgentNotFoundError as exc:
            raise HTTPException(404, f"unknown agent: {agent_id}") from exc

    @app.get("/posture", response_model=FleetEvidencePosture, dependencies=[Depends(read_access)])
    def fleet_posture(
        environment: str | None = None, stale_after_seconds: int = stale_after
    ) -> FleetEvidencePosture:
        return control_api.fleet_posture(
            environment=environment, stale_after_seconds=stale_after_seconds
        )

    def configuration_operator(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    ) -> Operator:
        authorize(credentials, write=False)
        if credentials is None:
            raise HTTPException(403, "Configuration actions require configured bearer credentials")
        token = credentials.credentials.encode()
        if write_token and compare_digest(token, write_token.encode()):
            return Operator(operator_id="http-writer", role="writer")
        if approval_token and compare_digest(token, approval_token.encode()):
            return Operator(operator_id="http-approver", role="approver")
        return Operator(operator_id="http-reader", role="reader")

    @app.get("/agents/{agent_id}/config/{capability}", dependencies=[Depends(read_access)])
    def configuration(agent_id: str, capability: str) -> object:
        try:
            return control_api.config.get(agent_id, capability)
        except AgentNotFoundError as exc:
            raise HTTPException(404, str(exc)) from exc

    @app.get("/agents/{agent_id}/audit", dependencies=[Depends(read_access)])
    def configuration_audit(agent_id: str) -> object:
        try:
            return control_api.config.audit(agent_id)
        except AgentNotFoundError as exc:
            raise HTTPException(404, str(exc)) from exc

    @app.post("/actions/preview")
    def preview_action(
        request: ActionRequest,
        operator: Operator = Depends(configuration_operator),
    ) -> object:
        try:
            return control_api.config.preview(request, operator)
        except AgentNotFoundError as exc:
            raise HTTPException(404, str(exc)) from exc
        except ConfigurationError as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.get("/actions/{action_id}", dependencies=[Depends(read_access)])
    def get_action(action_id: str) -> object:
        try:
            return control_api.config.action(action_id)
        except ConfigurationError as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.post("/actions/{action_id}/approval")
    def approve_action(
        action_id: str,
        request: ApprovalRequest,
        operator: Operator = Depends(configuration_operator),
    ) -> object:
        try:
            return control_api.config.approve(action_id, request.approved, operator)
        except ConfigurationError as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.post("/actions/{action_id}/revoke")
    def revoke_action(
        action_id: str,
        operator: Operator = Depends(configuration_operator),
    ) -> object:
        try:
            return control_api.config.revoke(action_id, operator)
        except ConfigurationError as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.post("/actions/{action_id}/execute")
    def execute_action(
        action_id: str,
        operator: Operator = Depends(configuration_operator),
    ) -> object:
        try:
            return control_api.config.execute(action_id, operator)
        except AgentNotFoundError as exc:
            raise HTTPException(404, str(exc)) from exc
        except ConfigurationError as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.post("/bulk/preview")
    def bulk_preview(
        request: BulkRequest, operator: Operator = Depends(configuration_operator)
    ) -> object:
        try:
            return control_api.bulk.preview(request, operator)
        except (ConfigurationError, AgentNotFoundError) as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.get("/bulk/{bulk_id}")
    def bulk_get(bulk_id: str, operator: Operator = Depends(configuration_operator)) -> object:
        try:
            return control_api.bulk.get(bulk_id, operator)
        except ConfigurationError as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.post("/bulk/{bulk_id}/approval")
    def bulk_approve(
        bulk_id: str, request: ApprovalRequest, operator: Operator = Depends(configuration_operator)
    ) -> object:
        try:
            return control_api.bulk.decide(bulk_id, request.approved, operator)
        except ConfigurationError as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.post("/bulk/{bulk_id}/revoke")
    def bulk_revoke(bulk_id: str, operator: Operator = Depends(configuration_operator)) -> object:
        try:
            return control_api.bulk.revoke(bulk_id, operator)
        except ConfigurationError as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.post("/bulk/{bulk_id}/execute")
    def bulk_execute(bulk_id: str, operator: Operator = Depends(configuration_operator)) -> object:
        try:
            return control_api.bulk.execute(bulk_id, operator)
        except ConfigurationError as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.get("/alerts", dependencies=[Depends(read_access)])
    def alerts(environment: str | None = None, active_only: bool = False) -> object:
        return control_api.operations.list(
            Operator(operator_id="http-reader", role="reader"),
            environment=environment,
            active_only=active_only,
        )

    @app.post("/alerts/evaluate")
    def evaluate_alerts(operator: Operator = Depends(configuration_operator)) -> object:
        try:
            return control_api.operations.evaluate(operator)
        except IncidentError as exc:
            raise HTTPException(403, str(exc)) from exc

    @app.post("/alerts/{alert_id}/acknowledge")
    def acknowledge_alert(
        alert_id: str, operator: Operator = Depends(configuration_operator)
    ) -> object:
        try:
            return control_api.operations.acknowledge(alert_id, operator)
        except IncidentError as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.get("/incidents/{incident_id}/view")
    def incident_view(
        incident_id: str, operator: Operator = Depends(configuration_operator)
    ) -> object:
        try:
            return control_api.operations.incident_view(incident_id, operator)
        except (IncidentError, AgentNotFoundError) as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.get("/incidents")
    def list_incidents(
        environment: str | None = None, operator: Operator = Depends(configuration_operator)
    ) -> object:
        return [
            i
            for i in control_api.incidents.list(operator)
            if environment is None or control_api.get_agent(i.agent_id).environment == environment
        ]

    @app.post("/incidents/detect")
    def detect_incident(
        request: DetectionRequest, operator: Operator = Depends(configuration_operator)
    ) -> object:
        try:
            return control_api.incidents.detect(request.agent_id, request.evidence_id, operator)
        except (IncidentError, EvidenceIngestError, AgentNotFoundError) as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.get("/incidents/{incident_id}")
    def incident_get(
        incident_id: str, operator: Operator = Depends(configuration_operator)
    ) -> object:
        try:
            return control_api.incidents.get(incident_id, operator)
        except (IncidentError, EvidenceIngestError, AgentNotFoundError) as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.post("/incidents/{incident_id}/investigate")
    def incident_investigate(
        incident_id: str, operator: Operator = Depends(configuration_operator)
    ) -> object:
        try:
            return control_api.incidents.investigate(incident_id, operator)
        except (IncidentError, EvidenceIngestError, AgentNotFoundError) as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.post("/incidents/{incident_id}/preview")
    def incident_preview(
        incident_id: str, request: PlanRequest, operator: Operator = Depends(configuration_operator)
    ) -> object:
        try:
            return control_api.incidents.preview(
                incident_id, request.dependency, request.expires_in_seconds, operator
            )
        except (IncidentError, EvidenceIngestError, AgentNotFoundError) as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.post("/incidents/{incident_id}/approval")
    def incident_decide(
        incident_id: str,
        request: DecisionRequest,
        operator: Operator = Depends(configuration_operator),
    ) -> object:
        try:
            return control_api.incidents.decide(
                incident_id, request.preview_digest, request.approved, operator
            )
        except (IncidentError, EvidenceIngestError, AgentNotFoundError) as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.post("/incidents/{incident_id}/revoke")
    def incident_revoke(
        incident_id: str, operator: Operator = Depends(configuration_operator)
    ) -> object:
        try:
            return control_api.incidents.revoke(incident_id, operator)
        except (IncidentError, EvidenceIngestError, AgentNotFoundError) as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.post("/incidents/{incident_id}/execute")
    def incident_execute(
        incident_id: str,
        request: ExecuteRequest,
        operator: Operator = Depends(configuration_operator),
    ) -> object:
        try:
            return control_api.incidents.execute(incident_id, request.preview_digest, operator)
        except (IncidentError, EvidenceIngestError, AgentNotFoundError) as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.post("/incidents/{incident_id}/verify")
    def incident_verify(
        incident_id: str,
        request: VerificationRequest,
        operator: Operator = Depends(configuration_operator),
    ) -> object:
        try:
            return control_api.incidents.verify(
                incident_id, request.lens_evidence_id, request.evals_evidence_id, operator
            )
        except (IncidentError, EvidenceIngestError, AgentNotFoundError) as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.post("/incidents/{incident_id}/control/{action}")
    def incident_control(
        incident_id: str, action: str, operator: Operator = Depends(configuration_operator)
    ) -> object:
        try:
            return control_api.incidents.control(incident_id, action, operator)
        except IncidentError as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.post("/incidents/{incident_id}/reconcile")
    def incident_reconcile(
        incident_id: str, operator: Operator = Depends(configuration_operator)
    ) -> object:
        try:
            return control_api.incidents.reconcile(incident_id, operator)
        except IncidentError as exc:
            raise HTTPException(409, str(exc)) from exc

    runbook_errors = (IncidentError, EvidenceIngestError, AgentNotFoundError)

    @app.get("/runbooks", dependencies=[Depends(read_access)])
    def runbook_catalog() -> object:
        return control_api.runbooks.definitions()

    @app.get("/runbooks/{runbook_id}/{version}/validations", dependencies=[Depends(read_access)])
    def runbook_validations(runbook_id: str, version: str) -> object:
        try:
            control_api.runbooks.catalog.get(runbook_id, version)
        except CatalogError as exc:
            raise HTTPException(404, str(exc)) from exc
        return control_api.runbooks.validations(runbook_id, version)

    @app.post("/runbooks/{runbook_id}/{version}/validations")
    def runbook_record_validation(
        runbook_id: str,
        version: str,
        request: RunbookValidationRequest,
        operator: Operator = Depends(configuration_operator),
    ) -> object:
        try:
            return control_api.runbooks.record_validation(runbook_id, version, request, operator)
        except CatalogError as exc:
            raise HTTPException(404, str(exc)) from exc
        except runbook_errors as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.get("/incidents/{incident_id}/runbooks")
    def runbook_recommendations(
        incident_id: str, operator: Operator = Depends(configuration_operator)
    ) -> object:
        try:
            return control_api.runbooks.recommend(incident_id, operator)
        except runbook_errors as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.get("/incidents/{incident_id}/runbook-executions")
    def runbook_executions(
        incident_id: str, operator: Operator = Depends(configuration_operator)
    ) -> object:
        try:
            return control_api.runbooks.list(incident_id, operator)
        except runbook_errors as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.post("/incidents/{incident_id}/runbooks/preview")
    def runbook_preview(
        incident_id: str,
        request: RunbookPreviewRequest,
        operator: Operator = Depends(configuration_operator),
    ) -> object:
        try:
            return control_api.runbooks.preview(incident_id, request, operator)
        except CatalogError as exc:
            raise HTTPException(404, str(exc)) from exc
        except runbook_errors as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.get("/runbook-executions/{execution_id}")
    def runbook_execution(
        execution_id: str, operator: Operator = Depends(configuration_operator)
    ) -> object:
        try:
            return control_api.runbooks.get(execution_id, operator)
        except runbook_errors as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.post("/runbook-executions/{execution_id}/approval")
    def runbook_decide(
        execution_id: str,
        request: RunbookDecisionRequest,
        operator: Operator = Depends(configuration_operator),
    ) -> object:
        try:
            return control_api.runbooks.decide(
                execution_id, request.preview_digest, request.approved, operator
            )
        except runbook_errors as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.post("/runbook-executions/{execution_id}/execute")
    def runbook_execute(
        execution_id: str,
        request: RunbookExecuteRequest,
        operator: Operator = Depends(configuration_operator),
    ) -> object:
        try:
            return control_api.runbooks.execute(execution_id, request.preview_digest, operator)
        except runbook_errors as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.post("/runbook-executions/{execution_id}/verify")
    def runbook_verify(
        execution_id: str,
        request: RunbookVerificationRequest,
        operator: Operator = Depends(configuration_operator),
    ) -> object:
        try:
            return control_api.runbooks.verify(
                execution_id, request.lens_evidence_id, request.evals_evidence_id, operator
            )
        except runbook_errors as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.post("/runbook-executions/{execution_id}/{transition}")
    def runbook_transition(
        execution_id: str, transition: str, operator: Operator = Depends(configuration_operator)
    ) -> object:
        handlers = {
            "revoke": control_api.runbooks.revoke,
            "cancel": control_api.runbooks.cancel,
            "reconcile": control_api.runbooks.reconcile,
        }
        if transition not in handlers:
            raise HTTPException(404, "Unknown runbook transition")
        try:
            return handlers[transition](execution_id, operator)
        except runbook_errors as exc:
            raise HTTPException(409, str(exc)) from exc

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
