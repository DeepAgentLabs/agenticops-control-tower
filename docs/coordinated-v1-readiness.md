# Coordinated v1.0 engineering readiness

Tower 0.11.0 adds
`agenticops_control_tower.incidents.export.export_investigation_report(incident, created_at=...)`.
Pass a held Incident obtained through an authorized native reader. This pure
projection does not fetch paths/URIs or execute recovery. It preserves native
incident state, affected deployment, producer attribution, observation times and
source references; summaries, findings, missing-input text and event details are
redacted. Native citations must name supplied same-deployment evidence and all
observation times precede recording.

Report-local evidence ids use disjoint record/event prefixes; findings and
timeline entries have their own prefixes. Incident closure alone yields unknown
recovery. A native verification.resolved event in a resolved incident is cited
as the native recovery conclusion, without recomputing or authenticating it.
This is distinct from proving that recovery actually succeeded. Run
`python examples/operational_artifacts.py` for the offline projection.

Migration/rollback: existing inventory, capability, incident, evidence and
storage contracts are unchanged. Disable the optional export and pin 0.10.0 to
roll back. Native evidence outcomes remain separate from deployment health.
Production connectors, distributed storage and per-agent tenancy remain outside
this local candidate; see the supported capability guide.

Independent acceptance, live/deployment evidence and the stable freeze remain
separate gates. See the [shared release policy](https://github.com/DeepAgentLabs/.github/blob/main/profile/RELEASE_POLICY.md).
