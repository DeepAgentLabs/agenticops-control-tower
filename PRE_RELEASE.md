# Pre-Release Checklist

Current target: `v0.9.0`. Keep this checklist aligned with the current API and
release procedure in [AGENTS.md](AGENTS.md#release).

## Scope and metadata

- Match `pyproject.toml`, `src/agenticops_control_tower/__init__.py` and `uv.lock`.
- Use a plain `## 0.9.0` changelog heading with the release date in its body.
- Align README/roadmap with implemented registry, SQLite persistence,
  authenticated API/CLI, controlled configuration approvals, evidence posture and
  read-only console. Evidence posture preserves producer outcomes independently
  of fleet health.
- Pull collection and production remediation remain planned; deterministic staging
  recovery ships with explicit connector installation. Siblings
  remain optional; this release requires no sibling package for Tower startup.

## Phase 6/6A validation

Run the two `examples/incident_recovery.py` paths in `docs/incident-recovery.md`.
Confirm resolved versus escalated, native Lens/Evals sources and no second dispatch.
Test local MCP 0.3.6 tools and hosted credential rejection. Base wheel startup must
not import optional siblings. Confirm `incidents list` and approval rejection.

## Phase 7 validation

Run `uv run python examples/fleet_operations.py`. Confirm deterministic sorted
scope, independent stale-target failure, durable audit/readback and consumed
approval. `tests/test_bulk.py` covers denial/revocation/expiry, changed scope,
concurrency, interrupted claims, actual optional Sidecar runtime, acknowledgement
deadlines and unsupported connectors. See `docs/fleet-operations.md`.

## Phase 8 validation

Run `uv run python examples/live_operations.py` and console DOM checks below.
Verify periodic startup/shutdown, idempotent detection, stale/future evidence,
scoped acknowledgements, append-only lifecycle audit, retained recovery events,
and explicit Lens integrity/coverage status. `tests/test_operations.py` covers
these boundaries. See `docs/live-operations.md` for latest-observation limits.

## Phase 9 validation

Run `uv run python examples/runbook_recovery.py` with no flag, `--fail-step` and
`--fail-verification`; expect `resolved`, `escalated` with drain compensation, and
`escalated` after verification. `tests/test_runbooks.py` covers denied, revoked,
expired, self and out-of-scope approvals, changed environment/catalog/connector,
timeouts, partial and raised steps, failed rollback, concurrent execute,
cancellation, lease reconciliation across a restart, validation and HTTP/CLI
parity. Check MCP 0.5.1 `tower.runbook*` tools against a local server and that no
MCP tool approves. See `docs/runbooks.md`.

## Validation

```bash
make check
make test-ecosystem-published
NODE_PATH=/tmp/tower-console-qa/node_modules node tests/console_ui.cjs
uv run python -m build --outdir /tmp/tower-0.9.0-dist
uv run twine check /tmp/tower-0.9.0-dist/*
# Install and test the built wheel outside the editable checkout.
tower_checkout="$PWD"
tower_smoke_dir="$(mktemp -d)"
uv venv "$tower_smoke_dir/venv"
uv pip install --python "$tower_smoke_dir/venv/bin/python" "/tmp/tower-0.9.0-dist/agenticops_control_tower-0.9.0-py3-none-any.whl[api]"
cd "$tower_smoke_dir"
"$tower_smoke_dir/venv/bin/agenticops-control-tower" --help
"$tower_smoke_dir/venv/bin/agenticops-control-tower" --snapshot "$tower_checkout/examples/sample_fleet_snapshot.json" agents list
"$tower_smoke_dir/venv/bin/agenticops-control-tower" --snapshot "$tower_checkout/examples/sample_fleet_snapshot.json" capabilities list
"$tower_smoke_dir/venv/bin/agenticops-control-tower" --snapshot "$tower_checkout/examples/sample_fleet_snapshot.json" status
"$tower_smoke_dir/venv/bin/agenticops-control-tower" --snapshot "$tower_checkout/examples/sample_fleet_snapshot.json" posture
"$tower_smoke_dir/venv/bin/python" - <<'PY'
from importlib.resources import files
from agenticops_control_tower import __version__
from agenticops_control_tower.adapters import summarize_evidence
from agenticops_control_tower.models.evidence import EvidenceLink
assert __version__ == "0.9.0"
assert files("agenticops_control_tower.console").joinpath("static/index.html").is_file()
link = EvidenceLink(agent_id="smoke", source="agentic-sidecar", source_version="0.7.0",
                    artifact_type="decision", artifact_ref="decision:smoke",
                    observed_at="2026-10-12T00:00:00Z")
result = summarize_evidence(link, {"decision_id": "smoke", "status": "PAUSE",
                                   "risk": "HIGH", "reason": "release smoke"})
assert result.availability == "available"
assert result.details["decision_id"] == "smoke"
from agenticops_control_tower.evidence import EvidenceStore, PostureService
from agenticops_control_tower.models import AgentRegistrationPayload, EvidenceIngestRequest
from agenticops_control_tower.registry import AgentRegistry
registry = AgentRegistry()
registry.register(AgentRegistrationPayload(agent_id="smoke", name="smoke", environment="test",
                                           runtime="custom", framework="custom"))
store = EvidenceStore(registry)
store.ingest(EvidenceIngestRequest(link=link, artifact={"status": "PAUSE", "risk": None,
                                                         "reason": "release smoke"}))
posture = PostureService(store).agent(registry.get("smoke"), now=link.observed_at)
assert {s.source: s.freshness for s in posture.sources}["agentic-sidecar"] == "fresh"
PY
cd "$tower_checkout"
```

Verify wheel/sdist name and version metadata, installed entry point, and packaged
console assets. The CLI/API need the optional `api` extra; base Python evidence
readers and the evidence store remain standalone. Missing optional producer tests
skip honestly; `make test-ecosystem-published` runs them against the published
sibling extras.

## Tag and publish

Prepare version/changelog changes on a branch, merge the reviewed PR, then tag
that merge commit. Extract the matching changelog section into a temporary file:

```bash
uv run python - <<'PY'
from pathlib import Path
text = Path("CHANGELOG.md").read_text()
section = text.split("## 0.9.0\n", 1)[1].split("\n## ", 1)[0].strip()
Path("/tmp/tower-0.9.0-release-notes.md").write_text(section + "\n")
PY
git tag -a v0.9.0 -F /tmp/tower-0.9.0-release-notes.md --cleanup=verbatim
git push origin v0.9.0
```

The release workflow builds artifacts, publishes to PyPI through Trusted
Publishing and creates the GitHub release using the same changelog section.
Do not manually create a second release or publish unrelated tags.

## Post-publication

- Confirm publishing and GitHub release jobs succeeded.
- Verify both wheel and source distribution on PyPI.
- Install `agenticops-control-tower[api]==0.9.0` in a fresh environment and smoke
  the CLI/offline snapshot posture, native evidence reader and evidence store.
