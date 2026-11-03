"""Append-only evidence history in memory or the shared SQLite database.

Only validated projections are stored. Repeating the same attributed
observation (deployment, source, artifact reference and observed time) is
idempotent, so producers can safely retry pushes.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from threading import RLock
from typing import Any

from agenticops_control_tower.adapters.evidence import summarize_evidence
from agenticops_control_tower.errors import AgenticOpsControlTowerError
from agenticops_control_tower.models.evidence import (
    EVIDENCE_SOURCES,
    EvidenceIngestRequest,
    EvidenceIngestResult,
    EvidenceRecord,
    EvidenceSource,
)
from agenticops_control_tower.registry import AgentRegistry

MAX_FUTURE_SKEW = timedelta(minutes=5)
MAX_HISTORY_LIMIT = 500


class EvidenceIngestError(AgenticOpsControlTowerError, ValueError):
    """An attributed observation cannot be accepted as stated."""


def as_utc(value: datetime) -> datetime:
    """Treat naive producer timestamps as UTC so freshness comparisons are defined."""
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def _sort_key(value: datetime) -> str:
    return as_utc(value).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


class EvidenceStore:
    def __init__(
        self,
        registry: AgentRegistry,
        database_path: str | None = None,
        *,
        trusted_lens_keys: dict[str, bytes] | None = None,
    ) -> None:
        self.trusted_lens_keys = dict(trusted_lens_keys or {})
        self.registry = registry
        self._lock = RLock()
        self._memory = sqlite3.connect(":memory:", check_same_thread=False)
        self._path = database_path
        with self._transaction() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS tower_evidence ("
                "seq INTEGER PRIMARY KEY AUTOINCREMENT, record_id TEXT UNIQUE NOT NULL, "
                "agent_id TEXT NOT NULL, source TEXT NOT NULL, observed_at TEXT NOT NULL, "
                "body TEXT NOT NULL)"
            )
            db.execute(
                "CREATE INDEX IF NOT EXISTS tower_evidence_agent_source "
                "ON tower_evidence(agent_id, source, observed_at)"
            )

    @contextmanager
    def _transaction(self, *, write: bool = True) -> Iterator[sqlite3.Connection]:
        with self._lock:
            db = sqlite3.connect(self._path) if self._path else self._memory
            try:
                db.execute("BEGIN IMMEDIATE" if write else "BEGIN")
                yield db
                db.commit()
            except BaseException:
                db.rollback()
                raise
            finally:
                if self._path:
                    db.close()

    @staticmethod
    def record_id(request: EvidenceIngestRequest) -> str:
        link = request.link
        identity = "\0".join(
            (link.agent_id, link.source, link.artifact_ref, _sort_key(link.observed_at))
        )
        return sha256(identity.encode()).hexdigest()

    def ingest(
        self,
        request: EvidenceIngestRequest,
        *,
        ingested_by: str = "python",
        now: datetime | None = None,
    ) -> EvidenceIngestResult:
        """Project and persist one observation; unavailable projections are kept too."""
        link = request.link
        self.registry.get(link.agent_id)
        now = now or datetime.now(timezone.utc)
        if as_utc(link.observed_at) > now + MAX_FUTURE_SKEW:
            raise EvidenceIngestError("observed_at is more than five minutes in the future")
        record_id = self.record_id(request)
        with self._transaction() as db:
            row = db.execute(
                "SELECT body FROM tower_evidence WHERE record_id=?", (record_id,)
            ).fetchone()
            if row:
                return EvidenceIngestResult(
                    record=EvidenceRecord.model_validate_json(row[0]), created=False
                )
            record = EvidenceRecord(
                record_id=record_id,
                ingested_at=now,
                ingested_by=ingested_by,
                summary=summarize_evidence(
                    link,
                    request.artifact,
                    gate=request.gate,
                    trusted_lens_keys=self.trusted_lens_keys,
                ),
            )
            db.execute(
                "INSERT INTO tower_evidence(record_id, agent_id, source, observed_at, body) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    record_id,
                    link.agent_id,
                    link.source,
                    _sort_key(link.observed_at),
                    record.model_dump_json(),
                ),
            )
            return EvidenceIngestResult(record=record, created=True)

    def get_record(self, agent_id: str, record_id: str) -> EvidenceRecord:
        """Read an exact stored record with deployment attribution checked."""
        self.registry.get(agent_id)
        with self._transaction(write=False) as db:
            row = db.execute(
                "SELECT body FROM tower_evidence WHERE agent_id=? AND record_id=?",
                (agent_id, record_id),
            ).fetchone()
            if row is None:
                raise EvidenceIngestError("Unknown evidence record for deployment")
            return EvidenceRecord.model_validate_json(row[0])

    def history(
        self,
        agent_id: str,
        *,
        source: EvidenceSource | None = None,
        since: datetime | None = None,
        limit: int | None = 50,
    ) -> list[EvidenceRecord]:
        """Newest observation first; ties keep the most recently ingested first.

        `limit=None` is unbounded and intended for trusted Python callers only.
        """
        if limit is not None and not 1 <= limit <= MAX_HISTORY_LIMIT:
            raise ValueError(f"limit must be between 1 and {MAX_HISTORY_LIMIT}")
        self.registry.get(agent_id)
        query = "SELECT body FROM tower_evidence WHERE agent_id=?"
        params: list[Any] = [agent_id]
        if source is not None:
            query += " AND source=?"
            params.append(source)
        if since is not None:
            query += " AND observed_at>=?"
            params.append(_sort_key(since))
        query += " ORDER BY observed_at DESC, seq DESC"
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
        with self._transaction(write=False) as db:
            return [EvidenceRecord.model_validate_json(row[0]) for row in db.execute(query, params)]

    def run_history(
        self, agent_id: str, run_id: str, *, limit: int = 100
    ) -> tuple[list[EvidenceRecord], bool]:
        """Bounded deployment/run lookup; filter in SQLite before decoding records.

        Link metadata correlates all producers. Validated native Lens run IDs also
        match when the caller omitted optional link-level correlation metadata.
        """
        if not 1 <= limit <= MAX_HISTORY_LIMIT:
            raise ValueError(f"limit must be between 1 and {MAX_HISTORY_LIMIT}")
        self.registry.get(agent_id)
        with self._transaction(write=False) as db:
            rows = db.execute(
                "SELECT body FROM tower_evidence WHERE agent_id=? AND "
                "(json_extract(body, '$.summary.link.run_id')=? OR "
                "(source='agenticlens' AND json_extract(body, '$.summary.details.run_id')=?)) "
                "ORDER BY observed_at DESC, seq DESC LIMIT ?",
                (agent_id, run_id, run_id, limit + 1),
            ).fetchall()
        return [EvidenceRecord.model_validate_json(row[0]) for row in rows[:limit]], len(
            rows
        ) > limit

    def source_views(
        self, agent_ids: list[str], since: datetime
    ) -> dict[tuple[str, str], tuple[EvidenceRecord | None, list[EvidenceRecord]]]:
        """Latest record and records since `since` per (agent, source), from one snapshot.

        Reading every view in one transaction keeps a posture internally consistent
        with concurrent ingestion or pruning.
        """
        views: dict[tuple[str, str], tuple[EvidenceRecord | None, list[EvidenceRecord]]] = {}
        order = " ORDER BY observed_at DESC, seq DESC"
        with self._transaction(write=False) as db:
            for agent_id in agent_ids:
                for source in EVIDENCE_SOURCES:
                    key = (agent_id, source)
                    latest_row = db.execute(
                        "SELECT body FROM tower_evidence WHERE agent_id=? AND source=?"
                        + order
                        + " LIMIT 1",
                        key,
                    ).fetchone()
                    recent = [
                        EvidenceRecord.model_validate_json(row[0])
                        for row in db.execute(
                            "SELECT body FROM tower_evidence WHERE agent_id=? AND source=? "
                            "AND observed_at>=?" + order,
                            (*key, _sort_key(since)),
                        )
                    ]
                    latest = (
                        EvidenceRecord.model_validate_json(latest_row[0]) if latest_row else None
                    )
                    views[key] = (latest, recent)
        return views

    def prune(self, before: datetime) -> int:
        """Delete observations older than `before`; returns the number removed."""
        with self._transaction() as db:
            cursor = db.execute(
                "DELETE FROM tower_evidence WHERE observed_at<?", (_sort_key(before),)
            )
            return cursor.rowcount
