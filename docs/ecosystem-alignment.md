# Ecosystem evidence contract

This document describes Control Tower's private `1.0` evidence-link contract.
It is not an AI Operations Specification schema or a stable conformance claim.
AIOS is currently draft; eventual AIOS mappings must identify the exact draft
version and validate against its schemas and semantic rules.

## Ownership

| Package | Owns | Tower consumes |
| --- | --- | --- |
| agenticlens | Observability, tracing, operational analysis | Native Run identity and execution outcome |
| agentic-evals | Output scoring and release-gate computation | EvaluationReport summaries and existing GateDecision |
| agentic-sidecar | Decision supervision, risk, intent and intervention | Native Decision outcome, risk, rationale and provenance |
| agentic-chaos | Fault injection and resilience experiments | ChaosReport identity, timing and event count |
| ai-operations-spec | Shared runtime semantics, draft schemas and conformance rules | Design vocabulary; no AIOS artifact reader implemented yet |
| agenticops-control-tower | Deployment inventory, fleet visibility and operator workflows | Explicitly attributed evidence projections |

The base Tower package needs no sibling package imports. Existing JSON exports
can be read without installing their producers. The adapter catalog also names
MCP, whose transport integration is still planned.

## Identity and attribution

`EvidenceLink.agent_id` identifies a registered deployment in Tower. It does
not identify a reusable agent definition or prove the identity of a runtime
participant. Attribution is provided explicitly by the caller; adapters never
join records by display name, application name, suite name or framework.

- `contract_version`: Tower link version, currently `1.0`.
- `source` and `source_version`: producer package and caller-reported version.
- `artifact_type`: native `run`, `evaluation_report`, `decision`, or `chaos_report`.
- `artifact_ref`: caller-owned stable artifact identifier/location. Tower neither
  fetches nor opens this reference. Sidecar Decisions and Evals Reports lack a
  universal artifact ID, so the producer/caller supplies one.
- `observed_at`: when the caller observed this evidence, distinct from source
  execution/creation timestamps.
- `run_id`: optional execution correlation. For a native Lens Run it must match
  the artifact's `run_id`; other producers' correlations are caller assertions.
- `runtime_agent_id`: optional runtime occurrence identity, separate from the
  deployment ID. Caller asserts the mapping; Tower does not infer it.
- `spec_version`: reserved for an explicit future AIOS mapping. Supplying it
  currently returns `unavailable`, rather than treating native JSON as AIOS.

AIOS distinguishes reusable agent definitions from runtime Agent occurrences.
Keep these identities separate when introducing future mappings; a deployment
registry record is not automatically an AIOS Run or Agent occurrence.

## Reading and failure behavior

Call `ControlTowerAPI.summarize_evidence(link, artifact, gate=...)` for a registered
deployment, or the standalone adapter for a projection without registry checks.
Both return `EvidenceSummary`. No evidence is stored and no registration,
heartbeat, health bucket or capability installation claim is changed.

`available` means the native fields used by the reader validated, not that the
artifact passed full producer-schema validation or its claims were verified.
Unconsumed fields are ignored, allowing additive producer changes. Unknown Lens
or Evals schema versions, unsupported outcomes, missing required fields,
source/type mismatches and absent artifacts yield `unavailable` with a reason.
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
installed producers and exercise each reader. Checked local package versions:
Lens 0.5.0, Evals 0.7.0, Sidecar 0.6.0 and Chaos 0.4.0. Example inventory versions
match these checkouts; they are illustrations, not minimum supported versions.

From this repository, run the full local-producer checks with:

```bash
uv run --with ../agenticlens --with ../agentic-evals \
  --with ../agentic-sidecar --with ../agentic-chaos python -m pytest
```

Base `make check` tests contract safety; absent optional siblings skip the actual
producer tests. This does not mean those integration tests passed.

Phase v0.5 is partial: local artifact readers and attribution are implemented.
Remote discovery/collection, persisted evidence history, HTTP/CLI posture views,
console integration, full artifact validation, AIOS mapping/conformance, and
producer-specific unavailable/unsupported diagnostics remain future work.
There is no new write-side runtime orchestration.
