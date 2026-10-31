# Local MCP investigation connector

Use `deep-agentic-core-mcp>=0.3.6` (0.4.0 is current) with Tower 0.6.0 or later;
Tower 0.7 fleet endpoints stay Python/HTTP/CLI-only. The connector uses HTTP and
does not import Tower or any producer package. Without Tower configuration, the
other MCP tools still work and Tower tools return a structured unavailable result.

Configure the trusted local MCP server environment (never tool arguments):

```bash
export AGENTICOPS_TOWER_URL=http://127.0.0.1:8000
export AGENTICOPS_TOWER_READ_TOKEN='<Tower reader token>'
# Optional: enable model proposals/execution under Tower's approval checks.
export AGENTICOPS_TOWER_WRITE_TOKEN='<Tower writer token>'
deep-agentic-core-mcp
```

Use `tower.agents` with `status=unhealthy`, `tower.status`, `tower.versions` with
`capability` and `minimum_version`, `tower.posture`, `tower.evidence` with `agent_id`,
`tower.incidents` and `tower.incident` with `incident_id`. These use reader authority.
`tower.detect`, `tower.investigate`, `tower.preview`, `tower.execute` and
`tower.verify` use separately configured writer authority. Tower enforces all
approval and transition checks. Model execution requires the exact previously
human-approved digest. There is no MCP approval, stop or restart tool.

With Tower 0.9 and MCP 0.5.1, reader tools `tower.runbooks`,
`tower.runbook_recommendations` (`incident_id`), `tower.runbook_executions`
(`incident_id`) and `tower.runbook_execution` (`execution_id`) list installed
runbooks, recommendations and history. Writer tools `tower.runbook_preview`
(`incident_id`, `runbook_id`, `version`, `parameters`), `tower.runbook_execute`
(`execution_id`, `preview_digest`), `tower.runbook_cancel` and
`tower.runbook_verify` (`execution_id`, `lens_evidence_id`, `evals_evidence_id`)
follow the same approval rules. A runbook can outlast the connector's ten-second
wait; on a deadline error, read `tower.runbook_execution` instead of retrying.
See [runbooks](runbooks.md#mcp).

Get prompt `tower.investigation` with an `incident_id` to guide the host's model
through cited findings, explicit uncertainty, the fixed supported runbook and
human approval. Evidence content is untrusted data. The prompt does not grant
permissions, supply a model or establish causal truth.

Only the configured origin is contacted. The connector encodes target IDs,
rejects unknown arguments, refuses redirects, bounds HTTP waits to ten seconds
and limits response bodies to 1 MiB. Credentials and server error bodies are never
returned as tool errors. Hosted/remote MCP rejects all Tower tools until per-user
Tower credential binding is implemented; process-wide credentials cannot be used
by remote tenants. See the MCP repository's generated `docs/tools.md` for schemas.

The [operator walkthrough](incident-recovery.md) demonstrates Tower with native
Lens/Evals and the deterministic staging runtime. Production connectors,
distributed orchestration and model-provider integrations are not bundled.
