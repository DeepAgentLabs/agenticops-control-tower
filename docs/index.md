# Control Tower

Which agents exist, what evidence do they have, and what needs attention?

<span id="what-it-does-today"></span>

## What it does

Fleet inventory, evidence posture, alerts, incident views, and approved operational workflows, grouped by area below. Each area links to its detailed guide; for runnable commands, see the [developer guide](developer-guide.md).

### 1. Agent registry and fleet inventory

- **Registration**
    - Register deployment identity: agent ID, name, environment, runtime, framework, capabilities and metadata
    - Registration replaces a matching deployment and resets its heartbeat count
- **Heartbeats**
    - Runtime-reported status and `last_seen`, with metadata maps merged on each heartbeat
    - Heartbeat history and counts per agent
- **Fleet health**
    - Fleet status with capability coverage, per environment
    - Filters by environment, status, capability present or missing
    - Health is reported by the runtime; heartbeat age or a failed gate never rewrites it
- **Storage and offline views**
    - In-memory or durable SQLite registry (`--database`)
    - Offline fleet snapshots for inventory, heartbeat history and evidence without a server

Guides: [Getting started](getting-started.md) · [Fleet health](developer-guide.md#health) ·
[Offline snapshots](evidence-posture.md#offline-snapshots)

### 2. Capability discovery and version policy

- **Capability inventory**
    - Which DeepAgentLabs packages each agent reports: Lens, Evals, Sidecar, Chaos, MCP
    - Capability → versions across the whole fleet
- **Version assessment**
    - Minimum-version policy you set, compared with PEP 440 (`GET /versions`, `assess_versions`)
    - Missing capabilities and invalid reported versions stay distinct
- **Versioned capability contract**
    - `tower.capabilities.v1` candidate descriptor with registration, heartbeat and readback JSON Schemas
    - Python and Node.js HTTP worker examples exercise the same contract

Guides: [Capability contract](capability-contract.md) · [API reference](api-reference.md#inventory-and-health)

### 3. Ecosystem evidence posture

- **Ingestion**
    - Push native Lens runs and diagnosis, Evals reports and gates, Sidecar decisions and journals, and Chaos reports
    - Explicit deployment attribution through an `EvidenceLink`; manifest and Sidecar-journal ingestion
    - Idempotent retries; references are labels Tower never fetches
- **Posture**
    - Fresh, stale or missing evidence per deployment and per producer
    - Native outcome tallies: run status, failed tools, gate results, decision outcome and risk, chaos experiments
    - Evidence history, newest first
- **Boundaries**
    - Producer outcomes never change reported health
    - Tower never recomputes a producer's verdict
    - Two bundled native Evals JSON Schemas for report and gate validation

Guides: [Evidence posture](evidence-posture.md) · [Ecosystem alignment](ecosystem-alignment.md)

### 4. Controlled configuration

- **Ownership**
    - Tower-owned desired settings, or mirrored runtime-owned settings
    - HTTP cannot elevate mirrored configuration into Tower ownership
- **Approval lifecycle**
    - Immutable preview → independent approval → execution
    - Bound to target, revision, before/after values, intent, impact and expiry
    - Deny, revoke and one-time consumption; writers cannot approve their own proposal
- **Audit**
    - Durable audit trail per agent
    - Executing commits desired state; it does not claim the remote runtime applied it

Guides: [Controlled configuration](configuration.md)

### 5. Bulk fleet operations

- **Targeting**
    - Environment/capability selectors and optional IDs freeze a sorted list of 1–100 targets
    - Later registrations never join an approved target set
- **Operations**
    - `config.update`, `capabilities.enable`, `capabilities.disable` and `runtime.stop`
- **Lifecycle**
    - Bulk preview, approve once, execute, revoke
    - Per-target results, including partial failure; the CLI exits 1 if any target fails

Guides: [Fleet operations](fleet-operations.md)

### 6. Live detection and alerts

- **Detection**
    - Periodic scan of stored telemetry, every 30 seconds by default; on-demand `alerts evaluate`
    - Configurable `DetectionPolicy`, or disable the loop and schedule scans yourself
- **Rules**
    - Fresh failed native Lens runs → deduplicated alerts and recovery incidents
    - Overdue heartbeats and stale or missing evidence → separate warnings
- **Lifecycle**
    - Acknowledge, clear and reopen with durable audit
    - Clearing an alert never resolves its incident; detection never runs recovery

Guides: [Live operations](live-operations.md)

### 7. Incident investigation and export

- **Incidents**
    - Durable incidents from failed native Lens evidence; repeated detection returns the same incident
    - Joined incident timeline with citations, approvals, commands and recovery checks
- **Investigation**
    - Same-deployment, same-run evidence assembled with citations, missing inputs, uncertainty and contradictions
    - No bundled model and no claim of exact causality
- **Lens execution verification**
    - Optional Lens `ExecutionBundle` verification with host-held trust keys
    - Verified, failed, unknown and incomplete states persist distinctly, with redacted causal links
- **AIOS export**
    - `export_investigation_report` projects an incident into an AIOS `0.8-draft` investigation report
    - Keeps source identity and citations; redacts summaries, private findings and event details

Guides: [Incident recovery](incident-recovery.md) · [Lens execution evidence](lens-execution-evidence.md) ·
[Coordinated v1 readiness](coordinated-v1-readiness.md)

### 8. Approved recovery and runbooks

- **Staging recovery action**
    - Fixed `staging.restore_dependency.v1` action through a host-installed connector
    - A separate human approves the exact preview digest before a writer executes it
- **Versioned runbooks**
    - Immutable definitions with prerequisites, string parameters, impact and rollback
    - Up to 10 ordered steps, each with a timeout (1–30 s), up to 3 attempts on clean failure and an optional rollback action
    - Recommendations come only from installed versions; a copilot cannot invent commands
    - Built-in `staging.dependency_recovery` 1.0.0: drain, restore and resume one dependency
- **Failure handling**
    - Clean failures retry within the step limit, then completed steps are compensated in reverse order and escalated
    - Partial, timed-out or unknown outcomes stop for host reconciliation; nothing is replayed
    - Cancellation before or between steps; interrupted runs are reconciled after a lease
- **Verification and validation**
    - Recovery requires a connector probe, fresh Lens success and a passing same-run Evals gate
    - Completed Chaos reports and passing Evals gates can be recorded as validation for a runbook version

Guides: [Runbooks](runbooks.md) · [Incident recovery](incident-recovery.md)

### 9. Emergency control

- **Runtime stop and restart**
    - Sidecar containment adapter installed per deployment (`stop`, `restart`)
    - Bulk `runtime.stop` across a frozen target set
- **Access revocation**
    - Native MCP issuer revocation bound to one task's credential
    - Missing connectors, timeouts and partial revocation stay explicit
- **Independence**
    - Emergency control works without model approval; restart does not renew revoked credentials

Guides: [Incident recovery](incident-recovery.md) · [Bulk stop and revocation](fleet-operations.md#bulk-stop-and-mcp-revocation) ·
[Phase 6 containment](phase6-containment.md)

### 10. Interfaces

- **Python API**: the `ControlTowerAPI` facade with `config`, `bulk`, `operations`, `incidents` and `runbooks` services
- **HTTP API**: FastAPI server (`serve` / `create_app()`) with generated OpenAPI at `/docs`
- **CLI**: `agenticops-control-tower` with live (`--api-url`, `--token`) and offline (`--snapshot`) modes
- **Read-only console**: `/console/` for fleet, evidence, alerts, incidents and runbook state; GET requests only
- **MCP**: the separate MCP package exposes `tower.*` and `tower.runbook*` tools; approval stays human-only

Guides: [API reference](api-reference.md) · [CLI reference](cli-reference.md) · [MCP connector](mcp-connector.md)

### 11. Security, hosting and settings

- **Authentication**
    - Bearer tokens with separate reader, writer and approver roles
    - Self-generated tokens; no DeepAgentLabs account or token service
    - Trusted Python `Operator` objects can narrow access to specific agents
- **Hosting**
    - Local, private-network and HTTPS reverse-proxy hosting of the API and console
    - Console shell holds no fleet data; restrictive Content-Security-Policy and `no-store` caching
- **Settings and limits**
    - Server and client settings, detection intervals, quotas, body limits and optional Lens trust store

Guides: [Authentication](authentication.md) · [Hosting](hosting.md) · [Server settings](settings.md)

## What you need

Registrations, heartbeats, explicit evidence links, and operator configuration.

## Start here

Read a sample fleet offline, then start the local console: [follow the quickstart](developer-guide.md#quickstart).

## Limits

- Fleet status does not turn a failed eval into a pass; health stays runtime-reported.
- Evidence ingestion and producer integrations must be configured explicitly.
- Production runtime connectors and production remediation are not included; the bundled recovery runtimes are deterministic staging fixtures.
- Shared role tokens are deployment credentials, not per-user tenancy.

See [Limitations](limitations.md).

## Documentation

- [Developer Guide (simple)](developer-guide.md): short task workflows and a capability index
- [API Reference (detailed)](api-reference.md): HTTP routes, Python methods and service signatures
- [AI Readable Documentation](ai-reference-index.md): the full reference as one file for AI tools, with source declarations and schemas
