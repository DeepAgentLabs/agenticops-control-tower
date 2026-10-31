"""Deterministic multi-step staging runtime for the supported runbook.

A durable local SQLite fixture, not a production process manager. Each action
commits its change and an idempotency receipt in one transaction. Fault hooks
exist so tests and walkthroughs can exercise retries, timeouts and partial
failure without shell or network dispatch.
"""

import sqlite3
import time
from collections.abc import Mapping
from threading import Lock
from typing import Literal

from agenticops_control_tower.runbooks.connectors import ConnectorOutcome

ACTIONS = frozenset({"traffic.drain", "traffic.resume", "dependency.restore"})
Fault = Literal["failed", "partial_failure", "hang", "raise"]


class StagingRunbookRuntime:
    def __init__(self, database_path: str, agent_id: str, dependency: str) -> None:
        self.database_path = database_path
        self.agent_id = agent_id
        self.dependency = dependency
        self.hang_seconds = 2.0
        self._faults: dict[str, list[Fault]] = {}
        self._lock = Lock()
        with sqlite3.connect(database_path, timeout=1) as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS staging_runbook_state "
                "(agent TEXT, dependency TEXT, available INTEGER, drained INTEGER, "
                "PRIMARY KEY(agent, dependency))"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS staging_runbook_receipts "
                "(key TEXT PRIMARY KEY, action TEXT, agent TEXT, dependency TEXT)"
            )
            db.execute(
                "INSERT OR IGNORE INTO staging_runbook_state VALUES (?, ?, 1, 0)",
                (agent_id, dependency),
            )

    def supports(self, agent_id: str, action: str, parameters: Mapping[str, str]) -> bool:
        return (
            agent_id == self.agent_id
            and action in ACTIONS
            and dict(parameters) == {"dependency": self.dependency}
        )

    def fail(self) -> None:
        """Deterministic dependency outage for walkthroughs and tests."""
        with sqlite3.connect(self.database_path, timeout=1) as db:
            db.execute(
                "UPDATE staging_runbook_state SET available=0 WHERE agent=? AND dependency=?",
                (self.agent_id, self.dependency),
            )

    def inject(self, action: str, *faults: Fault) -> None:
        """Queue faults for the next calls of one action (test hook)."""
        with self._lock:
            self._faults.setdefault(action, []).extend(faults)

    def state(self) -> dict[str, bool]:
        with sqlite3.connect(self.database_path, timeout=1) as db:
            row = db.execute(
                "SELECT available, drained FROM staging_runbook_state "
                "WHERE agent=? AND dependency=?",
                (self.agent_id, self.dependency),
            ).fetchone()
        return {"available": bool(row[0]), "drained": bool(row[1])}

    def receipts(self) -> list[tuple[str, str]]:
        with sqlite3.connect(self.database_path, timeout=1) as db:
            return [
                (key, action)
                for key, action in db.execute(
                    "SELECT key, action FROM staging_runbook_receipts ORDER BY rowid"
                )
            ]

    def run(
        self, idempotency_key: str, action: str, parameters: Mapping[str, str]
    ) -> ConnectorOutcome:
        if not self.supports(self.agent_id, action, parameters):
            raise ValueError("Unsupported staging action or target")
        with self._lock:
            queued = self._faults.get(action, [])
            fault = queued.pop(0) if queued else None
        if fault == "failed":
            return "failed"
        if fault == "raise":
            raise RuntimeError("Injected connector exception")
        if fault == "hang":
            time.sleep(self.hang_seconds)
        column, value = {
            "traffic.drain": ("drained", 1),
            "traffic.resume": ("drained", 0),
            "dependency.restore": ("available", 1),
        }[action]
        with sqlite3.connect(self.database_path, timeout=5) as db:
            db.execute("BEGIN IMMEDIATE")
            previous = db.execute(
                "SELECT action FROM staging_runbook_receipts WHERE key=?", (idempotency_key,)
            ).fetchone()
            if previous is not None and previous != (action,):
                raise ValueError("Idempotency key belongs to a different action")
            if previous is None:
                db.execute(
                    f"UPDATE staging_runbook_state SET {column}=? WHERE agent=? AND dependency=?",
                    (value, self.agent_id, self.dependency),
                )
                db.execute(
                    "INSERT INTO staging_runbook_receipts VALUES (?, ?, ?, ?)",
                    (idempotency_key, action, self.agent_id, self.dependency),
                )
        return "partial_failure" if fault == "partial_failure" else "succeeded"

    def probe(self, agent_id: str, parameters: Mapping[str, str]) -> bool:
        if agent_id != self.agent_id or dict(parameters) != {"dependency": self.dependency}:
            return False
        state = self.state()
        return state["available"] and not state["drained"]
