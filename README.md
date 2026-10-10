# agenticops-control-tower

**An AI-native operations command center and unified control plane for autonomous agents and the DeepAgentLabs ecosystem.**

> AgenticLens observes. Agentic Evals evaluates. Agentic Sidecar supervises. Agentic Chaos tests. Agentic
> MCP connects. Control Tower operates.

## Status

**v0.1–v0.3 implemented; release publication is separate.** The registry,
HTTP API and CLI support SQLite persistence, reader/writer bearer authorization,
shared fleet health and capability coverage, agent filters, and offline snapshots.
The read-only web console is served at `/console/`. See [ROADMAP_AUDIT.md](ROADMAP_AUDIT.md)
for milestone evidence and [ROADMAP.md](ROADMAP.md) for the build plan.

## Read-only console (v0.3)

Run `agenticops-control-tower serve --database registry.sqlite --port 8000`,
then open **http://localhost:8000/console/**. The `api` extra includes the
console; no Node build or separate UI server is required.

Enter the server's reader token and select **Connect / refresh** (leave it blank
for anonymous local development). The console shows reported fleet health,
searchable/filterable inventory, environment-scoped capability coverage,
versions, heartbeat timestamps and agent metadata. Select a capability and enter
an optional minimum version to identify outdated installations using PEP 440;
missing capabilities and invalid reported versions remain distinct. This minimum
is your policy, not an inferred latest release. Refresh is manual.

Select an agent to inspect details and incident/evidence readiness. Evidence is
currently unavailable because the service does not collect or persist artifacts;
native readers remain accessible through the Python API. Incident detection,
RCA, approval and remediation are planned.

The public HTML shell contains no fleet data. Every data request uses the same
reader/writer bearer authorization as API and CLI reads. Credentials are retained
only in page memory, cleared by **Disconnect** or page reload; failed refreshes
clear the displayed inventory. Use HTTPS when serving bearer-authenticated
traffic remotely. The console sends only GET requests.

Additional read endpoints: `GET /versions?capability=agenticlens&minimum_version=0.5.0`
(optionally `environment=staging`) and `GET /agents/{agent_id}/evidence` (readiness,
not artifact contents). Version policy is also available as
`ControlTowerAPI.assess_versions(capability, minimum_version, environment=...)`.

## Generate access tokens and host your console

Customers self-hosting this PyPI package generate and manage their own tokens;
no DeepAgentLabs account or token service is needed. Generate a reader value
with Python's standard library (Bash):

```bash
export AGENTICOPS_READ_TOKEN="$(python -c 'import secrets; print(secrets.token_hex(32))')"
```

Alternatively use `openssl rand -hex 32`; use `python3` if that is your Python
command. Configure a separate `AGENTICOPS_WRITE_TOKEN` for registration and
heartbeats. Save both in secret storage and reuse them when restarting the server.
Users paste the reader value into the console and select **Connect / refresh**.
These are shared deployment credentials, not user accounts. With only a reader
configured, writes are rejected; with neither token configured, access is anonymous.

- [Authentication guide](docs/authentication.md): generation, PowerShell setup,
  reader/writer roles, CLI access and rotation.
- [Hosting guide](docs/hosting.md): local `http://localhost:8000/console/`,
  private-network access and cloud `https://<your-hostname>/console/` links.
- [Examples](examples/README.md): local startup and an HTTPS reverse-proxy template.

The console and API run in the same Python service. Cloud deployments need
HTTPS ingress, configured tokens and persistent storage for durable inventory.
Installing from PyPI alone does not create a hosted URL. Localhost links work
only on the computer running the browser.

## Command-center vision

The intended workflow is **detect failure → investigate with live evidence →
explain the cause → recommend remediation → obtain human approval → execute a
runbook → verify recovery**. An operations copilot uses MCP tools to correlate
Lens traces, tool calls, prompt versions, dependencies and sibling evidence.
Diagnoses cite evidence and distinguish confirmed causes from hypotheses.
Tower owns incident coordination; the sibling packages retain their engines.

This full loop is planned, not implemented. The roadmap introduces the first
approved staging scenario in v0.6.x, broader live incident views in v0.8 and
reusable automated runbooks in v0.9. See [the command-center roadmap](ROADMAP.md#product-vision-ai-native-operations-command-center).

## Quickstart

```bash
pip install agenticops-control-tower[api]   # fastapi/uvicorn/httpx for the HTTP API + CLI

# Customers generate their own tokens. Save and reuse these values on restart.
export AGENTICOPS_READ_TOKEN="$(python -c 'import secrets; print(secrets.token_hex(32))')"
export AGENTICOPS_WRITE_TOKEN="$(python -c 'import secrets; print(secrets.token_hex(32))')"
export AGENTICOPS_TOKEN="$AGENTICOPS_WRITE_TOKEN"

# Terminal 1: durable registry (file survives server restarts)
agenticops-control-tower serve --database registry.sqlite --port 8000

# Terminal 2: obtain the SAME writer token from your deployment's secret storage.
# Exports in Terminal 1 are not automatically available in Terminal 2.
export AGENTICOPS_TOKEN='paste-your-generated-writer-token-here'
# Register an agent, send a heartbeat, and inspect the fleet
agenticops-control-tower agents register examples/sample_agent_registration.json
echo '{"status":"healthy","capabilities":{"agenticlens":"0.5.0"}}' > heartbeat.json
agenticops-control-tower agents heartbeat payment-agent heartbeat.json
agenticops-control-tower agents list
agenticops-control-tower capabilities list
agenticops-control-tower status
agenticops-control-tower agents list --unhealthy
agenticops-control-tower agents list --environment staging --missing-capability agentic-sidecar
agenticops-control-tower --snapshot examples/sample_fleet_snapshot.json status
```

`AGENTICOPS_TOKEN` authenticates the CLI. Reader tokens permit GET routes;
writer tokens permit reads, registration and heartbeats. With only a reader
token configured, writes are rejected. With no server tokens configured, access
is anonymous for local development. `AGENTICOPS_DATABASE` also selects SQLite
storage; omit it and `--database` for in-memory mode.

Health rollups count agent-reported `healthy`, `degraded`, `unhealthy`, and
`unknown` states. They do not infer failures from heartbeat age. Capability
versions are reported inventory, not an upgrade recommendation. New agent IDs
must start with an ASCII letter or digit and contain only ASCII letters, digits,
dots, underscores and hyphens (e.g. `payment-agent_1.0`).
Slashes, percent escapes, whitespace and dot-only IDs are rejected by registration
and snapshot validation. Use the free-form `name` field for display labels.
Existing stored records are not renamed automatically. Re-registering
an ID replaces its record; heartbeats merge metadata and increment its count.

Without the `api` extra, `pip install agenticops-control-tower` still gives
you the underlying Python control model (`ControlTowerAPI`, `AgentRegistry`,
`CapabilityDiscoveryService`) with zero web-framework dependency — the HTTP
server and CLI are optional surfaces over the same model, not the only way to
use it.

## Contents

- [Quickstart](#quickstart)
- [Why this exists](#why-this-exists)
- [What Control Tower is](#what-control-tower-is)
- [What it is not](#what-it-is-not)
- [Architecture](#architecture)
- [Control Tower surfaces](#control-tower-surfaces)
- [Human operators and AI operators](#human-operators-and-ai-operators)
- [Runtime and framework position](#runtime-and-framework-position)
- [The DeepAgentLabs ecosystem](#the-deepagentlabs-ecosystem)
- [Initial scope](#initial-scope)
- [Roadmap](#roadmap)

## Why this exists

The DeepAgentLabs projects each answer a different operational question:

- **AgenticLens** asks: what happened, why did it happen, and what should I fix?
- **Agentic Evals** asks: how well did the output meet expectations, and did it pass the release gate?
- **Agentic Sidecar** asks: should this action happen right now, given the
  user's intent and current risk?
- **Agentic Chaos** asks: what breaks under stress, failure, and silent
  degradation?
- **Agentic MCP** asks: how do hosts and agents access these capabilities
  through one MCP-native surface?

What is still missing is the layer above them:

> What is deployed, where is it running, which capabilities are enabled, what
> is unhealthy, and how do I operate all of it from one place?

That missing layer is the job of `agenticops-control-tower`.

## What Control Tower is

Control Tower is intended to be the **runtime-agnostic, framework-agnostic
operations layer** for teams running multiple agents and multiple
DeepAgentLabs capabilities.

At a high level, it should eventually provide:

- a central agent registry
- capability discovery across agents and environments
- health and status visibility
- centralized configuration for supported capabilities
- a unified control API
- a human CLI
- a web console for operators

The key distinction is that Control Tower is **not just a dashboard**. The
dashboard is only one interface to the underlying control plane.

## What it is not

- **Not a replacement for Agentic Evals.** Evals owns scoring and release-gate
  evaluation; Control Tower reads the resulting evidence.
- **Not a replacement for AgenticLens.** Control Tower may surface Lens
  insights, but Lens remains the observability and analysis engine, composing Evals for scoring.
- **Not a replacement for Agentic Sidecar.** Control Tower may surface
  Sidecar decisions and governance posture, but Sidecar remains the
  decision-time supervision layer.
- **Not a replacement for Agentic Chaos.** Control Tower may orchestrate or
  summarize chaos posture, but Chaos remains the resilience-testing engine.
- **Not the MCP layer itself.** Agentic MCP remains an independent package
  and should be able to connect both to individual DeepAgentLabs capabilities
  and to Control Tower.
- **Not tied to one runtime or one framework.** The control plane should sit
  above LangGraph, CrewAI, AutoGen, OpenAI Agents SDK, AWS AgentCore-style
  workloads, MCP-native agents, and custom Python systems rather than
  assuming one execution model.
- **Not the full architecture yet.** The concept doc describes a broader end
  state than what's built so far — see [Status](#status) for what's real
  today (registry, discovery, HTTP API, CLI, read-only console) versus [ROADMAP.md](ROADMAP.md)
  for the narrowed build order still ahead (configuration, MCP connector,
  bulk operations).

## Architecture

The ecosystem boundary should stay crisp:

```text
Control Tower = OPERATE
Agentic MCP   = CONNECT
AgenticLens   = OBSERVE
Agentic Evals = EVALUATE
Agentic Sidecar = SUPERVISE
Agentic Chaos = TEST
AI Operations Specification = STANDARDIZE
```

Conceptually:

```text
                   Human operators           AI operators
                          |                       |
                  Console / CLI / API        Agentic MCP
                          |                       |
                          +-----------+-----------+
                                      |
                                      v
                         DeepAgent Control Tower
                                      |
             +---------------+--------------+---------------+
             |               |              |               |
             v               v              v               v
         AgenticLens    Agentic Evals  Agentic Sidecar  Agentic Chaos
```

Control Tower's role is to centralize operations across agents and
capabilities, not to absorb the implementation logic of the sibling projects.

## Control Tower surfaces

The concept doc points to five main product surfaces:

- **Agent Registry**: inventory of known agents, runtimes, frameworks,
  environments, capability versions, and last-seen status
- **Capability Discovery**: detect which DeepAgentLabs packages and features
  are present on each agent wherever automatic discovery is technically
  feasible
- **Configuration**: centralized configuration and policy updates for
  supported capabilities
- **Unified Control API**: one programmatic interface over inventory, health,
  capability status, and supported operations
- **AgenticOps Console**: the human-facing dashboard over the same control
  plane used by the API and CLI

The CLI should be a first-class interface, not an afterthought. The same is
true for AI-facing operation through Agentic MCP once the underlying control
API exists.

## Human operators and AI operators

This project is unusual in that it has two equally important operator models:

- **Humans** should be able to use a console, CLI, or API to inspect and
  operate agents across environments.
- **AI systems** should be able to use Agentic MCP to inspect and operate the
  same control plane through an MCP-native interface.

That separation matters:

- Control Tower does **not** require MCP
- MCP does **not** require Control Tower
- when used together, MCP becomes the AI-native interface to the control
  plane

## Runtime and framework position

Control Tower should be:

- **runtime agnostic**: local Python, containers, VMs, Kubernetes,
  serverless, cloud-specific runtimes, and on-prem systems are all valid
  targets
- **framework agnostic**: LangGraph, CrewAI, AutoGen, OpenAI Agents SDK,
  custom harnesses, MCP-based agents, and future frameworks should all fit
  the model
- **modular**: teams should be able to adopt a single DeepAgentLabs
  capability without adopting the entire stack

That means deployment packaging is an implementation choice, not an
architectural dependency.

## The DeepAgentLabs ecosystem

Control Tower only makes sense if the package boundaries stay clear:

| Project | Role |
| --- | --- |
| `agenticlens` | Observe |
| `agentic-evals` | Evaluate |
| `agentic-sidecar` | Supervise |
| `agentic-chaos` | Test |
| `deep-agentic-core-mcp` | Connect |
| `ai-operations-spec` | Standardize |
| `agenticops-control-tower` | Operate |

- **Agentic Evals** remains the standalone scoring and release-gate engine
- **AgenticLens** remains package-first observability, evaluation workflows, and
  operational intelligence
- **Agentic Sidecar** remains package-first supervision and governance
- **Agentic Chaos** remains package-first resilience and fault injection
- **Agentic MCP** remains the MCP-native access layer
- **AI Operations Specification** remains the shared operational contract
- **Control Tower** becomes the centralized operate/manage layer across them

This repository should therefore stay focused on:

- inventory and registry concerns
- control-plane APIs
- capability discovery contracts
- health and readiness visibility
- centralized operations and configuration
- multi-agent, multi-environment control-room workflows

It should not quietly turn into a duplicate implementation of the sibling
projects.

## Initial scope

The concept doc describes a very broad end state. A good first implementation
needs to be much narrower.

The first usable version should likely prove four things only:

1. agents can register and heartbeat — **done**, with optional SQLite persistence
2. the system can discover installed DeepAgentLabs capabilities and versions
   — **done**, from agent-reported heartbeat data (not automatic detection)
3. operators can inspect that inventory through a simple API and CLI —
   **done**, via the optional `api` extra (see [Quickstart](#quickstart))
4. the same inventory is surfaced in a console over the same underlying
   control model — **done**, at `/console/` (v0.3)

That core is implemented as a Python API with optional SQLite storage.

## Current `v0.3` Surface

The package currently exposes:

- `register_agent(...)`
- `record_heartbeat(...)`
- `list_agents(...)`
- `get_agent(agent_id)`
- `list_capabilities()`
- `get_agent_capabilities(agent_id)`
- `get_status(...)`

The operator CLI is now available as:

- `agenticops-control-tower agents list`
- `agenticops-control-tower agents get <agent-id>`
- `agenticops-control-tower capabilities list`
- `agenticops-control-tower status`

The CLI talks to the HTTP API or reads a fleet snapshot with `--snapshot`.
Both paths use the same status and inventory model.

Example registration payloads are included for two runtime styles:

- [`examples/sample_agent_registration.json`](examples/sample_agent_registration.json)
- [`examples/sample_agent_registration_container.json`](examples/sample_agent_registration_container.json)
- [`examples/sample_fleet_snapshot.json`](examples/sample_fleet_snapshot.json)

That is enough to validate the control-plane idea without pretending the full
dashboard, configuration orchestration, and cross-agent operations engine
already exist.

## Roadmap

The build plan is in [ROADMAP.md](ROADMAP.md). In short, the intended order
should be:

- start with a narrow registry and discovery core
- add a real control API and CLI before building the dashboard
- surface Lens, Sidecar, and Chaos data gradually rather than simulating a
  complete integration layer
- add MCP connectivity to Control Tower after the underlying control surfaces
  are real

If you want the full architectural reasoning behind those choices, read the
concept doc first and the roadmap second.

## Ecosystem evidence alignment

Control Tower has thin Python readers for native Lens Runs, Evals reports and
gate decisions, Sidecar Decisions, and Chaos Reports. Supply an explicit
`EvidenceLink` to `ControlTowerAPI.summarize_evidence()` to attribute an artifact
to an existing registered deployment. The result preserves producer outcomes
and never changes fleet health. Invalid, unsupported or missing artifacts
return `unavailable`; unknown deployment IDs raise `AgentNotFoundError`.

These are local artifact readers, without remote collection, evidence storage,
HTTP posture routes, or console integration. Phase v0.5 remains partial.
AIOS is draft; native artifacts and Tower's link contract do not establish
AIOS conformance. See [the evidence contract](docs/ecosystem-alignment.md) and
[the runnable example](examples/inspect_ecosystem_evidence.py).


### Console DOM acceptance checks

Python console/API checks run with `make check`. Optional Node DOM checks exercise
rendering, safe text handling, filtering, details, credential retention on refresh,
failed-refresh clearing, disconnect and read-only network requests:

```bash
npm install --prefix /tmp/tower-console-qa --no-audit --no-fund jsdom
NODE_PATH=/tmp/tower-console-qa/node_modules node tests/console_ui.cjs
```

This is a test-only dependency; serving the packaged console requires no Node.
