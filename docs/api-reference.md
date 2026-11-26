# API Reference (detailed)

**Version:** 1.1.0

Control Tower has two programmatic surfaces: the **HTTP API** served by
`agenticops-control-tower serve` (or `create_app()`), and the **Python API**
(`ControlTowerAPI`), which the HTTP layer and CLI both use. The routes below are
taken from the current `api/http.py` surface; focused guides retain their feature-origin release labels. While the server runs, FastAPI's generated
OpenAPI page at `/docs` lists the exact request and response schemas.

## Authentication

Send `Authorization: Bearer <token>`. Roles come from the server's configured
tokens ([server settings](settings.md)):

| Role column | Accepted tokens |
| --- | --- |
| **read** | reader, writer or approval token (anonymous if no tokens are configured) |
| **write** | writer token (anonymous if no tokens are configured) |
| **operator** | any configured token; the route then checks the role it needs (writer to propose and execute, approval token to approve, deny and revoke). Anonymous access is refused. |

Errors: `401` missing or invalid token, `403` wrong role, `404` unknown agent,
`409` rejected state transition, `411`/`413` missing or oversized body on
`POST /evidence` and `POST /bulk/preview` (limit 1 MiB).

## HTTP routes

### Inventory and health

| Method and path | Role | Purpose |
| --- | --- | --- |
| `POST /agents/register` | write | Register an agent (`AgentRegistrationPayload`); returns `201` and the record. |
| `POST /agents/{agent_id}/heartbeat` | write | Record a heartbeat (`HeartbeatPayload`). |
| `GET /agents` | read | List agents. Query: `status`, `environment`, `capability`, `missing_capability`. |
| `GET /agents/{agent_id}` | read | One agent record. |
| `GET /capabilities` | read | Capability → versions across all agents. |
| `GET /status` | read | Fleet health and capability coverage. Query: `environment`. |
| `GET /versions` | read | Minimum-version assessment. Query: `capability`, `minimum_version`, `environment`. |

### Evidence and posture

| Method and path | Role | Purpose |
| --- | --- | --- |
| `POST /evidence` | write | `{"link": {...}, "artifact": {...}, "gate": {...}}`. Idempotent per observation. |
| `GET /agents/{agent_id}/evidence` | read | Per-producer posture for one agent. |
| `GET /agents/{agent_id}/evidence/history` | read | Stored records, newest first. |
| `GET /posture` | read | Fleet posture by producer. Query: `environment`, `stale_after_seconds`. |

### Controlled configuration and bulk operations

| Method and path | Role | Purpose |
| --- | --- | --- |
| `GET /agents/{agent_id}/config/{capability}` | read | Ownership, desired values and revision. |
| `GET /agents/{agent_id}/audit` | read | Configuration audit trail. |
| `POST /actions/preview` | operator (writer) | Create an immutable preview. |
| `GET /actions/{action_id}` | read | Read a stored proposal. |
| `POST /actions/{action_id}/approval` | operator (approver) | `{"approved": true}` or `false`. |
| `POST /actions/{action_id}/revoke` | operator (approver) | Revoke a pending or approved proposal. |
| `POST /actions/{action_id}/execute` | operator (writer) | Execute an approved, unexpired action. |
| `POST /bulk/preview`, `GET /bulk/{id}`, `POST /bulk/{id}/approval`, `POST /bulk/{id}/revoke`, `POST /bulk/{id}/execute` | operator | The same lifecycle for a frozen fleet target set. |

### Alerts and incidents

| Method and path | Role | Purpose |
| --- | --- | --- |
| `GET /alerts` | read | Query: `environment`, `active_only`. |
| `POST /alerts/evaluate` | operator (writer) | Run a detection scan now. |
| `POST /alerts/{alert_id}/acknowledge` | operator (writer) | Acknowledge an alert. |
| `GET /incidents`, `GET /incidents/{id}`, `GET /incidents/{id}/view` | operator | Read incidents; `view` is the joined timeline. |
| `POST /incidents/detect`, `POST /incidents/{id}/investigate`, `/preview`, `/approval`, `/revoke`, `/execute`, `/verify`, `/reconcile` | operator | Approved staging recovery; see [incident recovery](incident-recovery.md). |
| `POST /incidents/{id}/control/{action}` | operator (writer) | Emergency control: `action` is `stop` or `restart`; see [emergency control](#emergency-control). |

### Runbooks

| Method and path | Role | Purpose |
| --- | --- | --- |
| `GET /runbooks` | read | Installed runbook definitions. |
| `GET /runbooks/{id}/{version}/validations`, `POST` the same path | read / operator (writer) | Read or record Chaos and Evals validation for a version. |
| `GET /incidents/{id}/runbooks`, `GET /incidents/{id}/runbook-executions` | operator | Recommendations with unmet prerequisites; execution history. |
| `POST /incidents/{id}/runbooks/preview` | operator (writer) | Preview an exact digest for one catalog version and its parameters. |
| `GET /runbook-executions/{id}` | operator | Read one execution with step results and events. |
| `POST /runbook-executions/{id}/approval`, `/revoke` | operator (approver) | Approve, deny or revoke the exact preview. |
| `POST /runbook-executions/{id}/execute`, `/verify`, `/reconcile` | operator (writer) | Run bounded steps, verify recovery, reconcile an interrupted run. |
| `POST /runbook-executions/{id}/cancel` | operator (writer or approver) | Cancel before or between steps. |

See [runbooks](runbooks.md) for request bodies and outcomes.

### Console

| Method and path | Purpose |
| --- | --- |
| `GET /console/` | The read-only console shell. It contains no fleet data; the page reads the routes above with the token you paste. Served with a restrictive Content-Security-Policy and `Cache-Control: no-store`. |

## Complete HTTP route inventory

The current app registers the following method/path pairs, excluding FastAPI's documentation/OpenAPI routes. The detailed sections above and linked workflows define roles, bodies and state transitions. `GET /openapi.json` / `/docs` describe the running app's typed schemas. The console shell and assets are served by the same application; the browser issues reads only.

| Method | Path |
| --- | --- |
| `GET` | `/actions/{action_id}` |
| `GET` | `/agents` |
| `GET` | `/agents/{agent_id}` |
| `GET` | `/agents/{agent_id}/audit` |
| `GET` | `/agents/{agent_id}/config/{capability}` |
| `GET` | `/agents/{agent_id}/evidence` |
| `GET` | `/agents/{agent_id}/evidence/history` |
| `GET` | `/alerts` |
| `GET` | `/bulk/{bulk_id}` |
| `GET` | `/capabilities` |
| `GET` | `/console` |
| `GET` | `/console/` |
| `GET` | `/contracts/capabilities` |
| `GET` | `/incidents` |
| `GET` | `/incidents/{incident_id}` |
| `GET` | `/incidents/{incident_id}/runbook-executions` |
| `GET` | `/incidents/{incident_id}/runbooks` |
| `GET` | `/incidents/{incident_id}/view` |
| `GET` | `/posture` |
| `GET` | `/runbook-executions/{execution_id}` |
| `GET` | `/runbooks` |
| `GET` | `/runbooks/{runbook_id}/{version}/validations` |
| `GET` | `/status` |
| `GET` | `/versions` |
| `POST` | `/actions/preview` |
| `POST` | `/actions/{action_id}/approval` |
| `POST` | `/actions/{action_id}/execute` |
| `POST` | `/actions/{action_id}/revoke` |
| `POST` | `/agents/register` |
| `POST` | `/agents/{agent_id}/heartbeat` |
| `POST` | `/alerts/evaluate` |
| `POST` | `/alerts/{alert_id}/acknowledge` |
| `POST` | `/bulk/preview` |
| `POST` | `/bulk/{bulk_id}/approval` |
| `POST` | `/bulk/{bulk_id}/execute` |
| `POST` | `/bulk/{bulk_id}/revoke` |
| `POST` | `/evidence` |
| `POST` | `/incidents/detect` |
| `POST` | `/incidents/{incident_id}/approval` |
| `POST` | `/incidents/{incident_id}/control/{action}` |
| `POST` | `/incidents/{incident_id}/execute` |
| `POST` | `/incidents/{incident_id}/investigate` |
| `POST` | `/incidents/{incident_id}/preview` |
| `POST` | `/incidents/{incident_id}/reconcile` |
| `POST` | `/incidents/{incident_id}/revoke` |
| `POST` | `/incidents/{incident_id}/runbooks/preview` |
| `POST` | `/incidents/{incident_id}/verify` |
| `POST` | `/runbook-executions/{execution_id}/approval` |
| `POST` | `/runbook-executions/{execution_id}/execute` |
| `POST` | `/runbook-executions/{execution_id}/verify` |
| `POST` | `/runbook-executions/{execution_id}/{transition}` |
| `POST` | `/runbooks/{runbook_id}/{version}/validations` |

## Python API

`ControlTowerAPI` is the facade every other surface goes through. The base
package (no `api` extra) is enough.

```python
from agenticops_control_tower.snapshot import create_api, load_snapshot

api = create_api()                                   # empty, in memory
api = load_snapshot("examples/sample_fleet_snapshot.json")  # pre-filled, read-only use
print(api.get_status().degraded_agents)
```

```text
1
```

| Method | Returns |
| --- | --- |
| `register(payload)` / `register_agent` | `AgentRecord` |
| `heartbeat(agent_id, payload)` / `record_heartbeat` | `AgentRecord` |
| `list_agents(*, status, environment, capability, missing_capability)` | `list[AgentRecord]` |
| `get_agent(agent_id)` | `AgentRecord` (raises `AgentNotFoundError`) |
| `get_agent_capabilities(agent_id)` | `dict[str, str]` |
| `list_capabilities()` | `list[CapabilityInventoryRecord]` |
| `list_all_capabilities()` | `dict[str, list[str]]` |
| `get_status(*, environment)` | `FleetStatusSummary` |
| `assess_versions(capability, minimum_version, *, environment)` | `list[VersionAssessment]` |
| `summarize_evidence(link, artifact, *, gate)` | `EvidenceSummary` (not stored) |
| `ingest_evidence(request, *, ingested_by)` | `EvidenceIngestResult` |
| `evidence_history(agent_id, *, source, limit)` | `list[EvidenceRecord]` |
| `agent_posture(agent_id, *, stale_after_seconds, now)` | `AgentEvidencePosture` |
| `fleet_posture(*, environment, stale_after_seconds, now)` | `FleetEvidencePosture` |

`get_capability_contract()` returns the `tower.capabilities.v1` descriptor
(see [versioned capability discovery](#versioned-capability-discovery)).

### Service objects

Further services hang off the facade. Every method takes a trusted `Operator`
(from `agenticops_control_tower.config.models`); the service checks its role
(`reader`, `writer` or `approver`) and optional `agent_ids` scope. Runnable
flows: `examples/controlled_configuration.py`, `examples/fleet_operations.py`,
`examples/live_operations.py`, `examples/incident_recovery.py` and
`examples/runbook_recovery.py`.

**`api.config`**: `ConfigurationService` ([controlled configuration](configuration.md))

| Method | Returns |
| --- | --- |
| `get(agent_id, capability)` | `Configuration` (ownership, values, revision) |
| `declare(configuration, operator)` | `Configuration`; trusted-host only, sets Tower or mirrored ownership |
| `preview(request: ActionRequest, operator)` | `ActionPreview` (immutable) |
| `action(action_id)` | `ActionPreview` |
| `approve(action_id, approved, operator)` | `ActionPreview`; approver role |
| `revoke(action_id, operator)` | `ActionPreview`; approver role |
| `execute(action_id, operator)` | `ExecutionResult`; commits desired state |
| `audit(agent_id)` | `list[AuditRecord]` |

**`api.bulk`**: `BulkService` ([fleet operations](fleet-operations.md))

| Method | Returns |
| --- | --- |
| `preview(request: BulkRequest, operator)` | `BulkAction` with the frozen target list |
| `get(bulk_id, operator)` | `BulkAction` |
| `decide(bulk_id, approved, operator)` | `BulkAction`; approver role |
| `revoke(bulk_id, operator)` | `BulkAction`; approver role |
| `execute(bulk_id, operator)` | `BulkAction` with per-target `TargetResult`s |
| `install(agent_id, adapter: SidecarContainmentAdapter)` | `None`; trusted-host setup for `runtime.stop` |

`BulkRequest.operation` is one of `config.update`, `capabilities.enable`,
`capabilities.disable` or `runtime.stop`.

**`api.operations`**: `OperationsService` ([live operations](live-operations.md))

| Method | Returns |
| --- | --- |
| `evaluate(operator, *, now=None)` | `list[Alert]` from one detection scan |
| `list(operator, *, environment=None, active_only=False)` | `list[Alert]` |
| `acknowledge(alert_id, operator)` | `Alert` |
| `incident_view(incident_id, operator)` | `dict` joined incident timeline |

**`api.incidents`**: `IncidentService` ([incident recovery](incident-recovery.md))

| Method | Returns |
| --- | --- |
| `detect(agent_id, evidence_id, operator)` | `Incident` (deduplicated per observation) |
| `get(incident_id, operator)` / `list(operator)` | `Incident` / `list[Incident]` |
| `investigate(incident_id, operator)` | `Incident` with a cited `Investigation` |
| `preview(incident_id, dependency, expires_in_seconds, operator)` | `Incident` with a `RecoveryPlan` digest |
| `decide(incident_id, digest, approved, operator)` | `Incident`; approver role |
| `revoke(incident_id, operator)` | `Incident`; approver role |
| `execute(incident_id, digest, operator)` | `Incident` awaiting verification |
| `verify(incident_id, lens_id, evals_id, operator)` | `Incident` resolved or escalated |
| `control(incident_id, action, operator)` | `Incident`; `action` is `stop` or `restart` |
| `reconcile(incident_id, operator)` | `Incident` after host reconciliation |

Recovery connectors (`RecoveryConnector`) and containment adapters are passed to
`IncidentService(registry, evidence, connectors={...}, containment={...})` by the
trusted host. `StagingDependencyRuntime` is the bundled deterministic fixture.

**`api.runbooks`**: `RunbookService` ([runbooks](runbooks.md))

| Method | Returns |
| --- | --- |
| `definitions()` | `list[RunbookDefinition]` installed in the catalog |
| `recommend(incident_id, operator)` | `list[RunbookRecommendation]` with unmet prerequisites |
| `validations(runbook_id, version)` | `list[RunbookValidation]` |
| `record_validation(runbook_id, version, request, operator)` | `RunbookValidation` from a completed Chaos report and passing Evals gate |
| `preview(incident_id, request: RunbookPreviewRequest, operator)` | `RunbookExecution` with an exact digest |
| `get(execution_id, operator)` / `list(incident_id, operator)` | `RunbookExecution` / `list[RunbookExecution]` |
| `decide(execution_id, digest, approved, operator)` | `RunbookExecution`; approver role |
| `revoke(execution_id, operator)` | `RunbookExecution`; approver role |
| `execute(execution_id, digest, operator)` | `RunbookExecution` with `StepResult`s |
| `cancel(execution_id, operator)` | `RunbookExecution`; writer or approver |
| `reconcile(execution_id, operator)` | `RunbookExecution` |
| `verify(execution_id, lens_id, evals_id, operator)` | `RunbookExecution` resolved or escalated |
| `install(agent_id, connector: RunbookConnector)` | `None`; trusted-host connector setup |

`RunbookStep` fields: `step_id`, `action`, `description`, `timeout_seconds`
(1–30, default 5), `max_attempts` (1–3; retries only on a connector-reported
clean failure), `rollback_action` and `rollback_timeout_seconds`. A definition
holds 1–10 steps. The built-in `STAGING_DEPENDENCY_RECOVERY` is
`staging.dependency_recovery` 1.0.0 (`traffic.drain` → `dependency.restore` →
`traffic.resume`), run by the deterministic `StagingRunbookRuntime`.

### Emergency control

Emergency control is independent of model approval and of recovery verification.

| Symbol | Module | Purpose |
| --- | --- | --- |
| `SidecarContainmentAdapter(runtime)` | `adapters.containment` | Wraps a host-installed Sidecar runtime; `control(action, actor)` returns `acknowledged`, `incomplete`, `unsupported` or `failed`. |
| `MCPAccessRevoker(issuer, task_id, user, token)` | `adapters.containment` | Binds one task to its hosted MCP issuer credential; revokes it and confirms it no longer authenticates. |

Use them through `POST /incidents/{id}/control/{action}` (`stop`, `restart`),
`api.incidents.control(...)`, or a bulk `runtime.stop`. Restart does not renew
revoked credentials. See [phase 6 containment](phase6-containment.md).

### Lens execution verification

| Symbol | Module | Purpose |
| --- | --- | --- |
| `summarize_execution(artifact, *, trusted_keys, expected_run_id)` | `adapters.lens_execution` | Verifies a Lens `ExecutionBundle` with host-held keys; returns verification status and redacted causal links. Without the optional Lens verifier the status is `unknown`. |

On the server, configure `AGENTICOPS_LENS_TRUST_STORE` or pass
`create_app(trusted_lens_keys=...)`; HTTP requests cannot configure trust. See
[Lens execution evidence](lens-execution-evidence.md).

### AIOS investigation-report export

| Symbol | Module | Purpose |
| --- | --- | --- |
| `export_investigation_report(incident, *, created_at)` | `incidents.export` | Projects a held `Incident` into an AIOS `0.8-draft` investigation report with explicit citations and redacted summaries. Fetches nothing and executes no recovery. |

There is no HTTP route for export; call it in Python after reading an incident.
See `examples/operational_artifacts.py` and
[coordinated v1 readiness](coordinated-v1-readiness.md).

Models are importable from `agenticops_control_tower.models`, including
`AgentRegistrationPayload`, `HeartbeatPayload`, `AgentRecord`, `AgentStatus`,
`EvidenceIngestRequest` and `FleetStatusSummary`.

To serve HTTP from your own process, see
[server settings → Python hosts](settings.md#python-hosts).

## MCP connector

MCP access is provided by the separate `deep-agentic-core-mcp` package, not by this
API. Its `tower.*` and `tower.runbook*` tools call the HTTP routes above with
credentials configured on the MCP host, and the `tower.investigation` prompt guides
evidence-based review. No MCP tool can grant human approval. See
[MCP connector](mcp-connector.md).

## Versioned capability discovery

`GET /contracts/capabilities` requires inventory reader access and returns the `tower.capabilities.v1` candidate descriptor. Python: `api.get_capability_contract()`. See [schemas, runtime examples and evolution policy](capability-contract.md).


## Capability modules and evidence boundaries

| Module | Workflow and detailed contract |
| --- | --- |
| `registry`, `discovery`, `status`, `models` | [Inventory, health, versions and candidate capability descriptor](capability-contract.md) |
| `snapshot` | [Offline inventory/evidence views](evidence-posture.md#offline-snapshots) |
| `config` | [Ownership, desired settings, immutable previews and separate approval](configuration.md) |
| `evidence`, `adapters` | [Native projections, attributed ingestion, freshness and history](evidence-posture.md) |
| `adapters.lens_execution` | [Optional host-trusted execution verification](lens-execution-evidence.md) |
| `incidents` | [Detection, cited investigation, installed staging connectors and verified recovery](incident-recovery.md) |
| `bulk` | [Frozen target selection, execution and bounded stop/revoke](fleet-operations.md) |
| `operations` | [Detection policies, periodic scans, alerts and joined timeline](live-operations.md) |
| `runbooks` | [Versioned catalog, validation, approval, bounded steps, compensation and reconciliation](runbooks.md) |
| `incidents.export` | [Redacted AIOS investigation-report projection](coordinated-v1-readiness.md) |
| `api`, `cli`, `console` | [One role-controlled model through HTTP/CLI and read-only console](hosting.md) |

Module names in this table are relative to `agenticops_control_tower`. The [AI Reference (robust)](https://deepagentlabs.io/control-tower/docs/llms-full.md) includes declarations from every package module and both bundled Evals-native schemas. Undocumented helpers remain internal; static extraction does not promote them to public APIs. The capability descriptor's candidate inventory schemas are separate from those Evals schemas and from AIOS artifacts.

See [the capability index](ai-reference-index.md), [producer ownership](ecosystem-alignment.md), [Lens trust setup](lens-execution-evidence.md) and [current AIOS export](coordinated-v1-readiness.md). Serialized approval/evidence is not permission to execute; the live service rechecks the exact state and connector boundary.
