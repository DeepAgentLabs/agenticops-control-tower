# Contributing

This repository is still in the scaffold stage.

For now, contributions should stay focused on:

- clarifying the control-plane boundary
- tightening the registration and discovery model
- building narrow, testable implementation slices from [ROADMAP.md](ROADMAP.md)

Before opening a large feature PR, prefer aligning the milestone and package
boundary first in an issue or design note.

## Local development

```bash
make install
make check
```

## Scope discipline

`agenticops-control-tower` should own operator-facing control-plane behavior.
If a change mostly adds observability logic, governance logic, chaos logic, or
MCP logic, it may belong in a sibling repository instead.

