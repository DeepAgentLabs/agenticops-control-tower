"""Status and snapshot models for the v0.2 operator surface."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from .agent import AgentStatus


class CapabilityCoverageRecord(BaseModel):
    """Fleet-level coverage and version summary for one capability."""

    capability: str
    installed_agents: int
    missing_agents: int
    versions: list[str] = Field(default_factory=list)
    agent_ids: list[str] = Field(default_factory=list)
    missing_agent_ids: list[str] = Field(default_factory=list)


class AgentStatusSummary(BaseModel):
    """Operator-facing status summary for one agent."""

    agent_id: str
    name: str
    environment: str
    runtime: str
    framework: str
    status: AgentStatus
    last_seen: str | None = None
    heartbeat_count: int
    capability_count: int
    capabilities: dict[str, str] = Field(default_factory=dict)


class FleetStatusSummary(BaseModel):
    """Operator-facing fleet summary shared by API and CLI."""

    total_agents: int
    healthy_agents: int
    degraded_agents: int
    unhealthy_agents: int
    unknown_agents: int
    capability_count: int
    status_buckets: dict[str, list[str]] = Field(default_factory=dict)
    capabilities: list[CapabilityCoverageRecord] = Field(default_factory=list)


class HeartbeatEvent(BaseModel):
    """Snapshot event that applies a heartbeat to a known agent."""

    agent_id: str
    heartbeat: "SnapshotHeartbeatPayload"


class SnapshotAgentRegistration(BaseModel):
    """Registration data as stored in a fleet snapshot artifact."""

    agent_id: str
    name: str
    environment: str
    runtime: str
    framework: str
    status: AgentStatus = AgentStatus.UNKNOWN
    capabilities: dict[str, str] = Field(default_factory=dict)
    runtime_metadata: dict[str, str] = Field(default_factory=dict)
    package_metadata: dict[str, str] = Field(default_factory=dict)
    registered_at: datetime | None = None


class SnapshotHeartbeatPayload(BaseModel):
    """Heartbeat data as stored in a fleet snapshot artifact."""

    status: AgentStatus = AgentStatus.UNKNOWN
    last_seen: datetime | None = None
    capabilities: dict[str, str] = Field(default_factory=dict)
    runtime_metadata: dict[str, str] = Field(default_factory=dict)
    package_metadata: dict[str, str] = Field(default_factory=dict)


class FleetSnapshot(BaseModel):
    """Bootstrap artifact for loading a registry snapshot into the API."""

    captured_at: datetime
    registrations: list[SnapshotAgentRegistration] = Field(default_factory=list)
    heartbeats: list[HeartbeatEvent] = Field(default_factory=list)
