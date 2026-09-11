# Changelog

## [Unreleased]

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
