# Capability contract readiness (Tower 0.10)

`GET /contracts/capabilities` returns the Tower-local candidate
`tower.capabilities.v1` contract: JSON Schemas for registration, heartbeat and
agent readback, allowed statuses and mutation semantics. It requires the same
reader or writer bearer token as inventory. Python consumers can call
`ControlTowerAPI.get_capability_contract()`. This contract version is independent
of the package version and AIOS draft markers. It is a candidate for the
coordinated ecosystem v1.0 freeze.

## Supported integration patterns

| Pattern | Validation | Boundary |
| --- | --- | --- |
| Embedded Python facade | Existing registry/API suite | No API extra or sibling required |
| CPython standard-library HTTP worker | `examples/runtimes/python_worker.py` | Host reports its own inventory |
| Node.js 18+ native-fetch HTTP worker | `examples/runtimes/node_worker.mjs` | No Python SDK or npm dependency in client |
| Local/host-bound MCP operator | Existing `tower.*` tools | MCP owns tool access; Tower owns approval |
| Framework worker or container | Same explicit HTTP registration | Framework/container name is metadata, not discovery or certified support |

The two HTTP examples exercise actual independent runtime processes against a
live authenticated server. `tests/test_capability_contract.py` verifies their
registration, heartbeat, capability retention, aggregate discovery and SQLite
readback after restart. CI installs Node explicitly to prevent silently losing
second-runtime coverage. This is inventory interoperability, not a production
Kubernetes connector, remote runbook execution or framework instrumentation.

```bash
export AGENTICOPS_WRITE_TOKEN=local-writer
agenticops-control-tower serve
# In another terminal, with the same token:
python3 examples/runtimes/python_worker.py
node examples/runtimes/node_worker.mjs
```

Set `AGENTICOPS_API_URL` for a remote server. Use TLS at the deployment boundary;
the examples default to loopback. Retry registration only when replacement is
intended. Neither example sends evidence or grants execution authority.

## Core semantics

| Operation | Result and compatibility commitment |
| --- | --- |
| `POST /agents/register` | 201; same ID replaces the record and resets heartbeat count |
| `POST /agents/{id}/heartbeat` | 200; merges capability/runtime/package maps, replaces status and last_seen, increments count |
| `GET /agents/{id}` | 200 detached record; unknown ID returns 404 |
| `GET /agents` | Sorted by agent ID, with existing filters |
| `GET /capabilities` | Sorted capability keys and unique lexically sorted reported version strings |
| Invalid payload | 422; unknown status rejected; agent IDs are URL-safe |
| Protected inventory | Missing/invalid token: 401; reader cannot write: 403 |

Omitted heartbeat status becomes `unknown`. Omitted maps retain previous keys;
there is no heartbeat deletion marker. Registration is the explicit replacement
path. Repeated heartbeats increment the count and are not idempotent. Versions
are reported strings; minimum-version assessment is a separate operation.
Unknown fields follow existing Pydantic input behavior (ignored). Clients should
ignore additive response fields and inspect the contract identifier before
sending writes. No negotiation header is required by legacy clients.

Health is one of `healthy`, `degraded`, `unhealthy`, `unknown`, reported by the
host. Last-seen age does not automatically rewrite it. Evidence freshness,
Sidecar BLOCK, Evals gates, Lens verification and Chaos resilience outcomes are
independent of deployment health. Reported capabilities do not prove installed
packages, trusted evidence, approval or production readiness.

## Evolution and release gate

The existing payloads and endpoints remain compatible; existing clients need no
migration. New clients may fetch the candidate descriptor before registering.
Within this contract, preserve field types, status meaning, replacement/merge
behavior and authorization semantics. Incompatible changes require a new contract
identifier and documented migration, with old clients retained through a stated
transition. Additive optional fields may be introduced without changing the
identifier. JSON Schema snapshots and runtime tests guard this baseline.

Optional sibling ranges are unchanged: no sibling is imported to describe the
contract. Native producer schemas and AIOS exports are unchanged. MCP can keep
using existing Tower routes without adding a tool. Independent ecosystem v1.0
acceptance, production runtime connectors, deployment hardening and the final
stable freeze remain open. This phase makes Tower's implemented control-plane
behavior reviewable; it does not declare those gates passed.
