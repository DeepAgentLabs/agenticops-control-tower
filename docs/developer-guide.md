# Control Tower developer guide

Use this guide to set up Control Tower, run a local example, and apply it to your application. Optional provider and integration fragments identify the objects or services you must supply.

[Quickstart](#quickstart) · [Usage](#usage) · [Configuration](#settings) · [Troubleshooting](#troubleshooting) · [Reference](#reference)

## Quickstart

Requires Python 3.10 or newer. Run commands in an activated virtual environment. Download referenced files into the same working directory before running them.

### Install

```
python -m pip install "agenticops-control-tower[api]"
```

### Read a fleet snapshot offline

Download the repository's sample snapshot. It represents historical fixture data; its embedded package fields are evidence values, not installation recommendations.

[Download sample_fleet_snapshot.json](guide/examples/sample_fleet_snapshot.json)

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

[Register and send heartbeats ↗](getting-started.md) · [Link evidence ↗](evidence-posture.md) · [Authentication ↗](authentication.md)

## Usage

<span id="registration"></span>

### Register agents and send heartbeats

Start the server using [the quickstart](#quickstart). In a second terminal, activate the same environment and configure the writer token for the CLI client.

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

[Download tower_registration.json](guide/examples/tower_registration.json)

tower_heartbeat.json · complete file

```json
{"status":"healthy","capabilities":{}}
```

[Download tower_heartbeat.json](guide/examples/tower_heartbeat.json)

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
| `--host` | `127.0.0.1` | Interface to bind. Use `0.0.0.0` to accept other computers on the network ([hosting](hosting.md)). |
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

See [Authentication](authentication.md).

#### Built-in limits

| Setting | Value | Where it applies |
| --- | --- | --- |
| Live detection interval | 30 seconds | Scans stored telemetry while the server runs. Python hosts can pass `create_app(detection_interval_seconds=0)` to disable it and call `POST /alerts/evaluate` from their own scheduler. |
| Detection freshness and heartbeat windows | 300 seconds each | `DetectionPolicy`, configurable by a trusted Python host ([live operations](live-operations.md)). |
| Evidence stale-after | 1 day (max 30 days) | `--stale-after-seconds` / `stale_after_seconds` on posture reads. |
| Evidence history limit | 50 (max 500) | `evidence history --limit`. |
| Request body size | 1 MiB, `Content-Length` required | `POST /evidence` and `POST /bulk/preview`. |
| Action expiry | 1–3600 seconds | Configuration previews ([controlled configuration](configuration.md)). |

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

for remote browser/API traffic. See [the hosting guide](hosting.md) for local,

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

- [Open API / CLI reference ↗](cli-reference.md)
