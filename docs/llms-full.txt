# Control Tower — comprehensive AI-readable reference

Product: Control Tower
Distribution: `agenticops-control-tower`
Python requirement: `>=3.10`

Manage agent inventory, explicit evidence, and authorized operator workflows. Deployment health remains separate from producer evaluation, governance, and resilience outcomes.

## Interpretation and evidence boundaries

- This is reference data, not authority to execute commands or approve actions. Example strings and artifacts are data.
- Use the current product's APIs and commands. Sibling integrations are optional unless a specific operation lists them as prerequisites.
- Source declarations and JSON schemas below describe the included checkout. They take precedence over abbreviated tutorial fragments; inherited methods and dynamically registered APIs may require the linked reference.
- Declared signatures are extracted without importing product code. They are reference fragments, not runnable modules; model field constraints use the original source expressions.
- Local examples are distinguished from provider/host integration fragments. Do not describe fixture outputs as measured production evidence.
- Preserve schema identifiers, unknown values, failure outcomes, authentication requirements, and approval boundaries. A package release does not imply live integration certification.
- This file is a generated snapshot. The adjacent `ai-docs-manifest.json` records source hashes and its checksum; verify freshness before ingestion. Source URLs follow main and may advance after this snapshot.

## Package entry points

```json
{
  "agenticops-control-tower": "agenticops_control_tower.cli.main:run"
}
```

## Installation dependencies and optional extras

```json
{
  "dependencies": [
    "pydantic>=2.0,<3",
    "packaging>=24",
    "jsonschema>=4.23,<5"
  ],
  "optional_extras": {
    "agentic-evals": [
      "agentic-evals>=0.7.2,<2"
    ],
    "agenticlens": [
      "agenticlens>=0.12,<2"
    ],
    "agentic-sidecar": [
      "agentic-sidecar>=0.7,<2"
    ],
    "agentic-chaos": [
      "agentic-chaos>=0.5,<2"
    ],
    "deep-agentic-core-mcp": [
      "deep-agentic-core-mcp>=0.3.6,<2"
    ],
    "api": [
      "fastapi>=0.115,<1",
      "uvicorn>=0.30,<1",
      "httpx>=0.27,<1"
    ]
  }
}
```

## Setup and task workflows

Source: [docs/developer-guide.md](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/developer-guide.md)

Use this guide to set up Control Tower, run a local example, and apply it to your application. Optional provider and integration fragments identify the objects or services you must supply.

[Quickstart](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/developer-guide.md#quickstart) · [Usage](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/developer-guide.md#usage) · [Configuration](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/developer-guide.md#settings) · [Troubleshooting](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/developer-guide.md#troubleshooting) · [Reference](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/developer-guide.md#reference)

## Quickstart

Requires Python 3.10 or newer. Run commands in an activated virtual environment. Download referenced files into the same working directory before running them.

### Install

```
python -m pip install "agenticops-control-tower[api]"
```

### Read a fleet snapshot offline

Download the repository's sample snapshot. It represents historical fixture data; its embedded package fields are evidence values, not installation recommendations.

[Download sample_fleet_snapshot.json](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/guide/examples/sample_fleet_snapshot.json)

```
agenticops-control-tower --snapshot sample_fleet_snapshot.json status
agenticops-control-tower --snapshot sample_fleet_snapshot.json agents list
agenticops-control-tower --snapshot sample_fleet_snapshot.json posture
```

**Expected:** the fixture lists two agents and their recorded status/evidence. This reports the snapshot, not a live health check.

### Start a local console

Create separate reader and writer tokens, then configure them in the server terminal. The placeholders below must be replaced with generated secrets.

```
python -c "import secrets; print(secrets.token_hex(32))"
```

Windows PowerShell

```
$env:AGENTICOPS_READ_TOKEN = "YOUR_GENERATED_READER_TOKEN"
$env:AGENTICOPS_WRITE_TOKEN = "YOUR_GENERATED_WRITER_TOKEN"
agenticops-control-tower serve --database registry.sqlite --host 127.0.0.1 --port 8000
```

macOS / Linux

```
export AGENTICOPS_READ_TOKEN="YOUR_GENERATED_READER_TOKEN"
export AGENTICOPS_WRITE_TOKEN="YOUR_GENERATED_WRITER_TOKEN"
agenticops-control-tower serve --database registry.sqlite --host 127.0.0.1 --port 8000
```

Open [the local console](http://localhost:8000/console/), supply the reader token, and refresh. A fresh registry is empty until agents register; loading the offline snapshot does not populate the server.

### Connect agents and evidence

Register an agent using the documented registration payload, send heartbeats from its runtime, then push producer artifacts with explicit agent/run links. Use a writer token for mutations. Evidence posture and reported runtime health remain separate signals.

[Register and send heartbeats ↗](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/getting-started.md) · [Link evidence ↗](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/evidence-posture.md) · [Authentication ↗](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/authentication.md)

## Usage

<span id="registration"></span>

### Register agents and send heartbeats

Start the server using [the quickstart](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/developer-guide.md#quickstart). In a second terminal, activate the same environment and configure the writer token for the CLI client.

#### Client credentials

PowerShell

```
$env:AGENTICOPS_TOKEN = "THE_SERVER_WRITER_TOKEN"
```

macOS / Linux

```
export AGENTICOPS_TOKEN="THE_SERVER_WRITER_TOKEN"
```

The server's token setting is not automatically inherited by another terminal.

tower_registration.json · complete file

```json
{
  "agent_id": "support-demo",
  "name": "Support demo",
  "environment": "staging",
  "runtime": "local-python",
  "framework": "custom",
  "status": "unknown",
  "capabilities": {}
}
```

[Download tower_registration.json](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/guide/examples/tower_registration.json)

tower_heartbeat.json · complete file

```json
{"status":"healthy","capabilities":{}}
```

[Download tower_heartbeat.json](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/guide/examples/tower_heartbeat.json)

```
agenticops-control-tower agents register tower_registration.json
agenticops-control-tower agents heartbeat support-demo tower_heartbeat.json
agenticops-control-tower status
```

**Expected:** the registered demo deployment reports a healthy heartbeat. Refresh the console to inspect it. This is a manually supplied demo heartbeat, not a runtime probe.

<span id="evidence"></span>

### Ingest evidence and read posture

#### Ingesting evidence

| Surface | Call |
| --- | --- |
| Python | `ControlTowerAPI.ingest_evidence(EvidenceIngestRequest(link=..., artifact=..., gate=...))` |
| HTTP (writer) | `POST /evidence` with `{"link": {...}, "artifact": {...}, "gate": {...}}` |
| CLI (writer) | `evidence ingest AGENT SOURCE ARTIFACT.json --source-version V --artifact-ref REF` |
| CLI manifest | `evidence ingest-manifest examples/evidence/manifest.json` |
| CLI Sidecar journal | `evidence ingest-sidecar-journal AGENT journal.json --source-version 0.7.0` |

`--observed-at` defaults to the current time. `--gate` attaches an existing

Evals `GateDecision`, and `--run-id` and `--runtime-agent-id` add correlation.

Manifest entries contain a `link`, plus an optional `artifact_path` and

`gate_path`, resolved relative to the manifest. Files are read by the CLI

process; the server never opens caller paths. An entry without an artifact is

stored as an honest `unavailable` record.

Ingestion rules:

- The deployment must already be registered (`404` / `AgentNotFoundError`).
- The same deployment, source, `artifact_ref` and `observed_at` identify one

observation. Retries return the existing record with `created: false` (HTTP

`200` instead of `201`), so producers can safely retry.

- `observed_at` more than five minutes in the future is rejected (`422`).

Naive timestamps are treated as UTC.

- HTTP bodies need a `Content-Length` (`411`) and are limited to 1 MiB (`413`).

ASGI middleware enforces this before the body is parsed or authorized, and

also counts streamed bytes.

- Invalid or unsupported artifacts are stored as `unavailable`, with a reason

that names the failing native field without echoing producer values.

- Only the projection is stored. Raw artifacts, Lens span inputs/outputs and

error messages are not stored. Sidecar `trigger_details` are kept because

the native reader projects them.

#### History and posture

| Read | Python | HTTP (reader) | CLI |
| --- | --- | --- | --- |
| History, newest first | `evidence_history(agent, source=, limit=)` | `GET /agents/{id}/evidence/history?source=&limit=` (1–500) | `evidence history AGENT [--source] [--limit]` |
| Agent posture | `agent_posture(agent, stale_after_seconds=)` | `GET /agents/{id}/evidence?stale_after_seconds=` | `evidence posture AGENT` |
| Fleet posture | `fleet_posture(environment=, stale_after_seconds=)` | `GET /posture?environment=&stale_after_seconds=` | `posture [--environment]` |

Each deployment gets one entry per producer:

- `freshness`: `fresh` when the latest observation is inside the window

(default 86400 seconds, maximum 30 days over HTTP), `stale` when it is older,

`missing` when nothing was recorded. Missing evidence is never treated as healthy

or as a failed check.

Each agent or fleet posture is read from one store transaction, so concurrent

ingestion or pruning cannot make it internally inconsistent. History limits

(1–500) and windows (1 second to 30 days) are validated in Python, HTTP and CLI,

including `--snapshot` mode.

- `latest`: the newest record by `observed_at`, including an `unavailable` one,

so a broken producer feed stays visible.

- `recent_records` / `recent_unavailable`: counts inside the window.
- `summary`: counts of native values in available records inside the window:

| Source | Native tallies |
| --- | --- |
| agenticlens | `status_counts` (running/succeeded/failed; runs and diagnosis reports), `attribution_counts` (attributed/recovered/unattributed/no_failure), `faulty_agents`, `failed_tool_names` from failed spans |
| agentic-evals | `gate_counts`: producer gate passed/failed, or `not_supplied` when no gate was paired |
| agentic-sidecar | `status_counts` for all seven outcomes, `risk_counts` (null risk is `unclassified`, never LOW), `escalations_required` |
| agentic-chaos | `experiments`, `completed`/`incomplete` by report end time, `fault_events` |

Fleet posture lists `fresh_agents`, `stale_agents`, `missing_agents` and

`latest_unavailable_agents` per producer, and adds the per-agent tallies

together. The `reported_health` field in agent posture is the registry value,

shown for context only.

Lens runs now also project `trace_id`, timing, `task_success`, `error_type`,

`span_count`, `tool_names` and `failed_spans` (span ID, name, type, tool and

error type). These link a failed run to the failing tool dependency. Lens has

no native prompt-version field, so Tower does not infer one.

Diagnosis artifacts can also be ingested through the supported producer contract. Keep detailed failure analysis in Lens.

#### Storage and retention

`serve --database registry.sqlite` (or `AGENTICOPS_DATABASE`) stores evidence in

the same SQLite file as the registry and configuration audit. Without a database,

evidence lives in process memory. `EvidenceStore.prune(before)` removes older

observations from Python. No automatic retention policy runs.

#### Offline snapshots

A fleet snapshot can contain an `evidence` list of ingestion requests.

`--snapshot FILE posture`, `evidence posture` and `evidence history` evaluate

freshness as of the snapshot's `captured_at`, so offline results do not change

with wall-clock time. Ingest commands are rejected in snapshot mode.

#### Console

The read-only console shows an **Ecosystem evidence posture** panel for the

selected environment, plus a per-agent evidence table with freshness, the

latest record, the recent window and native tallies. Producer text is

rendered as text, and the console still sends only GET requests.

<span id="settings"></span>

## Configuration

### Configure the server and client

#### Server (`agenticops-control-tower serve`)

| Option | Default | Meaning |
| --- | --- | --- |
| `--host` | `127.0.0.1` | Interface to bind. Use `0.0.0.0` to accept other computers on the network ([hosting](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/hosting.md)). |
| `--port` | `8000` | Port for the API and the console. |
| `--database PATH` | none (in memory) | SQLite file for inventory, evidence, configuration, alerts and incidents. Relative to the working directory. Without it, everything is lost on restart. |

| Environment variable | Used by | Meaning |
| --- | --- | --- |
| `AGENTICOPS_DATABASE` | server | SQLite path when `--database` is not given. |
| `AGENTICOPS_READ_TOKEN` | server | Bearer token allowed to read. |
| `AGENTICOPS_WRITE_TOKEN` | server | Bearer token allowed to read and write (register, heartbeat, evidence, previews, execution). |
| `AGENTICOPS_APPROVAL_TOKEN` | server | Separate token for approving, denying and revoking actions. Must differ from the reader and writer tokens, or the server refuses to start. |

Token rules, enforced on every HTTP route:

- **No token configured:** anonymous access to inventory routes. Local development

only. Configuration actions, bulk operations and incidents still require

configured credentials.

- **Reader only:** reads work, all writes are rejected.
- A writer token also permits reads. Missing or wrong tokens return `401`; a

reader calling a write route gets `403`.

Generate tokens with `python -c 'import secrets; print(secrets.token_hex(32))'`

or `openssl rand -hex 32`, once per deployment, and keep them in secret storage.

See [Authentication](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/authentication.md).

#### Built-in limits

| Setting | Value | Where it applies |
| --- | --- | --- |
| Live detection interval | 30 seconds | Scans stored telemetry while the server runs. Python hosts can pass `create_app(detection_interval_seconds=0)` to disable it and call `POST /alerts/evaluate` from their own scheduler. |
| Detection freshness and heartbeat windows | 300 seconds each | `DetectionPolicy`, configurable by a trusted Python host ([live operations](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/live-operations.md)). |
| Evidence stale-after | 1 day (max 30 days) | `--stale-after-seconds` / `stale_after_seconds` on posture reads. |
| Evidence history limit | 50 (max 500) | `evidence history --limit`. |
| Request body size | 1 MiB, `Content-Length` required | `POST /evidence` and `POST /bulk/preview`. |
| Action expiry | 1–3600 seconds | Configuration previews ([controlled configuration](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/configuration.md)). |

#### CLI client

| Option | Environment variable | Default | Meaning |
| --- | --- | --- | --- |
| `--api-url` | `AGENTICOPS_API_URL` | `http://localhost:8000` | Server to talk to. |
| `--token` | `AGENTICOPS_TOKEN` | none | Bearer token sent with every request. |
| `--snapshot FILE` | — | none | Answer read commands from a snapshot file instead of a server. |

Options go **before** the command:

```
agenticops-control-tower --api-url https://tower.example.com --token "$READER_TOKEN" status
```

#### Python hosts

Embedding Control Tower in your own service uses the same settings as

arguments, which take precedence over the environment:

```
from agenticops_control_tower.api.http import create_app

app = create_app(
    database_path="registry.sqlite",
    read_token="...",
    write_token="...",
    approval_token="...",
    detection_interval_seconds=30,
)
```

Run it with any ASGI server, for example `uvicorn module:app`.

<span id="authentication"></span>

### Set up tokens and authorization

#### Generate tokens

Install the package into your Python environment:

```
python -m pip install "agenticops-control-tower[api]"
```

Generate independent reader and writer values with Python's standard library:

```
export AGENTICOPS_READ_TOKEN="$(python -c 'import secrets; print(secrets.token_hex(32))')"
export AGENTICOPS_WRITE_TOKEN="$(python -c 'import secrets; print(secrets.token_hex(32))')"
agenticops-control-tower serve --database registry.sqlite --host 127.0.0.1 --port 8000
```

These commands use Bash or a compatible shell. Use `python3` instead of `python`

if that is your interpreter name. `openssl rand -hex 32` is an alternative to the

Python generator. Both produce a random 64-character hexadecimal value.

Generate once per deployment and retain the values in your secret manager or a

restricted configuration file. Do not regenerate on every server start: clients

using the previous value would lose access. Environment variables exported in

one terminal do not automatically appear in another terminal or survive logout.

For PowerShell, the equivalent setup is:

```
$env:AGENTICOPS_READ_TOKEN = python -c "import secrets; print(secrets.token_hex(32))"
$env:AGENTICOPS_WRITE_TOKEN = python -c "import secrets; print(secrets.token_hex(32))"
agenticops-control-tower serve --database registry.sqlite --host 127.0.0.1 --port 8000
```

#### Give readers access

Open <http://localhost:8000/console/> on the server's

computer. Retrieve the reader value from your terminal or secret manager and

share it with authorized readers through a secure channel. Paste it into the

console's **Reader token** field and select **Connect / refresh**. The console

holds the token in page memory; reload or **Disconnect** clears it.

For CLI reads, set the client variable to that same reader value:

```
# In the server's shell this can reuse the generated value.
# In another shell, first obtain it from your deployment's secret storage.
export AGENTICOPS_TOKEN="$AGENTICOPS_READ_TOKEN"
agenticops-control-tower status
```

| Variable | Set on | Purpose |
| --- | --- | --- |
| `AGENTICOPS_READ_TOKEN` | Server | Authorizes inventory, status, version, evidence history and posture reads |
| `AGENTICOPS_WRITE_TOKEN` | Server | Authorizes reads plus agent registration, heartbeats and evidence ingestion |
| `AGENTICOPS_TOKEN` | CLI client | Sends a configured reader or writer value to the server |
| `AGENTICOPS_API_URL` | CLI client | Selects the server, e.g. `https://tower.example.com` |

Use the writer value for CLI registration/heartbeats or agent integrations:

```
export AGENTICOPS_TOKEN="$AGENTICOPS_WRITE_TOKEN"
agenticops-control-tower agents register examples/sample_agent_registration.json
```

The sample registration file is provided in the source repository; PyPI users

can supply their own JSON file. The console remains read-only even if given a

writer token, but reader tokens are the appropriate credentials to distribute.

#### Authorization behavior and rotation

With both server variables unset, the API permits anonymous local development.

With only a reader configured, writes are rejected. With only a writer configured,

reads and writes require that writer. Set different, nonempty values for both roles;

using the same value would give readers writer access.

To rotate a token, generate a new value, update the deployment's secret storage,

restart/redeploy the service, and distribute the replacement to its clients.

The service reads these settings at application startup. It supports one token

per role, with no overlap period, per-user revocation, expiry or tenant isolation.

Do not put tokens in URLs, tracked files, Docker images or shared logs. Use HTTPS

for remote browser/API traffic. See [the hosting guide](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/hosting.md) for local,

private-network and cloud access.

## Troubleshooting

Check the failing boundary before changing application behavior.

- Missing server command dependencies: install the API extra.
- Unauthorized: use the correct reader/writer token and pass it in the client terminal as documented.
- Empty console: register agents; the offline example does not seed the database.
- Stale posture: inspect evidence timestamps and links before inferring current health.

### Verify your environment

Run commands from the environment where you installed the package. Confirm the input file exists and matches the expected artifact contract. Keep the original evidence when diagnosing a failure.

## Reference

Use the current product reference for exact method signatures, command options, and supported artifacts. The code fragments in configuration and how-to articles build on the quickstart; they are not all standalone scripts.

- [Open API / CLI reference ↗](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/cli-reference.md)

---

## Api Reference

Source: [docs/api-reference.md](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/api-reference.md)

Control Tower has two programmatic surfaces: the **HTTP API** served by
`agenticops-control-tower serve` (or `create_app()`), and the **Python API**
(`ControlTowerAPI`), which the HTTP layer and CLI both use. The routes below are
taken from `api/http.py` in 0.9.0. While the server runs, FastAPI's generated
OpenAPI page at `/docs` lists the exact request and response schemas.

## Authentication

Send `Authorization: Bearer <token>`. Roles come from the server's configured
tokens ([server settings](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/settings.md)):

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
| `POST /incidents/detect`, `POST /incidents/{id}/investigate`, `/preview`, `/approval`, `/revoke`, `/execute`, `/verify`, `/control/{action}`, `/reconcile` | operator | Approved staging recovery; see [incident recovery](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/incident-recovery.md). |

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

See [runbooks](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/runbooks.md) for request bodies and outcomes.

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
[server settings → Python hosts](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/settings.md#python-hosts).

## Versioned capability discovery

`GET /contracts/capabilities` requires inventory reader access and returns the `tower.capabilities.v1` candidate descriptor. Python: `api.get_capability_contract()`. See [schemas, runtime examples and evolution policy](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/capability-contract.md).

---

## Cli Reference

Source: [docs/cli-reference.md](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/cli-reference.md)

The `agenticops-control-tower` command is installed with the package. Server
commands need the `api` extra (`httpx`); offline `--snapshot` reads and `serve`'s
argument parsing do not. Every command prints JSON to standard output.

Global options go **before** the command:

| Option | Environment variable | Default |
| --- | --- | --- |
| `--api-url URL` | `AGENTICOPS_API_URL` | `http://localhost:8000` |
| `--token TOKEN` | `AGENTICOPS_TOKEN` | none |
| `--snapshot FILE` | — | none (talk to the server) |

```bash
agenticops-control-tower --token "$READER_TOKEN" agents list --unhealthy
```

The package also runs as a module: `python -m agenticops_control_tower.cli.main …`.

## Server

| Command | Role | Description |
| --- | --- | --- |
| `serve [--host HOST] [--port PORT] [--database PATH]` | — | Run the HTTP API and console. Defaults: `127.0.0.1`, `8000`, in-memory storage. See [server settings](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/settings.md). |

## Inventory and health

| Command | Role | Description |
| --- | --- | --- |
| `agents register FILE.json` | writer | Register (or replace) an agent from a registration payload, e.g. `examples/sample_agent_registration.json`. |
| `agents heartbeat AGENT_ID FILE.json` | writer | Send a heartbeat: `{"status": "healthy", "capabilities": {...}}`. |
| `agents list [--status S] [--unhealthy] [--environment E] [--capability C] [--missing-capability C]` | reader | List agents; filters combine with AND. `--unhealthy` is `--status unhealthy`. Status is one of `healthy`, `degraded`, `unhealthy`, `unknown`. |
| `agents get AGENT_ID` | reader | One agent record. |
| `capabilities list` | reader | Capability → versions seen across all agents. |
| `status [--environment E]` | reader | Health counts, buckets and capability coverage. |

## Evidence and posture

| Command | Role | Description |
| --- | --- | --- |
| `evidence ingest AGENT_ID SOURCE ARTIFACT.json --source-version V --artifact-ref REF [--observed-at ISO] [--run-id ID] [--runtime-agent-id ID] [--gate GATE.json]` | writer | Push one native artifact. `SOURCE` is `agenticlens`, `agentic-evals`, `agentic-sidecar` or `agentic-chaos`. |
| `evidence ingest-manifest MANIFEST.json` | writer | Push every entry of a manifest, e.g. `examples/evidence/manifest.json`. Paths resolve relative to the manifest. |
| `evidence ingest-sidecar-journal AGENT_ID JOURNAL.json --source-version V [--run-id ID] [--runtime-agent-id ID]` | writer | Push decisions from a Sidecar journal export. |
| `evidence history AGENT_ID [--source SOURCE] [--limit N]` | reader | Newest records first; `--limit` 1–500, default 50. |
| `evidence posture AGENT_ID [--stale-after-seconds N]` | reader | Per-producer freshness for one agent; default 86400 (1 day), maximum 30 days. |
| `posture [--environment E] [--stale-after-seconds N]` | reader | Fleet evidence posture by producer. |

See [evidence posture](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/evidence-posture.md).

## Controlled configuration

| Command | Role | Description |
| --- | --- | --- |
| `config AGENT_ID CAPABILITY` | reader | Configuration ownership and values. |
| `audit AGENT_ID` | reader | Configuration action audit. |
| `actions preview REQUEST.json` | writer | Create an immutable preview; returns its ID. |
| `actions get ID` | reader | Read an action. |
| `actions approve ID` / `actions deny ID` / `actions revoke ID` | approver | Decide on a preview (a different identity from the proposer). |
| `actions execute ID` | writer | Execute an approved, unexpired action. |

See [controlled configuration](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/configuration.md).

## Bulk fleet operations

`bulk preview FILE.json`, `bulk get ID`, `bulk approve|deny|revoke ID`
(approver), `bulk execute ID` (writer). `bulk execute` exits with status 1 when
any target fails, after printing every result. See
[fleet operations](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/fleet-operations.md); `examples/bulk_tracing.json` is a
preview payload.

## Alerts and incidents

| Command | Role | Description |
| --- | --- | --- |
| `alerts list [--environment E] [--active-only]` | reader | Current alerts. |
| `alerts evaluate` | writer | Run a detection scan now (the server also scans every 30 seconds). |
| `alerts acknowledge ALERT_ID` | writer | Acknowledge an alert. |
| `incidents list` / `incidents get ID` / `incidents view ID` | configured credentials | Read incidents; `view` joins inventory, evidence, alerts, approvals and timeline. |
| `incidents detect FILE.json`, `investigate ID`, `preview ID FILE.json`, `approval ID FILE.json`, `revoke ID`, `execute ID FILE.json`, `verify ID FILE.json` | writer / approver | The approved staging-recovery workflow. Request formats are in [incident recovery](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/incident-recovery.md). |

See [live operations](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/live-operations.md).

## Runbooks

| Command | Role | Description |
| --- | --- | --- |
| `runbooks catalog`, `runbooks validations RUNBOOK VERSION` | reader | Installed definitions and their validation records. |
| `runbooks recommend INCIDENT_ID`, `runbooks history INCIDENT_ID`, `runbooks get EXECUTION_ID` | configured credentials | Recommendations, execution history and one execution. |
| `runbooks preview INCIDENT_ID FILE.json`, `execute ID FILE.json`, `verify ID FILE.json`, `reconcile ID` | writer | Preview, run, verify and reconcile. |
| `runbooks approval ID FILE.json`, `revoke ID` | approver | Approve, deny or revoke the exact preview. |
| `runbooks cancel ID` | writer or approver | Cancel before or between steps. |
| `runbooks validate RUNBOOK VERSION FILE.json` | writer | Record Chaos and Evals validation evidence. |

`execute` and `verify` exit 1 unless the runbook is awaiting verification or
resolved. See [runbooks](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/runbooks.md) for request files.

## Offline snapshot mode

With `--snapshot FILE`, these read commands are answered from the file with no
server, token or `httpx`:

`agents list` (all filters), `agents get`, `capabilities list`, `status`,
`posture`, `evidence posture`, `evidence history`.

Posture is evaluated as of the snapshot's `captured_at`, so dated sample evidence
reads as it did when captured. Every other command is refused:

```text
agenticops-control-tower: error: --snapshot supports read commands only
```

## Exit codes and errors

- `0` on success. `1` when the server returns an error; the message is
  `Control Tower API returned <status>: <detail>`.
- `2` for invalid arguments (argparse).
- Server commands without `httpx` exit with:
  `This command talks to the Control Tower HTTP API and needs `httpx`. Install it with: pip install agenticops-control-tower[api]`.

---

## Evidence Posture

Source: [docs/evidence-posture.md](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/evidence-posture.md)

Control Tower v0.5 stores attributed Lens, Evals, Sidecar and Chaos evidence
and reports its freshness and native outcomes next to fleet inventory. The
sibling packages remain the source of truth: Tower stores validated
projections, counts native values and never recomputes evaluations,
supervision decisions or resilience verdicts. Evidence never changes reported
deployment health.

Collection is **push-based**. Producers, pipelines or operators send native
JSON artifacts to Tower with an explicit `EvidenceLink`. Tower does not fetch
`artifact_ref`, connect to producer services or discover evidence by itself.
See [the evidence contract](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/ecosystem-alignment.md) for link fields and reader
behavior.

## Ingesting evidence

| Surface | Call |
| --- | --- |
| Python | `ControlTowerAPI.ingest_evidence(EvidenceIngestRequest(link=..., artifact=..., gate=...))` |
| HTTP (writer) | `POST /evidence` with `{"link": {...}, "artifact": {...}, "gate": {...}}` |
| CLI (writer) | `evidence ingest AGENT SOURCE ARTIFACT.json --source-version V --artifact-ref REF` |
| CLI manifest | `evidence ingest-manifest examples/evidence/manifest.json` |
| CLI Sidecar journal | `evidence ingest-sidecar-journal AGENT journal.json --source-version 0.7.0` |

`--observed-at` defaults to the current time. `--gate` attaches an existing
Evals `GateDecision`, and `--run-id` and `--runtime-agent-id` add correlation.
Manifest entries contain a `link`, plus an optional `artifact_path` and
`gate_path`, resolved relative to the manifest. Files are read by the CLI
process; the server never opens caller paths. An entry without an artifact is
stored as an honest `unavailable` record.

Ingestion rules:

- The deployment must already be registered (`404` / `AgentNotFoundError`).
- The same deployment, source, `artifact_ref` and `observed_at` identify one
  observation. Retries return the existing record with `created: false` (HTTP
  `200` instead of `201`), so producers can safely retry.
- `observed_at` more than five minutes in the future is rejected (`422`).
  Naive timestamps are treated as UTC.
- HTTP bodies need a `Content-Length` (`411`) and are limited to 1 MiB (`413`).
  ASGI middleware enforces this before the body is parsed or authorized, and
  also counts streamed bytes.
- Invalid or unsupported artifacts are stored as `unavailable`, with a reason
  that names the failing native field without echoing producer values.
- Only the projection is stored. Raw artifacts, Lens span inputs/outputs and
  error messages are not stored. Sidecar `trigger_details` are kept because
  the native reader projects them.

## History and posture

| Read | Python | HTTP (reader) | CLI |
| --- | --- | --- | --- |
| History, newest first | `evidence_history(agent, source=, limit=)` | `GET /agents/{id}/evidence/history?source=&limit=` (1–500) | `evidence history AGENT [--source] [--limit]` |
| Agent posture | `agent_posture(agent, stale_after_seconds=)` | `GET /agents/{id}/evidence?stale_after_seconds=` | `evidence posture AGENT` |
| Fleet posture | `fleet_posture(environment=, stale_after_seconds=)` | `GET /posture?environment=&stale_after_seconds=` | `posture [--environment]` |

Each deployment gets one entry per producer:

- `freshness`: `fresh` when the latest observation is inside the window
  (default 86400 seconds, maximum 30 days over HTTP), `stale` when it is older,
  `missing` when nothing was recorded. Missing evidence is never treated as healthy
  or as a failed check.
Each agent or fleet posture is read from one store transaction, so concurrent
ingestion or pruning cannot make it internally inconsistent. History limits
(1–500) and windows (1 second to 30 days) are validated in Python, HTTP and CLI,
including `--snapshot` mode.

- `latest`: the newest record by `observed_at`, including an `unavailable` one,
  so a broken producer feed stays visible.
- `recent_records` / `recent_unavailable`: counts inside the window.
- `summary`: counts of native values in available records inside the window:

| Source | Native tallies |
| --- | --- |
| agenticlens | `status_counts` (running/succeeded/failed; runs and diagnosis reports), `attribution_counts` (attributed/recovered/unattributed/no_failure), `faulty_agents`, `failed_tool_names` from failed spans |
| agentic-evals | `gate_counts`: producer gate passed/failed, or `not_supplied` when no gate was paired |
| agentic-sidecar | `status_counts` for all seven outcomes, `risk_counts` (null risk is `unclassified`, never LOW), `escalations_required` |
| agentic-chaos | `experiments`, `completed`/`incomplete` by report end time, `fault_events` |

Fleet posture lists `fresh_agents`, `stale_agents`, `missing_agents` and
`latest_unavailable_agents` per producer, and adds the per-agent tallies
together. The `reported_health` field in agent posture is the registry value,
shown for context only.

Lens runs now also project `trace_id`, timing, `task_success`, `error_type`,
`span_count`, `tool_names` and `failed_spans` (span ID, name, type, tool and
error type). These link a failed run to the failing tool dependency. Lens has
no native prompt-version field, so Tower does not infer one.

Since 0.5.1 Tower also reads AgenticLens 0.7.0 diagnosis reports
(`artifact_type: diagnosis_report`, produced by `agenticlens diagnose --save`).
The projection keeps the run ID, trace ID, run status, task success, taxonomy
and engine versions, the diagnosis summary (counts, unrecovered, highest
severity, categories) and Lens's attribution (status, faulty step and agent,
category, confidence). Individual diagnoses, span evidence and the timeline
stay in Lens; Tower shows Lens's verdict and never re-diagnoses.
`evidence ingest` detects a diagnosis report from its `engine_version` field.

## Storage and retention

`serve --database registry.sqlite` (or `AGENTICOPS_DATABASE`) stores evidence in
the same SQLite file as the registry and configuration audit. Without a database,
evidence lives in process memory. `EvidenceStore.prune(before)` removes older
observations from Python. No automatic retention policy runs.

## Offline snapshots

A fleet snapshot can contain an `evidence` list of ingestion requests.
`--snapshot FILE posture`, `evidence posture` and `evidence history` evaluate
freshness as of the snapshot's `captured_at`, so offline results do not change
with wall-clock time. Ingest commands are rejected in snapshot mode.

## Console

The read-only console shows an **Ecosystem evidence posture** panel for the
selected environment, plus a per-agent evidence table with freshness, the
latest record, the recent window and native tallies. Producer text is
rendered as text, and the console still sends only GET requests.

## Not included in v0.5

- Pull collection from remote producer services or artifact stores, and
  automatic discovery of producer endpoints.
- AIOS artifact mapping/conformance, full producer-schema validation and Sidecar
  journal hash-chain verification.
- Incident creation and alerting were outside v0.5. They now ship in
  v0.6 (MCP investigation) and v0.8 (live detection and incident views); see
  [the current live operations guide](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/live-operations.md). Causal confirmation
  remains evidence-dependent.
- Per-producer credentials: HTTP ingestion uses the shared writer token.

---

## Settings

Source: [docs/settings.md](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/settings.md)

Control Tower has no configuration file. The server is configured with
`serve` options and environment variables; the CLI with its own options and
environment variables. Defaults below are taken from the 0.8.0 source.

## Server (`agenticops-control-tower serve`)

| Option | Default | Meaning |
| --- | --- | --- |
| `--host` | `127.0.0.1` | Interface to bind. Use `0.0.0.0` to accept other computers on the network ([hosting](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/hosting.md)). |
| `--port` | `8000` | Port for the API and the console. |
| `--database PATH` | none (in memory) | SQLite file for inventory, evidence, configuration, alerts and incidents. Relative to the working directory. Without it, everything is lost on restart. |

| Environment variable | Used by | Meaning |
| --- | --- | --- |
| `AGENTICOPS_DATABASE` | server | SQLite path when `--database` is not given. |
| `AGENTICOPS_READ_TOKEN` | server | Bearer token allowed to read. |
| `AGENTICOPS_WRITE_TOKEN` | server | Bearer token allowed to read and write (register, heartbeat, evidence, previews, execution). |
| `AGENTICOPS_APPROVAL_TOKEN` | server | Separate token for approving, denying and revoking actions. Must differ from the reader and writer tokens, or the server refuses to start. |

Token rules, enforced on every HTTP route:

- **No token configured:** anonymous access to inventory routes. Local development
  only. Configuration actions, bulk operations and incidents still require
  configured credentials.
- **Reader only:** reads work, all writes are rejected.
- A writer token also permits reads. Missing or wrong tokens return `401`; a
  reader calling a write route gets `403`.

Generate tokens with `python -c 'import secrets; print(secrets.token_hex(32))'`
or `openssl rand -hex 32`, once per deployment, and keep them in secret storage.
See [Authentication](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/authentication.md).

## Built-in limits

| Setting | Value | Where it applies |
| --- | --- | --- |
| Live detection interval | 30 seconds | Scans stored telemetry while the server runs. Python hosts can pass `create_app(detection_interval_seconds=0)` to disable it and call `POST /alerts/evaluate` from their own scheduler. |
| Detection freshness and heartbeat windows | 300 seconds each | `DetectionPolicy`, configurable by a trusted Python host ([live operations](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/live-operations.md)). |
| Evidence stale-after | 1 day (max 30 days) | `--stale-after-seconds` / `stale_after_seconds` on posture reads. |
| Evidence history limit | 50 (max 500) | `evidence history --limit`. |
| Request body size | 1 MiB, `Content-Length` required | `POST /evidence` and `POST /bulk/preview`. |
| Action expiry | 1–3600 seconds | Configuration previews ([controlled configuration](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/configuration.md)). |

## CLI client

| Option | Environment variable | Default | Meaning |
| --- | --- | --- | --- |
| `--api-url` | `AGENTICOPS_API_URL` | `http://localhost:8000` | Server to talk to. |
| `--token` | `AGENTICOPS_TOKEN` | none | Bearer token sent with every request. |
| `--snapshot FILE` | — | none | Answer read commands from a snapshot file instead of a server. |

Options go **before** the command:

```bash
agenticops-control-tower --api-url https://tower.example.com --token "$READER_TOKEN" status
```

## Python hosts

Embedding Control Tower in your own service uses the same settings as
arguments, which take precedence over the environment:

```python
from agenticops_control_tower.api.http import create_app

app = create_app(
    database_path="registry.sqlite",
    read_token="...",
    write_token="...",
    approval_token="...",
    detection_interval_seconds=30,
)
```

Run it with any ASGI server, for example `uvicorn module:app`.

---

## Authentication

Source: [docs/authentication.md](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/authentication.md)

Control Tower is a self-hosted PyPI package. The customer operating the server
creates and manages its tokens; no DeepAgentLabs account or token service is
required. Tokens are shared deployment credentials, not individual user accounts.
There is no built-in token-generation command, sign-in page or token issuance API.

## Generate tokens

Install the package into your Python environment:

```bash
python -m pip install "agenticops-control-tower[api]"
```

Generate independent reader and writer values with Python's standard library:

```bash
export AGENTICOPS_READ_TOKEN="$(python -c 'import secrets; print(secrets.token_hex(32))')"
export AGENTICOPS_WRITE_TOKEN="$(python -c 'import secrets; print(secrets.token_hex(32))')"
agenticops-control-tower serve --database registry.sqlite --host 127.0.0.1 --port 8000
```

These commands use Bash or a compatible shell. Use `python3` instead of `python`
if that is your interpreter name. `openssl rand -hex 32` is an alternative to the
Python generator. Both produce a random 64-character hexadecimal value.

Generate once per deployment and retain the values in your secret manager or a
restricted configuration file. Do not regenerate on every server start: clients
using the previous value would lose access. Environment variables exported in
one terminal do not automatically appear in another terminal or survive logout.

For PowerShell, the equivalent setup is:

```powershell
$env:AGENTICOPS_READ_TOKEN = python -c "import secrets; print(secrets.token_hex(32))"
$env:AGENTICOPS_WRITE_TOKEN = python -c "import secrets; print(secrets.token_hex(32))"
agenticops-control-tower serve --database registry.sqlite --host 127.0.0.1 --port 8000
```

## Give readers access

Open [http://localhost:8000/console/](http://localhost:8000/console/) on the server's
computer. Retrieve the reader value from your terminal or secret manager and
share it with authorized readers through a secure channel. Paste it into the
console's **Reader token** field and select **Connect / refresh**. The console
holds the token in page memory; reload or **Disconnect** clears it.

For CLI reads, set the client variable to that same reader value:

```bash
# In the server's shell this can reuse the generated value.
# In another shell, first obtain it from your deployment's secret storage.
export AGENTICOPS_TOKEN="$AGENTICOPS_READ_TOKEN"
agenticops-control-tower status
```

| Variable | Set on | Purpose |
| --- | --- | --- |
| `AGENTICOPS_READ_TOKEN` | Server | Authorizes inventory, status, version, evidence history and posture reads |
| `AGENTICOPS_WRITE_TOKEN` | Server | Authorizes reads plus agent registration, heartbeats and evidence ingestion |
| `AGENTICOPS_TOKEN` | CLI client | Sends a configured reader or writer value to the server |
| `AGENTICOPS_API_URL` | CLI client | Selects the server, e.g. `https://tower.example.com` |

Use the writer value for CLI registration/heartbeats or agent integrations:

```bash
export AGENTICOPS_TOKEN="$AGENTICOPS_WRITE_TOKEN"
agenticops-control-tower agents register examples/sample_agent_registration.json
```

The sample registration file is provided in the source repository; PyPI users
can supply their own JSON file. The console remains read-only even if given a
writer token, but reader tokens are the appropriate credentials to distribute.

## Authorization behavior and rotation

With both server variables unset, the API permits anonymous local development.
With only a reader configured, writes are rejected. With only a writer configured,
reads and writes require that writer. Set different, nonempty values for both roles;
using the same value would give readers writer access.

To rotate a token, generate a new value, update the deployment's secret storage,
restart/redeploy the service, and distribute the replacement to its clients.
The service reads these settings at application startup. It supports one token
per role, with no overlap period, per-user revocation, expiry or tenant isolation.
Do not put tokens in URLs, tracked files, Docker images or shared logs. Use HTTPS
for remote browser/API traffic. See [the hosting guide](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/hosting.md) for local,
private-network and cloud access.

## v0.4 controlled configuration

See [configuration and approvals](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/configuration.md) for Tower ownership, action lifecycle, audit durability and API/CLI usage.
Runtime settings remain mirrored or unsupported without an adapter.

## v0.5 evidence ingestion

`POST /evidence` and the CLI `evidence ingest*` commands require the writer
token. Producers and pipelines share that deployment credential; per-producer
credentials are not implemented. Evidence history and posture reads accept the
reader token. See [evidence posture](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/evidence-posture.md).

---

## Capability Contract

Source: [docs/capability-contract.md](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/capability-contract.md)

`GET /contracts/capabilities` returns the Tower-local candidate
`tower.capabilities.v1` contract: JSON Schemas for registration, heartbeat and
agent readback, allowed statuses and mutation semantics. It requires the same
reader or writer bearer token as inventory. Python consumers can call
`ControlTowerAPI.get_capability_contract()`. This contract version is independent
of the package version and AIOS draft markers. It is a candidate for the
coordinated ecosystem v1.0 freeze.

## Supported integration patterns

| Pattern | Validation | Boundary |
| --- | --- | --- |
| Embedded Python facade | Existing registry/API suite | No API extra or sibling required |
| CPython standard-library HTTP worker | `examples/runtimes/python_worker.py` | Host reports its own inventory |
| Node.js 18+ native-fetch HTTP worker | `examples/runtimes/node_worker.mjs` | No Python SDK or npm dependency in client |
| Local/host-bound MCP operator | Existing `tower.*` tools | MCP owns tool access; Tower owns approval |
| Framework worker or container | Same explicit HTTP registration | Framework/container name is metadata, not discovery or certified support |

The two HTTP examples exercise actual independent runtime processes against a
live authenticated server. `tests/test_capability_contract.py` verifies their
registration, heartbeat, capability retention, aggregate discovery and SQLite
readback after restart. CI installs Node explicitly to prevent silently losing
second-runtime coverage. This is inventory interoperability, not a production
Kubernetes connector, remote runbook execution or framework instrumentation.

```bash
export AGENTICOPS_WRITE_TOKEN=local-writer
agenticops-control-tower serve
# In another terminal, with the same token:
python3 examples/runtimes/python_worker.py
node examples/runtimes/node_worker.mjs
```

Set `AGENTICOPS_API_URL` for a remote server. Use TLS at the deployment boundary;
the examples default to loopback. Retry registration only when replacement is
intended. Neither example sends evidence or grants execution authority.

## Core semantics

| Operation | Result and compatibility commitment |
| --- | --- |
| `POST /agents/register` | 201; same ID replaces the record and resets heartbeat count |
| `POST /agents/{id}/heartbeat` | 200; merges capability/runtime/package maps, replaces status and last_seen, increments count |
| `GET /agents/{id}` | 200 detached record; unknown ID returns 404 |
| `GET /agents` | Sorted by agent ID, with existing filters |
| `GET /capabilities` | Sorted capability keys and unique lexically sorted reported version strings |
| Invalid payload | 422; unknown status rejected; agent IDs are URL-safe |
| Protected inventory | Missing/invalid token: 401; reader cannot write: 403 |

Omitted heartbeat status becomes `unknown`. Omitted maps retain previous keys;
there is no heartbeat deletion marker. Registration is the explicit replacement
path. Repeated heartbeats increment the count and are not idempotent. Versions
are reported strings; minimum-version assessment is a separate operation.
Unknown fields follow existing Pydantic input behavior (ignored). Clients should
ignore additive response fields and inspect the contract identifier before
sending writes. No negotiation header is required by legacy clients.

Health is one of `healthy`, `degraded`, `unhealthy`, `unknown`, reported by the
host. Last-seen age does not automatically rewrite it. Evidence freshness,
Sidecar BLOCK, Evals gates, Lens verification and Chaos resilience outcomes are
independent of deployment health. Reported capabilities do not prove installed
packages, trusted evidence, approval or production readiness.

## Evolution and release gate

The existing payloads and endpoints remain compatible; existing clients need no
migration. New clients may fetch the candidate descriptor before registering.
Within this contract, preserve field types, status meaning, replacement/merge
behavior and authorization semantics. Incompatible changes require a new contract
identifier and documented migration, with old clients retained through a stated
transition. Additive optional fields may be introduced without changing the
identifier. JSON Schema snapshots and runtime tests guard this baseline.

Optional sibling ranges are unchanged: no sibling is imported to describe the
contract. Native producer schemas and AIOS exports are unchanged. MCP can keep
using existing Tower routes without adding a tool. Independent ecosystem v1.0
acceptance, production runtime connectors, deployment hardening and the final
stable freeze remain open. This phase makes Tower's implemented control-plane
behavior reviewable; it does not declare those gates passed.

See the [Phase 10 validation record](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/phase10-validation.md) for release evidence.

## MCP 0.6.5 capability discovery

MCP 0.6.5 adds read-only `tower.capability_contract` with `{}` over Tower 0.10's
`GET /contracts/capabilities`. It preserves `tower.capabilities.v1` candidate
maturity and schemas, reuses reader credentials and requires per-user binding
plus dispatch permission for hosted access. Tower needs no code, dependency or
patch release. Publishing MCP does not deploy the hosted service.
See the [MCP operator guide](https://github.com/DeepAgentLabs/mcp-server/blob/main/docs/tower-0.10-compatibility.md).

---

## Runbooks

Source: [docs/runbooks.md](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/runbooks.md)

Phase 9 turns the single approved staging action from 0.6.0 into reusable,
versioned runbooks. Tower owns the catalog, approvals, ordered execution,
cancellation, interruption handling and the incident timeline. Lens, Evals and
Chaos keep owning traces, scoring and fault injection; Tower only reads the
evidence they produce.

```mermaid
flowchart LR
    I[Investigated incident] --> R[Recommend installed runbooks]
    R --> P[Preview exact digest]
    P --> A[Separate human approval]
    A --> X[Claim, then run bounded steps]
    X -->|all steps succeeded| V[Verify with fresh evidence and probe]
    X -->|clean failure or cancel| C[Compensate completed steps]
    X -->|partial, timeout, unknown| Q[Stop for reconciliation]
    V --> D{Criteria pass?}
    D -->|yes| OK[Resolved]
    D -->|no| E[Escalated]
    C --> E
    Q --> E
```

## Runbook definitions

A runbook is a host-installed `RunbookDefinition` identified by `runbook_id` and
a semantic `version`. Versions are immutable: installing the same version again
must match its digest, so an approval can never run a changed definition.

| Field | Meaning |
| --- | --- |
| `environments` | Deployment environments the runbook may target. |
| `prerequisites` | Any of `incident.open`, `incident.investigated`, `investigation.not_contradictory`, `connector.installed`. |
| `parameters` | Named string parameters, each with a regex `pattern`, a `max_length` (default 100) and an optional `allowed` list. Preview must supply exactly these names. |
| `steps` | 1–10 ordered steps. Each names an `action`, a `timeout_seconds` (1–30), `max_attempts` (1–3) and an optional `rollback_action`. |
| `impact`, `rollback` | Operator-facing text retained in every preview. |
| `recovery` | Fixed criteria: connector probe, fresh successful Lens run, passing Evals gate, and a freshness window (default 300 s). |

The worst case, counting every attempt and every declared rollback, must fit in
120 seconds. Actions are identifiers such as `traffic.drain`, never commands,
URLs or credentials. Callers choose a catalog entry and parameter values; they
cannot supply steps.

Tower ships one definition, `staging.dependency_recovery` **1.0.0**:

| Step | Action | Attempts | Rollback |
| --- | --- | --- | --- |
| `drain` | `traffic.drain` | 1 | `traffic.resume` |
| `restore` | `dependency.restore` | 2 | none (restoring is not undone) |
| `resume` | `traffic.resume` | 2 | none |

Install your own versions with `RunbookCatalog([...])` or
`api.runbooks.catalog.install(definition)`.

## Connectors

A `RunbookConnector` is trusted host code installed per deployment with
`RunbookService(incidents, connectors={deployment_id: connector})` or
`api.runbooks.install(deployment_id, connector)`. It implements `supports`,
`run(idempotency_key, action, parameters)` and `probe`.

- Return `failed` only when the action made **no change**; Tower may retry it.
- Return `partial_failure` when state is unknown; Tower stops and never retries.
- Use the idempotency key durably. Tower passes `EXECUTION:STEP` for steps and
  `EXECUTION:STEP:rollback` for compensation; a repeated key after success must
  not repeat the side effect.

`StagingRunbookRuntime` is the supported deterministic fixture: a local SQLite
runtime that commits each change with its receipt. It is not a production
process manager. The default `serve` command installs no connector, so previews
fail honestly until a host installs one.

## Workflow

1. **Recommend.** `GET /incidents/{id}/runbooks` lists every installed version
   with `eligible`, the `unmet` prerequisites, its parameters, definition digest
   and validation status. The copilot can only choose from this list.
2. **Preview.** A writer posts `runbook_id`, `version`, `parameters` and optional
   `expires_in_seconds` (1–3600). Tower checks the environment, prerequisites and
   that the connector supports every step and rollback action with those
   parameters. The `preview_digest` binds the execution ID, incident, deployment,
   environment, definition digest, parameters and expiry. Previewing closes
   further investigation and the 0.6 single-action plan for that incident.
3. **Approve.** A separate approver posts the exact digest. The proposer cannot
   approve. Approvers can also revoke an unclaimed approval. A denied, revoked,
   cancelled or expired preview can be replaced by a new one; a dispatched one
   cannot.
4. **Execute.** A writer posts the digest. Tower re-checks the deployment's
   environment, the installed definition digest and connector support, consumes
   the approval and commits a `running` claim with an execution lease **before**
   any dispatch.
5. **Verify.** A writer posts `lens_evidence_id` and `evals_evidence_id` for the
   recovery run. Tower applies the same criteria as 0.6 recovery (see below) plus
   a bounded connector probe, then resolves or escalates the incident.

### Step outcomes

Each attempt is committed as `unknown` before the connector is called and is
bounded by the step timeout. Tower cannot kill a Python callback; a late call may
still finish, which is why timeouts are never retried.

| Connector result | Tower behavior | Runbook status |
| --- | --- | --- |
| `succeeded` | Next step | `awaiting_verification` after the last step |
| `failed` | Retry up to `max_attempts`; then compensate | `escalated` |
| `partial_failure`, timeout, exception or unsupported value | Stop. No retry, no compensation | `reconciliation_required` |
| Dispatch capacity full | Treated as `failed`; no call was made | as `failed` |

Compensation runs declared `rollback_action`s for succeeded steps in reverse
order. If any rollback is not clean, the runbook is `reconciliation_required`.
Steps after the stopping point are `skipped`. The incident is `escalated` in every
stopped case.

### Cancellation and interruption

`POST /runbook-executions/{id}/cancel` is available to writers and approvers.
Before execution it cancels without dispatch. During execution it stops before
the next step; the running step is not interrupted. Completed steps are then
compensated and the runbook ends `cancelled` with an escalated incident. A
cancellation that arrives after the last step has started has nothing left to
stop.

If the Tower process dies mid-run, the durable claim stays `running`. After the
lease (worst-case budget plus 30 seconds) a writer calls `reconcile`: claimed
steps keep `unknown`, others become `skipped`, the runbook becomes
`reconciliation_required` and nothing is replayed. Reconciling inside the lease
is rejected so a live execution is never declared lost.

### Recovery criteria

A runbook never resolves itself. Resolution requires all of:

- a successful connector probe within 5 seconds;
- an available native Lens run with `status=succeeded`, `task_success=true` and a
  run ID different from the detection run;
- a passing native Evals gate linked to that same run;
- both observed and ingested after execution started, no future timestamps, and
  observed within the runbook's freshness window;
- no failed Lens run for that run ID.

Unknown record IDs are rejected and leave the runbook awaiting verification.
Anything else that fails escalates.

## Chaos and Evals validation

`POST /runbooks/{runbook_id}/{version}/validations` records that a runbook version
was exercised under a controlled scenario. It takes `agent_id`,
`chaos_evidence_id` and `evals_evidence_id` for records already pushed to Tower.
It requires a completed native Chaos report and a passing Evals gate with the
same `run_id`, on a deployment in one of the runbook's environments.
Recommendations then report `validation: validated` with the validation IDs for
that definition digest and environment. Validation is evidence, not a gate: Tower
does not run Chaos experiments or compute Evals results.

## HTTP routes

All runbook routes need configured bearer credentials. Roles come from server
credentials, never request bodies. Errors in workflow order, role or scope return
409; unknown runbook versions return 404.

| Route | Role | Request |
| --- | --- | --- |
| `GET /runbooks` | reader | none |
| `GET /runbooks/{id}/{version}/validations` | reader | none |
| `POST /runbooks/{id}/{version}/validations` | writer | `agent_id`, `chaos_evidence_id`, `evals_evidence_id` |
| `GET /incidents/{id}/runbooks` | reader/writer/approver | none |
| `GET /incidents/{id}/runbook-executions` | reader/writer/approver | none |
| `POST /incidents/{id}/runbooks/preview` | writer | `runbook_id`, `version`, `parameters`, optional `expires_in_seconds` |
| `GET /runbook-executions/{id}` | reader/writer/approver | none |
| `POST /runbook-executions/{id}/approval` | separate approver | `preview_digest`, `approved` |
| `POST /runbook-executions/{id}/revoke` | approver | none |
| `POST /runbook-executions/{id}/execute` | writer | `preview_digest` |
| `POST /runbook-executions/{id}/cancel` | writer or approver | none |
| `POST /runbook-executions/{id}/verify` | writer | `lens_evidence_id`, `evals_evidence_id` |
| `POST /runbook-executions/{id}/reconcile` | writer | none; only after the lease |

Execution runs inside the request, bounded by the runbook's worst-case budget.
Incident views (`GET /incidents/{id}/view`) include a `runbooks` list, and every
runbook event is also an incident timeline event.

## CLI

```bash
agenticops-control-tower --token "$READER" runbooks catalog
agenticops-control-tower --token "$READER" runbooks recommend INCIDENT_ID
agenticops-control-tower --token "$WRITER" runbooks preview INCIDENT_ID preview.json
agenticops-control-tower --token "$APPROVER" runbooks approval EXECUTION_ID approval.json
agenticops-control-tower --token "$WRITER" runbooks execute EXECUTION_ID execute.json
agenticops-control-tower --token "$WRITER" runbooks verify EXECUTION_ID verify.json
```

Other commands: `history INCIDENT_ID`, `get`, `revoke`, `cancel` and `reconcile`
(each takes `EXECUTION_ID`), `validations RUNBOOK VERSION` and
`validate RUNBOOK VERSION FILE.json`. `execute` and `verify` exit 1 unless the
runbook is `awaiting_verification` or `resolved`. Snapshot mode rejects runbook
commands.

Example `preview.json`:

```json
{"runbook_id": "staging.dependency_recovery", "version": "1.0.0",
 "parameters": {"dependency": "search"}, "expires_in_seconds": 300}
```

## MCP

MCP 0.5.1 adds local `tower.runbooks`, `tower.runbook_recommendations`,
`tower.runbook_executions`, `tower.runbook_execution`, `tower.runbook_preview`,
`tower.runbook_execute`, `tower.runbook_cancel` and `tower.runbook_verify` tools.
They call these HTTP routes with the host's reader or writer credential, so the
same role, scope and approval checks apply. No MCP tool approves or revokes; a
human does that through HTTP or the CLI.

## Python

```python
from agenticops_control_tower.runbooks import RunbookService
from agenticops_control_tower.runbooks.models import RunbookPreviewRequest

runbooks = RunbookService(incidents, connectors={"staging": runtime})
execution = runbooks.preview(incident_id, RunbookPreviewRequest(
    runbook_id="staging.dependency_recovery", version="1.0.0",
    parameters={"dependency": "search"}), writer)
runbooks.decide(execution.execution_id, execution.preview_digest, True, approver)
runbooks.execute(execution.execution_id, execution.preview_digest, writer)
```

Pass the service as `ControlTowerAPI(..., runbook_service=runbooks)`; it must share
the API's incident service. Python callers are trusted hosts and must supply a
trusted `Operator`.

## Limits

- Steps are not atomic and there is no distributed exactly-once guarantee: Tower
  dispatches each step at most once per claim, and connectors own idempotency.
- Only `StagingRunbookRuntime` is supported. Production runtime connectors,
  multi-deployment runbooks and automatic approval are not provided.
- Timeouts bound how long Tower waits, not how long a connector runs.
- Recovery criteria are fixed in 0.9.0. Validation records are informational.
- Shared HTTP credentials are deployment-wide roles, not per-user identities.

See the [standalone example](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/examples/runbook_recovery.py)
and [incident recovery](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/incident-recovery.md) for the 0.6 single-action flow,
which remains supported.

---

## Fleet Operations

Source: [docs/fleet-operations.md](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/fleet-operations.md)

Tower freezes an explicit, sorted deployment list before any fleet mutation.
Use `api.bulk` in Python or the authenticated HTTP/CLI surface. The console
remains read-only. Fleet commands are Tower-local contracts, not AIOS schemas.

## Preview, approve, execute

Install `agenticops-control-tower[api]==0.7.0`. Configure distinct
`AGENTICOPS_WRITE_TOKEN` and `AGENTICOPS_APPROVAL_TOKEN` on the server.
The trusted host must declare Tower-owned desired settings through
`api.config.declare(Configuration(..., authority="tower"), writer)` first;
HTTP cannot elevate mirrored configuration into writable ownership.

Save this as `fleet.json` (also in `examples/bulk_tracing.json`):

```json
{
  "intent": "Enable enhanced tracing for staging Lens deployments",
  "selector": {"environment": "staging", "capability": "agenticlens"},
  "operation": "config.update",
  "patch": {"values": {"enhanced_tracing": true}},
  "expires_in_seconds": 300
}
```

```bash
agenticops-control-tower --token "$WRITER_TOKEN" bulk preview fleet.json
# Inspect targets, before/after settings, expiry, and reconciliation; copy bulk_id.
agenticops-control-tower --token "$APPROVER_TOKEN" bulk approve BULK_ID
agenticops-control-tower --token "$WRITER_TOKEN" bulk execute BULK_ID
agenticops-control-tower --token "$READER_TOKEN" bulk get BULK_ID
```

`bulk deny` and `bulk revoke` use the approver credential. The proposer cannot
approve their own batch, even using a Python identity with another role. Approval
covers the persisted preview; execute accepts only its ID and no replacement
selector or patch. CLI execution exits 1 when any target is unsuccessful, while
still printing all results. HTTP returns the durable results with status 200;
rejected state transitions return 409. Missing/invalid credentials return 401.
Anonymous local mode cannot perform fleet commands.

HTTP equivalents: `POST /bulk/preview`, `GET /bulk/{id}`,
`POST /bulk/{id}/approval` with `{"approved": true|false}`,
`POST /bulk/{id}/revoke`, and `POST /bulk/{id}/execute`. Approval is never
available through an MCP tool. Offline snapshots cannot operate on batches.

## Deterministic targeting and audit

Environment and installed capability are required and combined with AND.
Optional `agent_ids` restricts the selection; every explicit ID must match.
Duplicates are deduplicated, IDs sort lexically, and 1–100 matches are required.
New registrations after preview never join a batch. Execution rechecks expiry,
environment, capability version, runtime, framework and registration time for
each deployment, and checks the exact before-configuration and revision.
A failed target does not prevent remaining targets from being attempted.
Writer and approver scopes must each include the entire frozen list. Scoped
Python readers must also cover all targets; server bearer roles are global.

The batch retains intent, request, frozen deployment identities, command IDs,
proposer, decision actor, child configuration previews, per-target outcomes and
attributed timestamped events. `GET /bulk/{id}` is the durable audit/readback
path. Per-agent `/agents/{id}/audit` also records execution outcomes. Persist
with `serve --database tower.db`; batch and configuration writes share the same
SQLite transaction mechanism. Deployment health and evidence verdicts stay
independent of fleet operation results.

## Bulk stop and MCP revocation

Set `operation` to `runtime.stop`, omit the patch, and choose
`acknowledgement_seconds` (0.01–30, default 5). The trusted host installs a
`SidecarContainmentAdapter` per deployment with
`api.bulk.install(agent_id, adapter)`. Its Sidecar TaskRuntime must have an
issuer-backed `mcp` revoker; see [incident recovery](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/incident-recovery.md).
No caller-provided paths, commands, endpoint URLs or credentials are accepted.
A stop request blocks dispatch and requests configured MCP access revocation;
there is no standalone arbitrary credential-revocation or bulk restart endpoint.

Each target records requested then acknowledged, failed, unsupported, incomplete,
or timed_out; unrecognized receipts are unknown. Late receipts are durably
recorded in the target receipt and audit without replacing a timed_out outcome. In-flight calls and unsupported
downstream credentials stay explicit. A boundary acknowledgement does not prove
end-to-end containment or verified incident recovery. Missing adapters are
unsupported. Connector exceptions produce a generic failure without persisting
exception text. Acknowledgement waiting is bounded per target; a timed-out host
call may still finish. At most 16 host calls can remain outstanding per process;
capacity exhaustion records failed without dispatch. Host adapters must themselves
bound their network/runtime calls. This is synchronous sequential execution with an overall `execution_seconds`
budget (0.01–30, default 30). Each acknowledgement wait is capped by the
remaining budget; remaining targets fail without dispatch after it expires.
Storage work adds overhead to that budget. CLI execution allows a 60-second
HTTP timeout. This is not a background distributed scheduler.

## Partial failure, rollback and interruption

There is no fleet atomicity or automatic rollback. Successful desired-setting
updates remain committed; Tower does not assert remote application. To roll back,
preview a new batch with explicit previous values or the opposite capability
toggle and obtain a new approval. `config.update` merges keys and does not delete
keys. Runtime stop has no automatic rollback or restart.

Only one executor can consume an approval. Revocation is allowed before claiming,
not after execution starts. SQLite atomically commits each desired change with
its outcome, preventing reapplication after a crash. Runtime dispatch records
requested durably before calling the host, never automatically retries, and
persists the receipt afterward. If interrupted, the batch remains executing;
completed targets remain visible, requested means uncertain, and pending means
unattempted. Read it with `bulk get`; reconcile actual host state before creating
any newly approved action for unfinished targets. Never blindly retry a timed-out
or requested stop. No automatic resume is provided in 0.7.0.

## Sibling compatibility

All existing extras remain optional and their ranges remain sufficient. Lens
traces, Evals reports/gates, Sidecar decisions and Chaos events keep their native
meaning. Tower does not invoke their analysis/evaluation/fault engines for fleet
configuration. Local MCP 0.3.6 investigation tools remain compatible with Tower
0.7.0; new fleet endpoints are HTTP/CLI/Python-only and hosted MCP restrictions
remain in place. AIOS shared command semantics remain draft; no conformance claim
or new normative schema is introduced. No sibling patch release is required for
these documentation-only integration updates.

Run `uv run python examples/fleet_operations.py` for an offline, deterministic
preview → approval → partial failure → readback demonstration.

---

## Live Operations

Source: [docs/live-operations.md](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/live-operations.md)

Tower evaluates locally stored, explicitly attributed telemetry every 30 seconds
while the HTTP application's lifespan is running. `create_app(detection_interval_seconds=0)`
disables the worker; a trusted scheduler can instead call `POST /alerts/evaluate`.
The internal actor is `tower-detector`. Detection creates alerts and incidents,
never approvals, runtime controls or recovery execution. No LLM or sibling import
is required. Scanner failures are logged and retried on the next interval.

## Rules and freshness

`api.operations.policy = DetectionPolicy(...)` configures trusted host policy;
both freshness and heartbeat windows default to 300 seconds (range 1–86400).

| Rule | Condition | Meaning |
| --- | --- | --- |
| `lens.failed` | Latest native Lens record is an available failed `run`, observed within the freshness window and not in the future | Critical alert and idempotent recovery incident; cause unconfirmed |
| `heartbeat.stale` | Last heartbeat, or registration when none exists, is overdue | Warning; reported health unchanged |
| `evidence.stale` | Latest pushed record for a producer is older than the window | Warning; native verdict unchanged |
| `evidence.missing` | An installed producer capability has no pushed records | Warning; uninstalled optional packages do not cause alerts |

The latest observation per producer/deployment drives each scan. This is a
current-posture detector, not a lossless stream processor: a newer run or diagnosis
can supersede a failed run before a scan. Delayed pushes older than the window,
future timestamps and invalid native artifacts never create recovery incidents.
Unavailable projections remain visible in evidence posture. There is no remote
polling, arbitrary rule expression evaluation, automatic evidence fetching or
external notification delivery. The alert feed and console are the notification
surfaces in this release.

Alerts deduplicate by deployment, environment, rule, source and (for failures)
observation ID. Repeated scans preserve acknowledgement and first-seen time.
Absent conditions clear alerts; cleared warning conditions can reopen with a new
acknowledgement lifecycle. Append-only audit events preserve create, acknowledge,
clear and reopen history. Older scans cannot regress a newer saved scan. Incident and alert writes commit atomically with the scan watermark; interrupted
transactions roll back together and can be retried safely.

Correlation keys group same-source, explicitly same-run alerts across agents
**within an environment**. A shared run ID is a correlation hint, not a causal
finding or a cross-environment incident merge. Missing run IDs stay deployment
local. Each recovery incident and its approvals remain scoped to one deployment.
Clearing an alert never resolves its incident; recovery still requires the
existing probe, fresh native Lens success and same-run passing Evals gate.

## Operator workflow

```bash
export AGENTICOPS_TOKEN=writer-token  # or pass --token explicitly
agenticops-control-tower --token writer-token alerts evaluate
agenticops-control-tower --token reader-token alerts list --active-only --environment staging
agenticops-control-tower --token writer-token alerts acknowledge ALERT_ID
agenticops-control-tower --token reader-token incidents view INCIDENT_ID
uv run python examples/live_operations.py
```

HTTP reads: `GET /alerts?environment=staging&active_only=true`,
`GET /incidents?environment=staging`, `GET /incidents/{id}/view`.
Writes: `POST /alerts/evaluate`, `POST /alerts/{id}/acknowledge`.
Readers cannot evaluate or acknowledge. Incident reads use the existing
configured-credential contract; anonymous development inventory remains usable.
HTTP identities are server-derived `http-reader`, `http-writer`, `http-approver`;
tokens represent deployment-wide roles, not named end users. Trusted Python
`Operator.agent_ids` limits reads, scans, acknowledgements and joined views.
Offline inventory snapshots do not contain live alerts or incidents.

## Incident console and joined audit

Connect to `/console/` with a reader token. Active alerts, acknowledgements and
an incident queue refresh every 30 seconds. Select an incident to inspect its
inventory, reported health, evidence posture, findings/citations, plan, approval
state, execution claims/receipts and recovery checks. All console requests remain
GET-only; actions use the same authenticated API/CLI as before.

`incident_view` joins the original detection (even if evidence was pruned),
up to 100 recent same-run native evidence records within that deployment, the incident's durable
events, retained deployment configuration/bulk audit, and alert lifecycle audit.
The validated native detection run ID drives correlation even when optional
link-level metadata was omitted. `evidence_truncated` explicitly reports omitted
older records; the original detection is always retained in addition to the bound.
Each timeline entry includes time, actor, source and event. Configuration and
alert audit are deployment context and may include changes unrelated to the
incident; `change_scope` labels this explicitly. Policy decisions remain native
Sidecar evidence. Requested commands and actual connector acknowledgements retain
distinct events; a request is never proof of containment.

Lens integrity is `not_verified` and coverage is `not_assessed`, separately from
reported health and evidence freshness. Tower does not infer cryptographic
integrity, execution completeness or exact root cause from timestamps and links.
Native projections omit unsupported raw payloads; use authorized producer tools
for deeper inspection. Approval/recovery evidence remains in the embedded incident
even when its run differs from the detection run.

## Persistence and package boundaries

Use `AGENTICOPS_DATABASE` / `create_app(database_path=...)` for registry, evidence,
configuration, incidents, scans and alerts in one local SQLite database. Without
it all state is process-local. SQLite remains a single-host deployment model;
multiple workers may scan, but writes and incident identities deduplicate. Audit
is retained without automatic pruning; it is not an independently tamper-evident
ledger. No distributed leader election, alert retention policy or remote telemetry
subscription is supplied.

All sibling extras keep their current compatible ranges. Lens supplies native
runs; Evals supplies report/gate verdicts; Sidecar supplies native decisions and
runtime enforcement; Chaos supplies resilience evidence; MCP retains existing
`tower.*` tools. New alert/view endpoints are Tower API/CLI surfaces, not new MCP
tools. AIOS remains draft; these are Tower-local contracts. See
[ecosystem compatibility](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/tower-0.8-compatibility.md).

---

## Limitations

Source: [docs/limitations.md](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/limitations.md)

Known limits of 0.9.0, taken from the repository's
[implementation evidence and operational limits](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/ROADMAP.md#implementation-evidence-and-operational-limits)
and the feature guides.

## Release and maturity

- The package is **pre-alpha**. **0.9.0** is published on PyPI; repository
  checkouts are needed for walkthroughs that read bundled example files.
- No 1.0 compatibility contract yet. Experimental features (0.4–0.9) may change.

## Identity and access

- Authentication uses shared deployment tokens (reader, writer, approval). There
  are no user accounts, per-agent identities or tenant isolation.
- With no tokens configured, inventory routes are anonymous. Use this only on
  your own computer.
- Serve over HTTPS when anyone else connects; Tower does not terminate TLS itself.

## Storage and scale

- SQLite only, for a single host with a local database file. No distributed
  storage.
- Without `--database`, all state is in memory and lost on restart.

## Health and evidence

- Health is **agent-reported**. Tower does not time out silent agents into
  `unhealthy` (overdue heartbeats raise a warning alert instead) and does not
  detect installed packages automatically.
- Evidence collection is **push-only**. Tower never fetches `artifact_ref`s or
  connects to producer services.
- Tower never recomputes a producer's verdict, and evidence never changes
  reported health.

## Configuration and recovery

- Controlled configuration records **desired** values. No remote adapter applies
  them to running agents, so execution never claims remote application or
  rollback.
- Bulk operations have no fleet-wide atomicity or automatic rollback.
- Approved recovery and versioned runbooks support deterministic **staging**
  runtime fixtures only. Production runtime connectors are not provided.
- Runbook steps are not atomic. Tower dispatches each step at most once per claim;
  connectors own idempotency, and timeouts bound Tower's wait, not the connector.
  Partial, timed-out or unknown steps need manual reconciliation.
- Runbook recovery criteria are fixed, and Chaos/Evals validation records are
  informational rather than an execution gate.
- No model is bundled; investigation relies on an MCP host's model.

## Detection and console

- Detection is a current-posture scan of the latest observation, every 30
  seconds, not a lossless event stream. There is no external notification
  delivery; the alert feed and console are the notification surfaces.
- The console is read-only and refreshes manually.
- The hosted MCP endpoint rejects `tower.*` tools; the MCP connector works only
  with a local MCP server you configure.

---

## Source declarations: src/agenticops_control_tower/__init__.py

Source: [src/agenticops_control_tower/__init__.py](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/src/agenticops_control_tower/__init__.py)

```python
__all__ = ['__version__']
```

---

## Source declarations: src/agenticops_control_tower/models/__init__.py

Source: [src/agenticops_control_tower/models/__init__.py](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/src/agenticops_control_tower/models/__init__.py)

```python
__all__ = ['EVIDENCE_SOURCES', 'AgentEvidencePosture', 'AgentRecord', 'AgentRegistrationPayload', 'AgentStatusSummary', 'AgentStatus', 'CapabilityCoverageRecord', 'CapabilityInventoryRecord', 'EvidenceIngestRequest', 'EvidenceIngestResult', 'EvidenceLink', 'EvidenceRecord', 'EvidenceSummary', 'FleetEvidencePosture', 'FleetSnapshot', 'FleetSourcePosture', 'FleetStatusSummary', 'HeartbeatEvent', 'HeartbeatPayload', 'SnapshotAgentRegistration', 'SnapshotHeartbeatPayload', 'SourcePosture']
```

---

## Source declarations: src/agenticops_control_tower/models/agent.py

Source: [src/agenticops_control_tower/models/agent.py](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/src/agenticops_control_tower/models/agent.py)

```python
class AgentStatus(str, Enum):
    HEALTHY = 'healthy'
    DEGRADED = 'degraded'
    UNHEALTHY = 'unhealthy'
    UNKNOWN = 'unknown'
class AgentRegistrationPayload(BaseModel):
    agent_id: AgentId
    name: str
    environment: str
    runtime: str
    framework: str
    status: AgentStatus = AgentStatus.UNKNOWN
    capabilities: dict[str, str] = Field(default_factory=dict)
    runtime_metadata: dict[str, str] = Field(default_factory=dict)
    package_metadata: dict[str, str] = Field(default_factory=dict)
    registered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
class HeartbeatPayload(BaseModel):
    status: AgentStatus = AgentStatus.UNKNOWN
    last_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    capabilities: dict[str, str] = Field(default_factory=dict)
    runtime_metadata: dict[str, str] = Field(default_factory=dict)
    package_metadata: dict[str, str] = Field(default_factory=dict)
class AgentRecord(BaseModel):
    agent_id: str
    name: str
    environment: str
    runtime: str
    framework: str
    status: AgentStatus = AgentStatus.UNKNOWN
    capabilities: dict[str, str] = Field(default_factory=dict)
    runtime_metadata: dict[str, str] = Field(default_factory=dict)
    package_metadata: dict[str, str] = Field(default_factory=dict)
    registered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: datetime | None = None
    heartbeat_count: int = 0
class CapabilityInventoryRecord(BaseModel):
    capability: str
    versions: list[str] = Field(default_factory=list)
    agent_ids: list[str] = Field(default_factory=list)
```

---

## Source declarations: src/agenticops_control_tower/models/contract.py

Source: [src/agenticops_control_tower/models/contract.py](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/src/agenticops_control_tower/models/contract.py)

```python
class CapabilityContract(BaseModel):
    contract_version: Literal['tower.capabilities.v1'] = 'tower.capabilities.v1'
    maturity: Literal['candidate'] = 'candidate'
    capabilities: Literal['agent-reported; not verified installation'] = 'agent-reported; not verified installation'
    registration: Literal['replace record and reset heartbeat count'] = 'replace record and reset heartbeat count'
    heartbeat: Literal['merge metadata; replace status and last_seen'] = 'merge metadata; replace status and last_seen'
    health: Literal['reported; no automatic heartbeat expiry'] = 'reported; no automatic heartbeat expiry'
    statuses: list[str] = Field(default_factory=lambda: [status.value for status in AgentStatus])
    schemas: dict[str, dict[str, Any]] = Field(default_factory=lambda: {'registration': AgentRegistrationPayload.model_json_schema(), 'heartbeat': HeartbeatPayload.model_json_schema(), 'agent': AgentRecord.model_json_schema()})
```

---

## Source declarations: src/agenticops_control_tower/models/evidence.py

Source: [src/agenticops_control_tower/models/evidence.py](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/src/agenticops_control_tower/models/evidence.py)

```python
class EvidenceLink(BaseModel):
    contract_version: Literal['1.0'] = '1.0'
    agent_id: str = Field(min_length=1)
    source: EvidenceSource
    source_version: str = Field(min_length=1)
    artifact_type: Literal['run', 'diagnosis_report', 'execution_bundle', 'evaluation_report', 'decision', 'chaos_report']
    artifact_ref: str = Field(min_length=1)
    observed_at: datetime
    run_id: str | None = None
    runtime_agent_id: str | None = None
    spec_version: str | None = None
class EvidenceSummary(BaseModel):
    link: EvidenceLink
    availability: Literal['available', 'unavailable']
    reason: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
class EvidenceIngestRequest(BaseModel):
    link: EvidenceLink
    artifact: dict[str, Any] | None = None
    gate: dict[str, Any] | None = None
class EvidenceRecord(BaseModel):
    record_id: str
    ingested_at: datetime
    ingested_by: str
    summary: EvidenceSummary
class EvidenceIngestResult(BaseModel):
    record: EvidenceRecord
    created: bool
class SourcePosture(BaseModel):
    source: EvidenceSource
    freshness: EvidenceFreshness
    reason: str | None = None
    latest: EvidenceRecord | None = None
    recent_records: int = 0
    recent_unavailable: int = 0
    summary: dict[str, Any] = Field(default_factory=dict)
class AgentEvidencePosture(BaseModel):
    agent_id: str
    environment: str
    reported_health: AgentStatus
    evaluated_at: datetime
    stale_after_seconds: int
    sources: list[SourcePosture]
class FleetSourcePosture(BaseModel):
    source: EvidenceSource
    fresh_agents: list[str] = Field(default_factory=list)
    stale_agents: list[str] = Field(default_factory=list)
    missing_agents: list[str] = Field(default_factory=list)
    latest_unavailable_agents: list[str] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)
class FleetEvidencePosture(BaseModel):
    evaluated_at: datetime
    environment: str | None = None
    stale_after_seconds: int
    total_agents: int
    sources: list[FleetSourcePosture]
```

---

## Source declarations: src/agenticops_control_tower/models/status.py

Source: [src/agenticops_control_tower/models/status.py](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/src/agenticops_control_tower/models/status.py)

```python
class CapabilityCoverageRecord(BaseModel):
    capability: str
    installed_agents: int
    missing_agents: int
    versions: list[str] = Field(default_factory=list)
    agent_ids: list[str] = Field(default_factory=list)
    missing_agent_ids: list[str] = Field(default_factory=list)
class AgentStatusSummary(BaseModel):
    agent_id: str
    name: str
    environment: str
    runtime: str
    framework: str
    status: AgentStatus
    last_seen: str | None = None
    heartbeat_count: int
    capability_count: int
    capabilities: dict[str, str] = Field(default_factory=dict)
class FleetStatusSummary(BaseModel):
    total_agents: int
    healthy_agents: int
    degraded_agents: int
    unhealthy_agents: int
    unknown_agents: int
    capability_count: int
    status_buckets: dict[str, list[str]] = Field(default_factory=dict)
    capabilities: list[CapabilityCoverageRecord] = Field(default_factory=list)
class HeartbeatEvent(BaseModel):
    agent_id: AgentId
    heartbeat: SnapshotHeartbeatPayload
class SnapshotAgentRegistration(BaseModel):
    agent_id: AgentId
    name: str
    environment: str
    runtime: str
    framework: str
    status: AgentStatus = AgentStatus.UNKNOWN
    capabilities: dict[str, str] = Field(default_factory=dict)
    runtime_metadata: dict[str, str] = Field(default_factory=dict)
    package_metadata: dict[str, str] = Field(default_factory=dict)
    registered_at: datetime | None = None
class SnapshotHeartbeatPayload(BaseModel):
    status: AgentStatus = AgentStatus.UNKNOWN
    last_seen: datetime | None = None
    capabilities: dict[str, str] = Field(default_factory=dict)
    runtime_metadata: dict[str, str] = Field(default_factory=dict)
    package_metadata: dict[str, str] = Field(default_factory=dict)
class FleetSnapshot(BaseModel):
    captured_at: datetime
    registrations: list[SnapshotAgentRegistration] = Field(default_factory=list)
    heartbeats: list[HeartbeatEvent] = Field(default_factory=list)
    evidence: list[EvidenceIngestRequest] = Field(default_factory=list)
```

---

## Source declarations: src/agenticops_control_tower/models/version.py

Source: [src/agenticops_control_tower/models/version.py](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/src/agenticops_control_tower/models/version.py)

```python
class VersionAssessment(BaseModel):
    agent_id: str
    capability: str
    installed_version: str | None
    minimum_version: str
    assessment: Literal['meets_minimum', 'outdated', 'missing', 'unknown']
    reason: str | None = None
```

---

## Source declarations: src/agenticops_control_tower/api/surface.py

Source: [src/agenticops_control_tower/api/surface.py](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/src/agenticops_control_tower/api/surface.py)

```python
class ControlTowerAPI():
    def __init__(self, registry: AgentRegistry, discovery: CapabilityDiscoveryService, status_service: StatusService | None=None, configuration_service: ConfigurationService | None=None, evidence_store: EvidenceStore | None=None, incident_service: IncidentService | None=None, runbook_service: RunbookService | None=None) -> None: ...
    def get_capability_contract(self) -> CapabilityContract: ...
    def register(self, agent: AgentRegistrationPayload | AgentRecord) -> AgentRecord: ...
    def heartbeat(self, agent_id: str, heartbeat: HeartbeatPayload) -> AgentRecord: ...
    def list_agents(self, *, status: AgentStatus | None=None, environment: str | None=None, capability: str | None=None, missing_capability: str | None=None) -> list[AgentRecord]: ...
    register_agent = register
    record_heartbeat = heartbeat
    def get_status(self, *, environment: str | None=None) -> FleetStatusSummary: ...
    def get_agent(self, agent_id: str) -> AgentRecord: ...
    def get_agent_capabilities(self, agent_id: str) -> dict[str, str]: ...
    def list_capabilities(self) -> list[CapabilityInventoryRecord]: ...
    def list_all_capabilities(self) -> dict[str, list[str]]: ...
    def summarize_evidence(self, link: EvidenceLink, artifact: dict[str, Any] | None, *, gate: dict[str, Any] | None=None) -> EvidenceSummary: ...
    def ingest_evidence(self, request: EvidenceIngestRequest, *, ingested_by: str='python') -> EvidenceIngestResult: ...
    def evidence_history(self, agent_id: str, *, source: EvidenceSource | None=None, limit: int | None=50) -> list[EvidenceRecord]: ...
    def agent_posture(self, agent_id: str, *, stale_after_seconds: int=DEFAULT_STALE_AFTER_SECONDS, now: datetime | None=None) -> AgentEvidencePosture: ...
    def fleet_posture(self, *, environment: str | None=None, stale_after_seconds: int=DEFAULT_STALE_AFTER_SECONDS, now: datetime | None=None) -> FleetEvidencePosture: ...
    def assess_versions(self, capability: str, minimum_version: str, *, environment: str | None=None) -> list[VersionAssessment]: ...
```

---

## Example file: sample_fleet_snapshot.json

Source: [docs/guide/examples/sample_fleet_snapshot.json](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/guide/examples/sample_fleet_snapshot.json)

```json
{
  "captured_at": "2026-08-15T12:00:00Z",
  "registrations": [
    {
      "agent_id": "payment-agent",
      "name": "payment-agent",
      "environment": "production",
      "runtime": "aws-lambda",
      "framework": "langgraph",
      "status": "unknown",
      "capabilities": {
        "agenticlens": "0.7.0",
        "agentic-sidecar": "0.6.0"
      },
      "runtime_metadata": {
        "python_version": "3.12",
        "region": "us-east-1"
      },
      "package_metadata": {
        "build_sha": "5f3d0c9",
        "release_channel": "stable"
      }
    },
    {
      "agent_id": "support-agent",
      "name": "support-agent",
      "environment": "staging",
      "runtime": "docker",
      "framework": "openai-agents",
      "status": "unknown",
      "capabilities": {
        "agenticlens": "0.7.0"
      },
      "runtime_metadata": {
        "python_version": "3.11",
        "container_image": "deepagentlabs/support-agent:0.2.0"
      },
      "package_metadata": {
        "build_sha": "9a2c1de",
        "release_channel": "staging"
      }
    }
  ],
  "heartbeats": [
    {
      "agent_id": "payment-agent",
      "heartbeat": {
        "status": "healthy",
        "capabilities": {
          "deep-agentic-core-mcp": "0.2.0"
        },
        "runtime_metadata": {
          "region": "us-east-1"
        }
      }
    },
    {
      "agent_id": "support-agent",
      "heartbeat": {
        "status": "degraded",
        "capabilities": {
          "agentic-sidecar": "0.6.0"
        },
        "runtime_metadata": {
          "node": "staging-01"
        }
      }
    }
  ],
  "evidence": [
    {
      "link": {
        "agent_id": "payment-agent",
        "source": "agenticlens",
        "source_version": "0.6.1",
        "artifact_type": "run",
        "artifact_ref": "lens:run:pay-0815-01",
        "observed_at": "2026-08-15T11:40:00Z",
        "run_id": "pay-0815-01"
      },
      "artifact": {
        "schema_version": "1.0",
        "run_id": "pay-0815-01",
        "trace_id": "trace-pay-0815-01",
        "application_name": "payment-agent",
        "status": "failed",
        "started_at": "2026-08-15T11:39:58Z",
        "completed_at": "2026-08-15T11:40:00Z",
        "error_type": "DependencyUnavailable",
        "spans": [
          {
            "span_id": "plan-1",
            "name": "plan refund",
            "span_type": "planning",
            "status": "succeeded"
          },
          {
            "span_id": "tool-1",
            "parent_span_id": "plan-1",
            "name": "charge card",
            "span_type": "tool_call",
            "tool_name": "payments_api",
            "status": "failed",
            "error_type": "ConnectionError"
          }
        ]
      }
    },
    {
      "link": {
        "agent_id": "payment-agent",
        "source": "agentic-sidecar",
        "source_version": "0.7.0",
        "artifact_type": "decision",
        "artifact_ref": "sidecar:decision:pay-0815-01:1",
        "observed_at": "2026-08-15T11:39:59Z",
        "run_id": "pay-0815-01"
      },
      "artifact": {
        "decision_id": "pay-0815-01-d1",
        "status": "ESCALATE",
        "risk": "HIGH",
        "reason": "Refund above automatic limit",
        "escalation_required": true
      }
    },
    {
      "link": {
        "agent_id": "payment-agent",
        "source": "agentic-evals",
        "source_version": "0.7.2",
        "artifact_type": "evaluation_report",
        "artifact_ref": "evals:payments-regression:2026-08-15",
        "observed_at": "2026-08-15T09:00:00Z"
      },
      "artifact": {
        "schema_version": "1.0",
        "suite_name": "payments-regression",
        "suite_version": "3",
        "created_at": "2026-08-15T08:58:00Z",
        "summary": {
          "total_cases": 20,
          "passed_cases": 18,
          "failed_cases": 2,
          "pass_rate": 0.9,
          "average_score": 0.9,
          "total_cost_usd": null,
          "priced_cases": 0,
          "cost_sources": {},
          "average_latency_ms": 50.0,
          "metrics": {
            "exact_match": {
              "total": 20,
              "passed": 18,
              "failed": 2,
              "skipped": 0,
              "pass_rate": 0.9,
              "average_score": 0.9
            }
          },
          "tags": {}
        },
        "cases": [
          {
            "case_id": "payment-0",
            "case_name": "Payment 0",
            "passed": true,
            "scores": [
              {
                "name": "exact_match",
                "metric": "exact_match",
                "value": 1.0,
                "passed": true,
                "required": true,
                "skipped": false,
                "explanation": "Output exactly matches the reference.",
                "evaluator_type": "deterministic",
                "evaluator": "agentic_evals.builtin",
                "evaluator_version": "0.7.2",
                "metadata": {}
              }
            ],
            "output": "paid",
            "trace_id": "payment-trace-0",
            "latency_ms": 50.0,
            "cost_usd": null,
            "cost_source": null,
            "sample_available": true,
            "tags": [],
            "metadata": {}
          },
          {
            "case_id": "payment-1",
            "case_name": "Payment 1",
            "passed": true,
            "scores": [
              {
                "name": "exact_match",
                "metric": "exact_match",
                "value": 1.0,
                "passed": true,
                "required": true,
                "skipped": false,
                "explanation": "Output exactly matches the reference.",
                "evaluator_type": "deterministic",
                "evaluator": "agentic_evals.builtin",
                "evaluator_version": "0.7.2",
                "metadata": {}
              }
            ],
            "output": "paid",
            "trace_id": "payment-trace-1",
            "latency_ms": 50.0,
            "cost_usd": null,
            "cost_source": null,
            "sample_available": true,
            "tags": [],
            "metadata": {}
          },
          {
            "case_id": "payment-2",
            "case_name": "Payment 2",
            "passed": true,
            "scores": [
              {
                "name": "exact_match",
                "metric": "exact_match",
                "value": 1.0,
                "passed": true,
                "required": true,
                "skipped": false,
                "explanation": "Output exactly matches the reference.",
                "evaluator_type": "deterministic",
                "evaluator": "agentic_evals.builtin",
                "evaluator_version": "0.7.2",
                "metadata": {}
              }
            ],
            "output": "paid",
            "trace_id": "payment-trace-2",
            "latency_ms": 50.0,
            "cost_usd": null,
            "cost_source": null,
            "sample_available": true,
            "tags": [],
            "metadata": {}
          },
          {
            "case_id": "payment-3",
            "case_name": "Payment 3",
            "passed": true,
            "scores": [
              {
                "name": "exact_match",
                "metric": "exact_match",
                "value": 1.0,
                "passed": true,
                "required": true,
                "skipped": false,
                "explanation": "Output exactly matches the reference.",
                "evaluator_type": "deterministic",
                "evaluator": "agentic_evals.builtin",
                "evaluator_version": "0.7.2",
                "metadata": {}
              }
            ],
            "output": "paid",
            "trace_id": "payment-trace-3",
            "latency_ms": 50.0,
            "cost_usd": null,
            "cost_source": null,
            "sample_available": true,
            "tags": [],
            "metadata": {}
          },
          {
            "case_id": "payment-4",
            "case_name": "Payment 4",
            "passed": true,
            "scores": [
              {
                "name": "exact_match",
                "metric": "exact_match",
                "value": 1.0,
                "passed": true,
                "required": true,
                "skipped": false,
                "explanation": "Output exactly matches the reference.",
                "evaluator_type": "deterministic",
                "evaluator": "agentic_evals.builtin",
                "evaluator_version": "0.7.2",
                "metadata": {}
              }
            ],
            "output": "paid",
            "trace_id": "payment-trace-4",
            "latency_ms": 50.0,
            "cost_usd": null,
            "cost_source": null,
            "sample_available": true,
            "tags": [],
            "metadata": {}
          },
          {
            "case_id": "payment-5",
            "case_name": "Payment 5",
            "passed": true,
            "scores": [
              {
                "name": "exact_match",
                "metric": "exact_match",
                "value": 1.0,
                "passed": true,
                "required": true,
                "skipped": false,
                "explanation": "Output exactly matches the reference.",
                "evaluator_type": "deterministic",
                "evaluator": "agentic_evals.builtin",
                "evaluator_version": "0.7.2",
                "metadata": {}
              }
            ],
            "output": "paid",
            "trace_id": "payment-trace-5",
            "latency_ms": 50.0,
            "cost_usd": null,
            "cost_source": null,
            "sample_available": true,
            "tags": [],
            "metadata": {}
          },
          {
            "case_id": "payment-6",
            "case_name": "Payment 6",
            "passed": true,
            "scores": [
              {
                "name": "exact_match",
                "metric": "exact_match",
                "value": 1.0,
                "passed": true,
                "required": true,
                "skipped": false,
                "explanation": "Output exactly matches the reference.",
                "evaluator_type": "deterministic",
                "evaluator": "agentic_evals.builtin",
                "evaluator_version": "0.7.2",
                "metadata": {}
              }
            ],
            "output": "paid",
            "trace_id": "payment-trace-6",
            "latency_ms": 50.0,
            "cost_usd": null,
            "cost_source": null,
            "sample_available": true,
            "tags": [],
            "metadata": {}
          },
          {
            "case_id": "payment-7",
            "case_name": "Payment 7",
            "passed": true,
            "scores": [
              {
                "name": "exact_match",
                "metric": "exact_match",
                "value": 1.0,
                "passed": true,
                "required": true,
                "skipped": false,
                "explanation": "Output exactly matches the reference.",
                "evaluator_type": "deterministic",
                "evaluator": "agentic_evals.builtin",
                "evaluator_version": "0.7.2",
                "metadata": {}
              }
            ],
            "output": "paid",
            "trace_id": "payment-trace-7",
            "latency_ms": 50.0,
            "cost_usd": null,
            "cost_source": null,
            "sample_available": true,
            "tags": [],
            "metadata": {}
          },
          {
            "case_id": "payment-8",
            "case_name": "Payment 8",
            "passed": true,
            "scores": [
              {
                "name": "exact_match",
                "metric": "exact_match",
                "value": 1.0,
                "passed": true,
                "required": true,
                "skipped": false,
                "explanation": "Output exactly matches the reference.",
                "evaluator_type": "deterministic",
                "evaluator": "agentic_evals.builtin",
                "evaluator_version": "0.7.2",
                "metadata": {}
              }
            ],
            "output": "paid",
            "trace_id": "payment-trace-8",
            "latency_ms": 50.0,
            "cost_usd": null,
            "cost_source": null,
            "sample_available": true,
            "tags": [],
            "metadata": {}
          },
          {
            "case_id": "payment-9",
            "case_name": "Payment 9",
            "passed": true,
            "scores": [
              {
                "name": "exact_match",
                "metric": "exact_match",
                "value": 1.0,
                "passed": true,
                "required": true,
                "skipped": false,
                "explanation": "Output exactly matches the reference.",
                "evaluator_type": "deterministic",
                "evaluator": "agentic_evals.builtin",
                "evaluator_version": "0.7.2",
                "metadata": {}
              }
            ],
            "output": "paid",
            "trace_id": "payment-trace-9",
            "latency_ms": 50.0,
            "cost_usd": null,
            "cost_source": null,
            "sample_available": true,
            "tags": [],
            "metadata": {}
          },
          {
            "case_id": "payment-10",
            "case_name": "Payment 10",
            "passed": true,
            "scores": [
              {
                "name": "exact_match",
                "metric": "exact_match",
                "value": 1.0,
                "passed": true,
                "required": true,
                "skipped": false,
                "explanation": "Output exactly matches the reference.",
                "evaluator_type": "deterministic",
                "evaluator": "agentic_evals.builtin",
                "evaluator_version": "0.7.2",
                "metadata": {}
              }
            ],
            "output": "paid",
            "trace_id": "payment-trace-10",
            "latency_ms": 50.0,
            "cost_usd": null,
            "cost_source": null,
            "sample_available": true,
            "tags": [],
            "metadata": {}
          },
          {
            "case_id": "payment-11",
            "case_name": "Payment 11",
            "passed": true,
            "scores": [
              {
                "name": "exact_match",
                "metric": "exact_match",
                "value": 1.0,
                "passed": true,
                "required": true,
                "skipped": false,
                "explanation": "Output exactly matches the reference.",
                "evaluator_type": "deterministic",
                "evaluator": "agentic_evals.builtin",
                "evaluator_version": "0.7.2",
                "metadata": {}
              }
            ],
            "output": "paid",
            "trace_id": "payment-trace-11",
            "latency_ms": 50.0,
            "cost_usd": null,
            "cost_source": null,
            "sample_available": true,
            "tags": [],
            "metadata": {}
          },
          {
            "case_id": "payment-12",
            "case_name": "Payment 12",
            "passed": true,
            "scores": [
              {
                "name": "exact_match",
                "metric": "exact_match",
                "value": 1.0,
                "passed": true,
                "required": true,
                "skipped": false,
                "explanation": "Output exactly matches the reference.",
                "evaluator_type": "deterministic",
                "evaluator": "agentic_evals.builtin",
                "evaluator_version": "0.7.2",
                "metadata": {}
              }
            ],
            "output": "paid",
            "trace_id": "payment-trace-12",
            "latency_ms": 50.0,
            "cost_usd": null,
            "cost_source": null,
            "sample_available": true,
            "tags": [],
            "metadata": {}
          },
          {
            "case_id": "payment-13",
            "case_name": "Payment 13",
            "passed": true,
            "scores": [
              {
                "name": "exact_match",
                "metric": "exact_match",
                "value": 1.0,
                "passed": true,
                "required": true,
                "skipped": false,
                "explanation": "Output exactly matches the reference.",
                "evaluator_type": "deterministic",
                "evaluator": "agentic_evals.builtin",
                "evaluator_version": "0.7.2",
                "metadata": {}
              }
            ],
            "output": "paid",
            "trace_id": "payment-trace-13",
            "latency_ms": 50.0,
            "cost_usd": null,
            "cost_source": null,
            "sample_available": true,
            "tags": [],
            "metadata": {}
          },
          {
            "case_id": "payment-14",
            "case_name": "Payment 14",
            "passed": true,
            "scores": [
              {
                "name": "exact_match",
                "metric": "exact_match",
                "value": 1.0,
                "passed": true,
                "required": true,
                "skipped": false,
                "explanation": "Output exactly matches the reference.",
                "evaluator_type": "deterministic",
                "evaluator": "agentic_evals.builtin",
                "evaluator_version": "0.7.2",
                "metadata": {}
              }
            ],
            "output": "paid",
            "trace_id": "payment-trace-14",
            "latency_ms": 50.0,
            "cost_usd": null,
            "cost_source": null,
            "sample_available": true,
            "tags": [],
            "metadata": {}
          },
          {
            "case_id": "payment-15",
            "case_name": "Payment 15",
            "passed": true,
            "scores": [
              {
                "name": "exact_match",
                "metric": "exact_match",
                "value": 1.0,
                "passed": true,
                "required": true,
                "skipped": false,
                "explanation": "Output exactly matches the reference.",
                "evaluator_type": "deterministic",
                "evaluator": "agentic_evals.builtin",
                "evaluator_version": "0.7.2",
                "metadata": {}
              }
            ],
            "output": "paid",
            "trace_id": "payment-trace-15",
            "latency_ms": 50.0,
            "cost_usd": null,
            "cost_source": null,
            "sample_available": true,
            "tags": [],
            "metadata": {}
          },
          {
            "case_id": "payment-16",
            "case_name": "Payment 16",
            "passed": true,
            "scores": [
              {
                "name": "exact_match",
                "metric": "exact_match",
                "value": 1.0,
                "passed": true,
                "required": true,
                "skipped": false,
                "explanation": "Output exactly matches the reference.",
                "evaluator_type": "deterministic",
                "evaluator": "agentic_evals.builtin",
                "evaluator_version": "0.7.2",
                "metadata": {}
              }
            ],
            "output": "paid",
            "trace_id": "payment-trace-16",
            "latency_ms": 50.0,
            "cost_usd": null,
            "cost_source": null,
            "sample_available": true,
            "tags": [],
            "metadata": {}
          },
          {
            "case_id": "payment-17",
            "case_name": "Payment 17",
            "passed": true,
            "scores": [
              {
                "name": "exact_match",
                "metric": "exact_match",
                "value": 1.0,
                "passed": true,
                "required": true,
                "skipped": false,
                "explanation": "Output exactly matches the reference.",
                "evaluator_type": "deterministic",
                "evaluator": "agentic_evals.builtin",
                "evaluator_version": "0.7.2",
                "metadata": {}
              }
            ],
            "output": "paid",
            "trace_id": "payment-trace-17",
            "latency_ms": 50.0,
            "cost_usd": null,
            "cost_source": null,
            "sample_available": true,
            "tags": [],
            "metadata": {}
          },
          {
            "case_id": "payment-18",
            "case_name": "Payment 18",
            "passed": false,
            "scores": [
              {
                "name": "exact_match",
                "metric": "exact_match",
                "value": 0.0,
                "passed": false,
                "required": true,
                "skipped": false,
                "explanation": "Output does not exactly match the reference.",
                "evaluator_type": "deterministic",
                "evaluator": "agentic_evals.builtin",
                "evaluator_version": "0.7.2",
                "metadata": {}
              }
            ],
            "output": "declined",
            "trace_id": "payment-trace-18",
            "latency_ms": 50.0,
            "cost_usd": null,
            "cost_source": null,
            "sample_available": true,
            "tags": [],
            "metadata": {}
          },
          {
            "case_id": "payment-19",
            "case_name": "Payment 19",
            "passed": false,
            "scores": [
              {
                "name": "exact_match",
                "metric": "exact_match",
                "value": 0.0,
                "passed": false,
                "required": true,
                "skipped": false,
                "explanation": "Output does not exactly match the reference.",
                "evaluator_type": "deterministic",
                "evaluator": "agentic_evals.builtin",
                "evaluator_version": "0.7.2",
                "metadata": {}
              }
            ],
            "output": "declined",
            "trace_id": "payment-trace-19",
            "latency_ms": 50.0,
            "cost_usd": null,
            "cost_source": null,
            "sample_available": true,
            "tags": [],
            "metadata": {}
          }
        ]
      },
      "gate": {
        "passed": false,
        "reasons": [
          "pass_rate 0.90 below configured minimum 0.95"
        ],
        "observed": {
          "pass_rate": 0.9
        }
      }
    },
    {
      "link": {
        "agent_id": "payment-agent",
        "source": "agentic-chaos",
        "source_version": "0.5.1",
        "artifact_type": "chaos_report",
        "artifact_ref": "chaos:payments-dependency-outage:2026-08-10",
        "observed_at": "2026-08-10T15:00:00Z"
      },
      "artifact": {
        "id": "chaos-0810",
        "name": "payments dependency outage",
        "start_time": "2026-08-10T14:50:00Z",
        "end_time": "2026-08-10T15:00:00Z",
        "chaos_events": [
          {
            "fault": "connection_refused"
          },
          {
            "fault": "timeout"
          }
        ]
      }
    }
  ]
}
```
