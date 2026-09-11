"""Core agent inventory models for the v0.1 control-plane surface."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    """High-level health states for the initial registry model."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class AgentRegistrationPayload(BaseModel):
    """Explicit registration request for a runtime-agnostic agent."""

    agent_id: str
    name: str
    environment: str
    runtime: str
    framework: str
    status: AgentStatus = AgentStatus.UNKNOWN
    capabilities: dict[str, str] = Field(default_factory=dict)
    runtime_metadata: dict[str, str] = Field(default_factory=dict)
    package_metadata: dict[str, str] = Field(default_factory=dict)
    registered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HeartbeatPayload(BaseModel):
    """Runtime-reported status snapshot for a registered agent."""

    status: AgentStatus = AgentStatus.UNKNOWN
    last_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    capabilities: dict[str, str] = Field(default_factory=dict)
    runtime_metadata: dict[str, str] = Field(default_factory=dict)
    package_metadata: dict[str, str] = Field(default_factory=dict)


class AgentRecord(BaseModel):
    """Inventory record for one known agent."""

    agent_id: str
    name: str
    environment: str
    runtime: str
    framework: str
    status: AgentStatus = AgentStatus.UNKNOWN
    capabilities: dict[str, str] = Field(default_factory=dict)
    runtime_metadata: dict[str, str] = Field(default_factory=dict)
    package_metadata: dict[str, str] = Field(default_factory=dict)
    registered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: datetime | None = None
    heartbeat_count: int = 0


class CapabilityInventoryRecord(BaseModel):
    """Aggregated capability inventory across all known agents."""

    capability: str
    versions: list[str] = Field(default_factory=list)
    agent_ids: list[str] = Field(default_factory=list)
