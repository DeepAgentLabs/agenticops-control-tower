# Turn a failed AgenticLens run into an acknowledged alert and incident timeline

Push a failed AgenticLens run for a deployment, let Control Tower's live detection
raise a deduplicated critical alert and open an incident, acknowledge it, and read
the joined incident timeline, all with the Python API and no network.

| | |
|---|---|
| **For** | Operators wiring AgenticLens results into incident response |
| **Difficulty** | Intermediate |
| **Time** | ~15 minutes |
| **Capabilities** | [Live detection, alerts and incident views](https://deepagentlabs.io/control-tower/docs/features/#live-detection-alerts-and-incident-views), [Ecosystem evidence posture](https://deepagentlabs.io/control-tower/docs/features/#ecosystem-evidence-posture), [Agent registry](https://deepagentlabs.io/control-tower/docs/features/#agent-registry-and-heartbeats) |
| **Status** | Experimental (added in 0.8.0) |

## The problem

AgenticLens tells you a run failed, but that result sits in a report nobody is
watching. On-call needs one alert per real failure (not one per scan), a record
of who acknowledged it, and a single view of what happened, without a
dashboard deciding on its own that the agent is "down" or that the problem is
fixed.

## Architecture

<figure class="ct-sim" data-ct-sim="lens-incident" aria-label="Interactive illustration">
  <p class="ct-sim-fallback" style="padding:16px 22px;margin:0">A failed run raises one critical lens.failed alert and opens an incident; rescans do not duplicate it; a later successful run clears the alert while the incident stays open.</p>
  <figcaption>Interactive illustration of the walkthrough below. The alert, incident and timeline match <em>Expected output</em>; the Scan again button is simulated in your browser.</figcaption>
</figure>

Detection reads only evidence that was pushed to Tower. It never changes the
health the agent reports and never runs recovery on its own.

## Prerequisites

- Python 3.10 or newer.
- Control Tower **0.8.0**, installed from the repository for this walkthrough
  (the same version is also available on PyPI):

    ```bash
    git clone https://github.com/DeepAgentLabs/agenticops-control-tower.git
    cd agenticops-control-tower
    python -m venv .venv && source .venv/bin/activate
    python -m pip install .
    ```

- No AgenticLens install, server, token or network: the run is a native JSON
  artifact built in the script.

## Walkthrough

Save the script below as `lens_alert_walkthrough.py`, then run it:

```bash
python lens_alert_walkthrough.py
```

The numbered comments are the steps:

1. Register `checkout-agent` in staging with reported health `healthy`.
2. Push a **failed** AgenticLens run, observed 30 seconds ago (inside the default
   300-second freshness window).
3. Run a detection scan. A server does this every 30 seconds; here it is called
   directly as the `writer` operator.
4. Scan again to show the alert is deduplicated.
5. Acknowledge the alert as the on-call operator.
6. Read the joined incident view.
7. Push a newer **successful** run and scan again.

```python
"""Turn a failed AgenticLens run into an acknowledged alert and an incident timeline."""

from datetime import datetime, timedelta, timezone

from agenticops_control_tower.config.models import Operator
from agenticops_control_tower.models import AgentRegistrationPayload, EvidenceIngestRequest
from agenticops_control_tower.snapshot import create_api

api = create_api()
operator = Operator(operator_id="on-call", role="writer")

# 1. Register the deployment. Its reported health is "healthy".
api.register(
    AgentRegistrationPayload(
        agent_id="checkout-agent",
        name="checkout-agent",
        environment="staging",
        runtime="kubernetes",
        framework="langgraph",
        status="healthy",
        capabilities={"agenticlens": "0.10.0"},
    )
)


def push_lens_run(run_id: str, status: str, observed_at: datetime) -> None:
    """Push one native AgenticLens run artifact, attributed to checkout-agent."""
    api.ingest_evidence(
        EvidenceIngestRequest.model_validate(
            {
                "link": {
                    "agent_id": "checkout-agent",
                    "source": "agenticlens",
                    "source_version": "0.10.0",
                    "artifact_type": "run",
                    "artifact_ref": f"lens:run:{run_id}",
                    "run_id": run_id,
                    "observed_at": observed_at.isoformat(),
                },
                "artifact": {
                    "schema_version": "1.0",
                    "run_id": run_id,
                    "application_name": "checkout",
                    "status": status,
                    "task_success": status == "succeeded",
                    "spans": [],
                },
            }
        )
    )


now = datetime.now(timezone.utc)

# 2. AgenticLens reports a failed run.
push_lens_run("run-41", "failed", now - timedelta(seconds=30))

# 3. Scan (the server does this every 30 seconds; here we call it directly).
alert = api.operations.evaluate(operator)[0]
print("alert:", alert.rule, alert.severity, "incident:", alert.incident_id is not None)

# 4. A second scan does not duplicate the alert.
api.operations.evaluate(operator)
print("alerts after rescan:", len(api.operations.list(operator)))

# 5. Acknowledge it.
api.operations.acknowledge(alert.alert_id, operator)

# 6. Inspect the joined incident view.
view = api.operations.incident_view(alert.incident_id, operator)
print("incident state:", view["incident"].state)
print("reported health:", view["agent"].status.value)
print("timeline:", [event["event"] for event in view["timeline"]])

# 7. A newer successful run clears the alert, but the incident stays open:
#    recovery still needs the approved verification workflow.
push_lens_run("run-42", "succeeded", datetime.now(timezone.utc))
api.operations.evaluate(operator)
print("active alerts:", len(api.operations.list(operator, active_only=True)))
print("cleared:", api.operations.list(operator)[0].cleared_at is not None)
print("incident state:", api.operations.incident_view(alert.incident_id, operator)["incident"].state)
```

## Expected output

```text
alert: lens.failed critical incident: True
alerts after rescan: 1
incident state: open
reported health: healthy
timeline: ['evidence.observed', 'alert.created', 'detected', 'alert.acknowledged']
active alerts: 0
cleared: True
incident state: open
```

## Verify it worked

1. `alert: lens.failed critical incident: True`: one critical alert, linked to a
   recovery incident.
2. `alerts after rescan: 1`: rescanning did not create a duplicate.
3. `reported health: healthy`: the alert did not change the health the agent
   reports.
4. The timeline contains `alert.acknowledged`, so the acknowledgement was recorded.
5. After the successful run, `active alerts: 0` and `cleared: True`, but the
   incident is still `open`: clearing an alert never resolves an incident.

## Clean up

The API was in memory, so nothing was stored. Remove the script and environment:

```bash
rm lens_alert_walkthrough.py
deactivate && rm -rf .venv
```

## Variations and next steps

- **On a server:** push the run with
  `agenticops-control-tower evidence ingest checkout-agent agenticlens run.json --source-version 0.10.0 --artifact-ref lens:run:run-41 --run-id run-41`
  (writer token), then `alerts list --active-only`, `alerts acknowledge ALERT_ID` and
  `incidents view INCIDENT_ID`. The console shows the same alerts and timeline.
- **Stale or missing evidence:** stop pushing, or register a capability you never
  push, and the next scan raises `evidence.stale` or `evidence.missing` warnings.
- **Resolve the incident:** the approved recovery workflow (investigate, preview,
  approve, execute, verify) is in
  [Incident recovery](https://deepagentlabs.io/control-tower/docs/incident-recovery/).
- The repository's shorter version is `examples/live_operations.py`.

## Tested with

- agenticops-control-tower 0.8.0 (source, commit `36c5eb6`), Python 3.13.16, Linux, base dependencies only, verified 2026-10-21. The script was run with the package on `PYTHONPATH`; the server-based variation was not run.
