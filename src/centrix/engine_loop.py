from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Dict, Optional

if __name__ == "__main__" and __package__ is None:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from centrix.config_service import get_config, get_config_version, set_config
from centrix.control import (
    get_restart_needed,
    set_engine_state,
)
from centrix.db import init_schema
from centrix.heartbeat import write_heartbeat


def load_engine_config() -> Dict[str, int]:
    """Load engine loop configuration with defaults."""
    loop_sleep_ms = int(get_config("engine.loop_sleep_ms", default="500") or "500")
    heartbeat_interval_sec = int(
        get_config("engine.heartbeat_interval_sec", default="5") or "5"
    )
    return {
        "loop_sleep_ms": loop_sleep_ms,
        "heartbeat_interval_sec": heartbeat_interval_sec,
    }


def run_engine_loop(max_iterations: Optional[int] = None) -> None:
    """Run the engine loop, emitting heartbeats and reloading config on change."""
    init_schema()
    config = load_engine_config()
    loop_sleep_ms = config["loop_sleep_ms"]
    heartbeat_interval_sec = config["heartbeat_interval_sec"]

    set_engine_state("starting")
    current_version = get_config_version()
    set_engine_state("running")

    i = 0
    last_heartbeat_ts = 0.0

    while True:
        now = time.time()

        if now - last_heartbeat_ts >= heartbeat_interval_sec:
            write_heartbeat("engine", "ok")
            last_heartbeat_ts = now

        new_version = get_config_version()
        if new_version != current_version:
            config = load_engine_config()
            loop_sleep_ms = config["loop_sleep_ms"]
            heartbeat_interval_sec = config["heartbeat_interval_sec"]
            current_version = new_version
            print(f"[engine_loop] Config reloaded, version={current_version}")

        if get_restart_needed():
            print("[engine_loop] restart_needed = true, stopping loop")
            set_engine_state("stopping")
            break

        if max_iterations is not None:
            i += 1
            if i >= max_iterations:
                print("[engine_loop] max_iterations reached, stopping loop")
                break

        time.sleep(loop_sleep_ms / 1000.0)

    set_engine_state("stopped")


if __name__ == "__main__":
    init_schema()

    if get_config("engine.loop_sleep_ms") is None:
        set_config("engine.loop_sleep_ms", "200", value_type="int")
    if get_config("engine.heartbeat_interval_sec") is None:
        set_config("engine.heartbeat_interval_sec", "1", value_type="int")

    run_engine_loop(max_iterations=10)
