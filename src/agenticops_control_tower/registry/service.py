"""Thread-safe registry with optional durable SQLite storage."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from threading import RLock

from agenticops_control_tower.errors import AgentNotFoundError
from agenticops_control_tower.models import AgentRecord, AgentRegistrationPayload, HeartbeatPayload


class AgentRegistry:
    """Use memory by default, or a SQLite file for restart durability."""

    def __init__(self, database_path: str | Path | None = None) -> None:
        self._agents: dict[str, AgentRecord] = {}
        self._lock = RLock()
        self._database_path = str(database_path) if database_path is not None else None
        if self._database_path is not None:
            with sqlite3.connect(self._database_path) as connection:
                connection.execute(
                    "CREATE TABLE IF NOT EXISTS agents (id TEXT PRIMARY KEY, record TEXT NOT NULL)"
                )

    def _save(self, agent: AgentRecord) -> AgentRecord:
        if self._database_path is None:
            self._agents[agent.agent_id] = agent.model_copy(deep=True)
        else:
            with sqlite3.connect(self._database_path) as connection:
                connection.execute(
                    "INSERT OR REPLACE INTO agents VALUES (?, ?)",
                    (agent.agent_id, agent.model_dump_json()),
                )
        return agent.model_copy(deep=True)

    def register(self, registration: AgentRegistrationPayload) -> AgentRecord:
        with self._lock:
            agent = AgentRecord(**registration.model_dump(), last_seen=registration.registered_at)
            return self._save(agent)

    def heartbeat(self, agent_id: str, heartbeat: HeartbeatPayload) -> AgentRecord:
        with self._lock:
            if self._database_path is not None:
                with sqlite3.connect(self._database_path) as connection:
                    connection.execute("BEGIN IMMEDIATE")
                    row = connection.execute(
                        "SELECT record FROM agents WHERE id = ?", (agent_id,)
                    ).fetchone()
                    if row is None:
                        raise AgentNotFoundError(agent_id)
                    agent = AgentRecord.model_validate_json(row[0])
                    self._apply_heartbeat(agent, heartbeat)
                    connection.execute(
                        "UPDATE agents SET record = ? WHERE id = ?",
                        (agent.model_dump_json(), agent_id),
                    )
                return agent.model_copy(deep=True)
            agent = self.get(agent_id)
            self._apply_heartbeat(agent, heartbeat)
            return self._save(agent)

    @staticmethod
    def _apply_heartbeat(agent: AgentRecord, heartbeat: HeartbeatPayload) -> None:
        agent.status = heartbeat.status
        agent.last_seen = heartbeat.last_seen
        agent.capabilities.update(heartbeat.capabilities)
        agent.runtime_metadata.update(heartbeat.runtime_metadata)
        agent.package_metadata.update(heartbeat.package_metadata)
        agent.heartbeat_count += 1

    def list_agents(self) -> list[AgentRecord]:
        with self._lock:
            if self._database_path is not None:
                with sqlite3.connect(self._database_path) as connection:
                    return [
                        AgentRecord.model_validate_json(row[0])
                        for row in connection.execute("SELECT record FROM agents ORDER BY id")
                    ]
            return [self._agents[key].model_copy(deep=True) for key in sorted(self._agents)]

    def get(self, agent_id: str) -> AgentRecord:
        with self._lock:
            if self._database_path is not None:
                with sqlite3.connect(self._database_path) as connection:
                    row = connection.execute(
                        "SELECT record FROM agents WHERE id = ?", (agent_id,)
                    ).fetchone()
                if row is not None:
                    return AgentRecord.model_validate_json(row[0])
            elif agent_id in self._agents:
                return self._agents[agent_id].model_copy(deep=True)
            raise AgentNotFoundError(agent_id)
