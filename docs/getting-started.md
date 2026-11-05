# Getting started

This page installs Control Tower, reads a sample fleet without a server, then
starts the server with tokens and opens the console.

## Prerequisites

- Python 3.10 or newer (3.10–3.13 are tested in CI).
- Git for the sample files in the repository; 0.8.0 itself is available on PyPI.
- Optional: [uv](https://docs.astral.sh/uv/), which the repository uses for
  development (`make install` runs `uv sync --extra dev`).
- No DeepAgentLabs account, API key or sibling package is needed.

## Install

The base package needs only `pydantic`, `packaging` and `jsonschema`. The `api`
extra adds `fastapi`, `uvicorn` and `httpx` for the HTTP server, the server-mode
CLI and the console.

=== "pip (from the repository)"

    ```bash
    git clone https://github.com/DeepAgentLabs/agenticops-control-tower.git
    cd agenticops-control-tower
    python -m venv .venv && source .venv/bin/activate
    python -m pip install ".[api]"
    ```

=== "uv (from the repository)"

    ```bash
    git clone https://github.com/DeepAgentLabs/agenticops-control-tower.git
    cd agenticops-control-tower
    uv sync --extra api
    # prefix the commands below with `uv run`
    ```

=== "PyPI (0.8.0)"

    ```bash
    python -m pip install "agenticops-control-tower[api]==0.11.0"
    ```

    This includes the snapshot CLI, tokens, SQLite, console, evidence posture
    and live detection. Clone the repository for the example JSON files used below.

Check the installed version:

```bash
python -c "import agenticops_control_tower as t; print(t.__version__)"
```

```text
0.8.0
```

## 1. Read a sample fleet offline (no server)

The repository ships `examples/sample_fleet_snapshot.json`: two agents, their
heartbeats and some pushed evidence. `--snapshot` answers read commands from that
file directly, with no server or token.

```bash
agenticops-control-tower --snapshot examples/sample_fleet_snapshot.json status
```

```json
{
  "total_agents": 2,
  "healthy_agents": 1,
  "degraded_agents": 1,
  "unhealthy_agents": 0,
  "unknown_agents": 0,
  "capability_count": 3,
  "status_buckets": {
    "healthy": ["payment-agent"],
    "degraded": ["support-agent"],
    "unhealthy": [],
    "unknown": []
  },
  "capabilities": [ "... one entry per capability, see below ..." ]
}
```

The `capabilities` list shows coverage. Here `deep-agentic-core-mcp` is installed
on `payment-agent` and missing on `support-agent`:

```json
{
  "capability": "deep-agentic-core-mcp",
  "installed_agents": 1,
  "missing_agents": 1,
  "versions": ["0.2.0"],
  "agent_ids": ["payment-agent"],
  "missing_agent_ids": ["support-agent"]
}
```

Other read commands work the same way: `agents list`, `agents list --unhealthy`,
`agents get payment-agent`, `capabilities list`, `posture`. See the
[CLI reference](cli-reference.md#offline-snapshot-mode).

## 2. Run the server and open the console

Generate a reader and a writer token once per deployment and keep them in your
secret storage ([why and how](authentication.md)):

```bash
export AGENTICOPS_READ_TOKEN="$(python -c 'import secrets; print(secrets.token_hex(32))')"
export AGENTICOPS_WRITE_TOKEN="$(python -c 'import secrets; print(secrets.token_hex(32))')"
agenticops-control-tower serve --database registry.sqlite --host 127.0.0.1 --port 8000
```

Open <http://localhost:8000/console/>, paste the reader token and select
**Connect / refresh**. The fleet is empty until an agent registers.

In a second terminal, use the **same** writer token (exports do not carry over
between terminals) and register the sample agent:

```bash
export AGENTICOPS_TOKEN='paste-your-writer-token'
agenticops-control-tower agents register examples/sample_agent_registration.json
echo '{"status":"healthy","capabilities":{"agenticlens":"0.7.0"}}' > heartbeat.json
agenticops-control-tower agents heartbeat payment-agent heartbeat.json
agenticops-control-tower status
```

Refresh the console to see `payment-agent`. Interactive API docs are at
<http://localhost:8000/docs> (FastAPI).

!!! note "What was run for these docs"
    Steps **Install (version check)** and **1** were run against the 0.8.0
    source on Python 3.13 (Linux). Step **2** needs the `api` extra, which could
    not be installed in the docs verification environment; its commands come from
    the repository README and are exercised by `tests/test_cli.py` and
    `tests/test_http_api.py`. Run them yourself before relying on the exact output.

## Next steps

- Understand the moving parts: [Architecture](architecture.md).
- Configure ports, storage and tokens: [Server settings](settings.md).
- Feed in Lens, Evals, Sidecar and Chaos results:
  [Evidence posture](evidence-posture.md).
- Walk through a complete scenario:
  [Use cases](https://deepagentlabs.io/control-tower/usecases/).
