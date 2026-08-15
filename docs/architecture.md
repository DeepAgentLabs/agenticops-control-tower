# Architecture

This scaffold reserves the following control-plane domains:

- `registry/` for agent registration and heartbeat state
- `discovery/` for capability and version discovery
- `api/` for a unified control-plane surface
- `config/` for centralized configuration contracts
- `cli/` for operator workflows
- `console/` for the future AgenticOps Console
- `adapters/` for thin ecosystem integration boundaries

See [README.md](../README.md) and [ROADMAP.md](../ROADMAP.md) for the product
boundary and milestone order.

