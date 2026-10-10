from agenticops_control_tower import __version__
from agenticops_control_tower.adapters import ADAPTER_NAMES
from agenticops_control_tower.api import ControlTowerAPI
from agenticops_control_tower.cli.main import main, run
from agenticops_control_tower.console.app import console_status
from agenticops_control_tower.discovery import CapabilityDiscoveryService
from agenticops_control_tower.models import (
    AgentRegistrationPayload,
    CapabilityInventoryRecord,
    FleetStatusSummary,
)
from agenticops_control_tower.registry import AgentRegistry


def test_surface_imports() -> None:
    assert __version__ == "0.3.0"
    assert "agenticlens" in ADAPTER_NAMES
    # `cli.main` is a real CLI now (v0.2) -- see tests/test_cli.py for
    # command-level coverage. This just confirms the console-script entry
    # points (`main`/`run`) import cleanly even without the `api` extra.
    assert callable(main)
    assert callable(run)
    assert console_status() == "AgenticOps Console (read-only)"
    assert AgentRegistry is not None
    assert CapabilityDiscoveryService is not None
    assert ControlTowerAPI is not None
    assert AgentRegistrationPayload is not None
    assert CapabilityInventoryRecord is not None
    assert FleetStatusSummary is not None
