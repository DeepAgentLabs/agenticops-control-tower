# Architecture

The package separates the following control-plane domains:

- `registry/` for agent registration and heartbeat state
- `discovery/` for capability and version discovery
- `api/` for a unified control-plane surface
- `config/` for centralized configuration contracts
- `cli/` for operator workflows
- `console/` for the packaged read-only AgenticOps Console
- `adapters/` for thin ecosystem integration boundaries

See [README.md](../README.md) and [ROADMAP.md](../ROADMAP.md) for the product
boundary and milestone order.


Deployment and operator setup: [hosting](hosting.md) and
[customer-managed authentication](authentication.md).
