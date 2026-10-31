# Control Tower examples

## Generate customer-managed tokens and open the console

Install the PyPI package, generate two independent tokens, and run the server
in the same terminal (Bash):

```bash
python -m pip install "agenticops-control-tower[api]"
export AGENTICOPS_READ_TOKEN="$(python -c 'import secrets; print(secrets.token_hex(32))')"
export AGENTICOPS_WRITE_TOKEN="$(python -c 'import secrets; print(secrets.token_hex(32))')"
agenticops-control-tower serve --host 127.0.0.1 --port 8000 --database registry.sqlite
```

Open [http://localhost:8000/console/](http://localhost:8000/console/) and enter the
reader value from this deployment. Customers generate tokens themselves; no
DeepAgentLabs account is needed. Save tokens in secret storage and reuse them
on restart. `openssl rand -hex 32` is another generator; use `python3` if that
is the Python command in your environment.

From a source checkout, `bash examples/run_local_console.sh` starts the same
service after you export the tokens. It reuses credentials and never prints them. Set `AGENTICOPS_PORT` to override
the default port 8000, or `AGENTICOPS_DATABASE` to select another SQLite path.

In another terminal, obtain the same writer value from your secret storage and
set `AGENTICOPS_TOKEN` before registering a sample deployment:

```bash
export AGENTICOPS_TOKEN='your-generated-writer-value'
agenticops-control-tower agents register examples/sample_agent_registration.json
```

Refresh the console to see it. Sample payloads also cover containers and
Kubernetes. The files are in the source checkout; PyPI users can create their own
registration JSON following the README contract.

## Share a hosted console link

Localhost works on the computer running the browser. For remote users deploy the
Python service behind HTTPS and share `https://<your-hostname>/console/` along
with the reader token through a secure channel. Route both the console and API
to the same service. Use [docs/hosting.md](../docs/hosting.md) for cloud startup,
persistent storage, network routing, private SSH tunnels and troubleshooting.
[hosting/nginx.conf](hosting/nginx.conf) is a VM reverse-proxy example, requiring
your own hostname and existing certificates.

## Other examples

- `sample_fleet_snapshot.json`: offline read-only inventory using
  `agenticops-control-tower --snapshot examples/sample_fleet_snapshot.json status`.
- `inspect_ecosystem_evidence.py`: native evidence-reader attribution; see
  [ecosystem alignment](../docs/ecosystem-alignment.md).
- `push_ecosystem_evidence.py`: push the sample producer artifacts through the
  Python API and print per-producer posture.
- `evidence/manifest.json`: native Lens run, Evals report and gate, Sidecar
  decision and Chaos report for `payment-agent`. With a writer token, run
  `agenticops-control-tower evidence ingest-manifest examples/evidence/manifest.json`
  after registering `sample_agent_registration.json`, then
  `agenticops-control-tower posture`. The sample is dated 2026-08-15, so a live
  server reports it as stale; the snapshot below evaluates it as of capture time.
- `sample_fleet_snapshot.json` also carries this evidence:
  `agenticops-control-tower --snapshot examples/sample_fleet_snapshot.json posture`.

See [authentication](../docs/authentication.md) for PowerShell, role semantics,
client variables and rotation.

## v0.4 controlled configuration

See [configuration and approvals](../docs/configuration.md) for Tower ownership, action lifecycle, audit durability and API/CLI usage.
Runtime settings remain mirrored or unsupported without an adapter.

## Approved incident recovery (0.6.0)

`incident_recovery.py` runs the Phase 6/6A deterministic staging scenario through
HTTP routes using native Lens runs and an actual Evals gate. Run with local Lens
and Evals packages as shown in [the guide](../docs/incident-recovery.md); pass
`--fail-verification` to observe escalation. No model provider is required.

## Fleet operations (0.7.0)

`uv run python examples/fleet_operations.py` demonstrates approved bulk desired
configuration with a stale-target partial failure. `bulk_tracing.json` is the
HTTP/CLI preview payload. See [fleet operations](../docs/fleet-operations.md)
for host-installed stop/revoke adapters, audit and interruption handling.

## Live operations (0.8.0)

Run `uv run python examples/live_operations.py` for a standalone native-JSON
demo of detection, deduplication, acknowledgement and joined incident/audit views.
No optional siblings or network required. See [operator guide](../docs/live-operations.md).

## Runbook recovery (0.9.0)

Run `uv run python examples/runbook_recovery.py` for a standalone walkthrough of
the versioned `staging.dependency_recovery` runbook through real HTTP routes:
recommendation, exact preview, separate human approval, bounded drain/restore/resume
steps and evidence-based verification. Pass `--fail-step` to exhaust a clean-failure
retry and observe drain compensation, or `--fail-verification` to observe escalation
after every step succeeded. No optional siblings or network required. See
[runbooks](../docs/runbooks.md).
