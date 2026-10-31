"""Immutable host-installed runbook catalog plus the supported built-in definition."""

from __future__ import annotations

from threading import RLock

from agenticops_control_tower.runbooks.models import (
    ParameterSpec,
    RunbookDefinition,
    RunbookStep,
)

STAGING_DEPENDENCY_RECOVERY = RunbookDefinition(
    runbook_id="staging.dependency_recovery",
    version="1.0.0",
    title="Drain, restore and resume one staging dependency",
    description=(
        "Drain traffic from one staging deployment, restore one allowlisted tool "
        "dependency, then resume traffic. Recovery still requires fresh evidence."
    ),
    environments=["staging"],
    parameters={
        "dependency": ParameterSpec(
            description="Allowlisted dependency name; the installed connector must support it",
            pattern=r"^[a-z0-9_.-]{1,100}$",
        )
    },
    steps=[
        RunbookStep(
            step_id="drain",
            action="traffic.drain",
            description="Stop routing new staging work to the deployment",
            rollback_action="traffic.resume",
        ),
        RunbookStep(
            step_id="restore",
            action="dependency.restore",
            description="Restore the named dependency",
            max_attempts=2,
        ),
        RunbookStep(
            step_id="resume",
            action="traffic.resume",
            description="Resume routing staging work to the deployment",
            max_attempts=2,
        ),
    ],
    impact="One staging deployment and one dependency; no fleet or production changes",
    rollback=(
        "A clean failure or cancellation resumes drained traffic. Restored dependencies "
        "are not re-broken. Unknown outcomes require manual reconciliation."
    ),
)


class CatalogError(ValueError):
    """Unknown runbook version or attempt to change an installed version."""


class RunbookCatalog:
    """Versions are immutable: re-installing must match the original digest."""

    def __init__(self, definitions: list[RunbookDefinition] | None = None) -> None:
        self._lock = RLock()
        self._definitions: dict[tuple[str, str], RunbookDefinition] = {}
        for definition in definitions if definitions is not None else [STAGING_DEPENDENCY_RECOVERY]:
            self.install(definition)

    def install(self, definition: RunbookDefinition) -> RunbookDefinition:
        key = (definition.runbook_id, definition.version)
        with self._lock:
            existing = self._definitions.get(key)
            if existing is not None and existing.digest() != definition.digest():
                raise CatalogError("Runbook versions are immutable; publish a new version")
            self._definitions[key] = definition.model_copy(deep=True)
            return self._definitions[key].model_copy(deep=True)

    def get(self, runbook_id: str, version: str) -> RunbookDefinition:
        with self._lock:
            definition = self._definitions.get((runbook_id, version))
        if definition is None:
            raise CatalogError("Unknown runbook version")
        return definition.model_copy(deep=True)

    def list(self) -> list[RunbookDefinition]:
        with self._lock:
            return [
                self._definitions[key].model_copy(deep=True) for key in sorted(self._definitions)
            ]
