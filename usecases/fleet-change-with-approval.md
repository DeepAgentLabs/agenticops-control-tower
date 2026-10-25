# Change a setting on every staging agent, with a second person's approval

Turn on enhanced tracing for every staging agent that runs AgenticLens in one
operation. Control Tower freezes the exact list of agents, refuses to let the
person who proposed the change approve it, applies it only after a reviewer
says yes, and records who did what, all with the Python API and no network.

| | |
|---|---|
| **For** | Platform teams that change settings across many agents at once |
| **Difficulty** | Intermediate |
| **Time** | ~10 minutes |
| **Capabilities** | [Bulk fleet operations](https://deepagentlabs.io/control-tower/docs/features/#bulk-fleet-operations), [Controlled configuration](https://deepagentlabs.io/control-tower/docs/features/#controlled-configuration), [Agent registry](https://deepagentlabs.io/control-tower/docs/features/#agent-registry-and-heartbeats) |
| **Status** | Experimental (added in 0.7.0) |

## The problem

Before a release test, someone needs to switch on extra tracing for every
staging agent. Doing it agent by agent is slow and easy to get wrong. Doing it
with one script is fast but risky: a loose filter can catch a production agent,
an agent that appears halfway through can be changed without anyone reviewing
it, and afterwards nobody can say exactly which agents changed or who signed
off.

## Architecture

<figure class="ct-sim" data-ct-sim="fleet-change" aria-label="Interactive illustration">
  <p class="ct-sim-fallback" style="padding:16px 22px;margin:0">Alice previews one change for three staging agents; a later agent does not join; Alice's self-approval is rejected; Bob approves; three agents change and production is untouched.</p>
  <figcaption>Interactive illustration of the walkthrough below. Choose who approves at step 3. Agents, results and audit events match <em>Expected output</em>; nothing is called.</figcaption>
</figure>

The selector is turned into an explicit, sorted list of agents at preview time.
Approval covers that list and nothing else. Agents that register later, or that
live in another environment, are never touched.

## Prerequisites

- Python 3.10 or newer.
- Control Tower **0.7.0 or newer**, installed from the repository for this
  walkthrough (0.8.0 is also available on PyPI):

    ```bash
    git clone https://github.com/DeepAgentLabs/agenticops-control-tower.git
    cd agenticops-control-tower
    python -m venv .venv && source .venv/bin/activate
    python -m pip install .
    ```

- No `api` extra, server, token or sibling package.

## Walkthrough

Save the script below as `fleet_change_walkthrough.py`, then run it:

```bash
python fleet_change_walkthrough.py
```

The numbered comments are the steps:

1. Register three staging agents and one production agent, all with AgenticLens,
   and declare that Tower owns their AgenticLens settings.
2. Alice previews one change for every staging agent with AgenticLens.
3. A new staging agent registers after the preview.
4. Alice tries to approve her own change.
5. Bob approves it.
6. Alice executes the approved batch.
7. Read back the settings on a changed agent, the late agent and the production agent.
8. Read the batch's audit trail.

```python
"""Change one setting across every staging agent, with a second person's approval."""

from agenticops_control_tower.bulk import BulkRequest
from agenticops_control_tower.config import Configuration, ConfigurationError, Operator
from agenticops_control_tower.models import AgentRegistrationPayload
from agenticops_control_tower.snapshot import create_api

api = create_api()
alice = Operator(operator_id="alice", role="writer")  # proposes and runs the change
bob = Operator(operator_id="bob", role="approver")  # reviews and approves it


def add_agent(agent_id: str, environment: str) -> None:
    api.register(
        AgentRegistrationPayload(
            agent_id=agent_id,
            name=agent_id,
            environment=environment,
            runtime="kubernetes",
            framework="langgraph",
            status="healthy",
            capabilities={"agenticlens": "0.10.0"},
        )
    )
    # Tower owns this setting, so Tower is allowed to change it.
    api.config.declare(
        Configuration(agent_id=agent_id, capability="agenticlens", authority="tower"), alice
    )


# 1. Three staging agents and one production agent, all running AgenticLens.
for agent_id in ("checkout-agent", "refund-agent", "triage-agent"):
    add_agent(agent_id, "staging")
add_agent("checkout-agent-prod", "production")

# 2. Alice previews one change for every staging agent with AgenticLens.
preview = api.bulk.preview(
    BulkRequest(
        intent="Enable enhanced tracing on staging before the release test",
        operation="config.update",
        selector={"environment": "staging", "capability": "agenticlens"},
        patch={"values": {"enhanced_tracing": True}},
    ),
    alice,
)
print("frozen targets:", [t.agent_id for t in preview.targets])
print("status:", preview.status)

# 3. A new staging agent registers after the preview. It does not join the batch.
add_agent("search-agent", "staging")
print("still frozen:", [t.agent_id for t in api.bulk.get(preview.bulk_id, alice).targets])

# 4. Alice tries to approve her own change, even with an approver role.
try:
    api.bulk.decide(preview.bulk_id, True, Operator(operator_id="alice", role="approver"))
except ConfigurationError as error:
    print("self-approval rejected:", error)

# 5. Bob reviews and approves.
api.bulk.decide(preview.bulk_id, True, bob)

# 6. Alice runs the approved change.
result = api.bulk.execute(preview.bulk_id, alice)
for target in result.targets:
    print("result:", target.agent_id, target.outcome)

# 7. Check the blast radius: what changed and what did not.
for agent_id in ("checkout-agent", "search-agent", "checkout-agent-prod"):
    values = api.config.get(agent_id, "agenticlens").values
    print("config:", agent_id, values)

# 8. Read the audit trail.
for event in api.bulk.get(result.bulk_id, alice).events:
    print("audit:", " ".join(filter(None, [event.event, event.operator_id, event.agent_id])))
```

## Expected output

```text
frozen targets: ['checkout-agent', 'refund-agent', 'triage-agent']
status: pending
still frozen: ['checkout-agent', 'refund-agent', 'triage-agent']
self-approval rejected: Approval requires a different operator
result: checkout-agent succeeded
result: refund-agent succeeded
result: triage-agent succeeded
config: checkout-agent {'enhanced_tracing': True}
config: search-agent {}
config: checkout-agent-prod {}
audit: bulk.previewed alice
audit: bulk.approved bob
audit: bulk.claimed alice
audit: target.succeeded alice checkout-agent
audit: target.succeeded alice refund-agent
audit: target.succeeded alice triage-agent
audit: bulk.completed alice
```

## Verify it worked

1. `frozen targets` lists only the three staging agents: the production agent was
   never selected.
2. `still frozen` is unchanged after `search-agent` registered: approval covers
   the list that was reviewed, not whatever matches the filter later.
3. `self-approval rejected`: the proposer cannot approve their own batch, even
   with an approver role.
4. All three targets report `succeeded`, and `checkout-agent` now has
   `enhanced_tracing: True`.
5. `search-agent` and `checkout-agent-prod` have empty settings: nothing outside
   the approved list changed.
6. The audit trail names Alice as proposer and executor and Bob as approver, with
   one event per agent.

## Clean up

The API was in memory, so nothing was stored. Remove the script and environment:

```bash
rm fleet_change_walkthrough.py
deactivate && rm -rf .venv
```

## Variations and next steps

- **On a server:** save the request as `fleet.json` (see
  `examples/bulk_tracing.json`) and run `bulk preview fleet.json` with a writer
  token, `bulk approve BULK_ID` with a separate approver token, then
  `bulk execute BULK_ID` and `bulk get BULK_ID`. The server needs distinct
  `AGENTICOPS_WRITE_TOKEN` and `AGENTICOPS_APPROVAL_TOKEN` values.
- **Say no:** call `api.bulk.decide(preview.bulk_id, False, bob)` instead. The
  batch is denied and execute is refused.
- **One agent changes in between:** if one target's settings are changed after
  approval, that target reports `failed` and the others still succeed. There is
  no fleet-wide rollback. The repository's `examples/fleet_operations.py` shows
  this case.
- **Stop agents instead of changing them:** set `operation` to `runtime.stop`
  with a Sidecar containment adapter installed per agent. See
  [Fleet operations](https://deepagentlabs.io/control-tower/docs/fleet-operations/).

## Tested with

- agenticops-control-tower 0.8.0 installed with `python -m pip install .` as in [Prerequisites](#prerequisites), Python 3.13.15, Linux, base dependencies only, verified 2026-10-25. The output matched [Expected output](#expected-output) exactly; the server-based variation was not run.
