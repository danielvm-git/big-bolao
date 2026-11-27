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

# Every statement is built here from the fixed collection names, so no value
# from a caller or a request ever reaches the SQL text.
_SQL = {
    name: {
        "create_table": f"CREATE TABLE IF NOT EXISTS {name} ("
                        "id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT NOT NULL)",
        "insert": f"INSERT INTO {name} (data) VALUES (?)",
        "select_one": f"SELECT data FROM {name} WHERE id = ?",
        "update": f"UPDATE {name} SET data = ? WHERE id = ?",
        "select_all": f"SELECT id, data FROM {name} ORDER BY id LIMIT ?",
        "import": f"INSERT OR REPLACE INTO {name} (id, data) VALUES (?, ?)",
    }
    for name in (PARTICIPANTES, JOGOS, PALPITES)
}


class SqliteStore(BigBase):
    def __init__(self, path: str | None = None) -> None:  # noqa: D107 - no HTTP client
        self.path = path or config.DB_PATH
        self._lock = threading.Lock()
        self._db = sqlite3.connect(self.path, check_same_thread=False, isolation_level=None)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA busy_timeout=5000")
        self._db.execute("PRAGMA synchronous=NORMAL")
        for statements in _SQL.values():
            self._db.execute(statements["create_table"])

    async def close(self) -> None:
        with self._lock:
            self._db.close()

    @staticmethod
    def _sql(collection: str) -> dict[str, str]:
        try:
            return _SQL[collection]
        except KeyError:
            raise BigBaseError(f"unknown collection: {collection}") from None

    async def create(self, collection: str, data: dict) -> int:
        sql = self._sql(collection)
        clean = {k: v for k, v in data.items() if k != "id"}
        with self._lock:
            cur = self._db.execute(sql["insert"], (json.dumps(clean, ensure_ascii=False),))
        return int(cur.lastrowid)

    async def patch(self, collection: str, rec_id: int, data: dict) -> None:
        sql = self._sql(collection)
        clean = {k: v for k, v in data.items() if k != "id"}
        with self._lock:
            row = self._db.execute(sql["select_one"], (int(rec_id),)).fetchone()
            if row is None:
                raise BigBaseError(f"patch {collection}/{rec_id}: not found")
            merged = {**json.loads(row[0]), **clean}
            self._db.execute(sql["update"], (json.dumps(merged, ensure_ascii=False), int(rec_id)))

    async def list_records(self, collection: str, limit: int = 1000) -> list[dict]:
        sql = self._sql(collection)
        with self._lock:
            rows = self._db.execute(sql["select_all"], (int(limit),)).fetchall()
        return [{"id": rid, **json.loads(data)} for rid, data in rows]

    async def import_record(self, collection: str, rec_id: int, data: dict) -> None:
        """Insert a record keeping its original id (used by the BigBase export)."""
        sql = self._sql(collection)
        clean = {k: v for k, v in data.items() if k != "id"}
        with self._lock:
            self._db.execute(sql["import"], (int(rec_id), json.dumps(clean, ensure_ascii=False)))


def open_store() -> BigBase:
    """The configured store: SqliteStore when BOLAO_STORE=sqlite, else BigBase."""
    return SqliteStore() if config.STORE == "sqlite" else BigBase()
