# One posture view for AgenticLens, Evals, Sidecar and Chaos results

Push one native result from each sibling package for a deployment, and read a
single per-producer view of whether that evidence is fresh, stale or missing,
with the native outcomes counted, without Control Tower re-judging any of them.

| | |
|---|---|
| **For** | Teams running several DeepAgentLabs packages who want one place to see their results per deployment |
| **Difficulty** | Intermediate |
| **Time** | ~15 minutes |
| **Capabilities** | [Ecosystem evidence posture](https://deepagentlabs.io/control-tower/docs/features/#ecosystem-evidence-posture), [Integrations](https://deepagentlabs.io/control-tower/docs/integrations/) |
| **Status** | Experimental (added in 0.5.0) |

## The problem

Each package answers a different question about the same deployment: AgenticLens
says a run failed on `payments_api`, Agentic Evals says the release gate failed,
Agentic Sidecar escalated a high-risk action, and the last Agentic Chaos
experiment is days old. Those answers live in four different reports. Before a
release decision you want them side by side, with their age, and without a
fifth tool silently overriding their verdicts.

## Architecture

<figure class="ct-sim" data-ct-sim="evidence-posture" aria-label="Interactive illustration">
  <p class="ct-sim-fallback" style="padding:16px 22px;margin:0">AgenticLens, Evals and Sidecar evidence is fresh, Chaos is stale, a retry stores nothing twice, and reported health stays healthy.</p>
  <figcaption>Interactive illustration of the walkthrough below. Freshness and native outcomes match <em>Expected output</em>; no producer or Tower server is called.</figcaption>
</figure>

??? note "Static diagram"

    ```mermaid
    flowchart LR
        L[AgenticLens run] --> P
        E[Evals report + gate] --> P
        S[Sidecar decision] --> P
        C[Chaos report] --> P
        P[ingest_evidence<br/>EvidenceLink: agent, source,<br/>version, ref, observed_at] --> T[(Tower evidence store)]
        T --> V[agent_posture:<br/>fresh / stale / missing<br/>+ native counts per producer]
    ```

Collection is push-only and idempotent. Tower stores a validated projection of
each artifact, never fetches anything and never changes reported health.

## Prerequisites

- Python 3.10 or newer.
- Control Tower **0.5.0 or newer** (0.8.0 used here), from a checkout of the
  repository, because the walkthrough reads the sample artifacts in
  `examples/evidence/`:

    ```bash
    git clone https://github.com/DeepAgentLabs/agenticops-control-tower.git
    cd agenticops-control-tower
    python -m venv .venv && source .venv/bin/activate
    python -m pip install .
    ```

- None of the sibling packages need to be installed: the artifacts are their
  native JSON output.

## Walkthrough

The sample manifest `examples/evidence/manifest.json` links four artifacts to
`payment-agent`: a failed Lens run (`lens_run.json`), a Sidecar `ESCALATE`
decision, an Evals report with a failed gate, and a Chaos report from five days
earlier.

Save the script below as `ecosystem_posture.py` in the repository root and run:

```bash
python ecosystem_posture.py
```

Its steps:

1. Register `payment-agent` with the four producer capabilities installed.
2. Push each artifact with its `EvidenceLink`.
3. Push the first one again to show retries are safe.
4. Read per-producer posture as of the samples' capture time.
5. Confirm reported health is unchanged.

```python
"""Bring AgenticLens, Evals, Sidecar and Chaos results into one posture view.

Run from the root of a Control Tower checkout (it reads examples/evidence/).
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from agenticops_control_tower.models import AgentRegistrationPayload, EvidenceIngestRequest
from agenticops_control_tower.snapshot import create_api

evidence_dir = Path("examples/evidence")
manifest = json.loads((evidence_dir / "manifest.json").read_text())

api = create_api()

# 1. The deployment, with the four producers it has installed.
api.register(
    AgentRegistrationPayload(
        agent_id="payment-agent",
        name="payment-agent",
        environment="production",
        runtime="aws-lambda",
        framework="langgraph",
        status="healthy",
        capabilities={
            "agenticlens": "0.6.1",
            "agentic-evals": "0.7.2",
            "agentic-sidecar": "0.7.0",
            "agentic-chaos": "0.5.1",
        },
    )
)


def request_for(entry: dict) -> EvidenceIngestRequest:
    gate = entry.get("gate_path")
    return EvidenceIngestRequest(
        link=entry["link"],
        artifact=json.loads((evidence_dir / entry["artifact_path"]).read_text()),
        gate=json.loads((evidence_dir / gate).read_text()) if gate else None,
    )


# 2. Push one native artifact from each producer.
for entry in manifest["entries"]:
    result = api.ingest_evidence(request_for(entry), ingested_by="pipeline")
    print(f"pushed {entry['link']['source']:16} created={result.created}")

# 3. Pushing the same observation again is a no-op (safe pipeline retries).
retry = api.ingest_evidence(request_for(manifest["entries"][0]), ingested_by="pipeline")
print("retry created:", retry.created)

# 4. Read per-producer posture. The samples are dated 2026-08-15, so evaluate them
#    as of that time; a live deployment omits `now`.
as_of = datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc)
posture = api.agent_posture("payment-agent", now=as_of)
print("reported health:", posture.reported_health.value)
for source in posture.sources:
    print(f"{source.source:16} {source.freshness:6} {json.dumps(source.summary)}")

# 5. Producer outcomes never change health.
print("healthy agents:", api.get_status().healthy_agents)
```

## Expected output

```text
pushed agenticlens      created=True
pushed agentic-sidecar  created=True
pushed agentic-evals    created=True
pushed agentic-chaos    created=True
retry created: False
reported health: healthy
agenticlens      fresh  {"status_counts": {"running": 0, "succeeded": 0, "failed": 1}, "attribution_counts": {"attributed": 0, "recovered": 0, "unattributed": 0, "no_failure": 0}, "faulty_agents": [], "failed_tool_names": ["payments_api"]}
agentic-evals    fresh  {"gate_counts": {"passed": 0, "failed": 1, "not_supplied": 0}}
agentic-sidecar  fresh  {"status_counts": {"ALLOW": 0, "WARN": 0, "BLOCK": 0, "CHALLENGE": 0, "REPLAN": 0, "PAUSE": 0, "ESCALATE": 1}, "risk_counts": {"LOW": 0, "MEDIUM": 0, "HIGH": 1, "unclassified": 0}, "escalations_required": 1}
agentic-chaos    stale  {"experiments": 0, "completed": 0, "incomplete": 0, "fault_events": 0}
healthy agents: 1
```

## Verify it worked

1. Four `created=True` lines and `retry created: False`: every artifact was
   stored once, and the retry was recognised as the same observation.
2. AgenticLens, Evals and Sidecar are `fresh` (observed within one day of
   12:00 on 2026-08-15); Chaos is `stale` (observed 2026-08-10). Its counts are
   zero because counts cover only recent evidence.
3. The native outcomes appear unchanged: one failed Lens run on `payments_api`,
   one failed Evals gate, one Sidecar `ESCALATE` at `HIGH` risk.
4. `reported health: healthy` and `healthy agents: 1`: failures reported by the
   producers did not change the health the agent reports.

## Clean up

Everything was in memory. Remove the script and environment:

```bash
rm ecosystem_posture.py
deactivate && rm -rf .venv
```

## Variations and next steps

- **Without writing code:** the repository's sample snapshot already contains this
  evidence:
  `agenticops-control-tower --snapshot examples/sample_fleet_snapshot.json evidence posture payment-agent`
  (or `posture` for the whole fleet). Verified with 0.8.0.
- **On a server:** register the agent, then push the same manifest with a writer
  token: `agenticops-control-tower evidence ingest-manifest examples/evidence/manifest.json`,
  and read `agenticops-control-tower posture`. Because the samples are dated, a live
  server reports them all as stale. The console shows the same posture panel.
- **A Sidecar journal:** `evidence ingest-sidecar-journal AGENT journal.json --source-version V`
  pushes every decision in a Sidecar journal export.
- **Let failures raise alerts:** fresh failed Lens runs feed live detection; see the
  [AgenticLens failure use case](lens-failure-to-incident.md).
- Field-by-field rules: [Ecosystem alignment](https://deepagentlabs.io/control-tower/docs/ecosystem-alignment/).

## Tested with

- agenticops-control-tower 0.8.0 (source, commit `36c5eb6`), Python 3.13.16, Linux, base dependencies only, verified 2026-10-21. The server variation (`ingest-manifest`) was not run.
