# Evals 0.10.0 evaluation evidence compatibility

[Agentic Evals 0.10.0](https://github.com/DeepAgentLabs/agentic-evals/releases/tag/v0.10.0)
exports its native evaluation reports as AI Operations Specification
`0.4-draft` `evaluation` evidence and merges it into an existing Run artifact.

## What Tower reads

Nothing changes in Tower's evidence path:

- Tower keeps validating complete native reports and supplied gate decisions
  against its bundled Evals schemas before projecting evidence. Evals 0.10.0
  ships the same report and gate documents as 0.9.0 (`$id` at `v0.9.0`), so
  the bundled copies remain exact and no schema sync is needed.
- An AIOS Run carrying Evals evidence is not a Tower input. Tower does not read
  AIOS artifacts, and its explicit deployment/evidence link stays a Tower-local
  contract. Validate such Runs with MCP's `spec.validate_artifact`.
- An aligned Run is not fleet health and not a passing gate. A failed
  `release_gate` evaluation in an exported Run stays failed. Recovery
  verification still requires fresh, same-run passing native gate evidence,
  and Tower never recomputes scores.

The development dependency now pins `agentic-evals==0.10.0`. The optional
`agentic-evals>=0.7.2,<1` extra already admits it. Tower 0.8.0's full test suite
passes against Evals 0.10.0 (247 tests). No Tower release is needed.

See the [Evals guide](https://github.com/DeepAgentLabs/agentic-evals/blob/v0.10.0/docs/aios-evidence.md).
