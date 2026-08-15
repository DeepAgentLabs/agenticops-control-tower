"""Future-facing configuration models kept intentionally small."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ConfigScope(BaseModel):
    """Target scope for a future centralized config operation."""

    agent_id: str | None = None
    environment: str | None = None
    capability: str | None = None


class ConfigPatch(BaseModel):
    """Opaque patch payload for the scaffold stage."""

    values: dict[str, object] = Field(default_factory=dict)
