# Limitations

Known limits of the current release (1.1.0), taken from the repository's
[implementation evidence and operational limits](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/ROADMAP.md#implementation-evidence-and-operational-limits)
and the feature guides. Topic guides list further limits for their own features.

## Release and maturity

- The PyPI classifier is still **Pre-Alpha**. Version 1.0.0 marks the coordinated
  DeepAgentLabs milestone (2026-11-05); it does not certify AIOS conformance or
  production deployment readiness.
- The capability contract (`tower.capabilities.v1`) and AIOS `0.8-draft` exports
  keep their candidate/draft markers. Independent review, independent
  implementations, live-provider validation and the stable contract freeze remain
  open. See the [Phase 10 validation record](phase10-validation.md).
- Repository checkouts are needed for walkthroughs that read bundled example files.

## Identity and access

- Authentication uses shared deployment tokens (reader, writer, approval). There
  are no user accounts, per-agent identities or tenant isolation. Trusted Python
  `Operator.agent_ids` scoping is available only to in-process hosts.
- With no tokens configured, inventory routes are anonymous. Use this only on
  your own computer. Controlled operations always require credentials.
- Serve over HTTPS when anyone else connects; Tower does not terminate TLS itself.

## Storage and scale

- SQLite only, for a single host with a local database file. No distributed
  storage or multi-instance coordination.
- Without `--database`, all state is in memory and lost on restart.
- Alert and incident audit history is retained without automatic pruning and is
  not independently tamper-evident.

## Health and evidence

- Health is **agent-reported**. Tower does not time out silent agents into
  `unhealthy` (overdue heartbeats raise a warning alert instead) and does not
  detect installed packages automatically.
- Evidence collection is **push-only**. Tower never fetches `artifact_ref`s or
  connects to producer services.
- Tower never recomputes a producer's verdict, and evidence never changes
  reported health.
- Snapshots are offline views: they do not restore approvals, desired settings,
  live alerts, incident execution or credentials.

## Lens execution verification

- Optional; requires Lens `>=0.12,<2`. Without it, results are `unknown`.
- Verification uses host-held HMAC keys (trusted-host symmetric authentication),
  not independent public signing. HTTP requests cannot configure trust.
- Keys load at app start; restart after trust changes. Stored results reflect
  ingestion-time verification and are not rewritten by key rotation or revocation.
- Verified evidence does not prove complete execution, containment or recovery.

## Configuration and recovery

- Controlled configuration records **desired** values. No remote adapter applies
  them to running agents, so execution never claims remote application or
  rollback.
- Bulk operations have no fleet-wide atomicity or automatic rollback.
- Approved recovery and versioned runbooks support deterministic **staging**
  runtime fixtures only. Production runtime connectors are not provided.
- Runbook steps are not atomic. Tower dispatches each step at most once per claim;
  connectors own idempotency, and timeouts bound Tower's wait, not the connector.
  Partial, timed-out or unknown steps need manual reconciliation. A timeout or
  cancellation is not proof that side effects stopped or rolled back.
- Runbook recovery criteria are fixed, and Chaos/Evals validation records are
  informational rather than an execution gate.
- Emergency stop cannot recall work a runtime already reserved, and restart does
  not renew revoked credentials.

## Investigation and export

- No model is bundled; investigation relies on an MCP host's model and does not
  establish exact causality.
- AIOS investigation-report export is a Python-only, redacted projection. Incident
  closure alone yields unknown recovery, and a cited native verification event is
  not authenticated or recomputed.

## Detection, console and MCP

- Detection is a current-posture scan of the latest observation, every 30
  seconds by default, not a lossless event stream. There is no external
  notification delivery; the alert feed and console are the notification surfaces.
- The console is read-only (GET requests only). Alerts, acknowledgements and the
  incident queue refresh every 30 seconds; inventory refreshes on **Connect /
  refresh**.
- Hosted/remote MCP rejects all `tower.*` tools until per-user Tower credential
  binding is implemented; the connector works only with a local MCP server you
  configure.
