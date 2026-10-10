"""Packaged, dependency-free assets for the read-only console."""

from pathlib import Path

ASSET_DIRECTORY = Path(__file__).parent / "static"


def console_status() -> str:
    """Describe the shipped operator surface."""
    return "AgenticOps Console (read-only)"
