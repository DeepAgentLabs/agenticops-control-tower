# Tower 0.9.0 ecosystem compatibility

Tower 0.9.0 adds versioned runbooks with exact-digest approval, bounded ordered
steps, compensation, cancellation, interruption reconciliation and evidence-based
verification. Existing native evidence, 0.6 single-action recovery, fleet and
live-operations contracts remain compatible.

| Component | Compatibility and ownership |
| --- | --- |
| AgenticLens 0.11.0 | Native runs remain detection and recovery inputs. A fresh successful run, different from the detection run, is required to resolve a runbook. Tower does not compute diagnosis or trace integrity. |
| Agentic Evals 0.10.0 | Bundled report/gate schemas are unchanged. A passing native gate linked to the recovery run is required; Tower never computes scores or gates. |
| Agentic Chaos 0.9.0 | A completed native Chaos report and a passing same-run Evals gate can be recorded as validation for a runbook version. Tower does not run experiments, and validation is not a gate. |
| Agentic Sidecar 0.9.1 | Unchanged. Runtime stop/restart still goes through the host-installed containment adapter, not runbook steps. |
| MCP 0.5.1 | Adds local `tower.runbook*` tools over these HTTP routes. Approval stays human-only through HTTP/CLI. Hosted MCP still rejects the Tower connector. |
| AI Operations Specification v0.6.1 | No normative schema changes. Runbook definitions, executions and validations are Tower-local and do not claim AIOS conformance. |

Optional producer extras and dependency ranges are unchanged. MCP needs a patch
release for the new tools; other siblings need documentation only. Run
`make test-ecosystem-published` and `make test-ecosystem` to verify native
producer boundaries. See [runbooks](runbooks.md).
