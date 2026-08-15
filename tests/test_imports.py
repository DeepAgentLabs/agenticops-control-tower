from agenticops_control_tower import __version__
from agenticops_control_tower.adapters import ADAPTER_NAMES
from agenticops_control_tower.api import ControlTowerAPI
from agenticops_control_tower.cli.main import main
from agenticops_control_tower.console.app import console_status
from agenticops_control_tower.discovery import CapabilityDiscoveryService
from agenticops_control_tower.registry import AgentRegistry


def test_scaffold_imports() -> None:
    assert __version__ == "0.0.1"
    assert "agenticlens" in ADAPTER_NAMES
    assert main() == "agenticops-control-tower CLI scaffold"
    assert console_status() == "AgenticOps Console scaffold"
    assert AgentRegistry is not None
    assert CapabilityDiscoveryService is not None
    assert ControlTowerAPI is not None
