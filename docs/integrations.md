# Integrations

Control Tower stays usable on its own: the base package imports no sibling
package. Sibling results reach Tower as **native JSON artifacts that you push**,
and the MCP server reaches Tower over its HTTP API. Tower never fetches from,
reconfigures or recomputes the verdicts of another package.

| Package | How it connects | Direction | Guide |
| --- | --- | --- | --- |
| **AgenticLens** | Run and diagnosis reports pushed as `agenticlens` evidence. A fresh failed run raises a `lens.failed` alert. | Push into Tower | [Evidence posture](evidence-posture.md), [Live operations](live-operations.md) |
| **Agentic Evals** | Evaluation reports plus an existing `GateDecision`, pushed as `agentic-evals` evidence. | Push into Tower | [Evals report contract](evals-report-contract.md) |
| **Agentic Sidecar** | Decisions, or a whole journal export via `evidence ingest-sidecar-journal`. | Push into Tower | [Evidence posture](evidence-posture.md), [Sidecar 0.9](sidecar-0.9.md) |
| **Agentic Chaos** | Chaos reports pushed as `agentic-chaos` evidence. A completed report plus a passing same-run Evals gate can be recorded as runbook validation. | Push into Tower | [Chaos 0.9](chaos-0.9.md) (earlier: [0.8](chaos-0.8.md)), [Runbooks](runbooks.md#chaos-and-evals-validation) |
| **Agentic MCP** (`deep-agentic-core-mcp`) | `tower.*` tools call Tower's HTTP API with a reader (and optionally writer) token. Local only; the hosted MCP endpoint rejects Tower tools. From MCP 0.5.0, `MCPAccessRevoker` revocation also stops queued hosted calls ([MCP 0.5](mcp-0.5-access-control.md)). MCP 0.5.1 adds `tower.runbook*` tools for Tower 0.9 runbooks. | MCP → Tower | [MCP connector](mcp-connector.md) |
| **AI Operations Specification** | Shared semantics reference; Tower's fleet and bulk contracts are Tower-local, not AIOS schemas. | Reference | [AIOS v0.6](aios-v0.6.md), [AIOS v0.6.1](aios-0.6.1.md) |

## Optional extras

The package declares optional extras that install a sibling next to Tower, so
your pipeline can produce artifacts in the same environment. Tower itself still
reads only the JSON.

| Extra | Installs |
| --- | --- |
| `api` | `fastapi`, `uvicorn`, `httpx` (server, server-mode CLI, console) |
| `agenticlens` | `agenticlens>=0.7,<1` |
| `agentic-evals` | `agentic-evals>=0.7.2,<1` |
| `agentic-sidecar` | `agentic-sidecar>=0.7,<1` |
| `agentic-chaos` | `agentic-chaos>=0.5,<1` |
| `deep-agentic-core-mcp` | `deep-agentic-core-mcp>=0.3.6,<1` |

## Attribution

Every pushed artifact carries an `EvidenceLink`: the Tower `agent_id` it belongs
to, the `source` package and `source_version`, the artifact type, a stable
`artifact_ref` you own and the `observed_at` time, with optional `run_id` and
`runtime_agent_id` for correlation. Tower validates the artifact against the
producer's native shape; anything it cannot read is stored as **unavailable**
instead of guessed. See [ecosystem alignment](ecosystem-alignment.md) for every
field and reader rule.

## Your own agents and pipelines

Agents register and send heartbeats over HTTP with the writer token. Any HTTP
client works; the payloads are the JSON shapes in `examples/`. A minimal
heartbeat body is:

```json
{"status": "healthy", "capabilities": {"agenticlens": "0.7.0"}}
```

Compatibility with specific sibling releases is recorded per release under
**Ecosystem compatibility** in the navigation, starting with
[Tower 0.9 compatibility](tower-0.9-compatibility.md) (earlier:
[Tower 0.8](tower-0.8-compatibility.md)).
