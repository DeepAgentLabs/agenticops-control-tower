# agenticops-control-tower roadmap implementation audit

Audit date: 2026-09-11. Baseline: commit `664905b8b019e3f220795a98ca83c184165fc9e1`
(working tree clean at audit time). Scope: [ROADMAP.md](ROADMAP.md), its Release
Status table, Phase 0 checkboxes, and the milestone build order (v0.1-v1.0), cross
checked against the actual repository tree, `AGENTS.md`, `README.md`,
`CHANGELOG.md`, `CI.md`, and `DeepAgent-Control-Tower-Concept.md`
(`DeepAgent-Control-Tower-Concept.md` is the file referenced elsewhere as the
"concept document"; there is no separate `DeepAgent Control Tower End-to-End
Concept.md`).

**The roadmap's headline claim ("nothing has shipped yet... concept document,
this roadmap, and the README only") is stale.** A small but real, tested,
CI-wired Python package exists under `src/agenticops_control_tower/`. It does
not contradict the roadmap's milestone status (v0.1-v1.0 are still correctly
unshipped as usable product surfaces), but the repository is no longer
docs-only, and `ROADMAP.md`/`README.md` should say so precisely instead of
overstating the gap in the other direction.

## Implementation follow-up (post-audit)

The baseline findings below (v0.1 "no HTTP-reachable API", v0.2 "Missing as a
usable surface") described the state at the audit's commit
`664905b8b019e3f220795a98ca83c184165fc9e1`. A subsequent change closed both
gaps: `api/http.py` now exposes the roadmap's full "Suggested initial
surface" as real FastAPI endpoints (optional `api` extra), `cli/main.py` is a
real argparse-based CLI (`agenticops-control-tower` console script) talking
to that API over HTTP, and a second example registration payload
(`examples/sample_agent_registration_kubernetes.json`) closes the "at least
two runtime styles" gap. Persistence across restarts and authentication/
authorization remain open — see the updated v0.1/v0.2 sections below.
Verified with a real `uv run pytest` (not hand-traced, unlike the original
audit below, which had no working Python toolchain): **10 passed**, plus
`ruff check`, `ruff format --check`, and `mypy --strict` all clean, and
`python -m build` + `twine check` both pass.

## How to read this audit

- **Implemented (I):** usable code exists for the stated scope; evidence and
  limits are recorded below. This does not assert publication, PyPI release,
  or independent validation.
- **Partial (P):** a subset, placeholder, or narrower related capability
  exists (e.g., a Python facade where the roadmap text describes an HTTP API).
- **Missing (M):** no implementation of the stated capability was found.
- **Unverified (U):** a claim about a sibling repository or ecosystem
  coordination that cannot be checked from inside this repository.

## Milestone summary

| Milestone | Assessment | Main open work |
| --- | --- | --- |
| Phase 0 Concept and Product Boundary | Implemented | Concept doc, README, ROADMAP, and a real (if minimal) implementation scaffold all exist |
| v0.1 Registry and Discovery Core | Partial — HTTP API and second example now shipped (post-audit) | Registry/heartbeat/discovery/API facade plus a real HTTP API (`api/http.py`, optional `api` extra) and two example runtime-style payloads; still no persistence, no auth |
| v0.2 CLI and Status Model | Partial — CLI now shipped (post-audit) | `agenticops-control-tower` console script (`agents register/heartbeat/list/get`, `capabilities list`) talks to the HTTP API; no health rollups or unhealthy/missing-capability filters (`status` command) yet |
| v0.3 Read-Only Console | Missing as a usable surface | `console/app.py` is a one-function placeholder; no dashboard |
| v0.4 Configuration and Safe Write Operations | Missing as a usable surface | `config/models.py` defines two empty Pydantic shapes only; no write path, no audit |
| v0.5 Ecosystem Surface Integration | Missing | `adapters/catalog.py` is a tuple of four sibling package names; no adapter logic |
| v0.6 Agentic MCP Connector | Missing | No MCP-facing code found |
| v0.7 Multi-Agent Operations | Missing | No bulk/fleet operation code found |
| v0.8 Alerts, Audit, and Incident Views | Missing | No alerting/audit code found |
| v1.0 Stable Capability Contract | Missing | No stability/versioning contract beyond the `0.0.1` package version |

## Evidence index

Paths are relative to this repository.

| Key | Source | Test evidence |
| --- | --- | --- |
| MODELS | [agent models](src/agenticops_control_tower/models/agent.py) | [test_imports.py](tests/test_imports.py), [test_registry.py](tests/test_registry.py) |
| REGISTRY | [registry service](src/agenticops_control_tower/registry/service.py) | [test_registry.py](tests/test_registry.py) |
| DISCOVERY | [discovery service](src/agenticops_control_tower/discovery/service.py) | [test_registry.py](tests/test_registry.py) |
| API | [API facade](src/agenticops_control_tower/api/surface.py) | [test_registry.py](tests/test_registry.py), [test_imports.py](tests/test_imports.py) |
| HTTP | [HTTP API](src/agenticops_control_tower/api/http.py) (optional `api` extra) | [test_http_api.py](tests/test_http_api.py) (`pytest.importorskip`-guarded) |
| CLI | [CLI](src/agenticops_control_tower/cli/main.py) (optional `api` extra) | [test_cli.py](tests/test_cli.py), [test_imports.py](tests/test_imports.py) |
| CONSOLE | [console placeholder](src/agenticops_control_tower/console/app.py) | [test_imports.py](tests/test_imports.py) (import + string-return smoke check only) |
| CONFIG | [config models](src/agenticops_control_tower/config/models.py) | none |
| ADAPTERS | [adapter name catalog](src/agenticops_control_tower/adapters/catalog.py) | [test_imports.py](tests/test_imports.py) (membership check only) |
| CI | [CI workflow](.github/workflows/ci.yml), [release workflow](.github/workflows/release-pypi.yml) | Runs ruff, mypy, pytest, and a build/twine check across Python 3.10-3.13 on push/PR |
| EXAMPLE | [sample registration payload](examples/sample_agent_registration.json) | Matches `AgentRecord`/capability shape by inspection; no schema-validation test found |

## Phase 0: Concept and Product Boundary

| Roadmap deliverable | Status | Evidence / remaining boundary |
| --- | --- | --- |
| Architecture concept document | I | [DeepAgent-Control-Tower-Concept.md](DeepAgent-Control-Tower-Concept.md) exists and matches the "OPERATE" positioning referenced elsewhere |
| `README.md` | I | Present, but see correction below: its "no package code" line is now inaccurate |
| `ROADMAP.md` | I | Present; this audit corrects its stale opening claim |
| Implementation scaffold | I | `pyproject.toml`, `src/agenticops_control_tower/` (8 submodules), `tests/` (2 files), `Makefile`, `.github/workflows/` (CI + release), `docs/architecture.md`, `CHANGELOG.md`, `CI.md` all exist and are committed (see commits `4ea7758` and `4216cef`) |

All four Phase 0 checkboxes in `ROADMAP.md` are accurate as currently checked;
no correction was needed there.

## v0.1 Registry and Discovery Core

| Roadmap deliverable | Status | Evidence / remaining boundary |
| --- | --- | --- |
| Minimal agent registry | P | `AgentRegistry` is a plain in-memory `dict[str, AgentRecord]` (REGISTRY); no persistence, concurrency handling, or restart durability |
| Explicit registration and heartbeats | P | `register()` and `heartbeat()` methods exist and are exercised by a test, but there is no transport (no HTTP/RPC layer) — only a Python method call |
| Runtime/framework/environment/capability metadata | I | `AgentRecord` (MODELS) carries `environment`, `runtime`, `framework`, `capabilities: dict[str, str]`, `status`, `last_seen` |
| Read-only API for listing agents/capabilities | I | `ControlTowerAPI` (API) is a synchronous Python facade (`list_agents`, `get_agent`, `list_capabilities`, plus `register`/`heartbeat`/`list_all_capabilities` added for the HTTP layer); `api/http.py` (HTTP, optional `api` extra) now exposes it as real `GET`/`POST` routes |
| Suggested surface: `POST /agents/register`, `POST /agents/{id}/heartbeat`, `GET /agents`, `GET /agents/{id}`, `GET /capabilities` | I | All five implemented in [api/http.py](src/agenticops_control_tower/api/http.py) as FastAPI routes, covered by [test_http_api.py](tests/test_http_api.py); `GET /capabilities` aggregates capability versions across every registered agent, since the roadmap text doesn't specify per-agent vs. fleet-wide scope |
| Example registration payloads for at least two runtime styles | I | [examples/sample_agent_registration.json](examples/sample_agent_registration.json) (`aws-lambda`/`langgraph`) and [examples/sample_agent_registration_kubernetes.json](examples/sample_agent_registration_kubernetes.json) (`kubernetes`/`crewai`) now cover two distinct runtime styles, matching `AgentRecord`'s shape by inspection; still no schema-validation test loads either file |
| Works without assuming Kubernetes/Docker/one framework | I | Nothing in the current code assumes a runtime; `runtime`/`framework` are free-text strings |

Acceptance: the HTTP API and CLI are real, tested, network-reachable code, not
a Python-only facade — `POST /agents/register` then `agents list` from a
*separate* process against a running `agenticops-control-tower serve`
was smoke-tested end to end (see Implementation follow-up above). Still open:
no persistence across restarts (an in-memory `dict` resets on every server
restart) and no authentication/authorization on any endpoint.

## v0.2 CLI and Status Model

| Roadmap deliverable | Status | Evidence / remaining boundary |
| --- | --- | --- |
| First operator CLI | I | `agenticops-control-tower` console script ([cli/main.py](src/agenticops_control_tower/cli/main.py)); requires the optional `api` extra for `httpx`/`uvicorn` |
| `agents list` / `agents get <id>` / `capabilities list` | I | Implemented exactly as named (not under a `deepagent` binary — no such binary exists anywhere in this ecosystem; roadmap text names one that was never built) |
| `status` (health rollup) | M | Not implemented — no command, no health-rollup computation |
| Health rollups and version-inventory summaries | M | No aggregation beyond `GET /capabilities`'s per-capability version list; no "unhealthy agents" or "agents missing a capability" filter |
| CLI and API share the same underlying control model | I | The CLI is an `httpx` client of `api/http.py`'s routes, which wrap the same `ControlTowerAPI` facade exercised directly by [test_registry.py](tests/test_registry.py) |

Acceptance: the CLI genuinely talks to a running server over real HTTP (not
an in-process shortcut) — verified with both `pytest`'s `TestClient`-backed
tests and a manual `serve` + CLI session against a real socket. Health
rollups and status filters (the other half of the v0.2 goals) remain open.

## v0.3 through v1.0

All deliverables for v0.3 (console), v0.4 (configuration write paths), v0.5
(ecosystem adapters), v0.6 (MCP connector), v0.7 (multi-agent bulk
operations), v0.8 (alerts/audit/incident views), and v1.0 (stable contract)
remain **Missing** as usable product surfaces:

- `console/app.py` exports one function, `console_status() -> str`, returning
  a fixed string. No web framework, templates, or static assets exist.
- `config/models.py` defines `ConfigScope` and `ConfigPatch` as empty
  Pydantic shapes with no read/write logic, no validation beyond typing, and
  no caller anywhere in the source tree.
- `adapters/catalog.py` defines `ADAPTER_NAMES`, a 4-tuple of sibling package
  name strings. There is no adapter interface, no network/import bridge to
  `agenticlens`, `agentic-sidecar`, `agentic-chaos`, or
  `deep-agentic-core-mcp`, and none of those packages are runtime
  dependencies (they only appear as `pyproject.toml` optional extras that pin
  version floors, e.g. `agenticlens>=0.1.3`, without any code importing them).
- No MCP server/client code, bulk-operation code, alerting code, audit-log
  code, or versioned-contract code was found anywhere in `src/` or `tests/`.

This is consistent with `ROADMAP.md` correctly marking v0.3-v1.0 as
🚧 Planned.

## Cross-project dependency claims

The "Cross-Project Dependencies" section of `ROADMAP.md` describes future
coordination with `agenticlens`, `agentic-sidecar`, `agentic-chaos`,
`mcp-server` (`deep-agentic-core-mcp`), and `ai-operations-spec`. None of this
is checkable from inside this repository:

| Claim | Status | Note |
| --- | --- | --- |
| Coordinate with `agenticlens` on summarized observability signals | U | No code in this repo reads from `agenticlens`; sibling repo not audited here |
| Coordinate with `agentic-sidecar` on governance/risk signals | U | No code in this repo reads from `agentic-sidecar` |
| Coordinate with `agentic-chaos` on experiment/resilience summaries | U | No code in this repo reads from `agentic-chaos` |
| Validate MCP-facing path against `mcp-server` | U | No MCP code exists yet in this repo to validate |
| Coordinate with `ai-operations-spec` on shared contracts | U | No AIOS schema import, validation, or reference found in this repo |

These are marked Unverified rather than Missing because they are framed in
`ROADMAP.md` as future coordination commitments, not present-tense claims
about this repository's current code.

## Verification and uncovered acceptance risks

**Original audit baseline** (kept for the record): no Python interpreter or
`uv` toolchain was available in that audit's execution sandbox, so
`uv run pytest` could not be executed; both test files were read in full and
traced by hand against the corresponding source, and CI wiring was inspected
rather than re-run.

**Post-audit implementation session**: `uv` was installed fresh and the real
suite was run: `uv run pytest -q` -> **10 passed** (`test_registry.py`,
`test_imports.py`, `test_http_api.py`, `test_cli.py`, the last two guarded by
`pytest.importorskip("httpx")`/`pytest.importorskip("fastapi")` and exercised
with the `dev` extra, which now includes `fastapi`/`httpx`/`uvicorn`). Also
ran clean: `uv run ruff check src tests`, `uv run ruff format --check src
tests`, `uv run mypy` (strict), and `uv run python -m build` +
`python -m twine check dist/*`. A manual end-to-end smoke test (`serve` in
one process, the CLI as a separate process against a real TCP socket on
`127.0.0.1`) exercised register -> heartbeat -> list -> capabilities and
matched the automated tests' expectations.

Still unverified: persistence and auth remain intentionally out of scope
(not yet built); no independent/non-DeepAgentLabs consumer of the HTTP API
has been tried; load, concurrency, and multi-client behavior are untested.

All relative links above were checked against the actual repository tree and
resolve to real files.

## Recommended next step

v0.1's HTTP API and v0.2's CLI are the two items this audit previously
flagged as blocking "Implemented" status for those milestones, and both are
now closed. The next gaps to close, in the order the roadmap's own Design
Constraints imply (read-only/inventory before write-capable, API/CLI before
dashboard):

1. Persistence beyond an in-process `dict` — the registry resets on every
   `serve` restart, which is the main remaining v0.1 gap.
2. `agents list --unhealthy` / "missing capability" filters and a `status`
   health-rollup command — the other half of v0.2's stated goals.
3. Only then v0.3's read-only console, per Design Constraint 3 ("API and CLI
   before dashboard").
