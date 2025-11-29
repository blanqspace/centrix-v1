from __future__ import annotations

import sys
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from centrix.config_service import get_config, set_config
from centrix.control import get_safe_mode, set_safe_mode
from centrix.db import init_schema
from centrix.engine_loop import run_engine_loop
from centrix.risk import DummyOrder, evaluate_order, load_risk_limits


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
    elif cmd == "run-risk-demo":
        init_schema()
        set_safe_mode(False)
        if get_config("risk.max_daily_loss") is None:
            set_config("risk.max_daily_loss", "150", value_type="float")
        if get_config("risk.max_order_size") is None:
            set_config("risk.max_order_size", "100", value_type="float")

        limits = load_risk_limits()
        print(
            f"Risk-Limits: max_daily_loss={limits.max_daily_loss}, max_order_size={limits.max_order_size}"
        )

        effective_limit = limits.max_order_size if limits.max_order_size is not None else 100.0
        small_order = DummyOrder(symbol="AAPL", side="buy", quantity=effective_limit / 2)
        large_order = DummyOrder(symbol="AAPL", side="buy", quantity=effective_limit * 2)

        evaluate_order(small_order)
        evaluate_order(large_order)

        print(f"safe_mode={get_safe_mode()}")
    elif cmd == "show-safe-mode":
        init_schema()
        print(f"safe_mode={get_safe_mode()}")
    else:
        print(f"Unknown command: {cmd}")
        print("Available commands: init-db, run-engine, run-risk-demo, show-safe-mode")


if __name__ == "__main__":
    main()
