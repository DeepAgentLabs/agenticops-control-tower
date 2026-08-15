# agenticops-control-tower

**A unified control plane and operations console for the DeepAgentLabs ecosystem.**

> AgenticLens observes. Agentic Sidecar governs. Agentic Chaos tests. Agentic
> MCP connects. Control Tower operates.

## Status

**Concept / pre-implementation.** This repository currently contains the
architecture proposal ([`DeepAgent Control Tower End-to-End Concept.md`](DeepAgent%20Control%20Tower%20End-to-End%20Concept.md)),
this README, and the build plan in [ROADMAP.md](ROADMAP.md).

There is **no package code, no PyPI release, no API server, no CLI, and no web
console yet**. The point of the project today is to define the control-plane
shape clearly enough that implementation can start in a narrow, believable
order.

## Contents

- [Why this exists](#why-this-exists)
- [What Control Tower is](#what-control-tower-is)
- [What it is not](#what-it-is-not)
- [Architecture](#architecture)
- [Control Tower surfaces](#control-tower-surfaces)
- [Human operators and AI operators](#human-operators-and-ai-operators)
- [Runtime and framework position](#runtime-and-framework-position)
- [The DeepAgentLabs ecosystem](#the-deepagentlabs-ecosystem)
- [Initial scope](#initial-scope)
- [Roadmap](#roadmap)

## Why this exists

The DeepAgentLabs projects each answer a different operational question:

- **AgenticLens** asks: what happened, why did it happen, and what should I fix?
- **Agentic Sidecar** asks: should this action happen right now, given the
  user's intent and current risk?
- **Agentic Chaos** asks: what breaks under stress, failure, and silent
  degradation?
- **Agentic MCP** asks: how do hosts and agents access these capabilities
  through one MCP-native surface?

What is still missing is the layer above them:

> What is deployed, where is it running, which capabilities are enabled, what
> is unhealthy, and how do I operate all of it from one place?

That missing layer is the job of `agenticops-control-tower`.

## What Control Tower is

Control Tower is intended to be the **runtime-agnostic, framework-agnostic
operations layer** for teams running multiple agents and multiple
DeepAgentLabs capabilities.

At a high level, it should eventually provide:

- a central agent registry
- capability discovery across agents and environments
- health and status visibility
- centralized configuration for supported capabilities
- a unified control API
- a human CLI
- a web console for operators

The key distinction is that Control Tower is **not just a dashboard**. The
dashboard is only one interface to the underlying control plane.

## What it is not

- **Not a replacement for AgenticLens.** Control Tower may surface Lens
  insights, but Lens remains the observability and evaluation engine.
- **Not a replacement for Agentic Sidecar.** Control Tower may surface
  Sidecar decisions and governance posture, but Sidecar remains the
  decision-time supervision layer.
- **Not a replacement for Agentic Chaos.** Control Tower may orchestrate or
  summarize chaos posture, but Chaos remains the resilience-testing engine.
- **Not the MCP layer itself.** Agentic MCP remains an independent package
  and should be able to connect both to individual DeepAgentLabs capabilities
  and to Control Tower.
- **Not tied to one runtime or one framework.** The control plane should sit
  above LangGraph, CrewAI, AutoGen, OpenAI Agents SDK, AWS AgentCore-style
  workloads, MCP-native agents, and custom Python systems rather than
  assuming one execution model.
- **Not implemented yet.** The architecture in the concept doc is broader
  than what a first real release should attempt. See [ROADMAP.md](ROADMAP.md)
  for the narrowed build order.

## Architecture

The ecosystem boundary should stay crisp:

```text
Control Tower = OPERATE
Agentic MCP   = CONNECT
AgenticLens   = OBSERVE
Agentic Sidecar = GOVERN
Agentic Chaos = TEST
AI Operations Specification = STANDARDIZE
```

Conceptually:

```text
                   Human operators           AI operators
                          |                       |
                  Console / CLI / API        Agentic MCP
                          |                       |
                          +-----------+-----------+
                                      |
                                      v
                         DeepAgent Control Tower
                                      |
                   +------------------+------------------+
                   |                  |                  |
                   v                  v                  v
              AgenticLens      Agentic Sidecar     Agentic Chaos
```

Control Tower's role is to centralize operations across agents and
capabilities, not to absorb the implementation logic of the sibling projects.

## Control Tower surfaces

The concept doc points to five main product surfaces:

- **Agent Registry**: inventory of known agents, runtimes, frameworks,
  environments, capability versions, and last-seen status
- **Capability Discovery**: detect which DeepAgentLabs packages and features
  are present on each agent wherever automatic discovery is technically
  feasible
- **Configuration**: centralized configuration and policy updates for
  supported capabilities
- **Unified Control API**: one programmatic interface over inventory, health,
  capability status, and supported operations
- **AgenticOps Console**: the human-facing dashboard over the same control
  plane used by the API and CLI

The CLI should be a first-class interface, not an afterthought. The same is
true for AI-facing operation through Agentic MCP once the underlying control
API exists.

## Human operators and AI operators

This project is unusual in that it has two equally important operator models:

- **Humans** should be able to use a console, CLI, or API to inspect and
  operate agents across environments.
- **AI systems** should be able to use Agentic MCP to inspect and operate the
  same control plane through an MCP-native interface.

That separation matters:

- Control Tower does **not** require MCP
- MCP does **not** require Control Tower
- when used together, MCP becomes the AI-native interface to the control
  plane

## Runtime and framework position

Control Tower should be:

- **runtime agnostic**: local Python, containers, VMs, Kubernetes,
  serverless, cloud-specific runtimes, and on-prem systems are all valid
  targets
- **framework agnostic**: LangGraph, CrewAI, AutoGen, OpenAI Agents SDK,
  custom harnesses, MCP-based agents, and future frameworks should all fit
  the model
- **modular**: teams should be able to adopt a single DeepAgentLabs
  capability without adopting the entire stack

That means deployment packaging is an implementation choice, not an
architectural dependency.

## The DeepAgentLabs ecosystem

Control Tower only makes sense if the package boundaries stay clear:

| Project | Role |
| --- | --- |
| `agenticlens` | Observe |
| `agentic-sidecar` | Govern |
| `agentic-chaos` | Test |
| `deep-agentic-core-mcp` | Connect |
| `ai-operations-spec` | Standardize |
| `agenticops-control-tower` | Operate |

- **AgenticLens** remains package-first observability, evaluation, and
  operational intelligence
- **Agentic Sidecar** remains package-first supervision and governance
- **Agentic Chaos** remains package-first resilience and fault injection
- **Agentic MCP** remains the MCP-native access layer
- **AI Operations Specification** remains the shared operational contract
- **Control Tower** becomes the centralized operate/manage layer across them

This repository should therefore stay focused on:

- inventory and registry concerns
- control-plane APIs
- capability discovery contracts
- health and readiness visibility
- centralized operations and configuration
- multi-agent, multi-environment control-room workflows

It should not quietly turn into a duplicate implementation of the sibling
projects.

## Initial scope

The concept doc describes a very broad end state. A good first implementation
needs to be much narrower.

The first usable version should likely prove four things only:

1. agents can register and heartbeat
2. the system can discover installed DeepAgentLabs capabilities and versions
3. operators can inspect that inventory through a simple API and CLI
4. the same inventory can be surfaced later in a console without changing the
   underlying control model

That is enough to validate the control-plane idea without pretending the full
dashboard, configuration orchestration, and cross-agent operations engine
already exist.

## Roadmap

The build plan is in [ROADMAP.md](ROADMAP.md). In short, the intended order
should be:

- start with a narrow registry and discovery core
- add a real control API and CLI before building the dashboard
- surface Lens, Sidecar, and Chaos data gradually rather than simulating a
  complete integration layer
- add MCP connectivity to Control Tower after the underlying control surfaces
  are real

If you want the full architectural reasoning behind those choices, read the
concept doc first and the roadmap second.
