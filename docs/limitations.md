# Limitations

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
