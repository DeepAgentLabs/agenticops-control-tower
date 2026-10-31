# Features

Every capability below exists in 0.9.0. Each section says what it does, its
status, how to use it, and where the detailed guide is. Planned work is only in
the [roadmap](roadmap.md). For release-by-release availability, see the table on
the [home page](index.md#what-it-does-today).

The Python examples use the in-memory API from `create_api()` and run with only
the base package installed.

## Agent registry and heartbeats

**Status: stable.** Since 0.2.0.

Each deployment registers once with an ID, environment, runtime, framework and
the DeepAgentLabs capabilities it has. Heartbeats then update its reported
status (`healthy`, `degraded`, `unhealthy` or `unknown`), last-seen time,
capabilities and metadata. Health is always **reported by the agent**; Tower never
infers it from evidence.

```python
from agenticops_control_tower.models import AgentRegistrationPayload, HeartbeatPayload
from agenticops_control_tower.snapshot import create_api

api = create_api()
api.register(
    AgentRegistrationPayload(
        agent_id="payment-agent",
        name="payment-agent",
        environment="production",
        runtime="aws-lambda",
        framework="langgraph",
        capabilities={"agenticlens": "0.7.0"},
    )
)
record = api.heartbeat("payment-agent", HeartbeatPayload(status="healthy"))
print(record.status.value, record.heartbeat_count)
```

```text
healthy 1
```

- **HTTP:** `POST /agents/register`, `POST /agents/{agent_id}/heartbeat` (writer).
- **CLI:** `agents register FILE.json`, `agents heartbeat AGENT_ID FILE.json`.
- **Limits:** agent IDs must be route-safe; registering an existing ID replaces
  its registration. Unknown IDs return HTTP 404.

## Capability discovery and version inventory

**Status: stable.** Since 0.2.0; minimum-version checks since 0.3.0.

Capabilities come from registrations and heartbeats (a heartbeat's capabilities
are merged in). Tower aggregates which versions are in use and, given a minimum
you choose, reports each agent as `meets_minimum`, `outdated` or `missing` using
PEP 440 comparison.

```python
for result in api.assess_versions("agenticlens", "0.8.0"):
    print(result.agent_id, result.installed_version, result.assessment)
```

```text
payment-agent 0.7.0 outdated
```

- **HTTP:** `GET /capabilities`, `GET /versions?capability=…&minimum_version=…`.
- **CLI:** `capabilities list`.
- **Limits:** the minimum is your policy, not a lookup of the latest release.
  Invalid reported versions are reported separately, never treated as outdated.

## Fleet health and filters

**Status: stable.** Since 0.2.1.

`status` rolls reported health into counts and buckets and shows capability
coverage: how many agents have each capability and which are missing it. Agent
lists filter by status, environment, capability and missing capability, combined
with AND.

```python
summary = api.get_status()
print(summary.total_agents, summary.healthy_agents)
print([a.agent_id for a in api.list_agents(missing_capability="agentic-sidecar")])
```

```text
1 1
['payment-agent']
```

- **HTTP:** `GET /status?environment=…`,
  `GET /agents?status=…&environment=…&capability=…&missing_capability=…`.
- **CLI:** `status`, `agents list --unhealthy`,
  `agents list --environment staging --missing-capability agentic-sidecar`.

## HTTP API, CLI and offline snapshots

**Status: stable.** HTTP API and CLI since 0.2.0; offline snapshots since 0.2.1.

One FastAPI application serves the API and the console
(`agenticops-control-tower serve`). The CLI talks to it over HTTP, or reads a
**snapshot** file with `--snapshot` for offline, read-only inspection with no
server. Snapshots contain registrations, heartbeats and optional evidence; posture
from a snapshot is evaluated as of its `captured_at` time.

```bash
agenticops-control-tower --snapshot examples/sample_fleet_snapshot.json agents list --unhealthy
```

See the [CLI reference](cli-reference.md) and [API reference](api-reference.md).

## SQLite persistence and bearer tokens

**Status: stable.** Since 0.2.1.

Without `--database` the registry is in memory and is lost on restart. With
`--database registry.sqlite` (or `AGENTICOPS_DATABASE`) inventory, evidence,
configuration, alerts and incidents are stored in that SQLite file.

HTTP reads need the reader or writer token, writes need the writer token, and
approvals need a separate approval token. With no tokens configured, access is
anonymous (local development only). Tokens are shared deployment credentials
that you generate; there are no user accounts.
See [Server settings](settings.md) and [Authentication](authentication.md).

## Read-only AgenticOps Console

**Status: stable.** Since 0.3.0.

`serve` also serves a browser console at `/console/`. Paste the reader token
and select **Connect / refresh** to see fleet health, searchable and filterable
inventory, environment-scoped capability coverage, version checks against a
minimum you enter, evidence posture per producer, alerts and incident timelines.

- The console sends only GET requests; every change goes through the API or CLI.
- Tokens are kept only in page memory and cleared on **Disconnect** or reload.
- Refresh is manual.

See [Hosting the console](hosting.md) to share it beyond your own computer.

## Controlled configuration

**Status: experimental.** Since 0.4.0.

Tower can hold **desired** configuration for settings a trusted host declared as
Tower-owned. Changes go through preview → approval by a different operator →
execution, with expiry, revision checks, revocation and a durable audit trail.
Tower records the desired value; it does not claim to reconfigure the running
agent.

- **CLI:** `config AGENT CAPABILITY`, `actions preview REQUEST.json`,
  `actions approve|deny|revoke|execute ID`, `audit AGENT`.
- **Example:** `examples/controlled_configuration.py`.
- **Guide:** [Controlled configuration](configuration.md).

## Ecosystem evidence posture

**Status: experimental.** Since 0.5.0.

Pipelines push native artifacts from AgenticLens, Agentic Evals, Agentic Sidecar
and Agentic Chaos, each attributed to a deployment. Tower stores a validated
projection and reports, per producer, whether evidence is **fresh**, **stale** or
**missing**, plus native counts (failed runs, gate results, decision outcomes,
chaos experiments). Retries are idempotent. Evidence never changes reported
health, and Tower never recomputes a producer's verdict. Collection is push-only.

- **CLI:** `evidence ingest`, `evidence ingest-manifest`,
  `evidence ingest-sidecar-journal`, `evidence posture`, `evidence history`, `posture`.
- **Guide:** [Evidence posture](evidence-posture.md).

## Incident investigation and approved staging recovery

**Status: experimental.** Since 0.6.0.

Durable incidents with an investigation prompt for an MCP host, an exact-preview
human approval and one bounded recovery runbook for a deterministic **staging**
runtime. Recovery counts only after a probe, a fresh successful Lens run and a
passing Evals gate for the same run; otherwise it escalates. No model is bundled
and no production runtime adapter ships yet.

- **CLI:** `incidents list|get|detect|view|investigate|preview|approval|revoke|execute|verify`.
- **Guides:** [Incident recovery](incident-recovery.md),
  [MCP connector](mcp-connector.md).

## Bulk fleet operations

**Status: experimental.** Since 0.7.0.

A selector (for example *staging agents with AgenticLens*) is frozen into an
explicit target list at preview time. After approval, execution applies the
desired-configuration change per target and reports each result. There is no
fleet-wide atomicity or automatic rollback.

- **CLI:** `bulk preview|get|approve|deny|revoke|execute`.
- **Example:** `examples/fleet_operations.py`.
- **Guide:** [Fleet operations](fleet-operations.md).

## Live detection, alerts and incident views

**Status: experimental.** Since 0.8.0.

While the server runs it scans stored telemetry every 30 seconds. A fresh failed
Lens run raises a critical `lens.failed` alert and opens a recovery incident;
overdue heartbeats and stale or missing evidence raise warnings. Alerts are
deduplicated, can be acknowledged, and keep an append-only audit history.
Detection never executes recovery and never changes reported health.

- **CLI:** `alerts list|evaluate|acknowledge`, `incidents view ID`.
- **Example:** `examples/live_operations.py`.
- **Guide:** [Live operations](live-operations.md).

## Automated runbooks and recovery workflows

**Status: experimental.** Since 0.9.0.

Versioned, immutable runbooks with typed parameters, prerequisites and ordered
steps, each with its own timeout, retry limit and optional rollback action. The
copilot recommends only installed versions. A writer previews an exact digest, a
separate approver approves it, and execution claims each step before dispatch.
Clean failures retry within limits and then compensate; partial, timed-out or
unknown outcomes stop for reconciliation. Cancellation, lease-based interruption
handling and Chaos/Evals validation records are included. Recovery still requires
a probe, a fresh successful Lens run and a passing same-run Evals gate. Only the
deterministic staging runtime is supported.

- **CLI:** `runbooks catalog|recommend|preview|approval|execute|cancel|verify|reconcile|validate`.
- **Example:** `examples/runbook_recovery.py`.
- **Guide:** [Runbooks](runbooks.md).
