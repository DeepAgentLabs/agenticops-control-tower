## agenticops-control-tower Development Reference

## Ecosystem Context

### Role in DeepAgentLabs

`agenticops-control-tower` is the operations and control-plane layer in the
DeepAgentLabs ecosystem. Its job is to centralize inventory, visibility,
configuration, and operator workflows across many deployed agents and many
DeepAgentLabs capabilities.

### Owns

- Agent registry, heartbeat, and fleet-inventory concerns
- Capability discovery and version/status visibility across deployed agents
- The unified control-plane API, CLI, and future console surface
- Thin ecosystem adapters that summarize sibling-package posture without
  re-implementing sibling-package logic

### Does Not Own

- The canonical operational schema or shared normative object model — that
  belongs in `ai-operations-spec`
- Core observability, profiling, evaluation, or recommendation logic — that
  belongs in `agenticlens`
- Fault injection and resilience-testing logic — that belongs in
  `agentic-chaos`
- Decision-time supervision/governance or pre-action intervention logic — that
  belongs in `agentic-sidecar`
- The MCP-native access surface itself — that belongs in
  `deep-agentic-core-mcp`, even when it later connects to Control Tower

### Integrates With

- `ai-operations-spec` for shared terminology and any ecosystem-facing
  inventory, status, or configuration contracts
- `agenticlens` when Control Tower needs summarized observability or readiness
  posture
- `agentic-sidecar` when Control Tower needs summarized supervision/governance
  or risk posture
- `agentic-chaos` when Control Tower needs summarized experiment or resilience
  posture
- `deep-agentic-core-mcp` when the control plane is later exposed to AI
  operators through MCP

### Current Roadmap Focus

The current build focus is the completed v0.2 CLI and status model. Work in
this repo should now strengthen operator inventory views, shared status
semantics, and the console-ready read surface before attempting write-side
orchestration or bulk actions.

### Before You Build Here

- Ask whether the feature is about operator control and fleet visibility; if it
  is really analysis, governance, chaos execution, or MCP exposure, it may
  belong in a sibling repo instead
- Keep adapters thin and contract-driven; do not copy implementation logic from
  Lens, Sidecar, Chaos, or MCP into this package
- Build read-only inventory and status first; avoid jumping ahead to write-side
  orchestration without the underlying control model in place

## Status

This repository is a **pre-alpha implementation**. Package layout, docs,
tests, and CI/release workflows exist, along with an in-memory registry,
discovery, status, and CLI surface through `v0.2`. See [ROADMAP.md](ROADMAP.md)
for the remaining build order.

## Build and Run

- Install: `make install` (runs `uv sync --extra dev`)
- Test: `make test` or `make check` (lint + format + typecheck + test)
- Lint: `make lint`
- Type check: `make typecheck`
- CLI: `deepagent ...`

## Code Style

- Strict typing (mypy strict mode, Python 3.10+)
- Line length: 100
- Ruff rules: E, F, I, UP, B, SIM, N
- One purpose per file (separation of concerns)
- Control-plane artifacts should stay compatible with ecosystem-wide contract
  work once those shapes are formalized

## Design Constraints

These are load-bearing, not preferences — see
[ROADMAP.md](ROADMAP.md#design-constraints) for the full rationale:

1. **Inventory before orchestration.** v0.1 should answer what exists and what
   is installed before attempting remote change or fleet-wide mutation.
2. **Read-only before write-capable.** Registration, discovery, and status must
   be trustworthy before configuration or operations fan out across agents.
3. **API and CLI before dashboard.** The console should sit on the same control
   model, not become the hidden place where the real behavior lives.
4. **Adapters stay thin.** `adapters/` should summarize or bridge, not own
   Lens, Sidecar, Chaos, or MCP behavior.
5. **Runtime agnostic means no early runtime lock-in.** Do not quietly design
   the first release around one cloud, one orchestrator, or one framework.
6. **MCP comes after the control API.** AI-native access is valuable, but it
   should connect to a real control plane rather than a concept-only surface.

## Repo Map

| Path | Purpose | Planned version |
|------|---------|------------------|
| `src/agenticops_control_tower/models/` | Shared inventory and status models | v0.1 |
| `src/agenticops_control_tower/registry/` | Agent registration, heartbeat, and inventory state | v0.1 |
| `src/agenticops_control_tower/discovery/` | Capability discovery and normalization | v0.1 |
| `src/agenticops_control_tower/api/` | Unified read-only control-plane API surface | v0.1-v0.2 |
| `src/agenticops_control_tower/cli/` | Operator CLI | v0.2 |
| `src/agenticops_control_tower/status/` | Shared fleet and agent status rollups | v0.2 |
| `src/agenticops_control_tower/console/` | AgenticOps Console / dashboard | v0.3 |
| `src/agenticops_control_tower/config/` | Central configuration models and safe write paths | v0.4 |
| `src/agenticops_control_tower/adapters/` | Thin ecosystem adapters to sibling projects and MCP | v0.5+ |
| `examples/` | Sample registration and capability payloads | ongoing |
| `tests/` | Pytest test suite | ongoing |
| `Makefile` | Local dev automation | — |

Full architecture and build order: [ROADMAP.md](ROADMAP.md).

## Entry Points

- Python API: read-only control surface through `api/`
- CLI: `deepagent ...`
- Console: AgenticOps Console (planned in v0.3)

## Package Boundaries

- This package should stay **standalone** — `pip install
  agenticops-control-tower` must work without requiring any other
  DeepAgentLabs package
- Sibling integrations must remain optional and degrade honestly when the
  sibling package is unavailable
- `api/` may depend on `registry/` and `discovery/`; the reverse should not be
  true
- `models/` must not import from adapters or UI layers
- `console/` should consume the same underlying control model as `api/` and
  `cli/`, not invent a parallel one

## Adding a New Control-Plane Surface

1. Confirm the feature belongs to operator control, inventory, configuration,
   or fleet visibility rather than to a sibling runtime
2. Add or update the shared model first if the feature changes inventory or
   status meaning
3. Add tests covering the read path before adding any write path
4. Update `README.md` and `ROADMAP.md` if the feature changes milestone scope

## Feature Completion Expectations

- Every behavior change must include tests
- User-facing features must include or update examples in `README.md`,
  `examples/`, or docs
- When a roadmap item or milestone meaningfully changes status, update
  `README.md` and `ROADMAP.md` in the same change
- If that milestone or release changes the public ecosystem story, also update
  `/home/pramodbn27/PyPi Projects/.github/profile/README.md` and, when
  relevant, `/home/pramodbn27/PyPi Projects/.github/profile/ROADMAP.md`
- When work is packaged as a release-ready change, also update
  `pyproject.toml`, `src/agenticops_control_tower/__init__.py`, and
  `CHANGELOG.md`

## Pre-push Checklist

Run `make check` before every push. It runs: lint -> format-check -> typecheck
-> test.

## Pre-release Checklist

Use [PRE_RELEASE.md](PRE_RELEASE.md) before tagging or publishing.

## Release

Two phases, split by the merge to `main` — bumping happens before, and the
tag-driven release automation happens after. Run the [Pre-release
Checklist](#pre-release-checklist) above first.

**1. Pre-release (on the feature branch, before merge):** Bump version in
`pyproject.toml`, `src/agenticops_control_tower/__init__.py`, and
`CHANGELOG.md` (a dated release section under `[Unreleased]`). Commit as
part of the branch's normal history; goes in with the rest of the PR.

**2. Release (on `main`, once that branch has merged):** plain `git`, no
manual `gh release` step required.

1. Pull the merge commit on `main`.
2. Tag: create an annotated `vX.Y.Z` tag pointing at the merge commit,
   using the `CHANGELOG.md` release section for that version as the tag
   message:
   `git tag -a vX.Y.Z -F <file-with-that-section> --cleanup=verbatim`.
   `--cleanup=verbatim` is required — git's default cleanup silently strips
   lines starting with `#`, which would eat the changelog's `###` headers.
3. Push the tag: `git push origin vX.Y.Z`.

That tag push is the release trigger. `release-pypi.yml` runs automatically
and does both of the following from the same tag:

- publishes the package to PyPI via Trusted Publishing (OIDC)
- creates the GitHub Release object for `vX.Y.Z`

The GitHub Release title is the tag name, and its body is copied from the
matching `CHANGELOG.md` section so the changelog, tag, PyPI release, and
GitHub Releases page stay aligned.
