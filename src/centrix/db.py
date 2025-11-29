from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable, List


def get_db_path() -> Path:
    """Return the filesystem path of the SQLite database file."""
    project_root = Path(__file__).resolve().parents[2]
    return project_root / "centrix.db"


def get_connection() -> sqlite3.Connection:
    """Create a new SQLite connection with row access by column name."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_schema() -> None:
    """Create required tables if they do not yet exist."""
    schema = """
    CREATE TABLE IF NOT EXISTS config_settings (
        id INTEGER PRIMARY KEY,
        key TEXT NOT NULL,
        value TEXT NOT NULL,
        value_type TEXT NOT NULL,
        scope TEXT NOT NULL,
        updated_at INTEGER NOT NULL,
        updated_by TEXT,
        UNIQUE(key, scope)
    );

    CREATE TABLE IF NOT EXISTS control_flags (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS heartbeats (
        id INTEGER PRIMARY KEY,
        source TEXT NOT NULL,
        status TEXT NOT NULL,
        ts INTEGER NOT NULL
    );
    """

    with get_connection() as conn:
        conn.executescript(schema)


if __name__ == "__main__":
    init_schema()
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables: Iterable[str] = (row[0] for row in cursor.fetchall())
        print(list(tables))
