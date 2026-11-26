# Control Tower developer guide

Use this simple guide to choose a capability and run a local inventory or operator workflow. The [AI Reference (robust)](https://deepagentlabs.io/control-tower/docs/llms-full.md) includes detailed operational guides, current package/CLI declarations and both bundled Evals schemas. Deployment health, evidence outcomes, approvals and verified recovery remain separate signals.

[Capability index](#capability-index) · [Quickstart](#quickstart) · [Configuration](#settings) · [Troubleshooting](#troubleshooting) · [Reference](#reference)

## Capability index

Each row links to a short workflow below, with a detailed reference for payloads, roles, state transitions and limitations.

| Capability | What you can do |
| --- | --- |
| [Agent registration and heartbeats](#registration) | Register deployment identity and merge runtime-reported heartbeat metadata. |
| [Fleet health and version assessment](#health) | Filter fleet status/capability coverage and compare reported PEP 440 versions. |
| [Capability discovery and contract](#capabilities) | Read the versioned candidate registration/heartbeat contract and schemas. |
| [Offline snapshots](#snapshots) | Inspect captured inventory, heartbeat history and evidence without a server. |
| [Authentication and operator roles](#authentication) | Separate reader, writer and approver credentials and trusted operator identities. |
| [Configuration ownership and desired state](#configuration) | Declare Tower-owned or mirrored settings and preview bounded desired-state changes. |
| [Exact approval lifecycle](#approvals) | Bind immutable previews, revisions, expiry and one-time approval to the intended change. |
| [Bulk fleet operations](#bulk) | Freeze deployment targets, approve once and report bounded per-target results. |
| [Runtime stop and access revocation](#stop) | Coordinate host-installed Sidecar stop and MCP revocation without inferring cancellation. |
| [Evidence ingestion and posture](#evidence) | Push attributed native observations and retain freshness, availability and native outcome tallies. |
| [Native artifact readers and schemas](#native-contracts) | Read Lens/Evals/Sidecar/Chaos artifacts with explicit owner/correlation boundaries. |
| [Lens execution verification](#execution) | Verify expected-run bundles using host trust keys and preserve distinct verification states. |
| [Incident detection and investigation](#incidents) | Create durable incidents from native failures and assemble cited, uncertain investigations. |
| [Approved staging recovery](#staging) | Run the fixed bounded staging dependency action through an installed connector. |
| [Periodic detection and alerts](#alerts) | Scan stored observations, deduplicate/acknowledge alerts and join incident timelines. |
| [Versioned runbooks](#runbooks) | Discover, validate, recommend, preview and execute installed versioned runbooks. |
| [Cancellation, compensation and reconciliation](#cancellation) | Cancel between bounded steps, compensate known completions and reconcile unknown execution. |
| [Recovery verification](#verification) | Require a successful probe and fresh same-run Lens/Evals evidence before resolution. |
| [Read-only console](#console) | Inspect fleet, evidence, alerts, incidents and runbook state through authenticated reads. |
| [MCP operator integration](#mcp) | Expose Tower evidence/recovery through separate MCP tools while keeping approval human-only. |
| [AIOS investigation-report export](#aios) | Project a held native Incident with redacted summaries and explicit citations. |
| [Python, HTTP and CLI surfaces](#interfaces) | Use one control model through the facade, authenticated API or operator CLI. |
| [Persistence and hosting](#hosting) | Persist local SQLite state and host the API/console with deployment-owned access. |
| [Settings and operational limits](#settings) | Configure server/client options, detection windows, quotas and optional verification trust. |
| [Compatibility and acceptance](#acceptance) | Distinguish candidate inventory interoperability from production/runtime or AIOS certification. |

## Quickstart

Requires Python 3.10 or newer in an activated virtual environment:

```bash
python -m pip install 'agenticops-control-tower[api]'
```

[Download sample_fleet_snapshot.json](guide/examples/sample_fleet_snapshot.json) into the working folder. It is historical fixture evidence, not a package-install recommendation:

```bash
agenticops-control-tower --snapshot sample_fleet_snapshot.json status
agenticops-control-tower --snapshot sample_fleet_snapshot.json agents list
agenticops-control-tower --snapshot sample_fleet_snapshot.json posture
```

Expect two recorded agents and their captured health/evidence. This is an offline view, not a live health probe. Loading the snapshot does not populate a running server.

For a live local server, generate separate reader/writer/approver secrets, configure `AGENTICOPS_READ_TOKEN`, `AGENTICOPS_WRITE_TOKEN` and `AGENTICOPS_APPROVAL_TOKEN`, then run:

```bash
agenticops-control-tower serve --database registry.sqlite --host 127.0.0.1 --port 8000
```

Open [the local console](http://localhost:8000/console/) with the reader token. A fresh registry is empty until agents register. See [token generation](authentication.md) and [hosting](hosting.md).

## Usage

Commands referencing `examples/` require a source checkout and run from its root. Other payload files, IDs and tokens are inputs you supply. Global CLI options (`--api-url`, `--token`, `--snapshot`) go before the command. Use the appropriate credential for each lifecycle step.

<span id="registration"></span>

### Agent registration and heartbeats

This complete in-memory Python example needs only the base package:

```python
from agenticops_control_tower.snapshot import create_api
from agenticops_control_tower.models import AgentRegistrationPayload, HeartbeatPayload

api = create_api()
api.register(AgentRegistrationPayload(
    agent_id="demo-agent", name="Demo agent", environment="staging",
    runtime="python", framework="custom", capabilities={"agenticlens": "1.0.3"},
))
agent = api.heartbeat("demo-agent", HeartbeatPayload(status="healthy"))
assert agent.heartbeat_count == 1
assert agent.capabilities["agenticlens"] == "1.0.3"
```

HTTP/CLI equivalents use `agents register payload.json` and `agents heartbeat AGENT_ID heartbeat.json`. Registration replaces a matching deployment and resets heartbeat count; heartbeat merges metadata maps and updates reported status/last_seen. See [registration payloads](getting-started.md) and [merge/replacement contract](capability-contract.md).

<span id="health"></span>

### Fleet health and version assessment

Use `status`, `agents list` filters and `GET /versions` / `api.assess_versions(...)` for reported fleet state and minimum-version assessment. Filters combine environment, status, capability presence or absence. Health is explicitly reported by the runtime; heartbeat age or a failed Evals gate does not rewrite it. Version comparisons use PEP 440, with missing/invalid versions represented separately. See [inventory/status API](api-reference.md) and [health semantics](limitations.md).

<span id="capabilities"></span>

### Capability discovery and contract

`GET /contracts/capabilities` or `api.get_capability_contract()` returns `tower.capabilities.v1`, with registration/heartbeat/readback JSON Schemas and mutation semantics. `capabilities list` inventories reported capabilities across registered agents. Python and Node.js worker examples exercise the same HTTP contract; framework metadata is not certified framework integration. See [contract, runtime examples and compatibility policy](capability-contract.md).

<span id="snapshots"></span>

### Offline snapshots

`read_snapshot()` validates captured data; `load_snapshot()` builds an in-memory facade. The CLI fixes posture freshness to the snapshot's capture time. Inventory/evidence reads work without a server; snapshots do not restore approvals, desired settings, live alerts, incident execution or credentials. See [snapshot fields and offline commands](evidence-posture.md#offline-snapshots) and [CLI support limits](cli-reference.md#offline-snapshot-mode).

<span id="authentication"></span>

### Authentication and operator roles

Reader tokens inspect state; writer tokens register, push evidence, preview and execute authorized operations; a distinct approver token approves/denies/revokes. Writers cannot approve their own proposal. HTTP identities derive from configured credentials, not request bodies. Trusted Python `Operator` objects can narrow `agent_ids`; shared HTTP role tokens are not per-user tenancy.

Set `AGENTICOPS_TOKEN` in a client terminal or pass `--token`. Anonymous development inventory is possible with no tokens, but controlled operations still require credentials. See [authentication/rotation](authentication.md), [server settings](settings.md) and [exact role requirements](api-reference.md#authentication).

<span id="configuration"></span>

### Configuration ownership and desired state

Trusted Python setup declares configuration as Tower-owned or mirrored. HTTP cannot elevate ownership. `config AGENT_ID CAPABILITY` reads values/revision; an action preview proposes a bounded patch or desired enable/disable. Executing a configuration action commits desired state; it does not mutate heartbeat inventory or prove a remote runtime applied it.

```bash
uv run python examples/controlled_configuration.py
```

See [declaration, patch semantics and desired-state boundaries](configuration.md). No generic production remote configuration connector is shipped.

<span id="approvals"></span>

### Exact approval lifecycle

```bash
agenticops-control-tower --token "$WRITER_TOKEN" actions preview request.json
agenticops-control-tower --token "$APPROVER_TOKEN" actions approve ACTION_ID
agenticops-control-tower --token "$WRITER_TOKEN" actions execute ACTION_ID
```

Inspect the returned preview before approval. It binds target/environment, revision, before/after values, intent, impact and expiry; changed/stale/revoked/consumed proposals cannot dispatch. Denial/revocation use approver authority. See [immutable previews and one-time consumption](configuration.md).

<span id="bulk"></span>

### Bulk fleet operations

`bulk preview` freezes a sorted 1–100 target list from explicit environment/capability selectors and optional IDs. Separate approval binds that exact set; later registrations do not join it. Execute rechecks target identity/revision and reports every result, including partial failure. The CLI exits 1 if any target fails.

```bash
uv run python examples/fleet_operations.py
```

See [bulk payloads, scope, deterministic targeting, audit and interruption](fleet-operations.md).

<span id="stop"></span>

### Runtime stop and access revocation

Trusted hosts install `SidecarContainmentAdapter` per deployment and configure issuer-backed MCP revocation (`MCPAccessRevoker`). `POST /incidents/{id}/control/{action}` accepts `stop` or `restart`. Incident control routes and bulk `runtime.stop` coordinate bounded acknowledgements; they do not discover arbitrary runtimes or accept caller-selected endpoints/commands. Already-reserved work can complete. Missing connectors, timeout and partial revocation remain explicit.

See [incident runtime controls and revoker contract](incident-recovery.md), [bulk stop semantics](fleet-operations.md#bulk-stop-and-mcp-revocation) and [containment integration limits](phase6-containment.md). Restart does not renew revoked credentials.

<span id="evidence"></span>

### Evidence ingestion and posture

Push native artifacts with an `EvidenceLink` naming a registered deployment, producer/version, artifact type/reference, observation time and optional run/runtime-agent correlation. `evidence ingest`, manifest ingestion and Sidecar-journal ingestion preserve explicit attribution. References are labels: Tower neither fetches nor opens them.

Read `evidence history`, per-agent evidence posture and fleet `posture`. Idempotent ingestion, history retention and freshness are separate from producer outcomes. See [payloads, storage and native tallies](evidence-posture.md) and [identity/reader boundaries](ecosystem-alignment.md).

<span id="native-contracts"></span>

### Native artifact readers and schemas

Thin adapters project native Lens runs/diagnosis, Evals reports/gates, Sidecar decisions/journals and Chaos reports. They do not recompute producer judgments. Two bundled native Evals JSON Schemas support report/gate validation; native availability, schema validity, authentication and task success remain different claims.

The capability descriptor generates its own Tower-local schemas; it is not an AIOS artifact. See [reader failure behavior and ownership](ecosystem-alignment.md), [native Evals contracts](evals-report-contract.md), and [capability contract](capability-contract.md).

<span id="execution"></span>

### Lens execution verification

Ingest a Lens `ExecutionBundle` with expected run identity and `spec_version="0.4-draft"`. Configure `AGENTICOPS_LENS_TRUST_STORE` or host `trusted_lens_keys`; the HTTP request cannot configure trust. Only verified bundles produce available evidence/causal claims. Failed, unknown and incomplete states persist distinctly without raw payloads.

Keys are loaded at app creation; restart after trust-file changes. Stored results are historical ingestion-time verification; changing trust does not rewrite them. See [complete key setup, rotation, identity mapping and limits](lens-execution-evidence.md).

<span id="incidents"></span>

### Incident detection and investigation

`incidents detect` consumes available failed native Lens evidence for a registered deployment. Repeated detection of that observation returns the same incident. `incidents investigate` assembles same-deployment/run evidence with citations, missing inputs, uncertainty and contradictory signals. It does not call a bundled model or establish exact causality.

See [detection/investigation inputs and timeline windows](incident-recovery.md) and [joined incident views](live-operations.md#incident-console-and-joined-audit).

<span id="staging"></span>

### Approved staging recovery

The fixed `staging.restore_dependency.v1` action needs a host-installed `StagingDependencyRuntime` connector. A separate human approves the exact preview digest before writer execution. The default `serve` instance has no installed remediation connector; it cannot execute a production fix by itself.

```bash
uv run --with ../agenticlens --with ../agentic-evals python examples/incident_recovery.py
```

This offline fixture runs no shell commands. A successful action moves to awaiting verification, not resolved. See [connector installation, exact request bodies, durable claims and negative walkthrough](incident-recovery.md).

<span id="alerts"></span>

### Periodic detection and alerts

The local server scans stored telemetry every 30 seconds by default; trusted hosts can configure `DetectionPolicy` or disable the loop and schedule `POST /alerts/evaluate`. Rules cover failed native evidence, heartbeat gaps and evidence freshness. Alerts deduplicate, retain acknowledgement and clear/reopen lifecycle audit.

```bash
agenticops-control-tower --token "$WRITER_TOKEN" alerts evaluate
agenticops-control-tower --token "$READER_TOKEN" alerts list --active-only
```

This is current-posture scanning, not lossless remote polling. Clearing an alert never resolves its incident. See [rules, freshness, correlation and atomic scan persistence](live-operations.md).

<span id="runbooks"></span>

### Versioned runbooks

Runbook catalog versions define up to 10 bounded steps, prerequisites, impact, rollback and recovery criteria. Each step has a 1–30 s timeout, up to 3 attempts (retried only after a connector-reported clean failure) and an optional rollback action. The built-in `staging.dependency_recovery` 1.0.0 drains, restores and resumes one dependency on the deterministic `StagingRunbookRuntime`. Read `runbooks catalog`, validate a version against explicitly supplied Chaos/Evals evidence, request recommendations for an incident, then preview exact version/parameters/digest. Separate human approval precedes execution.

```bash
uv run --with ../agenticlens --with ../agentic-evals python examples/runbook_recovery.py
```

Hosts install trusted connectors; no arbitrary model-generated shell action is executed. See [catalog, connector interfaces, validation, limits and CLI](runbooks.md).

<span id="cancellation"></span>

### Cancellation, compensation and reconciliation

`runbooks cancel EXECUTION_ID` requests cancellation before/between steps. Known completed steps may receive bounded compensation; partial, timed-out, interrupted or unknown execution can require manual reconciliation. Approval consumption and execution claims commit before dispatch to avoid unsafe replay after a crash.

A timeout or cancellation request is not proof that external side effects stopped or rolled back. See [step outcomes, cancellation, interruption and compensation](runbooks.md#step-outcomes) and [reconciliation limits](limitations.md).

<span id="verification"></span>

### Recovery verification

Resolution requires a successful connector probe plus fresh native Lens success and a passing Evals gate linked to the same recovery run/deployment, with observations and ingestion after execution began. Missing, stale, future, contradictory or mismatched evidence cannot establish recovery. Tower reads producer conclusions; it does not recompute Lens/Evals policy.

See [verification request fields and evidence-age rules](incident-recovery.md#evidence-uncertainty-and-verification) and [versioned runbook recovery criteria](runbooks.md#recovery-criteria).

<span id="console"></span>

### Read-only console

The `/console/` shell loads no fleet data until authenticated reads succeed. Inspect inventory, reported health, capability/version coverage, evidence posture, alerts, incidents and runbook executions. Joined timelines identify citations, approval/execution state and truncated evidence windows. Console requests remain GET-only; mutations use the same role-protected API/CLI. See [console and joined audit](live-operations.md#incident-console-and-joined-audit) and [hosting](hosting.md).

<span id="mcp"></span>

### MCP operator integration

The separate MCP package exposes Tower read, investigation, preview, execution and verification tools. Configure trusted connector origins/read-write credentials on the MCP host; hosted MCP uses per-user bindings. Prompt `tower.investigation` guides evidence-based review. No model tool grants human approval, and execution must use the separately approved digest.

See [connector setup, timeouts, tools and approval boundary](mcp-connector.md), [runbook MCP surface](runbooks.md#mcp) and [candidate capability discovery](capability-contract.md).

<span id="aios"></span>

### AIOS investigation-report export

`incidents.export.export_investigation_report(incident, created_at=...)` projects a held authorized native Incident into an AIOS `0.8-draft` report. It preserves deployment/source identity, native state and explicit evidence citations while redacting summaries, private findings and event details. It fetches nothing and executes no recovery.

```bash
uv run python examples/operational_artifacts.py
```

Closure alone yields unknown recovery; a supported native verification event is cited separately without authenticating/recomputing it. See [projection checks and rollback](coordinated-v1-readiness.md) and [operational artifact boundaries](aios-0.8-operational-artifacts.md).

<span id="interfaces"></span>

### Python, HTTP and CLI surfaces

The base `ControlTowerAPI` facade composes registry/discovery, configuration, evidence, incidents, bulk, operations and runbook services. The optional `[api]` extra adds FastAPI, server and HTTP client dependencies. Global CLI options precede commands. `/docs` exposes the running API's OpenAPI shapes; `GET /contracts/capabilities` is the separate candidate inventory descriptor.

See [API Reference (detailed)](api-reference.md) for the full route inventory, facade methods and every service signature and [all CLI commands/arguments](cli-reference.md). Python service calls are trusted-host calls; authentication is the host's responsibility.

<span id="hosting"></span>

### Persistence and hosting

Use `--database` / `AGENTICOPS_DATABASE` for local SQLite persistence. With no database, state is memory-local and disappears on restart. Registry, evidence, desired configuration, approvals, incidents, alerts and runbook claims share the configured local control model; fixture/runtime state can use its own database.

Host one Python API/console service with deployment-owned secrets and an HTTPS/access boundary. The package does not provision cloud resources, distribute SQLite or install production connectors. See [local/private/remote hosting and storage responsibilities](hosting.md) and [concurrency/scale limits](limitations.md).

<span id="settings"></span>

## Settings and operational limits

Configure `serve --host`, `--port`, `--database`, role-token environment variables and optional Lens trust. Client options are `--api-url`, `--token` and `--snapshot`. Python hosts can configure detection intervals/policies, service instances, trusted connectors, operator scopes and verification keys explicitly.

See [all server/client settings and built-in limits](settings.md), [configuration ownership](configuration.md), [authentication](authentication.md) and [limitations](limitations.md). Reported packages/capabilities are inventory assertions, not installation or production-readiness proof.

<span id="acceptance"></span>

### Compatibility and acceptance

The capability contract has its own candidate identifier; native evidence and AIOS markers remain independently versioned. Python/Node HTTP fixtures and installed-wheel tests demonstrate inventory interoperability within their recorded matrix, not production runtime connectors, general causal diagnosis, distributed control or independent AIOS conformance.

See [candidate validation record](phase10-validation.md), [contract evolution](capability-contract.md#evolution-and-release-gate), [ecosystem compatibility](integrations.md) and [coordinated acceptance limits](coordinated-v1-readiness.md). Version-labelled notes apply to their stated releases.

## Troubleshooting

Check server/client token roles, global option order, exact deployment/evidence IDs and whether a required connector/trust store is installed. For rejected operations inspect preview expiry, revision, approval actor/digest, consumed state and durable execution claims. Reconcile unknown work rather than retrying a side effect blindly. See [troubleshooting](troubleshooting.md).

## Reference

- [API reference](api-reference.md), [CLI reference](cli-reference.md) and [capability descriptor](capability-contract.md).
- [AI Reference (robust)](https://deepagentlabs.io/control-tower/docs/llms-full.md) and [capability/source index](ai-reference-index.md).
- [Source manifest and checksums](ai-docs-manifest.json).
