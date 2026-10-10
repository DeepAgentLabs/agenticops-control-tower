# Control Tower milestone implementation audit

Verified against the repository on 2026-10-10. This replaces the earlier
scaffold audit, whose missing-method and transport findings are now resolved.

| Milestone | Status | Evidence |
| --- | --- | --- |
| v0.1 Registry and Discovery Core | Implemented locally; merge/release pending | Registry, metadata, heartbeats, capability inventory, five HTTP routes, runtime-agnostic examples, SQLite persistence and reader/writer authorization |
| v0.2 CLI and Status Model | Implemented locally; merge/release pending | Shared StatusService, GET /status, CLI status, environment/status/present/missing capability filters, coverage and version summaries, offline snapshot reads |
| v0.3 Console | Implemented locally; merge/release pending | Packaged `/console/`, authenticated API reads, fleet health/inventory/coverage/details, explicit minimum versions, honest evidence readiness |
| v0.4 Configuration | Planned | No remote configuration writes |
| v0.5 Ecosystem adapters | Partial | Native Lens/Evals/Sidecar/Chaos readers and link contract; remote collection and operator views remain future work |
| v0.6 MCP Connector and Investigation Copilot | Planned | No MCP/copilot implementation yet |
| v0.6.x First Approved Incident-to-Recovery Scenario | Planned | No complete detect/investigate/approve/execute/verify workflow yet |
| v0.7 Multi-Agent Operations | Planned | No bulk operations yet |
| v0.8 Live Detection and Incident Views | Planned | No live incident collection or console timeline yet |
| v0.9 Automated Runbooks and Recovery | Planned | No runbook executor or recovery verifier yet |

Implementation: `registry/service.py`, `discovery/service.py`,
`status/service.py`, `api/surface.py`, `api/http.py`, `cli/main.py`,
`snapshot.py` under `src/agenticops_control_tower/`.

Acceptance tests: `tests/test_registry.py`, `tests/test_http_api.py`,
`tests/test_cli.py`, `tests/test_milestones.py`. Tests cover restart durability,
concurrent heartbeat transactions, detached registry reads, authorization,
unknown-agent errors, filters, coverage, snapshots, and registration examples.

Operational scope: optional SQLite is suitable for a single host with a shared
local database file. Authentication uses deployment-configured reader/writer
bearer tokens, without per-agent identities or tenant isolation. No tokens means
anonymous local development. Health is agent-reported; timeout-based health,
automatic package detection, and distributed storage remain future work.

Validation command: `make check` (lint, formatting, strict typing, tests).

Validation result: `make check` passed 34 base tests (four optional producer
tests skipped without siblings). The full local-sibling run passed all 38 tests,
including real Lens 0.5.0, Evals 0.7.0, Sidecar 0.6.0 and Chaos 0.4.0 artifacts.
Total coverage is 93%, with 100% of evidence reader statements covered.
`make test-ecosystem` reproduces the actual-producer run with local checkouts.
The evidence example preserves BLOCK separately from healthy fleet status.

Wheel/source distribution validation and the live API/CLI restart-persistence
smoke test are also recorded for the combined 0.2.1 change. Implementation is
local; merge and publication remain pending.


v0.3 adds `console/static/`, `models/version.py`, shared
`ControlTowerAPI.assess_versions`, and authorized version/evidence-readiness
reads. The public shell carries no inventory. No write requests, persisted
credentials, incident records or artifact collection are introduced.
`tests/test_console.py` verifies asset serving, authorization, version policy,
missing/invalid versions, environment scoping and unavailable evidence.

v0.3 validation: `make check` passed 43 tests (four optional sibling tests
skipped), with 93% Python coverage. Node/jsdom acceptance checks passed for
rendering, escaping, filters, details, refresh/authentication, error clearing,
disconnect and GET-only requests. Wheel and sdist builds and `twine check`
passed; the wheel contains all three console assets. Visual browser QA was
unavailable in this environment; DOM checks do not verify rendered layout.

Pre-push v0.3 ecosystem validation: `make test-ecosystem` passed all 47 tests
against the local sibling packages, with 94% Python coverage.
