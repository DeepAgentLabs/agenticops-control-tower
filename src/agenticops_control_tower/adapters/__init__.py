"""Thin ecosystem artifact readers and integration catalog."""

from .catalog import ADAPTER_NAMES
from .evidence import summarize_evidence

__all__ = ["ADAPTER_NAMES", "summarize_evidence"]
