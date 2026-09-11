# Pre-Release Checklist

This checklist is for preparing a release candidate or first published
pre-release of `agenticops-control-tower`.

Current target: `v0.2.0`

## Scope Check

- Confirm the version is aligned in:
  - `pyproject.toml`
  - `src/agenticops_control_tower/__init__.py`
  - `CHANGELOG.md`
- Confirm `README.md`, `ROADMAP.md`, and `AGENTS.md` describe the same shipped
  milestone and do not overclaim future surfaces.
- Confirm examples reflect the current milestone behavior:
  - registration payload examples
  - fleet snapshot example
  - CLI command examples

## Quality Gates

Run the full local validation suite:

```bash
make check
```

This must cover:

- `ruff check src tests`
- `ruff format --check src tests`
- `mypy`
- `pytest`

If the environment does not yet have dev dependencies installed:

```bash
make install
make check
```

## Packaging Checks

Build the distribution artifacts:

```bash
make build
```

Expected outputs:

- `dist/*.whl`
- `dist/*.tar.gz`

Validate the built metadata:

```bash
uv run twine check dist/*
```

## CLI Smoke Tests

Verify the published entry point shape before tagging:

```bash
PYTHONPATH=src python3 -m agenticops_control_tower.cli.main --help
PYTHONPATH=src python3 -m agenticops_control_tower.cli.main --snapshot examples/sample_fleet_snapshot.json agents list
PYTHONPATH=src python3 -m agenticops_control_tower.cli.main --snapshot examples/sample_fleet_snapshot.json capabilities list
PYTHONPATH=src python3 -m agenticops_control_tower.cli.main --snapshot examples/sample_fleet_snapshot.json status
PYTHONPATH=src python3 -m agenticops_control_tower.cli.main --snapshot examples/sample_fleet_snapshot.json status support-agent
```

Also verify the installed console script after a local package install if
release confidence needs to be higher:

```bash
uv pip install dist/*.whl
deepagent --help
```

## Release Notes Check

- Confirm the top `CHANGELOG.md` entry matches the actual feature set.
- Confirm the release notes mention the current limitations:
  - no HTTP server yet
  - no web console yet
  - snapshot-backed CLI, not a persistent control-plane service

## Tagging and Publish

Once the tree is clean and checks are green:

```bash
git status --short
git commit -am "release: v0.2.0"
git tag -a v0.2.0 -m "Release v0.2.0"
git push origin main --tags
```

If using a GitHub Release instead of tag-only publishing, use the latest
`CHANGELOG.md` section as the release body.

## Post-Tag Verification

- Confirm the release workflow started.
- Confirm PyPI Trusted Publishing completed successfully.
- Confirm the package page shows version `0.2.0`.
- Confirm installation works from a clean environment.
- Confirm `deepagent --help` works from the published package.

## Known `v0.2.0` Limits

These are expected and should not block release unless the milestone changes:

- in-memory control model only
- no HTTP API server yet
- no read-only console yet
- no write-side operations yet
