# API reference

Control Tower has two programmatic surfaces: the **HTTP API** served by
`agenticops-control-tower serve` (or `create_app()`), and the **Python API**
(`ControlTowerAPI`), which the HTTP layer and CLI both use. The routes below are
taken from `api/http.py` in 0.9.0. While the server runs, FastAPI's generated
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
| `POST /incidents/detect`, `POST /incidents/{id}/investigate`, `/preview`, `/approval`, `/revoke`, `/execute`, `/verify`, `/control/{action}`, `/reconcile` | operator | Approved staging recovery; see [incident recovery](incident-recovery.md). |

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

Further services hang off the facade: `api.config` (controlled configuration),
`api.bulk` (fleet operations), `api.operations` (detection, alerts, incident
views), `api.incidents` (investigation and recovery) and `api.runbooks`
(versioned runbooks). Their usage is shown in
`examples/controlled_configuration.py`, `examples/fleet_operations.py`,
`examples/live_operations.py`, `examples/incident_recovery.py` and
`examples/runbook_recovery.py`.

Models are importable from `agenticops_control_tower.models`, including
`AgentRegistrationPayload`, `HeartbeatPayload`, `AgentRecord`, `AgentStatus`,
`EvidenceIngestRequest` and `FleetStatusSummary`.

To serve HTTP from your own process, see
[server settings → Python hosts](settings.md#python-hosts).
