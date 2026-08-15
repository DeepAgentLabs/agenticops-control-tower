"""Snapshot loading helpers for CLI and tests."""

from __future__ import annotations

import json
from pathlib import Path

from agenticops_control_tower.api import ControlTowerAPI
from agenticops_control_tower.discovery import CapabilityDiscoveryService
from agenticops_control_tower.models import FleetSnapshot
from agenticops_control_tower.registry import AgentRegistry
from agenticops_control_tower.status import StatusService


def create_api() -> ControlTowerAPI:
    """Create an empty control-plane API using the shared v0.2 services."""

    discovery = CapabilityDiscoveryService()
    return ControlTowerAPI(
        registry=AgentRegistry(),
        discovery=discovery,
        status_service=StatusService(discovery),
    )


def load_snapshot(snapshot_path: str | Path) -> ControlTowerAPI:
    """Build an in-memory control-plane API from a snapshot artifact."""

    snapshot = FleetSnapshot.model_validate(json.loads(Path(snapshot_path).read_text()))
    api = create_api()
    for registration in snapshot.registrations:
        api.register_agent(registration)
    for event in snapshot.heartbeats:
        api.record_heartbeat(event.agent_id, event.heartbeat)
    return api
