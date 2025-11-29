from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Optional

if __name__ == "__main__" and __package__ is None:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from centrix.db import get_connection, init_schema


def get_flag(key: str, default: Optional[str] = None) -> Optional[str]:
    """Return the control flag value for the given key or a default if missing."""
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT value FROM control_flags WHERE key = ?", (key,)
        )
        row = cursor.fetchone()
        if row is None:
            return default
        return row["value"]


def set_flag(key: str, value: str) -> None:
    """Insert or replace a control flag value."""
    ts = int(time.time())
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO control_flags (key, value, updated_at)
            VALUES (?, ?, ?)
            """,
            (key, value, ts),
        )


def get_safe_mode() -> bool:
    """Return True if safe_mode flag is set to 'true'."""
    value = get_flag("safe_mode", default="false")
    return value.lower() == "true" if value is not None else False


def set_safe_mode(enabled: bool) -> None:
    """Set the safe_mode flag to 'true' or 'false'."""
    set_flag("safe_mode", "true" if enabled else "false")


def get_restart_needed() -> bool:
    """Return True if restart_needed flag is set to 'true'."""
    value = get_flag("restart_needed", default="false")
    return value.lower() == "true" if value is not None else False


def set_restart_needed(enabled: bool) -> None:
    """Set the restart_needed flag to 'true' or 'false'."""
    set_flag("restart_needed", "true" if enabled else "false")


if __name__ == "__main__":
    init_schema()
    set_safe_mode(True)
    print(get_safe_mode())
    set_restart_needed(True)
    print(get_restart_needed())
    set_safe_mode(False)
    print(get_safe_mode())
    set_restart_needed(False)
    print(get_restart_needed())
