# Control Tower

## Control Tower overview

Which agents exist, what evidence do they have, and what needs attention?

Registrations, heartbeats, explicit evidence links, and operator configuration. Fleet inventory, evidence posture, alerts, incident views, and approved operational workflows.

**When to start here**

Read a sample fleet offline; then start the local console.

## Inputs and outputs

| You provide | You receive |
| --- | --- |
| Registrations, heartbeats, explicit evidence links, and operator configuration. | Fleet inventory, evidence posture, alerts, incident views, and approved operational workflows. |

## Execution boundary

Fleet status does not turn a failed eval into a pass. Evidence ingestion and producer integrations must be configured explicitly.

[Start the Control Tower quickstart →](guide/quickstart.md)

<span id="what-it-does-today"></span>

## Capabilities

Use these capabilities to address operate tasks in your application.

| Capability | What it provides |
| --- | --- |
| Inventory and heartbeats | Register deployments and inspect their reported runtime status. |
| Capability coverage | Identify installed and missing producer capabilities across registered agents. |
| Evidence posture | Store attributed producer outcomes and show freshness without rewriting their verdicts. |
| Operational console | Read fleet inventory and evidence through a local service and console. |
| Controlled changes | Preview actions, collect authorization, execute bounded operations, and verify results. |
| Detection and runbooks | Work with alerts, incidents, recovery workflows, and recorded operational evidence. |

## Supported scope

Fleet status does not turn a failed eval into a pass. Evidence ingestion and producer integrations must be configured explicitly.

## Core concepts

| Concept | Meaning |
| --- | --- |
| Registration | Identifies an agent deployment and its declared runtime/capabilities. |
| Heartbeat | A reported runtime status, not proof that every task succeeded. |
| EvidenceLink | Attributes a producer artifact to a deployment and observation time. |
| Posture | A view of freshness and native outcomes, separate from reported deployment health. |
| Projection | Tower stores supported fields for operations; it does not reproduce every producer's raw trace. |
| Approval and execution | A preview, authorization, dispatch, and verification are distinct steps. |

## Recommended workflow

## Register before sending evidence

Define the deployment identity and runtime fields. Register it, then send periodic heartbeats from the runtime. A registration by itself does not prove current health.

## Push native evidence

Producer pipelines send a native artifact plus an EvidenceLink. Tower does not fetch an artifact merely because its reference looks like a URL. The deployment must already exist.

## Read posture

Inspect freshness, the latest available or unavailable record, and native outcomes. Missing evidence is not a healthy check or a failed quality score. A producer failure remains a producer failure even if the runtime heartbeat is healthy.

## Handle incidents

Review alerts and supporting evidence, preview a bounded action, obtain the required authorization, then execute and verify. Preserve the resulting audit trail.

## Retain operations state

Choose a persistent SQLite database when you need state after restart. Establish explicit retention for evidence; do not assume automatic cleanup.

## Next steps

Read a sample fleet offline; then start the local console.

[Open the developer quickstart →](guide/quickstart.md)
