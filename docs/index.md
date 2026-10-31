# AgenticOps Control Tower

**Unified control plane and operations console for the DeepAgentLabs ecosystem.**

> AgenticLens observes. Agentic Evals evaluates. Agentic Sidecar supervises.
> Agentic Chaos tests. Agentic MCP connects. **Control Tower operates.**

Control Tower keeps an inventory of the agents you run, where they run and
which DeepAgentLabs capabilities each one has. It rolls their heartbeats up into
fleet health, stores evidence pushed by the sibling packages, raises alerts when
that evidence shows a failure, and coordinates approved, audited changes. One
Python service provides the HTTP API, the CLI backend and a read-only web
console.

!!! info "Verified version"
    These docs describe the published **0.9.0** release, available on
    [PyPI](https://pypi.org/project/agenticops-control-tower/0.9.0/) since
    31 October 2026. Install `agenticops-control-tower[api]==0.9.0` for the HTTP
    server and console. Examples using `examples/` files also need a repository
    checkout. The package is **pre-alpha**; no 1.0 compatibility promise is made.


## What it does today

| Capability | Added in | In PyPI 0.9.0 | Status |
| --- | --- | --- | --- |
| [Agent registry and heartbeats](features.md#agent-registry-and-heartbeats) | 0.2.0 | Yes | Stable |
| [Capability discovery and version inventory](features.md#capability-discovery-and-version-inventory) | 0.2.0 | Yes | Stable |
| [HTTP API and CLI](features.md#http-api-cli-and-offline-snapshots) | 0.2.0 | Yes | Stable |
| [Fleet health, filters and offline snapshots](features.md#fleet-health-and-filters) | 0.2.1 | Yes | Stable |
| [SQLite persistence and reader/writer tokens](features.md#sqlite-persistence-and-bearer-tokens) | 0.2.1 | Yes | Stable |
| [Read-only AgenticOps Console](features.md#read-only-agenticops-console) | 0.3.0 | Yes | Stable |
| [Controlled configuration with approvals](features.md#controlled-configuration) | 0.4.0 | Yes | Experimental |
| [Ecosystem evidence posture](features.md#ecosystem-evidence-posture) | 0.5.0 | Yes | Experimental |
| [Incident investigation and approved staging recovery](features.md#incident-investigation-and-approved-staging-recovery) | 0.6.0 | Yes | Experimental |
| [Bulk fleet operations](features.md#bulk-fleet-operations) | 0.7.0 | Yes | Experimental |
| [Live detection, alerts and incident views](features.md#live-detection-alerts-and-incident-views) | 0.8.0 | Yes | Experimental |
| [Automated runbooks and recovery workflows](features.md#automated-runbooks-and-recovery-workflows) | 0.9.0 | Yes | Experimental |

**Stable** means the surface has existed since 0.3 or earlier and is covered by
the test suite; it is not yet a 1.0 compatibility promise. **Experimental**
means it was added in 0.4–0.9, may change before 1.0, even though it is included in the 0.9.0 release.
Planned work appears only in the [roadmap](roadmap.md).

## Where to go next

- **New here?** [Getting started](getting-started.md) installs Control Tower,
  reads a sample fleet offline and runs the server with the console.
- **Running it for a team?** [Server settings](settings.md),
  [authentication](authentication.md) and [hosting](hosting.md).
- **Connecting the other packages?** [Integrations](integrations.md) and
  [evidence posture](evidence-posture.md).
- **Looking for a task-based walkthrough?**
  [Use cases](https://deepagentlabs.io/control-tower/usecases/).
- **Reference:** [CLI](cli-reference.md), [HTTP and Python API](api-reference.md).

## Links

- Product page: [deepagentlabs.io/agenticops-control-tower](https://deepagentlabs.io/control-tower/)
- Source: [github.com/DeepAgentLabs/agenticops-control-tower](https://github.com/DeepAgentLabs/agenticops-control-tower)
- PyPI: [agenticops-control-tower](https://pypi.org/project/agenticops-control-tower/)
- Changelog: [CHANGELOG.md](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/CHANGELOG.md)
- DeepAgentLabs: [deepagentlabs.io](https://deepagentlabs.io/)
