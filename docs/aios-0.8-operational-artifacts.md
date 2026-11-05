# AIOS operational-artifact compatibility

AIOS repository v0.8.1 distributes the v0.8.0 schema snapshot under MIT.
Run/Workflow remain **0.4-draft**, provenance **0.6-draft**, and operational
companions **0.8-draft**. Independent acceptance and coordinated v1.0 gates remain open.

## Incidents and investigations

Tower 0.11.0 ships `incidents.export.export_investigation_report` for held native Incidents. It preserves native state, same-deployment citations and attributed observations with redacted summaries. Closure alone does not prove recovery. A supported native verification conclusion is cited separately from deployment health. Native readers do not become AIOS validators.

## Adoption and validation

See [coordinated readiness and examples](coordinated-v1-readiness.md) for the
public API and migration path. The [canonical schemas and rules](https://github.com/DeepAgentLabs/ai-operations-spec/tree/v0.8.1/specification/v0.8)
define the projection contract. Source and citation presence do not authenticate
a producer or verify its conclusion. Reference URIs are not instructions to
fetch or execute anything. Use Lens or MCP for optional schema and semantic
checks; source/native identity and unavailable/unknown states remain explicit.

## Dependencies and rollback

The implementation is released in the owning package's minor version, with no
AIOS Python runtime dependency. Native contracts retain their own versions.
Disable optional companion emission or pin the preceding package version to
roll back; do not relabel a companion as an older artifact family.
