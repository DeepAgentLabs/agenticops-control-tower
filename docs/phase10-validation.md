# Phase 10 validation record

Validated 2026-11-04 for Tower 0.10.0. Stable ecosystem acceptance remains open.

| Gate | Result |
| --- | --- |
| `make check` | Ruff, format, strict mypy and 312 tests pass |
| `make test-ecosystem-published` | 312 pass with published optional siblings |
| CPython / Node.js authenticated HTTP | Both real clients register, heartbeat and read inventory; SQLite restart preserves both |
| Candidate schemas | JSON Schema validation and checked-in descriptor snapshot pass |
| Console DOM suite | Rendering, escaping, filters, evidence and runbook views pass |
| Build and Twine | Wheel and sdist validate |
| Isolated wheel without API extra | Version, facade discovery and packaged console resources pass |
| Isolated wheel with API extra | Offline snapshot posture CLI passes |
| Strict MkDocs | Documentation builds successfully |

Sibling documentation gates also pass: Chaos 732 tests, Evals 403, Sidecar 529,
Lens 835, MCP 372 and AIOS schema checks. Optional provider SDK, MCP and
PostgreSQL checks skip where the local dependency/service is unavailable;
GitHub CI supplies additional integration environments. Documentation-only
siblings need no release. CI and first Copilot review must complete on the PRs
before merging; package publication is verified after the merge/tag workflow.

These checks establish control-plane inventory compatibility. They do not
validate production runtime connectors, independent AIOS conformance or the
coordinated v1.0 stable freeze.
