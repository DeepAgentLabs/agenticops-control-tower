# AI Reference capability index

This index opens the generated [AI Reference (robust)](https://deepagentlabs.io/control-tower/docs/llms-full.md). In that raw Markdown file, **Full reference** identifies an included topic section; **Source** links to the maintained document. Use the [Developer Guide (simple)](developer-guide.md#capability-index) for short workflows.

## Capability index

| Capability | Included scope | Detailed reference |
| --- | --- | --- |
| Agent registration and heartbeats | Register deployment identity and merge runtime-reported heartbeat metadata. | <a href="#registration-and-getting-started">Full reference</a> · [Source](getting-started.md) |
| Fleet health and version assessment | Filter fleet status/capability coverage and compare reported PEP 440 versions. | <a href="#api-reference">Full reference</a> · [Source](api-reference.md) |
| Capability discovery and contract | Read the versioned candidate registration/heartbeat contract and schemas. | <a href="#capability-discovery-contract">Full reference</a> · [Source](capability-contract.md) |
| Offline snapshots | Inspect captured inventory, heartbeat history and evidence without a server. | <a href="#evidence-ingestion-and-posture">Full reference</a> · [Source](evidence-posture.md) |
| Authentication and operator roles | Separate reader, writer and approver credentials and trusted operator identities. | <a href="#authentication-and-roles">Full reference</a> · [Source](authentication.md) |
| Configuration ownership and desired state | Declare Tower-owned or mirrored settings and preview bounded desired-state changes. | <a href="#controlled-configuration">Full reference</a> · [Source](configuration.md) |
| Exact approval lifecycle | Bind immutable previews, revisions, expiry and one-time approval to the intended change. | <a href="#controlled-configuration">Full reference</a> · [Source](configuration.md) |
| Bulk fleet operations | Freeze deployment targets, approve once and report bounded per-target results. | <a href="#bulk-fleet-operations">Full reference</a> · [Source](fleet-operations.md) |
| Runtime stop and access revocation | Coordinate host-installed Sidecar stop and MCP revocation without inferring cancellation. | <a href="#incident-investigation-and-staging-recovery">Full reference</a> · [Source](incident-recovery.md) |
| Evidence ingestion and posture | Push attributed native observations and retain freshness, availability and native outcome tallies. | <a href="#evidence-ingestion-and-posture">Full reference</a> · [Source](evidence-posture.md) |
| Native artifact readers and schemas | Read Lens/Evals/Sidecar/Chaos artifacts with explicit owner/correlation boundaries. | <a href="#ecosystem-evidence-boundaries">Full reference</a> · [Source](ecosystem-alignment.md) |
| Lens execution verification | Verify expected-run bundles using host trust keys and preserve distinct verification states. | <a href="#lens-execution-verification">Full reference</a> · [Source](lens-execution-evidence.md) |
| Incident detection and investigation | Create durable incidents from native failures and assemble cited, uncertain investigations. | <a href="#incident-investigation-and-staging-recovery">Full reference</a> · [Source](incident-recovery.md) |
| Approved staging recovery | Run the fixed bounded staging dependency action through an installed connector. | <a href="#incident-investigation-and-staging-recovery">Full reference</a> · [Source](incident-recovery.md) |
| Periodic detection and alerts | Scan stored observations, deduplicate/acknowledge alerts and join incident timelines. | <a href="#live-detection-and-incident-views">Full reference</a> · [Source](live-operations.md) |
| Versioned runbooks | Discover, validate, recommend, preview and execute installed versioned runbooks. | <a href="#runbook-execution-and-recovery">Full reference</a> · [Source](runbooks.md) |
| Cancellation, compensation and reconciliation | Cancel between bounded steps, compensate known completions and reconcile unknown execution. | <a href="#runbook-execution-and-recovery">Full reference</a> · [Source](runbooks.md) |
| Recovery verification | Require a successful probe and fresh same-run Lens/Evals evidence before resolution. | <a href="#incident-investigation-and-staging-recovery">Full reference</a> · [Source](incident-recovery.md) |
| Read-only console | Inspect fleet, evidence, alerts, incidents and runbook state through authenticated reads. | <a href="#live-detection-and-incident-views">Full reference</a> · [Source](live-operations.md) |
| MCP operator integration | Expose Tower evidence/recovery through separate MCP tools while keeping approval human-only. | <a href="#mcp-investigation-connector">Full reference</a> · [Source](mcp-connector.md) |
| AIOS investigation-report export | Project a held native Incident with redacted summaries and explicit citations. | <a href="#aios-export-and-coordinated-readiness">Full reference</a> · [Source](coordinated-v1-readiness.md) |
| Python, HTTP and CLI surfaces | Use one control model through the facade, authenticated API or operator CLI. | <a href="#api-reference">Full reference</a> · [Source](api-reference.md) |
| Persistence and hosting | Persist local SQLite state and host the API/console with deployment-owned access. | <a href="#hosting-the-api-and-console">Full reference</a> · [Source](hosting.md) |
| Settings and operational limits | Configure server/client options, detection windows, quotas and optional verification trust. | <a href="#server-and-client-settings">Full reference</a> · [Source](settings.md) |
| Compatibility and acceptance | Distinguish candidate inventory interoperability from production/runtime or AIOS certification. | <a href="#candidate-validation-record">Full reference</a> · [Source](phase10-validation.md) |

## How to use the robust reference

1. Select a capability, then read its prerequisites, payload/role requirements, transitions, output meaning and operational limits. Complete CLI/HTTP inventories supplement the focused API examples.
2. Consult **Source declarations: src/agenticops_control_tower/...** for current statically extracted signatures, models and exports from every package module. Extraction imports no product code. Internal helpers remain internal; their appearance is not a public API or new HTTP operation.
3. Consult **Data contract: src/.../schemas/evals/...** for both bundled Evals-native schemas. Tower's capability descriptor dynamically supplies its own candidate inventory schemas. Tower-local evidence/approval/runbook contracts and AIOS `0.8-draft` projections are distinct artifact families with independent versions and owners.
4. Preserve deployment attribution, producer-native conclusions, explicit operator identity, connector installation and approval boundaries. Evidence references are labels, not paths to open or URLs to fetch. Configuration execution commits desired state; actual remote effects require the explicitly supported runtime connector.
5. Distinguish reported health, evidence freshness/authenticity, operator approval, execution receipt and verified recovery. Historical release/validation sections record their stated environments and do not establish production connector or independent ecosystem acceptance.
6. Verify `ai-docs-manifest.json` before ingestion. It records normalized source hashes and the generated reference checksum, including the downloadable snapshot example.

## Maintaining coverage

`docs/ai-docs.json` selects full topic/operator/integration guides, all package Python modules and both bundled native schemas. Keep both indexes and CLI/HTTP inventories aligned with new user-facing surfaces. From this repository root, regenerate with the shared sibling documentation checkout and Python 3.11 or newer:

```bash
python3 ../deepagentlabs.github.io/scripts/build_ai_docs.py --sources .. --project agenticops-control-tower
python3 ../deepagentlabs.github.io/scripts/build_ai_docs.py --sources .. --project agenticops-control-tower --check
```

The shared site publishes the robust pack verbatim as a raw Markdown download, separate from rendered pages/search.
