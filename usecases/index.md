# AgenticOps Control Tower Use Cases

Practical, end-to-end walkthroughs for operating agents with Control Tower. Every
use case below was run against **agenticops-control-tower 0.8.0** and lists the
exact versions it was tested with.

!!! info "Install 0.8.0 and get the example files"
    Control Tower **0.8.0** is available on PyPI. These walkthroughs use a
    repository checkout for the example files and can also install the package
    with `python -m pip install agenticops-control-tower==0.8.0`.

## Catalog

| Use case | Summary | Difficulty | Capabilities | Verified version |
|---|---|---|---|---|
| [Find unhealthy agents and capability gaps in five minutes](fleet-health-snapshot.md) | Describe your fleet in a snapshot file and find unhealthy agents, missing guardrails and version drift with no server. | Beginner | [Fleet health](https://deepagentlabs.io/control-tower/docs/features/#fleet-health-and-filters), [Capability discovery](https://deepagentlabs.io/control-tower/docs/features/#capability-discovery-and-version-inventory), [Offline snapshots](https://deepagentlabs.io/control-tower/docs/features/#http-api-cli-and-offline-snapshots) | 0.8.0 |
| [Turn a failed AgenticLens run into an acknowledged alert and incident timeline](lens-failure-to-incident.md) | Push a failed Lens run, get one deduplicated critical alert and an open incident, acknowledge it and read the timeline. | Intermediate | [Live detection and alerts](https://deepagentlabs.io/control-tower/docs/features/#live-detection-alerts-and-incident-views), [Evidence posture](https://deepagentlabs.io/control-tower/docs/features/#ecosystem-evidence-posture) | 0.8.0 |
| [One posture view for AgenticLens, Evals, Sidecar and Chaos results](ecosystem-evidence-posture.md) | Push native results from all four sibling packages and read fresh / stale / missing posture with their native outcomes. | Intermediate | [Evidence posture](https://deepagentlabs.io/control-tower/docs/features/#ecosystem-evidence-posture), [Integrations](https://deepagentlabs.io/control-tower/docs/integrations/) | 0.8.0 |
| [Change a setting on every staging agent, with a second person's approval](fleet-change-with-approval.md) | Preview one change for a whole environment, freeze the target list, require a different approver, execute and read the per-agent audit trail. | Intermediate | [Bulk fleet operations](https://deepagentlabs.io/control-tower/docs/features/#bulk-fleet-operations), [Controlled configuration](https://deepagentlabs.io/control-tower/docs/features/#controlled-configuration) | 0.8.0 |

The four cover a quick-value check, an end-to-end incident workflow, a
cross-package integration and a reviewed fleet-wide change.

## Verified package version

- **Package version:** agenticops-control-tower 0.8.0, repository `main` at commit `36c5eb6`
- **Environment:** Python 3.13.16 on Linux, base dependencies only (`pydantic`, `packaging`, `jsonschema`)
- **Verification date:** 2026-10-21
- **Scope:** every command and script in the walkthroughs was run and its output copied
  into the page. Variations that need the `api` extra (a running server) were not run.

## Pending verification

These are supported by 0.8.0 but have not been run end to end yet, so they are
not published as use cases:

| Candidate | What is needed to verify it |
|---|---|
| Self-host Control Tower with tokens and share the console | A machine with the `api` extra (`fastapi`, `uvicorn`, `httpx`) to run `serve`, register agents over HTTP and check the console in a browser. Steps exist in [Getting started](https://deepagentlabs.io/control-tower/docs/getting-started/) and [Hosting](https://deepagentlabs.io/control-tower/docs/hosting/). |
| Approved staging recovery for an incident | Local AgenticLens and Agentic Evals installs to run `examples/incident_recovery.py`; see [Incident recovery](https://deepagentlabs.io/control-tower/docs/incident-recovery/). |

## Quick navigation

- [Control Tower documentation](https://deepagentlabs.io/control-tower/docs/)
- [Control Tower product page](https://deepagentlabs.io/control-tower/)
- [Source on GitHub](https://github.com/DeepAgentLabs/agenticops-control-tower)
