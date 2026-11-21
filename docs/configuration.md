# Configuration and controlled actions

Tower is authoritative only for settings explicitly declared `authority="tower"`
by trusted Python setup. `mirrored` settings belong to their producer; absent
surfaces return `unsupported` and an honest reason. Ownership cannot be elevated
through HTTP. The base package imports no sibling runtime for ordinary native artifact reading. Current optional dependency ranges are declared in `pyproject.toml`; they do not install a production configuration connector.

Run `examples/controlled_configuration.py` to declare a desired configuration,
preview an update, approve it as a different operator and execute it. A patch is
a shallow key replacement; JSON null is a value, not deletion. Capability
`enable`/`disable` sets desired state only and never edits heartbeat inventory.

An immutable stored preview binds target deployment/environment, capability,
operation, parameters, before/after values, impact, revision and expiry (1–3600
seconds). Returned models are copies. Writer and approver roles are distinct;
self-approval is rejected. Optional Python `Operator.agent_ids` limits deployment
scope. Trusted Python callers are responsible for authenticating their operators.
HTTP derives identities from configured server tokens, ignoring client identity
claims. Its two service identities have fleet-wide scope; per-user and task-scoped
credentials are future work. Use HTTPS remotely.

A pending action can be approved or denied. Pending/approved actions can be
revoked. Execution requires approved, unexpired state and an unchanged target and
configuration revision. Approval is consumed once. To change a proposal, create a
new preview. Re-registering an environment invalidates an environment-bound action.
There is no direct update or toggle endpoint bypassing approval.

Configure `AGENTICOPS_WRITE_TOKEN`, `AGENTICOPS_READ_TOKEN` and a distinct
`AGENTICOPS_APPROVAL_TOKEN`. Anonymous development mode supports inventory writes
but does not authorize configuration actions. Approval credentials can read but
cannot register agents or execute changes. A writer cannot approve changes.

| HTTP | Purpose |
|---|---|
| `GET /agents/{id}/config/{capability}` | Ownership, desired values and revision |
| `POST /actions/preview` | Body matching `ActionRequest` |
| `GET /actions/{id}` | Inspect exact stored proposal |
| `POST /actions/{id}/approval` | `{"approved": true}` or `false` |
| `POST /actions/{id}/revoke` | Revoke pending/approved proposal |
| `POST /actions/{id}/execute` | Consume approval and commit desired settings |
| `GET /agents/{id}/audit` | Declaration, lifecycle and rejected commands |

CLI equivalents: `config AGENT CAPABILITY`, `actions preview REQUEST.json`,
`actions get|approve|deny|revoke|execute ID`, and `audit AGENT`. Pass the appropriate
credential through `AGENTICOPS_TOKEN`. Offline snapshots do not include settings,
approvals or audit records and reject configuration commands.

`--database`/`AGENTICOPS_DATABASE` persists registry and configuration tables in
one SQLite file. Transactions serialize configuration changes across processes.
Without a database, each facade has isolated memory state. Configuration changes,
approval consumption and success audit commit together; any storage exception
rolls them back and propagates. There is no local partial success. Rejected domain
commands for known targets are audited with generic details; malformed requests,
invalid credentials and unknown actions are rejected before domain audit.
Previews include settings; audit records contain lifecycle metadata, not setting
values. Avoid storing secrets in configuration. Capability identifiers use the
same URL-safe syntax as agent IDs and are required in action targets.

The execution result explicitly states that remote application is unverified.
`failed`/`partial_failure`, rollback and reconciliation fields are reserved for
future remote adapters. No remote adapter is shipped; Tower never claims a remote
rollback or recovery. Separate host-installed Sidecar stop/MCP revocation coordination is implemented through incident and bulk runtime-control paths; see [incident recovery](incident-recovery.md) and [fleet operations](fleet-operations.md). It does not turn desired configuration into generic remote application or guarantee remote rollback. The console still sends GET only.
