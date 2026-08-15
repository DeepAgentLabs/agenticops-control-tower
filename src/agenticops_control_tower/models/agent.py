"""Minimal agent inventory models for the scaffold stage."""

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


class HeartbeatPayload(BaseModel):
    """Runtime-reported status snapshot for a registered agent."""

    status: AgentStatus = AgentStatus.UNKNOWN
    last_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    capabilities: dict[str, str] = Field(default_factory=dict)


class AgentRecord(BaseModel):
    """Inventory record for one known agent."""

    agent_id: str
    name: str
    environment: str
    runtime: str
    framework: str
    status: AgentStatus = AgentStatus.UNKNOWN
    capabilities: dict[str, str] = Field(default_factory=dict)
    last_seen: datetime | None = None
