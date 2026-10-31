# Examples

Everything below lives in the repository's
[`examples/`](https://github.com/DeepAgentLabs/agenticops-control-tower/tree/main/examples)
folder. Run the scripts from a source checkout with `uv run python examples/NAME.py`,
or `python examples/NAME.py` inside an environment where the package is installed.

| Example | Needs | What it shows | Verified for these docs |
| --- | --- | --- | --- |
| `sample_fleet_snapshot.json` | base package | Offline fleet: `agenticops-control-tower --snapshot examples/sample_fleet_snapshot.json status` | Yes |
| `live_operations.py` | base package | A failed Lens run raises one deduplicated `lens.failed` alert, it is acknowledged, and the incident view shows the timeline. | Yes |
| `push_ecosystem_evidence.py` | base package | Pushes the four sample producer artifacts and prints per-producer posture. | Yes |
| `controlled_configuration.py` | base package | Declare a Tower-owned setting, preview, approve as another operator, execute. | Yes |
| `fleet_operations.py` | base package | Approved bulk configuration with one stale target failing. | Yes |
| `runbook_recovery.py` | base package, `api` | Versioned runbook through HTTP: recommend, preview, separate approval, bounded steps and verification. `--fail-step` shows compensation; `--fail-verification` shows escalation. | Yes |
| `inspect_ecosystem_evidence.py` | base package | Reads native evidence with explicit attribution, without storing it. | Yes |
| `inspect_sidecar_journal.py` | base package | `python examples/inspect_sidecar_journal.py JOURNAL.json --source-version V`: read decisions from a Sidecar journal export. | No (needs your own journal file) |
| `incident_recovery.py` | `agenticlens`, `agentic-evals`, `api` | Phase 6/6A staging recovery through the HTTP routes; `--fail-verification` shows escalation. | No (needs sibling packages) |
| `run_local_console.sh` | `api` | Starts `serve` with tokens you exported, without printing them. | No (needs `api` extra) |
| `sample_agent_registration*.json` | — | Registration payloads for Lambda, container and Kubernetes deployments. | Used in getting started |
| `evidence/manifest.json` | — | One native Lens run, Evals report and gate, Sidecar decision and Chaos report for `payment-agent`. | Yes (via `push_ecosystem_evidence.py`) |
| `bulk_tracing.json` | — | Preview payload for `bulk preview`. | No |
| `hosting/nginx.conf` | — | HTTPS reverse-proxy template for a VM. | No |

"Verified" means the command ran against the 0.9.0 source on Python 3.12 with the
development dependencies installed (`runbook_recovery.py` also needs the `api`
extra for FastAPI's test client).

## Expected output: `live_operations.py`

```json
{
  "rule": "lens.failed",
  "alerts": 1,
  "reported_health": "healthy",
  "state": "open",
  "lens_integrity": "not_verified",
  "events": [
    "evidence.observed",
    "alert.created",
    "detected",
    "alert.acknowledged"
  ]
}
```

Note that `reported_health` stays `healthy`: alerts never change the health an
agent reports.

## Expected output: `push_ecosystem_evidence.py`

```text
agenticlens: available
agentic-sidecar: available
agentic-evals: available
agentic-chaos: available
agenticlens fresh {"status_counts": {"running": 0, "succeeded": 0, "failed": 1}, "attribution_counts": {"attributed": 0, "recovered": 0, "unattributed": 0, "no_failure": 0}, "faulty_agents": [], "failed_tool_names": ["payments_api"]}
agentic-evals fresh {"gate_counts": {"passed": 0, "failed": 1, "not_supplied": 0}}
agentic-sidecar fresh {"status_counts": {"ALLOW": 0, "WARN": 0, "BLOCK": 0, "CHALLENGE": 0, "REPLAN": 0, "PAUSE": 0, "ESCALATE": 1}, "risk_counts": {"LOW": 0, "MEDIUM": 0, "HIGH": 1, "unclassified": 0}, "escalations_required": 1}
agentic-chaos stale {"experiments": 0, "completed": 0, "incomplete": 0, "fault_events": 0}
```

For step-by-step walkthroughs built on these, see the
[use cases](https://deepagentlabs.io/control-tower/usecases/).
