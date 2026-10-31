# MCP 0.5.0 hosted access control

[MCP 0.5.0](https://github.com/DeepAgentLabs/mcp-server/releases/tag/v0.5.0) completes MCP Phase 5 with hosted access control. Each hosted key can carry allow and deny tool globs, an expiry and a task scope. The server enforces them at dispatch, outside the model: before each hosted handler runs, it re-authenticates the key and reloads its policy. Revocation, a narrower policy or expiry therefore stops queued calls, retries and calls on existing connections. Calls already running finish. Denied calls return an MCP-local `mcp.access-decision.v1` record, and every hosted call logs `dispatch`/`completion` records that share a `correlation_id`. These records are not AIOS artifacts. `core.access_status` reports a key's effective policy, and operators use `deep-agentic-core-mcp-admin` to narrow or revoke a key by user ID.

## What changes for Tower

- `MCPAccessRevoker` is unchanged. It still revokes a task's hosted key through
  the key store's `revoke(user, token)` and confirms the revocation with
  `authenticate`. From MCP 0.5.0 that revocation also rejects calls already
  queued for that key, and each rejected call returns a
  `revocation_acknowledged` record.
- `mcp.access-decision.v1` records carry `correlation_id`, `subject` (the MCP
  user ID) and `task_id`, so log pipelines can join them to Tower containment
  actions. Tower does not ingest them yet. A shared AIOS evidence format comes
  first.
- Operators can also revoke or narrow a key with `deep-agentic-core-mcp-admin`,
  using MCP's store credentials and not the agent's key.
- The `tower.*` connector tools are unchanged and remain local-only. Hosted
  `tower.*` with per-user Tower credentials moves to MCP Phase 6.

## Compatibility

MCP 0.5.0 is within Tower's `deep-agentic-core-mcp>=0.3.6,<1` range, and the full
Tower suite passes against it (`uv run --with deep-agentic-core-mcp==0.5.0 pytest`).
No Tower change or release is needed.

See the [MCP hosted access control guide](https://github.com/DeepAgentLabs/mcp-server/blob/v0.5.0/docs/access-control.md).
