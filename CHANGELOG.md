# Changelog

## [Unreleased]

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
