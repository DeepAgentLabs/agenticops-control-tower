"""Operator-specified version policy; never infers a latest release."""

from typing import Literal

from pydantic import BaseModel


class VersionAssessment(BaseModel):
    """One capability compared against an explicit minimum version."""

    agent_id: str
    capability: str
    installed_version: str | None
    minimum_version: str
    assessment: Literal["meets_minimum", "outdated", "missing", "unknown"]
    reason: str | None = None
