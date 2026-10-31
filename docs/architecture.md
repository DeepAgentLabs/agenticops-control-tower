# Architecture

Control Tower is one Python package. A single `ControlTowerAPI` facade holds the
control model; the HTTP API, the CLI, offline snapshots and the console are all
thin surfaces over it, so they always agree.

```mermaid
flowchart LR
    subgraph Producers["Agents and sibling packages"]
        A[Your agents<br/>register + heartbeat]
        L[AgenticLens]
        E[Agentic Evals]
        S[Agentic Sidecar]
        C[Agentic Chaos]
    end
    subgraph Tower["Control Tower service (serve)"]
        H[HTTP API<br/>bearer tokens]
        F[ControlTowerAPI facade]
        R[(SQLite or memory:<br/>registry, evidence,<br/>config, alerts, incidents,<br/>runbook executions)]
        D[Detector<br/>every 30 s]
        U[Console /console/<br/>read-only]
    end
    CLI[CLI] --> H
    SNAP[Snapshot file] -->|--snapshot, read only| F
    MCP[Agentic MCP<br/>tower.* tools] --> H
    A --> H
    L & E & S & C -->|push native JSON| H
    H --> F --> R
    D --> F
    U -->|GET with reader token| H
```

- **Inventory first.** Agents register and report their own health; Tower
  aggregates, it does not probe.
- **Push, never pull.** Sibling results arrive as attributed native artifacts.
  Tower stores projections and never recomputes their verdicts.
- **Read-only surfaces, approved writes.** The console only reads. Configuration,
  bulk, recovery and runbook changes need a preview, a separate approval and an
  audit record.
- **Named actions, not commands.** Runbooks call host-installed connectors by
  action name with validated parameters; steps are claimed before dispatch and
  never replayed.

## Package layout

The package separates the following control-plane domains:

- `registry/` for agent registration and heartbeat state
- `discovery/` for capability and version discovery
- `api/` for a unified control-plane surface
- `config/` for centralized configuration contracts
- `cli/` for operator workflows
- `console/` for the packaged read-only AgenticOps Console
- `adapters/` for thin ecosystem integration boundaries
- `evidence/` for pushed evidence storage and freshness posture
- `incidents/` for incident investigation and approved recovery, `bulk/` for fleet operations, and `operations/` for live detection and alerts
- `runbooks/` for the versioned runbook catalog, connectors, staging fixture and approved bounded execution
- `status/` for fleet health and capability coverage rollups

See [README.md](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/README.md) and [ROADMAP.md](roadmap.md) for the product
boundary and milestone order.


Deployment and operator setup: [hosting](hosting.md) and
[customer-managed authentication](authentication.md).

## v0.4 controlled configuration

See [configuration and approvals](configuration.md) for Tower ownership, action lifecycle, audit durability and API/CLI usage.
Runtime settings remain mirrored or unsupported without an adapter.
