# Ecosystem evidence contract

This document describes Control Tower's private `1.0` evidence-link contract.
It is not an AI Operations Specification schema or a stable conformance claim.
AIOS is currently draft; eventual AIOS mappings must identify the exact draft
version and validate against its schemas and semantic rules.

## Ownership

| Package | Owns | Tower consumes |
| --- | --- | --- |
| agenticlens | Observability, tracing, operational analysis | Native Run identity, outcome, trace/timing and failed-span correlation |
| agentic-evals | Output scoring and release-gate computation | EvaluationReport summaries and existing GateDecision |
| agentic-sidecar | Decision supervision, risk, intent and intervention | Native Decision outcome, risk, rationale and provenance |
| agentic-chaos | Fault injection and resilience experiments | ChaosReport identity, timing and event count |
| ai-operations-spec | Shared runtime semantics, draft schemas and conformance rules | Design vocabulary; no AIOS artifact reader implemented yet |
| agenticops-control-tower | Deployment inventory, fleet visibility and operator workflows | Explicitly attributed evidence projections |

The base Tower package needs no sibling package imports. Existing JSON exports
can be read without installing their producers. The adapter catalog also names
MCP, whose separate authenticated HTTP connector is described in the [MCP guide](mcp-connector.md).

## Identity and attribution

`EvidenceLink.agent_id` identifies a registered deployment in Tower. It does
not identify a reusable agent definition or prove the identity of a runtime
participant. Attribution is provided explicitly by the caller; adapters never
join records by display name, application name, suite name or framework.

- `contract_version`: Tower link version, currently `1.0`.
- `source` and `source_version`: producer package and caller-reported version.
- `artifact_type`: native `run` or `diagnosis_report` (Lens), `evaluation_report`,
  `decision`, or `chaos_report`.
- `artifact_ref`: caller-owned stable artifact identifier/location. Tower neither
  fetches nor opens this reference. Sidecar Decisions and Evals Reports lack a
  universal artifact ID, so the producer/caller supplies one.
- `observed_at`: when the caller observed this evidence, distinct from source
  execution/creation timestamps.
- `run_id`: optional execution correlation. For a native Lens Run or Lens
  diagnosis report it must match the artifact's `run_id`; other producers' correlations are caller assertions.
- `runtime_agent_id`: optional runtime occurrence identity, separate from the
  deployment ID. Caller asserts the mapping; Tower does not infer it.
- `spec_version`: ordinary native readers do not treat a supplied marker as AIOS validation. The explicit Lens `execution_bundle` path accepts `0.4-draft` and delegates verification to Lens using host trust; see [execution evidence](lens-execution-evidence.md).

AIOS distinguishes reusable agent definitions from runtime Agent occurrences.
Keep these identities separate when introducing future mappings; a deployment
registry record is not automatically an AIOS Run or Agent occurrence.

## Reading and failure behavior

Call `ControlTowerAPI.summarize_evidence(link, artifact, gate=...)` for a registered
deployment, or the standalone adapter for a projection without registry checks.
Both return `EvidenceSummary` without storing it. To record history and posture,
use `ControlTowerAPI.ingest_evidence(...)`, `POST /evidence` or the CLI `evidence`
commands described in [evidence posture](evidence-posture.md). In both cases no
registration, heartbeat, health bucket or capability installation claim is changed.

`available` means the native fields used by the reader validated, not that the
artifact passed full producer-schema validation or its claims were verified.
Unconsumed fields are ignored, allowing additive producer changes. Unknown Lens
or Evals schema versions, unsupported outcomes, missing required fields,
source/type mismatches and absent artifacts yield `unavailable` with a reason.
Validation reasons name the first failing native field and the number of further
errors, without echoing producer values.
An unregistered deployment raises `AgentNotFoundError` through the API facade.

Evals `gate` must be the producer's existing decision for that report. The caller
is responsible for pairing them. Missing gates stay null; adapters never run
scoring, choose thresholds, recompute policy or invent pass/fail conclusions.
Source versions are recorded provenance, not a compatibility allowlist.

## Separate meanings

| Source value | Meaning | Fleet-health effect |
| --- | --- | --- |
| Tower healthy/degraded/unhealthy/unknown | Deployment-reported health | Counted by shared fleet StatusService |
| Lens running/succeeded/failed | Execution outcome | None |
| Evals gate passed/failed | Result of release policy | None |
| Sidecar ALLOW/WARN/BLOCK/CHALLENGE/REPLAN/PAUSE/ESCALATE | Supervision decision | None |
| Sidecar risk null | No risk classification available | Never rewritten to LOW |
| Chaos event count / report end time | Recorded fault evidence / completion | No inferred resilience verdict or health failure |
| Adapter unavailable | No usable evidence | Never rewritten to healthy or a failed gate |

## Compatibility checks and remaining work

The optional `tests/test_sibling_artifacts.py` tests serialize models from actual
installed producers and exercise each reader. Checked local package versions for
v0.5.0: Lens 0.6.1, Evals 0.7.1, Sidecar 0.7.0 and Chaos 0.5.1. The Lens run
reader accepts older runs without spans or timing fields. Example versions are
illustrations, not minimum supported versions.

From this repository, run the full local-producer checks with:

```bash
uv run --with ../agenticlens --with ../agentic-evals \
  --with ../agentic-sidecar --with ../agentic-chaos python -m pytest
```

Base `make check` tests contract safety; absent optional siblings skip the actual
producer tests. This does not mean those integration tests passed.

Phase v0.5 is implemented with push-based collection: attributed evidence is
persisted (memory or SQLite) and shown as posture in the Python API, HTTP, CLI,
offline snapshots and console. Unavailable results now name the failing field.
Pull collection from producer services, full artifact validation and AIOS
mapping/conformance remain future work. There is no write-side runtime
orchestration.

## Sidecar v0.7 runtime journal readback

The native decision reader preserves `decision_id`, `trigger_details` and
`causal_link` alongside verdict/risk fields. Older native decisions without the
new optional fields remain supported. Sidecar v0.7 emits decision snapshots as
`event["payload"]["decision"]`; extract that object from a trusted journal, direct JSON export array or
recording and attribute it to a registered deployment through EvidenceLink.
`agenticops_control_tower.adapters.sidecar_journal_decisions()` performs this
extraction for JSON objects, export arrays and JSONL, and
`evidence ingest-sidecar-journal` pushes each decision to a running Tower.
The journal task_id is producer correlation, not a Tower deployment ID.

The optional local-producer tests check all seven v0.7 outcomes, decision IDs,
parent links and unchanged deployment health. Run without adding a required
Sidecar dependency:

```bash
uv run --with ../agentic-sidecar python -m pytest tests/test_sibling_artifacts.py -k sidecar
uv run python examples/inspect_sidecar_journal.py \
  ../agentic-sidecar/tests/validation/v0_7_lifecycle.json --source-version 0.7.0
```

This reads producer-supplied decision evidence. It does not verify a journal's
hash chain, infer tool completion, collect runtime events remotely or send
operator controls. Sidecar owns its authenticated task-level Control Room;
Tower's fleet console remains read-only. Credential revocation stays with its
issuer/harness and requires Sidecar's configured acknowledgement callbacks.
No dependency-floor change is needed for native JSON readback: the existing
optional Sidecar extra permits 0.7.0; v0.7 APIs require the v0.7 checkout until
that package is published.

## v0.4 controlled configuration

See [configuration and approvals](configuration.md) for Tower ownership, action lifecycle, audit durability and API/CLI usage.
Runtime settings remain mirrored or unsupported without an adapter.

## Phase 6/6A compatibility (0.6.0)

Tower consumes native Lens 0.7.1, Evals 0.7.1, Sidecar 0.8.0 and Chaos 0.5.3
artifacts without raising producer floors. MCP 0.3.6 adds the local authenticated
Tower connector. The first staging recovery example uses actual Lens runs and
an Evals-computed gate; failed recovery escalates. Thin emergency control
adapters are separate from the read-only native readers above. `ai-operations-spec` catalog release 0.5.1 retains AIOS v0.4-draft
schemas and Tower incident/approval objects remain local. See
[the incident guide](incident-recovery.md) and [MCP setup](mcp-connector.md).

## Agentic Chaos 0.6.0 compatibility

Chaos 0.6.0 adds a pytest plugin and chaos contracts. Each contract result is
`passed`, `failed` or `inconclusive` (the report cannot support the check, for
example no baseline or a pre-0.6 report); inconclusive fails closed and never
counts as a pass. Its native
reports gain the additive fields `calls`, `calls_dropped` and
`unhandled_error`. Tower's native `chaos_report` reader ignores them and
summarizes events as before, which agentic-chaos's sibling-integration CI
checks. The optional `agentic-chaos>=0.5,<1` extra already admits 0.6; no Tower
change or release is needed. Contract verdicts are Chaos-native per-run checks;
they do not become deployment health, and Evals still computes release gates.

## Tower 0.7.0 fleet coordination

See [fleet operations](fleet-operations.md). Fleet selectors, command IDs,
approvals and receipts are Tower-local contracts. Existing optional sibling
ranges stay sufficient. Native evidence, deployment health, runtime enforcement
and issuer revocation retain separate ownership and meaning. New fleet writes
are HTTP/CLI/Python-only; MCP investigation remains compatible and cannot approve.


## Current operational export

The opt-in `incidents.export.export_investigation_report` projects held native incidents into AIOS `0.8-draft` investigation reports with redacted text and explicit citations. This producer projection is separate from native evidence readers and does not make Tower an AIOS validator. See [current export/migration behavior](coordinated-v1-readiness.md) and [operational artifacts](aios-0.8-operational-artifacts.md). Historical sections describe their stated release's native reader scope.
