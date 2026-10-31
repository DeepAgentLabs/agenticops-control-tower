# Investigation and approved staging recovery (0.6.0)

Phase 6 and Phase 6A ship together in **0.6.0**. Tower owns the durable incident
and approval workflow; MCP 0.3.6 exposes tools over the actual authenticated API.
A model host uses the `tower.investigation` prompt and evidence-query tools. No
model provider, API key or autonomous causal engine is bundled in Tower.

## Supported runtime and walkthrough

The supported first runtime is `StagingDependencyRuntime`, a deterministic local
SQLite dependency fixture. It restores one host-allowlisted dependency, records a
transactional idempotency receipt and bounds lock waits to the plan timeout (five
seconds, one attempt). It runs no shell commands. This deliberately controlled
fixture meets the first staging scenario. Reusable multi-step runbooks ship in
0.9.0 (see [runbooks](runbooks.md)); production runtime adapters remain planned.

```bash
uv sync --extra dev
uv run --with ../agenticlens --with ../agentic-evals python examples/incident_recovery.py
uv run --with ../agenticlens --with ../agentic-evals python examples/incident_recovery.py --fail-verification
```

The walkthrough registers staging through HTTP, injects a deterministic dependency
failure, pushes a native Lens failed tool run, detects and investigates an incident,
previews the fixed runbook, approves its digest as a separate human identity,
executes once, probes the dependency, records a fresh native Lens run, computes an
actual Evals report and gate, then verifies recovery. Outputs are `resolved` and
`escalated`, respectively. TestClient exercises the same API routes without opening
ports. Demo tokens are local fixture values; supply deployment-owned credentials
when hosting. No external model or service is needed.

Hosts explicitly construct `IncidentService(registry, evidence, database_path,
connectors={deployment_id: runtime})` and pass it as `incident_service` to
`ControlTowerAPI`, then call `create_app(api, ...)`. The default `serve` API has no
installed remediation connector, so previews fail honestly. Use the same local
SQLite path for registry, evidence and incidents; runtime state uses its own file.

## HTTP and CLI

All incident routes require configured bearer credentials, even when registry
reads allow anonymous development. Reader, writer and approver identities come
from server credentials, never request bodies. Python callers are trusted hosts
and must supply a trusted `Operator`; optional `agent_ids` bounds Python scope.
Shared HTTP credentials are deployment-wide, not per-user identities or tenancy.

| Route | Role | Request |
| --- | --- | --- |
| `GET /incidents`, `GET /incidents/{id}` | reader/writer/approver | none |
| `POST /incidents/detect` | writer | `agent_id`, `evidence_id` |
| `POST /incidents/{id}/investigate` | writer | none |
| `POST /incidents/{id}/preview` | writer | `dependency`, optional `expires_in_seconds` (1–3600) |
| `POST /incidents/{id}/approval` | separate approver | `preview_digest`, `approved` |
| `POST /incidents/{id}/revoke` | approver | none |
| `POST /incidents/{id}/execute` | writer | `preview_digest` |
| `POST /incidents/{id}/verify` | writer | `lens_evidence_id`, `evals_evidence_id` |
| `POST /incidents/{id}/reconcile` | writer | none; escalates an interrupted execution |
| `POST /incidents/{id}/control/stop` | writer | none; host-installed Sidecar adapter |
| `POST /incidents/{id}/control/restart` | writer | none; explicit human restart |

The CLI mirrors the workflow: `incidents list`, `get ID`, `detect REQUEST.json`,
`investigate ID`, `preview ID REQUEST.json`, `approval ID REQUEST.json`, `revoke ID`,
`execute ID REQUEST.json`, `verify ID REQUEST.json`. Pass `--token` or
`AGENTICOPS_TOKEN` for the appropriate role. Incident snapshots are unsupported;
existing inventory/evidence snapshot commands retain their read-only behavior.
Runtime stop/restart and reconciliation are also available through HTTP/Python.

Example preview JSON: `{"dependency":"search","expires_in_seconds":300}`.
Approval JSON: `{"preview_digest":"<exact digest from preview>","approved":true}`.
Execution JSON: `{"preview_digest":"<same digest>"}`. A changed digest, target
scope, denied/revoked/expired approval or an already consumed action dispatches
nothing. Preview scope, parameters, prerequisite, impact, rollback and recovery
criteria are retained in the incident. The approver cannot be the proposer.

## Evidence, uncertainty and verification

Detection accepts an available failed native Lens run already stored for that
deployment. Repeated detection of the same evidence returns the same incident.
Investigation retains the detection projection and a chronological, same-run
window of up to 500 recent evidence records, including producer outcomes, trace
IDs, failed spans, tool names and dependency error types. Record IDs and artifact
references are citations; references are never fetched. Prompt versions and
change history are explicitly unavailable. This is evidence assembly for a
copilot, not a claim of exact RCA. A failure is observed; dependency causality
remains a hypothesis without independent producer evidence. Contradictory
same-run success/failure blocks the remediation recommendation.

A successful command only moves to `awaiting_verification`. Resolution requires:

- a successful connector probe;
- available native Lens evidence with `status=succeeded` and `task_success=true`;
- an existing passing native Evals gate linked to that recovery run;
- both observations and ingestions after execution began, no future timestamps,
  and observations no more than five minutes old.

Tower never computes Evals policy or Lens diagnosis. The trusted producer pipeline
must attribute the Evals gate to the correct report/run. Missing record IDs reject
the request; stale, mismatched, failed or future evidence escalates. Failed or
partial execution escalates and records manual reconciliation instructions.
Evidence outcomes never rewrite agent-reported fleet health.

## Durability and execution limits

SQLite transitions serialize across processes. Approval is consumed and the
`executing/unknown` claim is committed **before** runtime dispatch. A crash cannot
repeat an unsafe action; it leaves unknown execution for explicit reconciliation.
`reconcile` escalates, keeps approval consumed, and never replays. This provides
at-most-one Tower dispatch, not a distributed exactly-once guarantee. The supported
runtime also commits a durable action receipt atomically with its change.

Custom connectors are trusted host code. They must enforce the fixed plan's
execution/probe timeout, return accurate partial outcomes and use incident IDs as
durable idempotency keys. Tower cannot kill an arbitrary Python callback. Automatic
retries and rollback of external side effects are not claimed. Denial, revocation,
execution, verification and failed control acknowledgements remain in the timeline.
The console remains read-only; incident views ship in 0.8.0 ([live operations](live-operations.md)).

## Emergency braking and explicit restart

Install `SidecarContainmentAdapter(runtime)` in the service's `containment` map.
The supported local Sidecar `TaskRuntime` must have an `mcp` revoker installed.
`MCPAccessRevoker(issuer, task_id, user, token)` binds that callback to an existing
MCP key issuer (for example MCP's `DynamoDBKeyStore`), invokes its native revocation,
and checks authentication is no longer possible. Secrets remain host-owned and
are never emitted to the incident. This adapter does not provision AWS resources.

Stop requires a scoped writer and does not require approval from a model or
agent. Tower records requested, acknowledged, failed, unsupported and incomplete outcomes;
Sidecar owns dispatch blocking and performs its revocation callbacks. Only a
confirmed MCP revocation plus Sidecar acknowledgement and no in-flight calls is
reported as `boundary_acknowledged`. Incomplete or failed containment is never
recorded as an acknowledged command. Restart validates its own runtime response. Downstream credentials remain `unsupported`;
this is not a claim of universal containment. Restart is a separate explicit
operator operation, delegated to Sidecar's stopped/idle/revocation preconditions.
A revoked MCP credential must be replaced by its issuer for future MCP access.
