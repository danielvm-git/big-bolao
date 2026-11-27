"""SQLite store with the same three primitives as the BigBase client.

Every domain method in BigBase (participantes, jogos, palpites) is built on
create / patch / list_records, so this subclass swaps only those. Each
collection is a table of (id, data JSON); records come back flat, as BigBase
returns them: {"id": 1, **data}.
"""
from __future__ import annotations

import json
import sqlite3
import threading

from bolao import config
from bolao.bigbase import JOGOS, PALPITES, PARTICIPANTES, BigBase, BigBaseError

COLLECTIONS = frozenset({PARTICIPANTES, JOGOS, PALPITES})


class SqliteStore(BigBase):
    def __init__(self, path: str | None = None) -> None:  # noqa: D107 - no HTTP client
        self.path = path or config.DB_PATH
        self._lock = threading.Lock()
        self._db = sqlite3.connect(self.path, check_same_thread=False, isolation_level=None)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA busy_timeout=5000")
        self._db.execute("PRAGMA synchronous=NORMAL")
        for name in COLLECTIONS:
            self._db.execute(
                f"CREATE TABLE IF NOT EXISTS {name} ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT NOT NULL)")

    async def close(self) -> None:
        with self._lock:
            self._db.close()

    @staticmethod
    def _table(collection: str) -> str:
        if collection not in COLLECTIONS:
            raise BigBaseError(f"unknown collection: {collection}")
        return collection

    async def create(self, collection: str, data: dict) -> int:
        table = self._table(collection)
        clean = {k: v for k, v in data.items() if k != "id"}
        with self._lock:
            cur = self._db.execute(
                f"INSERT INTO {table} (data) VALUES (?)", (json.dumps(clean, ensure_ascii=False),))
        return int(cur.lastrowid)

    async def patch(self, collection: str, rec_id: int, data: dict) -> None:
        table = self._table(collection)
        clean = {k: v for k, v in data.items() if k != "id"}
        with self._lock:
            row = self._db.execute(f"SELECT data FROM {table} WHERE id = ?", (int(rec_id),)).fetchone()
            if row is None:
                raise BigBaseError(f"patch {collection}/{rec_id}: not found")
            merged = {**json.loads(row[0]), **clean}
            self._db.execute(
                f"UPDATE {table} SET data = ? WHERE id = ?",
                (json.dumps(merged, ensure_ascii=False), int(rec_id)))

    async def list_records(self, collection: str, limit: int = 1000) -> list[dict]:
        table = self._table(collection)
        with self._lock:
            rows = self._db.execute(
                f"SELECT id, data FROM {table} ORDER BY id LIMIT ?", (int(limit),)).fetchall()
        return [{"id": rid, **json.loads(data)} for rid, data in rows]

    async def import_record(self, collection: str, rec_id: int, data: dict) -> None:
        """Insert a record keeping its original id (used by the BigBase export)."""
        table = self._table(collection)
        clean = {k: v for k, v in data.items() if k != "id"}
        with self._lock:
            self._db.execute(
                f"INSERT OR REPLACE INTO {table} (id, data) VALUES (?, ?)",
                (int(rec_id), json.dumps(clean, ensure_ascii=False)))


def open_store() -> BigBase:
    """The configured store: SqliteStore when BOLAO_STORE=sqlite, else BigBase."""
    return SqliteStore() if config.STORE == "sqlite" else BigBase()
