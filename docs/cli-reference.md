# CLI reference

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

## Complete command inventory

Every registered leaf command is listed below, including nested lifecycle operations. Global options go before the command; arguments/options below follow it. Use `agenticops-control-tower COMMAND --help` for defaults, allowed choices and exact request-file semantics. These are CLI commands; additional Python/HTTP-only operations are listed in the API reference and detailed guides.

| Command | Arguments and command options |
| --- | --- |
| `serve` | `[--host HOST] [--port PORT] [--database DATABASE]` |
| `agents register` | `PAYLOAD_FILE` |
| `agents heartbeat` | `AGENT_ID PAYLOAD_FILE` |
| `agents list` | `[--status STATUS] [--unhealthy] [--environment ENVIRONMENT] [--capability CAPABILITY] [--missing-capability MISSING_CAPABILITY]` |
| `agents get` | `AGENT_ID` |
| `capabilities list` | `—` |
| `status` | `[--environment ENVIRONMENT]` |
| `config` | `AGENT_ID CAPABILITY` |
| `audit` | `AGENT_ID` |
| `actions preview` | `PAYLOAD_FILE` |
| `actions get` | `ACTION_ID` |
| `actions approve` | `ACTION_ID` |
| `actions deny` | `ACTION_ID` |
| `actions revoke` | `ACTION_ID` |
| `actions execute` | `ACTION_ID` |
| `bulk preview` | `PAYLOAD_FILE` |
| `bulk get` | `BULK_ID` |
| `bulk approve` | `BULK_ID` |
| `bulk deny` | `BULK_ID` |
| `bulk revoke` | `BULK_ID` |
| `bulk execute` | `BULK_ID` |
| `alerts list` | `[--environment ENVIRONMENT] [--active-only]` |
| `alerts evaluate` | `—` |
| `alerts acknowledge` | `ALERT_ID` |
| `incidents list` | `—` |
| `incidents get` | `INCIDENT_ID` |
| `incidents detect` | `PAYLOAD_FILE` |
| `incidents view` | `INCIDENT_ID` |
| `incidents investigate` | `INCIDENT_ID` |
| `incidents preview` | `INCIDENT_ID PAYLOAD_FILE` |
| `incidents approval` | `INCIDENT_ID PAYLOAD_FILE` |
| `incidents revoke` | `INCIDENT_ID` |
| `incidents execute` | `INCIDENT_ID PAYLOAD_FILE` |
| `incidents verify` | `INCIDENT_ID PAYLOAD_FILE` |
| `runbooks catalog` | `—` |
| `runbooks recommend` | `INCIDENT_ID` |
| `runbooks history` | `INCIDENT_ID` |
| `runbooks preview` | `INCIDENT_ID PAYLOAD_FILE` |
| `runbooks validations` | `RUNBOOK_ID VERSION` |
| `runbooks validate` | `RUNBOOK_ID VERSION PAYLOAD_FILE` |
| `runbooks get` | `EXECUTION_ID` |
| `runbooks approval` | `EXECUTION_ID PAYLOAD_FILE` |
| `runbooks revoke` | `EXECUTION_ID` |
| `runbooks execute` | `EXECUTION_ID PAYLOAD_FILE` |
| `runbooks cancel` | `EXECUTION_ID` |
| `runbooks verify` | `EXECUTION_ID PAYLOAD_FILE` |
| `runbooks reconcile` | `EXECUTION_ID` |
| `evidence ingest` | `AGENT_ID SOURCE ARTIFACT_FILE [--source-version SOURCE_VERSION] [--artifact-ref ARTIFACT_REF] [--observed-at OBSERVED_AT] [--run-id RUN_ID] [--runtime-agent-id RUNTIME_AGENT_ID] [--gate GATE]` |
| `evidence ingest-manifest` | `MANIFEST_FILE` |
| `evidence ingest-sidecar-journal` | `AGENT_ID JOURNAL_FILE [--source-version SOURCE_VERSION] [--run-id RUN_ID] [--runtime-agent-id RUNTIME_AGENT_ID]` |
| `evidence history` | `AGENT_ID [--source SOURCE] [--limit LIMIT]` |
| `evidence posture` | `AGENT_ID [--stale-after-seconds STALE_AFTER_SECONDS]` |
| `posture` | `[--environment ENVIRONMENT] [--stale-after-seconds STALE_AFTER_SECONDS]` |

## Server

| Command | Role | Description |
| --- | --- | --- |
| `serve [--host HOST] [--port PORT] [--database PATH]` | — | Run the HTTP API and console. Defaults: `127.0.0.1`, `8000`, in-memory storage. See [server settings](settings.md). |

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

See [evidence posture](evidence-posture.md).

## Controlled configuration

| Command | Role | Description |
| --- | --- | --- |
| `config AGENT_ID CAPABILITY` | reader | Configuration ownership and values. |
| `audit AGENT_ID` | reader | Configuration action audit. |
| `actions preview REQUEST.json` | writer | Create an immutable preview; returns its ID. |
| `actions get ID` | reader | Read an action. |
| `actions approve ID` / `actions deny ID` / `actions revoke ID` | approver | Decide on a preview (a different identity from the proposer). |
| `actions execute ID` | writer | Execute an approved, unexpired action. |

See [controlled configuration](configuration.md).

## Bulk fleet operations

`bulk preview FILE.json`, `bulk get ID`, `bulk approve|deny|revoke ID`
(approver), `bulk execute ID` (writer). `bulk execute` exits with status 1 when
any target fails, after printing every result. See
[fleet operations](fleet-operations.md); `examples/bulk_tracing.json` is a
preview payload.

## Alerts and incidents

| Command | Role | Description |
| --- | --- | --- |
| `alerts list [--environment E] [--active-only]` | reader | Current alerts. |
| `alerts evaluate` | writer | Run a detection scan now (the server also scans every 30 seconds). |
| `alerts acknowledge ALERT_ID` | writer | Acknowledge an alert. |
| `incidents list` / `incidents get ID` / `incidents view ID` | configured credentials | Read incidents; `view` joins inventory, evidence, alerts, approvals and timeline. |
| `incidents detect FILE.json`, `investigate ID`, `preview ID FILE.json`, `approval ID FILE.json`, `revoke ID`, `execute ID FILE.json`, `verify ID FILE.json` | writer / approver | The approved staging-recovery workflow. Request formats are in [incident recovery](incident-recovery.md). |

See [live operations](live-operations.md).

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
resolved. See [runbooks](runbooks.md) for request files.

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
