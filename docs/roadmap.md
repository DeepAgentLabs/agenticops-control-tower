# Roadmap

This page summarizes the repository's
[ROADMAP.md](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/ROADMAP.md),
which is authoritative. Everything on this page that is not marked implemented
is **planned** and does not work today.

## Release status

| Version | Theme | Status |
| --- | --- | --- |
| 0.1–0.2 | Registry, discovery, HTTP API, CLI, status, snapshots, SQLite, tokens | Implemented |
| 0.3 | Read-only AgenticOps Console | Implemented |
| 0.4 | Controlled configuration and approvals | Implemented |
| 0.5 | Ecosystem evidence ingestion and posture | Implemented |
| 0.6 | MCP investigation and approved staging recovery | Implemented |
| 0.7 | Multi-agent operations and bulk actions | Implemented |
| 0.8 | Live detection, alerts, audit trails and incident views | Implemented |
| 0.9 | Automated runbooks and recovery workflows | Implemented (0.9.0 on PyPI) |
| 1.0 | Stable control plane and published capability contract | **Planned** |

## 0.9: automated runbooks (implemented)

- Versioned, immutable runbooks with prerequisites, named string parameters, ordered
  steps, exact-digest human approval, bounded retries and timeouts, and
  compensation or reconciliation.
- Recommendations come only from installed versions, so the copilot cannot invent
  commands or extend an operator's authority.
- Execution and verification after approval, with cancellation, lease-based
  interruption recovery and escalation.
- Chaos scenarios and Evals results can be recorded as validation for a version.

See [runbooks](runbooks.md). Production runtime connectors remain planned.

## 1.0: stable contract (planned)

- A published, stable capability-discovery contract and locked core API semantics.
- Documented runtime and framework integration patterns, with at least two
  materially different runtimes validated end to end.

## Other planned work

From the repository's operational limits:

- Timeout-based health and automatic package detection.
- Pull-based evidence collection and remote configuration application.
- Production runtime connectors for runbooks.
- Distributed storage, per-user identities and tenant isolation.
- Per-user credential binding so the hosted MCP endpoint can offer Tower tools.

## Vision

Detect agent failures → investigate live evidence through MCP → explain
evidence-backed causes → get human approval → run a bounded runbook → verify
recovery. 0.6–0.8 deliver the first loop for one staging runtime; 0.9 makes it
reusable through versioned runbooks.
