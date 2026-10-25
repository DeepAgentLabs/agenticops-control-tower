# Find unhealthy agents and capability gaps in five minutes

Write down your fleet as a snapshot file and ask Control Tower which agents are
unhealthy, which are missing a DeepAgentLabs capability and where versions have
drifted. No server, token or network is needed.

| | |
|---|---|
| **For** | Platform and on-call engineers who want a quick inventory check |
| **Difficulty** | Beginner |
| **Time** | ~5 minutes |
| **Capabilities** | [Fleet health and filters](https://deepagentlabs.io/control-tower/docs/features/#fleet-health-and-filters), [Capability discovery](https://deepagentlabs.io/control-tower/docs/features/#capability-discovery-and-version-inventory), [Offline snapshots](https://deepagentlabs.io/control-tower/docs/features/#http-api-cli-and-offline-snapshots) |
| **Status** | Stable |

## The problem

Agents run in different places (Kubernetes, Docker, Lambda) and each team knows
only its own. Before an incident review or an upgrade, someone has to answer
three questions by hand: which agents are not healthy, which ones lack a
guardrail such as Agentic Sidecar, and which are on older versions of a tool.
Spreadsheets go stale and nobody trusts them.

## Architecture

<figure class="ct-sim" data-ct-sim="fleet-health" aria-label="Interactive illustration">
  <p class="ct-sim-fallback" style="padding:16px 22px;margin:0">research-bot is unhealthy; triage-bot is degraded, has no Agentic Sidecar and runs AgenticLens 0.9.0; checkout-agent is healthy.</p>
  <figcaption>Interactive illustration of the walkthrough below. Click a step to see which agents each command returns. The agents and results are the same as in <em>Expected output</em>; nothing is called.</figcaption>
</figure>

??? note "Static diagram"

    ```mermaid
    flowchart LR
        F[my-fleet.json<br/>registrations + heartbeats] -->|--snapshot| CLI[agenticops-control-tower CLI]
        CLI --> API[ControlTowerAPI<br/>in memory]
        API --> O1[status: health + coverage]
        API --> O2[agents list filters]
        API --> O3[capabilities list: versions]
    ```

The CLI loads the file into the same `ControlTowerAPI` the server uses and
answers read commands directly. Nothing is written anywhere.

## Prerequisites

- Python 3.10 or newer.
- Control Tower **0.2.1 or newer**, installed from the repository for this walkthrough. The tested
  0.8.0 version is also available on PyPI:

    ```bash
    git clone https://github.com/DeepAgentLabs/agenticops-control-tower.git
    cd agenticops-control-tower
    python -m venv .venv && source .venv/bin/activate
    python -m pip install .
    ```

- No `api` extra, server, token or sibling package.

## Walkthrough

### 1. Describe your fleet

Save this as `my-fleet.json`. Each registration is one deployment; each heartbeat
reports its latest status. Replace the values with your own agents.

```json
{
  "captured_at": "2026-10-21T09:00:00Z",
  "registrations": [
    {
      "agent_id": "checkout-agent",
      "name": "checkout-agent",
      "environment": "production",
      "runtime": "kubernetes",
      "framework": "langgraph",
      "capabilities": {
        "agenticlens": "0.10.0",
        "agentic-sidecar": "0.9.0"
      },
      "registered_at": "2026-10-20T10:00:00Z"
    },
    {
      "agent_id": "triage-bot",
      "name": "triage-bot",
      "environment": "staging",
      "runtime": "docker",
      "framework": "crewai",
      "capabilities": {
        "agenticlens": "0.9.0"
      },
      "registered_at": "2026-10-20T10:00:00Z"
    },
    {
      "agent_id": "research-bot",
      "name": "research-bot",
      "environment": "staging",
      "runtime": "aws-lambda",
      "framework": "openai-agents",
      "capabilities": {
        "agenticlens": "0.10.0",
        "agentic-sidecar": "0.9.0"
      },
      "registered_at": "2026-10-20T10:00:00Z"
    }
  ],
  "heartbeats": [
    {
      "agent_id": "checkout-agent",
      "heartbeat": {
        "status": "healthy",
        "last_seen": "2026-10-21T08:59:30Z"
      }
    },
    {
      "agent_id": "triage-bot",
      "heartbeat": {
        "status": "degraded",
        "last_seen": "2026-10-21T08:58:10Z"
      }
    },
    {
      "agent_id": "research-bot",
      "heartbeat": {
        "status": "unhealthy",
        "last_seen": "2026-10-21T08:41:00Z"
      }
    }
  ]
}
```

### 2. Check fleet health

```bash
agenticops-control-tower --snapshot my-fleet.json status
```

### 3. List the agents that are down

```bash
agenticops-control-tower --snapshot my-fleet.json agents list --unhealthy
```

### 4. Find staging agents without Agentic Sidecar

Filters combine with AND:

```bash
agenticops-control-tower --snapshot my-fleet.json agents list --environment staging --missing-capability agentic-sidecar
```

### 5. Look for version drift

```bash
agenticops-control-tower --snapshot my-fleet.json capabilities list
```

## Expected output

Step 2 (`status`):

```json
{
  "total_agents": 3,
  "healthy_agents": 1,
  "degraded_agents": 1,
  "unhealthy_agents": 1,
  "unknown_agents": 0,
  "capability_count": 2,
  "status_buckets": {
    "healthy": [
      "checkout-agent"
    ],
    "degraded": [
      "triage-bot"
    ],
    "unhealthy": [
      "research-bot"
    ],
    "unknown": []
  },
  "capabilities": [
    {
      "capability": "agentic-sidecar",
      "installed_agents": 2,
      "missing_agents": 1,
      "versions": [
        "0.9.0"
      ],
      "agent_ids": [
        "checkout-agent",
        "research-bot"
      ],
      "missing_agent_ids": [
        "triage-bot"
      ]
    },
    {
      "capability": "agenticlens",
      "installed_agents": 3,
      "missing_agents": 0,
      "versions": [
        "0.10.0",
        "0.9.0"
      ],
      "agent_ids": [
        "checkout-agent",
        "research-bot",
        "triage-bot"
      ],
      "missing_agent_ids": []
    }
  ]
}
```

Step 3 (`agents list --unhealthy`):

```json
[
  {
    "agent_id": "research-bot",
    "name": "research-bot",
    "environment": "staging",
    "runtime": "aws-lambda",
    "framework": "openai-agents",
    "status": "unhealthy",
    "capabilities": {
      "agenticlens": "0.10.0",
      "agentic-sidecar": "0.9.0"
    },
    "runtime_metadata": {},
    "package_metadata": {},
    "registered_at": "2026-10-20T10:00:00Z",
    "last_seen": "2026-10-21T08:41:00Z",
    "heartbeat_count": 1
  }
]
```

Step 4 (staging agents missing Sidecar):

```json
[
  {
    "agent_id": "triage-bot",
    "name": "triage-bot",
    "environment": "staging",
    "runtime": "docker",
    "framework": "crewai",
    "status": "degraded",
    "capabilities": {
      "agenticlens": "0.9.0"
    },
    "runtime_metadata": {},
    "package_metadata": {},
    "registered_at": "2026-10-20T10:00:00Z",
    "last_seen": "2026-10-21T08:58:10Z",
    "heartbeat_count": 1
  }
]
```

Step 5 (`capabilities list`). AgenticLens runs two versions across the fleet:

```json
{
  "agentic-sidecar": [
    "0.9.0"
  ],
  "agenticlens": [
    "0.10.0",
    "0.9.0"
  ]
}
```

## Verify it worked

1. Every command exits with status `0` (`echo $?`).
2. `total_agents` in step 2 equals the number of registrations in your file, and
   the four bucket lists together contain every agent ID exactly once.
3. Each agent in step 4's output has `"environment": "staging"` and no
   `agentic-sidecar` key in `capabilities`.
4. A quick automated check:

    ```bash
    agenticops-control-tower --snapshot my-fleet.json status \
      | python -c "import json,sys; s=json.load(sys.stdin); assert s['total_agents']==3 and s['unhealthy_agents']==1; print('ok')"
    ```

    ```text
    ok
    ```

## Clean up

Nothing was installed system-wide or written by Control Tower. Remove the file and
the virtual environment:

```bash
rm my-fleet.json
deactivate && rm -rf .venv
```

## Variations and next steps

- **Use the sample fleet:** `--snapshot examples/sample_fleet_snapshot.json` from the
  repository includes pushed evidence, so `posture` also works.
- **Filter by status:** `agents list --status degraded`.
- **Check a minimum version:** offline snapshots have no versions command; in Python,
  `load_snapshot("my-fleet.json").assess_versions("agenticlens", "0.10.0")` reports
  `triage-bot` as `outdated`. On a server, use `GET /versions`.
- **Go live:** run `agenticops-control-tower serve` and have agents register and send
  heartbeats; the same commands then work without `--snapshot`. See
  [Getting started](https://deepagentlabs.io/control-tower/docs/getting-started/).

## Tested with

- agenticops-control-tower 0.8.0 (source, commit `36c5eb6`), Python 3.13.16, Linux, base dependencies only, verified 2026-10-21.
  Commands were run through `python -m agenticops_control_tower.cli.main`, the same entry point as the installed `agenticops-control-tower` script.
