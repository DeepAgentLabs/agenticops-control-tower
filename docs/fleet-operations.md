# Fleet operations — 0.7.0

Tower freezes an explicit, sorted deployment list before any fleet mutation.
Use `api.bulk` in Python or the authenticated HTTP/CLI surface. The console
remains read-only. Fleet commands are Tower-local contracts, not AIOS schemas.

## Preview, approve, execute

Install `agenticops-control-tower[api]`. Configure distinct
`AGENTICOPS_WRITE_TOKEN` and `AGENTICOPS_APPROVAL_TOKEN` on the server.
The trusted host must declare Tower-owned desired settings through
`api.config.declare(Configuration(..., authority="tower"), writer)` first;
HTTP cannot elevate mirrored configuration into writable ownership.

Save this as `fleet.json` (also in `examples/bulk_tracing.json`):

```json
{
  "intent": "Enable enhanced tracing for staging Lens deployments",
  "selector": {"environment": "staging", "capability": "agenticlens"},
  "operation": "config.update",
  "patch": {"values": {"enhanced_tracing": true}},
  "expires_in_seconds": 300
}
```

```bash
agenticops-control-tower --token "$WRITER_TOKEN" bulk preview fleet.json
# Inspect targets, before/after settings, expiry, and reconciliation; copy bulk_id.
agenticops-control-tower --token "$APPROVER_TOKEN" bulk approve BULK_ID
agenticops-control-tower --token "$WRITER_TOKEN" bulk execute BULK_ID
agenticops-control-tower --token "$READER_TOKEN" bulk get BULK_ID
```

`bulk deny` and `bulk revoke` use the approver credential. The proposer cannot
approve their own batch, even using a Python identity with another role. Approval
covers the persisted preview; execute accepts only its ID and no replacement
selector or patch. CLI execution exits 1 when any target is unsuccessful, while
still printing all results. HTTP returns the durable results with status 200;
rejected state transitions return 409. Missing/invalid credentials return 401.
Anonymous local mode cannot perform fleet commands.

HTTP equivalents: `POST /bulk/preview`, `GET /bulk/{id}`,
`POST /bulk/{id}/approval` with `{"approved": true|false}`,
`POST /bulk/{id}/revoke`, and `POST /bulk/{id}/execute`. Approval is never
available through an MCP tool. Offline snapshots cannot operate on batches.

## Deterministic targeting and audit

Environment and installed capability are required and combined with AND.
Optional `agent_ids` restricts the selection; every explicit ID must match.
Duplicates are deduplicated, IDs sort lexically, and 1–100 matches are required.
New registrations after preview never join a batch. Execution rechecks expiry,
environment, capability version, runtime, framework and registration time for
each deployment, and checks the exact before-configuration and revision.
A failed target does not prevent remaining targets from being attempted.
Writer and approver scopes must each include the entire frozen list. Scoped
Python readers must also cover all targets; server bearer roles are global.

The batch retains intent, request, frozen deployment identities, command IDs,
proposer, decision actor, child configuration previews, per-target outcomes and
attributed timestamped events. `GET /bulk/{id}` is the durable audit/readback
path. Per-agent `/agents/{id}/audit` also records execution outcomes. Persist
with `serve --database tower.db`; batch and configuration writes share the same
SQLite transaction mechanism. Deployment health and evidence verdicts stay
independent of fleet operation results.

## Bulk stop and MCP revocation

Set `operation` to `runtime.stop`, omit the patch, and choose
`acknowledgement_seconds` (0.01–30, default 5). The trusted host installs a
`SidecarContainmentAdapter` per deployment with
`api.bulk.install(agent_id, adapter)`. Its Sidecar TaskRuntime must have an
issuer-backed `mcp` revoker; see [incident recovery](incident-recovery.md).
No caller-provided paths, commands, endpoint URLs or credentials are accepted.
A stop request blocks dispatch and requests configured MCP access revocation;
there is no standalone arbitrary credential-revocation or bulk restart endpoint.

Each target records requested then acknowledged, failed, unsupported, incomplete,
or timed_out; unrecognized receipts are unknown. Late receipts are durably
recorded in the target receipt and audit without replacing a timed_out outcome. In-flight calls and unsupported
downstream credentials stay explicit. A boundary acknowledgement does not prove
end-to-end containment or verified incident recovery. Missing adapters are
unsupported. Connector exceptions produce a generic failure without persisting
exception text. Acknowledgement waiting is bounded per target; a timed-out host
call may still finish. At most 16 host calls can remain outstanding per process;
capacity exhaustion records failed without dispatch. Host adapters must themselves
bound their network/runtime calls. This is synchronous sequential execution with an overall `execution_seconds`
budget (0.01–30, default 30). Each acknowledgement wait is capped by the
remaining budget; remaining targets fail without dispatch after it expires.
Storage work adds overhead to that budget. CLI execution allows a 60-second
HTTP timeout. This is not a background distributed scheduler.

## Partial failure, rollback and interruption

There is no fleet atomicity or automatic rollback. Successful desired-setting
updates remain committed; Tower does not assert remote application. To roll back,
preview a new batch with explicit previous values or the opposite capability
toggle and obtain a new approval. `config.update` merges keys and does not delete
keys. Runtime stop has no automatic rollback or restart.

Only one executor can consume an approval. Revocation is allowed before claiming,
not after execution starts. SQLite atomically commits each desired change with
its outcome, preventing reapplication after a crash. Runtime dispatch records
requested durably before calling the host, never automatically retries, and
persists the receipt afterward. If interrupted, the batch remains executing;
completed targets remain visible, requested means uncertain, and pending means
unattempted. Read it with `bulk get`; reconcile actual host state before creating
any newly approved action for unfinished targets. Never blindly retry a timed-out
or requested stop. No automatic resume is provided in 0.7.0.

## Sibling compatibility

All existing extras remain optional and their ranges remain sufficient. Lens
traces, Evals reports/gates, Sidecar decisions and Chaos events keep their native
meaning. Tower does not invoke their analysis/evaluation/fault engines for fleet
configuration. Local MCP 0.3.6 investigation tools remain compatible with Tower
0.7.0; new fleet endpoints are HTTP/CLI/Python-only and hosted MCP restrictions
remain in place. AIOS shared command semantics remain draft; no conformance claim
or new normative schema is introduced. No sibling patch release is required for
these documentation-only integration updates.

Run `uv run python examples/fleet_operations.py` for an offline, deterministic
preview → approval → partial failure → readback demonstration.
