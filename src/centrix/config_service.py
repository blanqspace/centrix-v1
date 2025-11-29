from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Optional

if __name__ == "__main__" and __package__ is None:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from centrix.db import get_connection, init_schema


def get_config(key: str, scope: str = "global", default: Optional[str] = None) -> Optional[str]:
    """Return a config value for the given key and scope or the provided default."""
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT value FROM config_settings WHERE key = ? AND scope = ?", (key, scope)
        )
        row = cursor.fetchone()
        if row is None:
            return default
        return row["value"]


def get_config_float(
    key: str, scope: str = "global", default: Optional[float] = None
) -> Optional[float]:
    """Return a config value converted to float or the provided default on failure/missing."""
    raw = get_config(key, scope=scope)
    if raw is None:
        return default
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default


def set_config(
    key: str,
    value: str,
    scope: str = "global",
    value_type: str = "str",
    updated_by: str = "system",
) -> None:
    """Insert or replace a config value for the given key and scope."""
    ts = int(time.time())
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO config_settings
            (id, key, value, value_type, scope, updated_at, updated_by)
            VALUES (
                (
                    SELECT id FROM config_settings WHERE key = ? AND scope = ?
                ),
                ?, ?, ?, ?, ?, ?
            )
            """,
            (key, scope, key, value, value_type, scope, ts, updated_by),
        )


def get_config_version() -> int:
    """Return the current config version stored in control_flags."""
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT value FROM control_flags WHERE key = 'config_version'"
        )
        row = cursor.fetchone()
        if row is None:
            return 0
        try:
            return int(row["value"])
        except (TypeError, ValueError):
            return 0


def bump_config_version(reason: str = "") -> int:
    """Increase config_version and return the new value."""
    current = get_config_version()
    new_version = current + 1
    ts = int(time.time())
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO control_flags (key, value, updated_at)
            VALUES ('config_version', ?, ?)
            """,
            (str(new_version), ts),
        )
    return new_version


def _ensure_config_version_row() -> None:
    """Ensure config_version exists in control_flags; initialize to 0 if absent."""
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT 1 FROM control_flags WHERE key = 'config_version' LIMIT 1"
        )
        if cursor.fetchone() is None:
            ts = int(time.time())
            conn.execute(
                """
                INSERT INTO control_flags (key, value, updated_at)
                VALUES ('config_version', '0', ?)
                """,
                (ts,),
            )


if __name__ == "__main__":
    init_schema()
    _ensure_config_version_row()
    set_config("risk.max_daily_loss", "200", value_type="float")
    print(get_config("risk.max_daily_loss"))
    print(get_config_version())
    print(bump_config_version())
    print(get_config_version())
