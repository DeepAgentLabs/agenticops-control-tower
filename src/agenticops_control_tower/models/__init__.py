"""Core models shared across the control-plane modules."""

from .agent import (
    AgentRecord,
    AgentRegistrationPayload,
    AgentStatus,
    CapabilityInventoryRecord,
    HeartbeatPayload,
)
from .status import (
    AgentStatusSummary,
    CapabilityCoverageRecord,
    FleetSnapshot,
    FleetStatusSummary,
    HeartbeatEvent,
    SnapshotAgentRegistration,
    SnapshotHeartbeatPayload,
)

__all__ = [
    "AgentRecord",
    "AgentRegistrationPayload",
    "AgentStatusSummary",
    "AgentStatus",
    "CapabilityCoverageRecord",
    "CapabilityInventoryRecord",
    "FleetSnapshot",
    "FleetStatusSummary",
    "HeartbeatEvent",
    "HeartbeatPayload",
    "SnapshotAgentRegistration",
    "SnapshotHeartbeatPayload",
]
