# Changelog

## [Unreleased]

## 0.9.0

Released 2026-10-31. Pairs with MCP 0.5.1 local `tower.runbook*` tools.

### Added

- Versioned, immutable runbook catalog with prerequisites, typed parameters,
  ordered steps, per-step timeouts, clean-failure retry limits, declared rollback
  actions, fixed recovery criteria and a 120-second worst-case budget. The built-in
  `staging.dependency_recovery` 1.0.0 drains, restores and resumes one dependency.
- `RunbookConnector` named-action protocol and the deterministic
  `StagingRunbookRuntime` fixture with durable idempotency receipts and fault hooks.
- `RunbookService` recommendations limited to installed versions, exact-digest
  previews, separate human approval, revocation, claim-before-dispatch execution,
  compensation on clean failure or cancellation, stop-for-reconciliation on
  partial, timed-out or unknown outcomes, lease-based interruption reconciliation
  and evidence-based verification.
- Chaos and Evals validation records for runbook versions, reported in
  recommendations without becoming an execution gate.
- Runbook HTTP routes, `runbooks` CLI commands, runbook history in incident views
  and timelines, and runbook links on console incident cards.
- `examples/runbook_recovery.py`, `docs/runbooks.md` and
  `docs/tower-0.9-compatibility.md`.

### Changed

- Recovery evidence criteria are shared by the 0.6 single-action plan and
  runbooks (`IncidentService.recovery_evidence`). Previewing a runbook closes
  investigation and the single-action plan for that incident.
- Development dependency pins `agentic-evals==0.10.0`. Native report and gate
  schemas are unchanged, so bundled copies stay exact; AIOS evaluation evidence
  Runs are not a Tower input. See `docs/evals-0.10-aios-evidence.md`.

### Compatibility

- Existing evidence, incident, fleet and alert contracts are unchanged; stored
  incidents gain an optional `runbook_execution_id`. Optional sibling ranges are
  unchanged. Only the staging fixture is a supported runbook runtime; production
  connectors are not included.

## 0.8.0

Released 2026-10-20.

### Added

- Periodic latest-observation detection over pushed telemetry: fresh native Lens
  failures create deduplicated incidents; stale heartbeats and stale/missing
  producer evidence create warnings independently of reported deployment health.
- Durable scoped alerts, idempotent acknowledgement, explicit same-run/environment
  correlation, clearing/reopening lifecycle and append-only attributed audit.
- Reader alert feed and joined incident views; writer evaluate/acknowledge HTTP
  routes and CLI commands. Automatic detection never approves or executes recovery.
- Read-only incident console with 30-second refresh, findings, approvals, native
  policy evidence, command receipts and verification history. Lens integrity and
  coverage remain explicitly unverified/unassessed.
- Standalone example, operational boundaries, sibling compatibility guide and
  persistence/freshness/authorization/concurrency/console acceptance coverage.

### Compatibility

- Existing evidence schemas, recovery/fleet contracts and optional sibling ranges
  are unchanged. No sibling runtime release is needed. Detection is local polling,
  not lossless streaming, external notification delivery or production remediation.

## 0.7.1

Released 2026-10-19. Pairs with Agentic Evals 0.9.0 (roadmap v0.9 judge
reliability, cost and live-target resilience).

### Changed

- Re-sync the bundled native Evals report and gate schemas from
  `agentic-evals==0.9.0`, so validation enforces the new optional judge summary,
  live-target summary and per-case `target_status` fields. Reports from Evals
  0.7.2 to 0.8.0 still validate.
- Evaluation evidence details project `summary.judge` (judge scores, unavailable
  judgments and cases, judge cost, lowest agreement) and `summary.live` (retried,
  timed-out and errored cases). Both are `null` in reports written before Evals
  0.9.0; `summary.live` is also `null` for offline runs, and `summary.judge` for
  runs without judge scores (offline judged runs do carry it).
  Producer gate decisions are carried unchanged.
- The contract-test dev pin moves to `agentic-evals==0.9.0`. The optional
  `agentic-evals` extra keeps `>=0.7.2,<1`, and the base package imports no sibling.

## 0.7.0

Released 2026-10-18.

### Added

- Deterministic environment/capability fleet selectors with frozen sorted targets,
  explicit intent, before/after configuration previews and separate human approval.
- Durable SQLite bulk actions, per-target audit/results, expiry, revocation,
  scoped Python identities and single-use transactional execution claims.
- Bulk desired settings and capability toggles with independent stale-target failures.
- Host-installed Sidecar stop/MCP revocation coordination, bounded acknowledgement
  waits, a 30-second maximum batch wait budget, capped outstanding calls, durable
  late receipts and explicit unsupported/incomplete/timeout outcomes.
- Authenticated Python/HTTP/CLI workflows, partial-failure CLI status and runnable
  offline example, with documented rollback and interrupted-work reconciliation.

### Compatibility

- Siblings remain optional; existing dependency ranges remain sufficient. Native
  evidence and deployment health are unchanged. Fleet contracts are Tower-local.
- Local MCP investigation remains compatible; new bulk writes are Python/HTTP/CLI-only.
  No hosted MCP fleet exposure, remote configuration application, fleet atomicity,
  automatic rollback/resume or full downstream containment is asserted.

## 0.6.1

Released 2026-10-17.

### Added

- Offline validation against the exact published Evals 0.7.2 report and gate
  schemas, with pinned upstream parity tests and packaged schema resources.
- Native JSON boundary tests for nested invalid scores, failed gates, unknown
  additive fields, unsupported versions and value-free diagnostics.

### Changed

- Report consumers reject malformed/partial native artifacts before projecting
  or analyzing them. Send full JSON reports rather than summary-only objects.
- Evidence ingestion marks invalid reports/gates unavailable without retaining a usable gate.
- The Evals extra floor is 0.7.2; base validation needs no installed sibling.

## 0.6.0

Released 2026-10-17. Phase 6 and Phase 6A ship as one milestone.

### Added

- Durable evidence-led incidents, cited chronological investigation and explicit
  uncertainty; contradictory same-run outcomes block runbook proposals.
- One allowlisted deterministic staging dependency recovery runtime, exact-plan
  digests, separate human approval, expiry/revocation and consumed execution claims.
- Fresh Lens success, correlated passing Evals gate and probe-based recovery
  verification, with failure escalation and interrupted-execution reconciliation.
- Authenticated HTTP and CLI incident workflows; MCP 0.3.6 local query/proposal
  tools and investigation prompt use the real Tower API with separate credentials.
- Thin Sidecar emergency stop/explicit restart and native MCP issuer revocation
  adapters with honest in-flight and downstream-credential limits.
- Native Lens/Evals operator walkthrough and approval, crash, duplicate, timeout,
  partial-failure and recovery tests. Siblings remain optional.

### Limits

- The supported runtime is a local SQLite staging fixture, not a production
  process manager. No hosted MCP tenant credential bridge, automatic polling,
  model provider, production runbooks or incident console is claimed.


## 0.5.2

Released 2026-10-17.

### Fixed

- Accept Lens diagnosis schema 1.1 alongside 1.0 after Sidecar supervision timeline
  events were added in Lens 0.7.1. Unknown schema versions remain unavailable;
  producer governance outcomes remain separate from deployment health.
- Document Sidecar 0.8 shared/exclusive scope and evidence integration boundaries.


## 0.5.1

Released 2026-10-13.

### Added

- Native AgenticLens 0.7.0 diagnosis reports as Lens evidence
  (`artifact_type: diagnosis_report`). The projection keeps run and trace IDs,
  run status, task success, taxonomy and engine versions, diagnosis counts,
  and Lens's attribution (status, faulty step and agent, category,
  confidence). Diagnoses, span evidence and timelines stay in Lens.
- Lens posture tallies `attribution_counts` and `faulty_agents` next to run
  `status_counts`.
- `evidence ingest` picks `diagnosis_report` automatically for Lens artifacts
  with an `engine_version` field.
- `examples/evidence/lens_diagnosis.json` sample and tests, including one
  against the real `agenticlens.diagnosis` package.

### Changed

- Sample registrations and heartbeats report `agenticlens` 0.7.0. Checked
  against Lens 0.7.0 and Chaos 0.5.3.
- The optional `agenticlens` extra requires `>=0.7`; the lock resolves Lens
  0.7.0 and Chaos 0.5.3, so the ecosystem CI job tests the diagnosis reader.

## 0.5.0

Released 2026-10-13.

### Added

- Push-based ecosystem evidence ingestion through `ControlTowerAPI.ingest_evidence`,
  `POST /evidence` (writer) and CLI `evidence ingest`, `ingest-manifest` and
  `ingest-sidecar-journal`. Retries of one attributed observation are idempotent.
- Durable evidence history in memory or the shared SQLite database, with
  future-time rejection, 1 MiB HTTP body limit and Python pruning. Only validated
  projections are stored; unavailable results are kept with their reason.
- Agent and fleet evidence posture (`GET /agents/{id}/evidence`, `GET /posture`,
  CLI `evidence posture` and `posture`): fresh/stale/missing freshness, latest
  record, recent counts and tallies of native producer values. Producer outcomes
  never change reported health and no verdict is recomputed.
- `GET /agents/{id}/evidence/history` and CLI `evidence history`.
- Lens run projection of trace ID, timing, task success, error type, tool names
  and failed spans, without span payloads or error messages.
- `sidecar_journal_decisions()` for Sidecar JSON, export-array and JSONL journals.
- Read-only console fleet posture panel and per-agent evidence table.
- Offline snapshots accept an `evidence` list, evaluated as of `captured_at`.
- Evidence guide, native sample artifacts, collection manifest, Python push
  example and a CI job against published sibling extras.

### Changed

- `GET /agents/{id}/evidence` returns per-producer posture instead of a fixed
  `unavailable` readiness message.
- Unavailable evidence reasons name the failing native field without echoing values.
- Optional sibling floors: Lens 0.6, Chaos 0.5 and MCP 0.3.4 (Evals 0.7 and
  Sidecar 0.7 unchanged). Checked against Lens 0.6.1, Evals 0.7.1, Sidecar 0.7.0
  and Chaos 0.5.1.

### Limits

- Tower does not pull from producer services or fetch artifact references.
  Producers share the writer token; per-producer credentials, AIOS mapping,
  journal integrity verification and automatic retention remain planned.

## 0.4.0

Released 2026-10-12.

### Added

- Tower-owned desired configuration with explicit mirrored/unsupported ownership.
- Bounded action previews, independent approvals, denial, expiry, revocation,
  revision matching and one-use execution; deployment-scoped Python operators.
- Transactional SQLite configuration, action state and audit persistence,
  including rejected commands; concurrent stale actions cannot overwrite state.
- Configuration/action/audit HTTP and CLI surfaces with separate approval tokens.
- Configuration examples, safety regression tests and updated optional sibling
  dependency floors for Lens 0.5, Sidecar 0.7, Chaos 0.4 and MCP 0.3.1.

### Limits

- Desired settings are local to Tower. Runtime reconfiguration, stop/revoke
  transport, remote partial-failure reconciliation and console writes remain planned.
- Local writes are atomic: storage errors roll back settings, approval consumption
  and success audit together. Result contracts reserve remote failure/rollback states.

## 0.3.1

Released 2026-10-12.

### Fixed

- Journal readback accepts direct native JSON export arrays in addition to
  recording objects and JSONL, with regular-suite regression coverage.

- Native Sidecar decision summaries preserve optional decision IDs and trigger
  details alongside causal links. Legacy artifacts remain compatible.
- Added Sidecar v0.7 journal readback examples and actual-producer tests for all
  seven outcomes, causal identity and deployment-health separation.

### Documentation

- Expanded the command-center roadmap with evidence-backed copilot investigation,
  a first human-approved incident-to-recovery scenario (v0.6.x), live incident
  views (v0.8), and automated runbooks with recovery verification (v0.9).

- Added customer-managed token generation and rotation instructions, local/cloud
  console hosting guidance, and local startup/HTTPS proxy examples.

## 0.3.0

### Fixed

- Reject route-unsafe agent IDs at registration and snapshot validation; cover
  accepted IDs through real HTTP detail, heartbeat and evidence routes.
- Reconcile README implementation status with the shipped read-only console.

### Added

- Packaged read-only AgenticOps Console at `/console/`, using existing authenticated
  APIs for health, filtered inventory, coverage, versions and agent details.
- Shared PEP 440 minimum-version assessments and authorized `GET /versions`.
- Agent evidence-readiness read endpoint and console view that explicitly show
  unavailable evidence collection and planned incident/remediation workflows.
- Memory-only console credentials, disconnect/failed-refresh clearing, responsive
  accessible controls and a restrictive content security policy.

## 0.2.1

### Added

- Native Lens, Evals, Sidecar and Chaos evidence readers with explicit deployment
  attribution, unavailable results, and optional actual-producer contract tests.
- Ecosystem ownership/correlation documentation and aligned example versions.
- Optional durable SQLite registry with transactional heartbeat updates.
- Reader/writer bearer authorization for HTTP routes and CLI token support.
- Shared fleet status, capability coverage/version rollups, HTTP and CLI filters.
- Offline snapshot CLI reads and milestone acceptance tests.

### Fixed

- Reconciled Python registration, heartbeat and discovery APIs with snapshot
  loading and existing models; unknown agents now return HTTP 404.
- Updated roadmap, audit and operator documentation to reflect completed v0.1/v0.2.


### Added

- HTTP API (`agenticops_control_tower.api.http.create_app()`, optional `api`
  extra) implementing the v0.1 roadmap's suggested surface: `POST
  /agents/register`, `POST /agents/{id}/heartbeat`, `GET /agents`, `GET
  /agents/{id}`, `GET /capabilities` (aggregated across all agents).
- Operator CLI (`agenticops-control-tower` console script, optional `api`
  extra): `serve`, `agents register|heartbeat|list|get`, `capabilities list`.
- `ControlTowerAPI.register()`, `.heartbeat()`, and `.list_all_capabilities()`
  facade methods backing the HTTP layer.
- `examples/sample_agent_registration_kubernetes.json`, a second example
  registration payload (`kubernetes`/`crewai`) alongside the existing
  `aws-lambda`/`langgraph` one.
- `tests/test_http_api.py` and `tests/test_cli.py` (skip automatically
  without the `api` extra installed).

## 0.0.1

- Initial repository scaffold
- Concept-stage README and roadmap
- Package layout, tests, and CI/release workflows
