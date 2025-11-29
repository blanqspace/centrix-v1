from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Dict, Optional

if __name__ == "__main__" and __package__ is None:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from centrix.db import get_connection, init_schema


def write_heartbeat(source: str, status: str = "ok") -> None:
    """Insert a heartbeat entry for the given source with current timestamp."""
    ts = int(time.time())
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO heartbeats (source, status, ts)
            VALUES (?, ?, ?)
            """,
            (source, status, ts),
        )


def get_latest_heartbeat(source: str) -> Optional[Dict[str, int | str]]:
    """Return the most recent heartbeat for a source or None if missing."""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT source, status, ts
            FROM heartbeats
            WHERE source = ?
            ORDER BY ts DESC
            LIMIT 1
            """,
            (source,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return {"source": row["source"], "status": row["status"], "ts": row["ts"]}


if __name__ == "__main__":
    init_schema()

    write_heartbeat("engine", "ok")
    time.sleep(1)
    write_heartbeat("engine", "ok")
    time.sleep(1)
    write_heartbeat("engine", "ok")

    write_heartbeat("gateway", "ok")

    print(get_latest_heartbeat("engine"))
    print(get_latest_heartbeat("gateway"))
