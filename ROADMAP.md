# agenticops-control-tower — Roadmap & Architecture

## Release Status

- **v0.1** 🚧 Planned — Registry, Heartbeats, Capability Discovery, Read-Only API
- **v0.2** 🚧 Planned — CLI, Status Views, Health Rollups, Version Inventory
- **v0.3** 🚧 Planned — AgenticOps Console (read-only dashboard)
- **v0.4** 🚧 Planned — Configuration Model and Controlled Write Operations
- **v0.5** 🚧 Planned — Lens, Sidecar, and Chaos Surface Integration
- **v0.6** 🚧 Planned — Agentic MCP Connector for Control Tower
- **v0.7** 🚧 Planned — Multi-Agent Operations and Bulk Actions
- **v0.8** 🚧 Planned — Alerts, Audit Trails, and Incident Views
- **v1.0** 🚧 Planned — Stable Control Plane and Published Capability Contract

Nothing has shipped yet. This repository currently contains the concept
document, this roadmap, and the README only.

## Design Constraints

These should shape the build order from the start, not be rediscovered later.

1. **Inventory before orchestration.** The first release should answer
   "what exists and what is installed?" before attempting "change it
   remotely." A control plane without trusted inventory is theater.
2. **Read-only before write-capable.** Cross-agent configuration and
   operations are the highest-risk part of the vision. Prove registration,
   discovery, and status first.
3. **API and CLI before dashboard.** The web console should sit on top of the
   same control model, not become the place where the actual behavior lives.
4. **Capability adapters should stay thin.** Control Tower should reuse
   sibling project contracts and metadata rather than re-implement Lens,
   Sidecar, or Chaos logic locally.
5. **Runtime-agnostic means avoiding runtime assumptions in v0.1.** Do not
   build the first version around Kubernetes-specific or cloud-specific
   registration mechanics.
6. **MCP is downstream of the control API.** Agentic MCP integration is
   valuable, but only after there is a real control-plane surface to expose.
7. **Automatic discovery where possible, explicit registration where
   necessary.** The architecture should prefer discovery, but not block the
   product on perfect autodetection across every environment.

## Cross-Project Dependencies

`agenticops-control-tower` is the ecosystem control plane, so its roadmap is
mostly about coordinating with sibling projects without absorbing them.

- `agenticlens`
  Coordinate with: how Control Tower reads summarized observability,
  evaluation, and readiness signals without replacing Lens as the engine.
- `agentic-sidecar`
  Coordinate with: how governance posture, decision summaries, and risk
  signals are surfaced centrally once Sidecar exposes stable runtime output.
- `agentic-chaos`
  Coordinate with: how experiment inventory, last-run status, and resilience
  posture are summarized in the control plane once Chaos artifacts stabilize.
- `mcp-server` (`deep-agentic-core-mcp`)
  Validate in: a future MCP-facing path for AI-native operation against
  Control Tower rather than only against individual sibling packages.
- `ai-operations-spec`
  Coordinate with: agent identity, capability metadata, status events,
  configuration contracts, and operational artifacts that should not drift
  away from the shared ecosystem model.

For roadmap planning, use these meanings consistently:

- `Depends on`: the item cannot ship first.
- `Coordinate with`: sibling repos should be updated in the same window.
- `Validate in`: end-to-end checks should happen in another repo or adapter.

## Definition of Done

A roadmap item is done only when all applicable work is complete:

- implementation is merged and usable through the intended API, CLI, or UI
- tests or fixtures cover the behavior
- operator-facing docs and examples are updated
- `README.md` and this roadmap are updated when the feature changes user
  expectations or milestone status
- capability contracts and ecosystem-facing artifact shapes are documented
- sibling-project checks are recorded where relevant
- release metadata is updated when the work is part of a release-ready change
  set

---

## Architecture

Control Tower should become the **operate/manage layer** across the
DeepAgentLabs stack:

```text
Control Tower = OPERATE
Agentic MCP   = CONNECT
AgenticLens   = OBSERVE
Agentic Sidecar = GOVERN
Agentic Chaos = TEST
AI Operations Specification = STANDARDIZE
```

From a developer or operator perspective, the project exists to answer:

`What agents do I have, where are they running, what DeepAgentLabs
capabilities are installed, what is unhealthy, and how do I manage all of that
through one control plane?`

That keeps the package focused on:

- agent registry and lifecycle visibility
- capability inventory and discovery
- control-plane API design
- centralized configuration and safe operations
- operator UX across CLI, console, and AI-facing control

It should not become a hidden duplicate of the sibling runtimes.

## Proposed Product Surfaces

```text
agenticops-control-tower
├── registry/        # agent inventory, heartbeat, runtime metadata
├── discovery/       # capability detection and version inventory
├── api/             # unified control-plane API
├── config/          # central configuration model and safe write paths
├── cli/             # operator CLI
├── console/         # AgenticOps Console / dashboard
└── adapters/        # thin ecosystem adapters (Lens, Sidecar, Chaos, MCP)
```

This is a proposed shape, not a committed implementation layout.

## Capability Direction

Over time, the control plane should grow around a few clear domains:

- inventory and registration
- health and readiness
- capability discovery
- version and compatibility visibility
- centralized configuration
- operational actions
- auditability and incident posture
- AI-native control through MCP

Contributors should be able to ask:

`Is this feature helping operators understand or safely control deployed
agents, or is it really work that belongs in Lens, Sidecar, Chaos, MCP, or the
spec repo instead?`

---

## Build Order

## Phase 0: Concept and Product Boundary

Status: current

Goals:

- define what Control Tower is and is not
- keep boundaries clear against Lens, Sidecar, Chaos, MCP, and AIOS
- narrow the first implementation into a believable control-plane core

Deliverables:

- [x] architecture concept document
- [x] `README.md`
- [x] `ROADMAP.md`
- [x] implementation scaffold

## Phase 1: Registry and Discovery Core (`v0.1`)

Goals:

- create a minimal agent registry
- accept explicit agent registration and heartbeats
- record runtime, framework, environment, and package metadata
- expose a read-only API for listing agents and capabilities

Suggested initial surface:

- `POST /agents/register`
- `POST /agents/{id}/heartbeat`
- `GET /agents`
- `GET /agents/{id}`
- `GET /capabilities`

Success criteria:

- operators can see which agents are known to the system
- each agent record includes capability versions and last-seen status
- the system works without assuming Kubernetes, Docker, or one framework
- example registration payloads exist for at least two runtime styles

## Phase 2: CLI and Status Model (`v0.2`)

Goals:

- ship a first operator CLI
- add health rollups and version inventory summaries
- expose useful filters such as unhealthy agents or agents missing a
  capability

Suggested commands:

- `deepagent agents list`
- `deepagent agents get <agent-id>`
- `deepagent capabilities list`
- `deepagent status`

Success criteria:

- CLI and API share the same underlying control model
- a user can answer basic inventory questions without touching raw JSON
- health state is computed consistently rather than ad hoc per interface

## Phase 3: Read-Only Console (`v0.3`)

Goals:

- ship the first AgenticOps Console
- visualize inventory, health, versions, and capability presence
- keep the dashboard read-only at first

Success criteria:

- the console is a thin view over the real API
- one operator can identify unhealthy or outdated agents quickly
- the dashboard does not introduce write-side behavior the API cannot do

## Phase 4: Configuration and Safe Write Operations (`v0.4`)

Goals:

- define a central configuration model for supported capabilities
- add controlled write paths for safe updates
- document which configuration is authoritative versus merely mirrored

Potential operations:

- `config.get(agent_id)`
- `config.update(agent_id, patch)`
- `capabilities.enable(agent_id, capability)`
- `capabilities.disable(agent_id, capability)`

Open risk:

- configuration semantics will differ across Lens, Sidecar, and Chaos, so
  v0.4 must avoid pretending one generic toggle model covers everything.

Success criteria:

- write operations are auditable
- partial failure behavior is explicit
- unsupported configuration surfaces degrade honestly

## Phase 5: Ecosystem Surface Integration (`v0.5`)

Goals:

- surface Lens, Sidecar, and Chaos summaries in the control plane
- keep adapters thin and contract-driven
- avoid copying sibling project logic into Control Tower

Examples:

- Lens: evaluation summaries, health signals, recent findings
- Sidecar: decision summaries, risk posture, intervention counts
- Chaos: experiment inventory, last run, resilience posture

Success criteria:

- operators can inspect high-level posture centrally
- the source of truth for the underlying capability remains in the sibling
  package
- integration failures degrade to "unavailable" rather than crashing the
  control plane

## Phase 6: Agentic MCP Connector (`v0.6`)

Goals:

- expose Control Tower to AI operators through Agentic MCP
- support AI-native inventory and status queries first
- add write-capable operations only after authorization and audit shape are
  clear

Examples:

- list registered agents
- list unhealthy agents
- show agents with outdated package versions
- inspect recent high-risk Sidecar posture

Success criteria:

- MCP connects to a real control API rather than a demo surface
- read and write operations have distinct authorization boundaries
- examples exist showing MCP with and without Control Tower

## Phase 7: Multi-Agent Operations (`v0.7`)

Goals:

- add bulk operations and fleet-wide targeting
- support environment-scoped and capability-scoped actions
- make operational intent explicit before write actions fan out

Examples:

- enable enhanced tracing for all staging agents
- find all agents missing a minimum Sidecar version
- pause a class of experiments across an environment

Success criteria:

- bulk actions include preview and audit paths
- rollback or reconciliation behavior is documented
- targeting semantics are deterministic

## Phase 8: Alerts, Audit, and Incident Views (`v0.8`)

Goals:

- add operator-facing alerts and warnings
- add audit trails for configuration and operations
- add incident-oriented views over agent and capability posture

Success criteria:

- the system explains what changed, when, and by whom or by what control path
- incident views join inventory, health, and recent changes coherently

## Phase 9: Stable Capability Contract (`v1.0`)

Goals:

- publish a stable capability discovery contract
- lock the core control-plane API semantics
- document supported runtime and framework integration patterns

Success criteria:

- at least two materially different runtimes are validated end to end
- capability metadata and status semantics are versioned
- Control Tower can be described as a stable control-plane product rather than
  a concept repo

---

## Open Questions

- What is the minimum viable registration contract for agents that is still
  useful across runtimes?
- Which fields should be standardized in AIOS versus left as Control Tower
  implementation detail?
- How much of capability discovery can be automatic versus agent-reported?
- When configuration updates fail midway across a fleet, what is the expected
  reconciliation model?
- Should the first implementation be a local-first Python service only, or
  should remote deployment concerns appear in v0.1?

## North Star

The long-term goal is not "a nice dashboard." The goal is a **real control
room** for agentic operations: one place where human operators and AI operators
can understand, inspect, and safely operate the DeepAgentLabs ecosystem across
many agents and environments.
