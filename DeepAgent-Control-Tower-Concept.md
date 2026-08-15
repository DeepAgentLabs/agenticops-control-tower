# DeepAgent Control Tower

> **A runtime-agnostic, framework-agnostic unified control plane for Agentic AI operations.**

**Product:** DeepAgent Control Tower  
**Control Tower PyPI:** `agenticops-control-tower`

```bash
pip install agenticops-control-tower
```

---

# 1. Overview

**DeepAgent Control Tower** is the centralized **Control Room and unified management plane** for the DeepAgentLabs open-source ecosystem.

DeepAgentLabs provides modular capabilities for operating Agentic AI systems:

- **AgenticLens — OBSERVE**
- **Agentic-Sidecar — SUPERVISE**
- **Agentic-Chaos — TEST**
- **Agentic MCP — CONNECT**
- **DeepAgent Control Tower — OPERATE**

Each project remains independently usable.

As developers begin using multiple DeepAgentLabs components across multiple AI agents and environments, however, they need one place to answer:

- What AI agents are running?
- Where are they running?
- Which DeepAgentLabs PyPI packages/capabilities are being used?
- Which versions are deployed?
- Are the agents and capabilities healthy?
- What is AgenticLens observing?
- What decisions and risks is Agentic-Sidecar identifying?
- What Chaos experiments are configured or running?
- What configuration is active?
- Can capabilities be enabled, disabled, or reconfigured centrally?
- Can operations be performed across one agent or many agents?
- Can an AI agent interact with all these capabilities through MCP?

**DeepAgent Control Tower provides this missing Control Room.**

---

# 2. The Missing Layer — Control Room

Without Control Tower:

```text
AI Agent
│
├── AgenticLens
├── Agentic-Sidecar
├── Agentic-Chaos
└── Agentic MCP
```

Each component performs its own specialized function.

But there is no centralized operational layer answering:

> **What is deployed, where is it running, what is happening, and how do I manage everything from one place?**

DeepAgent Control Tower fills this gap.

```text
            ┌─────────────────────────────────┐
            │            DEEPAGENT            │
            │          CONTROL TOWER          │
            │                                 │
            │      AgenticOps Console         │
            │      Agent Registry             │
            │      Capability Discovery       │
            │      Configuration              │
            │      Unified Control API        │
            │      CLI                        │
            └────────────────┬────────────────┘
                             │
                  Manage / Configure / Control
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
          ▼                  ▼                  ▼
    AgenticLens       Agentic-Sidecar     Agentic-Chaos
      OBSERVE            SUPERVISE             TEST
```

DeepAgent Control Tower is therefore **not merely a dashboard**.

The dashboard is only one interface to the underlying Control Tower.

---

# 3. DeepAgent Control Tower Components

```text
DeepAgent Control Tower
│
├── AgenticOps Console
│      └── Web Dashboard / Control Room
│
├── Control API
│      └── Unified programmatic interface
│
├── Agent Registry
│      └── Inventory of registered AI agents
│
├── Capability Discovery
│      └── Discover DeepAgentLabs capabilities/packages
│
├── Configuration
│      └── Central configuration management
│
└── CLI
       └── Human/operator command-line interface
```

These components together form the **Control Tower**.

---

# 4. AgenticOps Console — Web Dashboard

The **AgenticOps Console** is the graphical interface to DeepAgent Control Tower.

It provides a centralized view across registered AI agents and DeepAgentLabs capabilities.

Example:

```text
┌────────────────────────────────────────────────────┐
│              DEEPAGENT CONTROL TOWER               │
├────────────────────────────────────────────────────┤
│                                                    │
│ Agents                                      17     │
│ Healthy                                     15     │
│ Needs Attention                              2     │
│                                                    │
│ Capabilities                                       │
│                                                    │
│ AgenticLens                                 14     │
│ Agentic-Sidecar                              9     │
│ Agentic-Chaos                                6     │
│ Agentic MCP                                 11     │
│                                                    │
├────────────────────────────────────────────────────┤
│ payment-agent                                      │
│                                                    │
│ Runtime                         AWS Lambda          │
│ Status                          ● Healthy           │
│                                                    │
│ AgenticLens                     ● Enabled           │
│ Agentic-Sidecar                 ● Enabled           │
│ Agentic-Chaos                   ○ Disabled          │
│ Agentic MCP                     ● Enabled           │
│                                                    │
│ Evaluation                      98.2%               │
│ Risk Events                     7                   │
│ Recent Failures                 3                   │
│                                                    │
│ [Lens] [Sidecar] [Chaos] [Config] [Operations]     │
└────────────────────────────────────────────────────┘
```

The Console should eventually provide:

- Agent inventory
- Agent health
- Runtime information
- Capability inventory
- Package versions
- AgenticLens insights
- Agentic-Sidecar decisions and risks
- Agentic-Chaos experiments
- Configuration
- Operational actions
- Alerts and warnings
- Cross-agent visibility

---

# 5. Agent Registry

Control Tower maintains a centralized inventory of known AI agents.

For example:

```text
Agent Registry

payment-agent
customer-support-agent
research-agent
security-agent
coding-agent
```

Each registered agent can contain metadata such as:

```text
Agent
├── Agent ID
├── Name
├── Environment
├── Runtime
├── Framework
├── Status
├── Capabilities
├── Package Versions
└── Last Seen
```

Example:

```text
payment-agent

Environment        production
Runtime            AWS Lambda
Framework          LangGraph
Status             Healthy

Capabilities
├── AgenticLens          0.8.1
├── Agentic-Sidecar      0.4.0
└── Agentic MCP          0.3.0
```

---

# 6. Capability Discovery

One of the major responsibilities of Control Tower is **discovering what DeepAgentLabs capabilities are being used by each agent**.

Developers should ideally not have to manually maintain this inventory.

For example, the individual packages can identify themselves through a common capability contract:

```json
{
  "agent_id": "payment-agent",
  "environment": "production",
  "runtime": "aws-lambda",
  "capabilities": {
    "agenticlens": "0.8.1",
    "agentic-sidecar": "0.4.0",
    "agentic-chaos": "0.5.2",
    "agentic-mcp": "0.3.0"
  }
}
```

Control Tower can then automatically understand:

```text
payment-agent

✓ AgenticLens
✓ Agentic-Sidecar
✓ Agentic-Chaos
✓ Agentic MCP
```

Capability Discovery should eventually identify:

- Which DeepAgentLabs capabilities are present
- Package versions
- Capability status
- Supported features
- Runtime/environment
- Framework
- Last heartbeat/communication
- Compatibility information

---

# 7. Configuration Management

Control Tower provides centralized configuration management for supported DeepAgentLabs capabilities.

Example:

```text
payment-agent
────────────────────────────

AgenticLens

Tracing                  ON
Evaluation               ON
Sampling                 50%

Agentic-Sidecar

Supervision              ON
Risk Threshold           HIGH
Human Approval           ON

Agentic-Chaos

Chaos Testing            OFF
Production Experiments   DISABLED
```

The objective is:

> **Manage supported configuration across one or many agents without independently configuring every deployed component.**

---

# 8. Unified Control API

Control Tower exposes a **Unified Control API**.

Instead of external systems needing to understand every individual package independently, Control Tower provides one operational interface.

Conceptually:

```text
                 Unified Control API
                         │
            ┌────────────┼────────────┐
            │            │            │
            ▼            ▼            ▼
          Lens        Sidecar       Chaos
```

Possible operations include:

```text
agents.list()
agents.get()
agents.health()

capabilities.list()
capabilities.status()

lens.get_traces()
lens.get_evaluations()

sidecar.get_decisions()
sidecar.get_risks()

chaos.list_experiments()
chaos.run_experiment()

config.get()
config.update()
```

The exact API contract can evolve independently from the high-level architecture.

---

# 9. CLI

Control Tower can expose a CLI for developers and operators.

For example:

```bash
deepagent agents list
```

```bash
deepagent status payment-agent
```

```bash
deepagent capabilities payment-agent
```

```bash
deepagent config get payment-agent
```

```bash
deepagent lens status payment-agent
```

```bash
deepagent sidecar status payment-agent
```

```bash
deepagent chaos experiments payment-agent
```

The CLI and AgenticOps Console should operate against the same underlying Control Tower APIs.

---

# 10. Agentic MCP — Independent Universal Connector

**Agentic MCP is an independent DeepAgentLabs PyPI project.**

It is **not a subcomponent of DeepAgent Control Tower**.

Its purpose is to provide **AI-native access to DeepAgentLabs capabilities through MCP**.

The core architectural principle is:

> **Agentic MCP can connect directly to individual DeepAgentLabs PyPI capabilities AND to DeepAgent Control Tower.**

Therefore:

```text
Agentic MCP
│
├── AgenticLens Connector
├── Agentic-Sidecar Connector
├── Agentic-Chaos Connector
└── DeepAgent Control Tower Connector
```

This makes Agentic MCP the **CONNECT layer** across the entire DeepAgentLabs ecosystem.

---

# 11. MCP Direct Mode

Control Tower is **not required** for MCP.

For example, a developer may only use AgenticLens:

```text
AI Agent / MCP Client
         │
         ▼
     Agentic MCP
         │
         ▼
    AgenticLens
```

Or:

```text
AI Agent / MCP Client
         │
         ▼
     Agentic MCP
         │
         ▼
    Agentic-Chaos
```

Or MCP could expose multiple installed capabilities:

```text
             Agentic MCP
                  │
       ┌──────────┼──────────┐
       ▼          ▼          ▼
     Lens      Sidecar     Chaos
```

This preserves the modular architecture.

---

# 12. MCP Control Tower Mode

When DeepAgent Control Tower is present, MCP can connect to it as another capability.

```text
AI / Copilot / Agent
        │
        ▼
    Agentic MCP
        │
        ▼
DeepAgent Control Tower
        │
   ┌────┼─────┐
   ▼    ▼     ▼
 Lens Sidecar Chaos
```

An authorized AI agent could potentially request:

> List all registered agents.

> Which agents are unhealthy?

> Which agents have Agentic-Chaos installed?

> Show all agents using an outdated AgenticLens version.

> Show the recent high-risk decisions from Agentic-Sidecar.

> Enable enhanced tracing for payment-agent.

> Run an approved API-timeout Chaos experiment against payment-agent in staging.

MCP translates AI-native interaction into operations against the Control Tower's Unified Control API.

---

# 13. MCP Can Access Every DeepAgentLabs PyPI

The intended relationship is:

```text
                       AGENTIC MCP
                          CONNECT
                             │
       ┌─────────────────────┼──────────────────────┐
       │                     │                      │
       ▼                     ▼                      ▼
 AgenticLens          Agentic-Sidecar        Agentic-Chaos
       │                     │                      │
       │                     │                      │
       └─────────────────────┼──────────────────────┘
                             │
                             ▼
                  DeepAgent Control Tower
```

Therefore MCP can provide AI-native access to:

```text
AgenticLens              ✓
Agentic-Sidecar          ✓
Agentic-Chaos            ✓
DeepAgent Control Tower  ✓
```

Future DeepAgentLabs capabilities can follow the same connector model.

---

# 14. Independence Between MCP and Control Tower

A critical architectural principle is:

> **Agentic MCP does not require DeepAgent Control Tower.**

And:

> **DeepAgent Control Tower does not require Agentic MCP.**

They are independently usable components.

```text
Control Tower without MCP

Human
 │
 ├── AgenticOps Console
 │
 ├── CLI
 │
 └── Control API
          │
          ▼
     Control Tower
```

And:

```text
MCP without Control Tower

AI Agent
   │
   ▼
Agentic MCP
   │
   ▼
AgenticLens / Sidecar / Chaos
```

When combined:

```text
AI Agent
   │
   ▼
Agentic MCP
   │
   ▼
Control Tower
   │
   ├── Lens
   ├── Sidecar
   └── Chaos
```

This provides maximum flexibility.

---

# 15. Human and AI Interfaces

The architecture therefore supports two primary types of operators.

## Human Operators

Humans interact through:

```text
AgenticOps Console
CLI
Control API
```

## AI Operators

AI systems interact through:

```text
Agentic MCP
```

Conceptually:

```text
                  HUMAN                         AI
                    │                           │
          ┌─────────┼─────────┐                 │
          ▼         ▼         ▼                 ▼
       Console     CLI       API          Agentic MCP
          │         │         │                 │
          └─────────┴────┬────┘                 │
                         │                      │
                         ▼                      ▼
                  DeepAgent Control Tower
                         │
             ┌───────────┼───────────┐
             ▼           ▼           ▼
           Lens       Sidecar      Chaos
```

---

# 16. Runtime Agnostic

DeepAgent Control Tower must not assume where an AI agent runs.

Supported environments can eventually include:

```text
AWS Lambda
AWS AgentCore
Amazon ECS
Amazon EKS
Azure Functions
Azure Container Apps
Google Cloud Run
Kubernetes
VMs
Local Python
On-premises
Serverless
Custom runtimes
```

For example:

```text
 AWS Lambda       AgentCore         Kubernetes        Local
     │                │                 │                │
     ▼                ▼                 ▼                ▼
   Agent A          Agent B           Agent C          Agent D
     │                │                 │                │
     └────────────────┴────────┬────────┴────────────────┘
                              │
                              ▼
                   DeepAgent Control Tower
```

The architecture does not require Docker or Kubernetes.

Docker, Helm, cloud services, or other packaging/deployment mechanisms can be supported as optional deployment choices.

> **Deployment mechanism is an implementation choice, not an architectural dependency.**

---

# 17. Framework Agnostic

The same architecture should work across Agentic AI frameworks.

Potential integrations include:

- LangGraph
- CrewAI
- AutoGen
- OpenAI Agents SDK
- Microsoft Agent Framework
- AWS AgentCore workloads
- MCP-based agents
- Custom Python agents
- Future agent frameworks

The Control Tower operates on the DeepAgentLabs capability model rather than requiring one specific agent framework.

---

# 18. Modular Installation

Every component remains independently installable.

For example:

```bash
pip install agenticlens
```

or:

```bash
pip install agentic-sidecar
```

or:

```bash
pip install agentic-chaos
```

or the existing Agentic MCP package.

When centralized management is needed:

```bash
pip install agenticops-control-tower
```

The ecosystem philosophy is:

> **Start with the capability you need. Add others when required. Use DeepAgent Control Tower when you need centralized operations.**

---

# 19. Relationship with AgenticOps Specification

The **AgenticOps Specification** can provide the common conceptual and interoperability foundation underneath the ecosystem.

Potential standardized concepts include:

- Agent identity
- Agent capabilities
- Runs
- Sessions
- Intent
- Plans
- Decisions
- Tool calls
- MCP interactions
- Evaluations
- Risk events
- Faults
- Experiments
- Evidence
- Outcomes
- Operational states
- Capability discovery
- Configuration contracts

Conceptually:

```text
                 DeepAgent Control Tower
                          │
         ┌────────────────┼────────────────┐
         ▼                ▼                ▼
   AgenticLens      Agentic-Sidecar   Agentic-Chaos
         ▲                ▲                ▲
         └────────────────┼────────────────┘
                          │
                     Agentic MCP
                          │
                          ▼
                AgenticOps Specification
                 Common Operational Model
```

---

# 20. Complete Architecture

```text
                          DEEPAGENTLABS

                               │
                               ▼

               ┌─────────────────────────────┐
               │   DEEPAGENT CONTROL TOWER   │
               │                             │
               │          OPERATE            │
               │                             │
               │  AgenticOps Console         │
               │  Agent Registry             │
               │  Capability Discovery       │
               │  Configuration              │
               │  Unified Control API        │
               │  CLI                        │
               └──────────────┬──────────────┘
                              │
                     Manage / Control
                              │
           ┌──────────────────┼──────────────────┐
           │                  │                  │
           ▼                  ▼                  ▼
     ┌───────────┐      ┌─────────────┐    ┌─────────────┐
     │AgenticLens│      │   Agentic   │    │   Agentic   │
     │           │      │   Sidecar   │    │    Chaos    │
     │  OBSERVE  │      │ SUPERVISE   │    │    TEST     │
     └───────────┘      └─────────────┘    └─────────────┘
           ▲                  ▲                  ▲
           │                  │                  │
           └──────────────────┼──────────────────┘
                              │
                        ┌─────┴─────┐
                        │ Agentic   │
                        │    MCP    │
                        │           │
                        │  CONNECT  │
                        └─────┬─────┘
                              │
                              │ Also connects directly to
                              ▼
                   DeepAgent Control Tower

────────────────────────────────────────────────────────────────

                       AgenticOps Spec

              Common contracts and semantics

                         STANDARDIZE
```

The important architectural distinction is:

```text
CONTROL TOWER = OPERATE

MCP           = CONNECT

LENS          = OBSERVE

SIDECAR       = SUPERVISE

CHAOS         = TEST

AGENTICOPS    = STANDARDIZE
```

---

# 21. Control Tower Internal Architecture

At the highest level:

```text
                    ┌────────────────────────────┐
                    │         DEEPAGENT          │
                    │       CONTROL TOWER        │
                    │                            │
                    │  AgenticOps Console        │
                    │  Agent Registry            │
                    │  Capability Discovery      │
                    │  Configuration             │
                    │  Unified Control API       │
                    │  CLI                       │
                    └─────────────┬──────────────┘
                                  │
                       Unified Operations
                                  │
               ┌──────────────────┼──────────────────┐
               │                  │                  │
               ▼                  ▼                  ▼
          AgenticLens      Agentic-Sidecar    Agentic-Chaos
```

This is the central **Control Room** for DeepAgentLabs.

---

# 22. Design Principles

## 1. Runtime Agnostic

No dependency on Kubernetes, Docker, Lambda, AgentCore, or any particular runtime.

## 2. Framework Agnostic

No dependency on one Agentic AI framework.

## 3. Modular

Every DeepAgentLabs project works independently.

## 4. Control Tower Optional

Using AgenticLens, Sidecar, Chaos, or MCP does not require Control Tower.

## 5. MCP Independent

Agentic MCP remains an independent PyPI project.

## 6. Universal MCP Connectivity

MCP can provide AI-native access to individual DeepAgentLabs capabilities as well as DeepAgent Control Tower.

## 7. Automatic Capability Discovery

Control Tower should automatically discover available DeepAgentLabs capabilities wherever technically possible.

## 8. Unified Control

Control Tower provides one operational interface across multiple agents and capabilities.

## 9. Human + AI Operable

Humans operate through Console, CLI, and API.

AI systems operate through MCP.

## 10. Safe by Default

Sensitive operations should support authorization, auditability, policy boundaries, and human approval.

## 11. Open Source First

The ecosystem should remain useful without requiring a proprietary hosted platform.

---

# 23. DeepAgentLabs Product Model

The entire ecosystem can now be communicated in five words:

### OBSERVE

**AgenticLens**

Understand what agents are doing.

### SUPERVISE

**Agentic-Sidecar**

Supervise decisions, intent, risk, and policy.

### TEST

**Agentic-Chaos**

Validate how agents behave under failure.

### CONNECT

**Agentic MCP**

Provide AI-native access to every DeepAgentLabs capability, including Control Tower.

### OPERATE

**DeepAgent Control Tower**

Discover, configure, manage, and control the ecosystem from one place.

And underneath everything:

### STANDARDIZE

**AgenticOps Specification**

Provide common operational concepts, contracts, and semantics.

---

# 24. Final Positioning

> **DeepAgent Control Tower is the open-source, runtime- and framework-agnostic Control Room for Agentic AI operations, providing centralized agent discovery, capability discovery, configuration, visibility, and operational control across the DeepAgentLabs ecosystem.**

Agentic MCP complements it by providing the AI-native connectivity layer:

> **Agentic MCP provides a universal MCP interface to individual DeepAgentLabs capabilities—including AgenticLens, Agentic-Sidecar, Agentic-Chaos—and to the unified DeepAgent Control Tower.**

Together, the ecosystem provides:

> **Observe. Govern. Test. Connect. Operate. Standardize.**
