# Ingest evidence and read posture

Reference examples below show API composition and configuration fragments. Start with the complete quickstart before adapting these to your application.

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

Diagnosis artifacts can also be ingested through the supported producer contract. Keep detailed failure analysis in Lens.

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
