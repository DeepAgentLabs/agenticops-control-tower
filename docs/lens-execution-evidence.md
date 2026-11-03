# Lens execution evidence

Tower accepts attributed `execution_bundle` evidence from Lens through the
existing Python and authenticated HTTP evidence-ingestion APIs. Supply a Lens
`ExecutionBundle` as `artifact`, `link.source="agenticlens"`,
`link.artifact_type="execution_bundle"`, the expected `link.run_id`, and
`link.spec_version="0.4-draft"`. References are labels: Tower never fetches them.

Configure trusted keys only on the host:

```python
store = EvidenceStore(registry, database_path, trusted_lens_keys={"capture-2026-11": key})
# Or when constructing the HTTP server:
app = create_app(database_path=database_path, trusted_lens_keys={"capture-2026-11": key})
```

For CLI/server startup, `AGENTICOPS_LENS_TRUST_STORE` can name a protected JSON
file mapping key IDs to hex keys. It is read once when the HTTP app is created;
restart the app after changing that file. Invalid configuration fails startup.

Use `ControlTowerAPI(..., evidence_store=store)` to share the configured store
with the facade and HTTP surface. When passing an existing API to `create_app`,
its store owns trust configuration; do not pass a second key map.

Lens is optional; install Lens >=0.12,<1 for its execution-verification API.
Absent/older Lens yields unknown/unavailable, rather than trusting the caller.
The host provides the key map; no HTTP request field configures trust. Use
32-byte or longer random HMAC keys, rotate key IDs and retain historical keys
for the evidence retention period. HMAC verifiers can also authenticate new manifests;
this is trusted-host symmetric authentication, not independent public signing.

Tower calls Lens to verify authentication, AIOS schema/semantic alignment and
agreement between the native evidence and its projection. Only verified bundles
produce available evidence. Failed, unknown and incomplete results are persisted
with their distinct verification states and no causal claims. Verified projections
retain run/trace IDs and causal event/action/decision/policy/actor/approval links;
native payloads, arbitrary attributes and recorded outputs are not persisted.
Per-source posture includes separate verification counts. Fleet health, native
Evals gates and recovery verification rules do not change.

Records are historical verification results at ingestion time. Key revocation
or rotation does not retroactively rewrite persisted results. Reverify and submit
a new attributed observation with a new observed time/ref when trust changes;
an idempotent retry returns the original record. No completeness of actual
execution, containment result, live Sidecar bridge or recovery is inferred.
