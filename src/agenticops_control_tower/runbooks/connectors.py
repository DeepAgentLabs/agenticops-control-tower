"""Explicit runbook connector boundary. Actions are named, never command strings."""

from collections.abc import Mapping
from typing import Literal, Protocol

ConnectorOutcome = Literal["succeeded", "failed", "partial_failure"]


class RunbookConnector(Protocol):
    """Installed by the trusted host for one deployment.

    `failed` means the action made no change and may be retried when the step
    allows it. `partial_failure` means state is unknown. Connectors must use the
    idempotency key durably: a repeated key after success must not repeat a side
    effect. Tower bounds how long it waits but cannot kill a Python callback.
    """

    def supports(self, agent_id: str, action: str, parameters: Mapping[str, str]) -> bool: ...

    def run(
        self, idempotency_key: str, action: str, parameters: Mapping[str, str]
    ) -> ConnectorOutcome: ...

    def probe(self, agent_id: str, parameters: Mapping[str, str]) -> bool: ...
