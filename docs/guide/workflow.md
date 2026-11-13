# Recommended workflow

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
