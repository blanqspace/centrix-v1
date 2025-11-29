from __future__ import annotations

import sys
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from centrix.db import init_schema
from centrix.engine_loop import run_engine_loop


def main() -> None:
    if len(sys.argv) == 1:
        print("Centrix v1 – skeleton ready")
        return

    cmd = sys.argv[1]

    if cmd == "init-db":
        init_schema()
        print("DB schema initialized")
    elif cmd == "run-engine":
        init_schema()
        run_engine_loop(max_iterations=20)
        print("Engine loop finished (test mode)")
    else:
        print(f"Unknown command: {cmd}")
        print("Available commands: init-db, run-engine")


if __name__ == "__main__":
    main()
