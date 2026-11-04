"""Tower-local candidate discovery contract, independent of package and AIOS versions."""

from typing import Any, Literal

from pydantic import BaseModel, Field

from agenticops_control_tower.models.agent import (
    AgentRecord,
    AgentRegistrationPayload,
    AgentStatus,
    HeartbeatPayload,
)


class CapabilityContract(BaseModel):
    """Machine-readable negotiation and schemas for existing inventory routes."""

    contract_version: Literal["tower.capabilities.v1"] = "tower.capabilities.v1"
    maturity: Literal["candidate"] = "candidate"
    capabilities: Literal["agent-reported; not verified installation"] = (
        "agent-reported; not verified installation"
    )
    registration: Literal["replace record and reset heartbeat count"] = (
        "replace record and reset heartbeat count"
    )
    heartbeat: Literal["merge metadata; replace status and last_seen"] = (
        "merge metadata; replace status and last_seen"
    )
    health: Literal["reported; no automatic heartbeat expiry"] = (
        "reported; no automatic heartbeat expiry"
    )
    statuses: list[str] = Field(default_factory=lambda: [status.value for status in AgentStatus])
    schemas: dict[str, dict[str, Any]] = Field(
        default_factory=lambda: {
            "registration": AgentRegistrationPayload.model_json_schema(),
            "heartbeat": HeartbeatPayload.model_json_schema(),
            "agent": AgentRecord.model_json_schema(),
        }
    )
