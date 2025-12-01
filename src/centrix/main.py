from __future__ import annotations

import sys
import time
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from centrix.config_service import get_config, set_config
from centrix.control import get_safe_mode, set_safe_mode
from centrix.db import init_schema
from centrix.engine_loop import run_engine_loop
from centrix.heartbeat import get_latest_heartbeat, write_heartbeat
from centrix.ib_client import (
    connect_ib,
    create_ib_client,
    disconnect_ib,
    is_ib_connected,
)
from centrix.order_model import NewOrder
from centrix.order_service import (
    check_risk,
    create_order_proposal,
    execute_order,
    get_order,
)
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
    elif cmd == "test-ib-connection":
        init_schema()
        client = create_ib_client()
        ok = connect_ib(client)
        if ok and is_ib_connected(client):
            write_heartbeat("gateway", "connected")
            print("IBKR: connected")
        else:
            write_heartbeat("gateway", "disconnected")
            print("IBKR: connection failed")
        disconnect_ib(client)
    elif cmd == "show-gateway-status":
        init_schema()
        hb = get_latest_heartbeat("gateway")
        if hb is None:
            print("gateway: kein Heartbeat vorhanden")
        else:
            age = int(time.time() - hb["ts"])
            print(f"gateway: {hb['status']} (vor {age} Sekunden)")
    elif cmd == "run-order-demo":
        init_schema()

        # Optional connectivity check (non-fatal)
        client = create_ib_client()
        if connect_ib(client):
            write_heartbeat("gateway", "connected")
            disconnect_ib(client)
        else:
            write_heartbeat("gateway", "disconnected")

        demo_order = NewOrder(symbol="AAPL", side="buy", quantity=10)
        order_id = create_order_proposal(demo_order)
        print(f"Order angelegt: id={order_id}, symbol={demo_order.symbol}, side={demo_order.side}, qty={demo_order.quantity}")

        allowed, reason = check_risk(order_id)
        if not allowed:
            ord_rec = get_order(order_id)
            print(f"Order geblockt: id={order_id}, status={ord_rec.status if ord_rec else 'unknown'}, reason={reason}")
            return

        ok = execute_order(order_id)
        final_order = get_order(order_id)
        if final_order is None:
            print(f"Order {order_id} nicht gefunden")
            return
        print(
            f"Order fertig: id={final_order.id}, symbol={final_order.symbol}, side={final_order.side}, qty={final_order.quantity}, status={final_order.status}, error={final_order.error_message}"
        )
    else:
        print(f"Unknown command: {cmd}")
        print(
            "Available commands: init-db, run-engine, run-risk-demo, show-safe-mode, "
            "test-ib-connection, show-gateway-status, run-order-demo"
        )


if __name__ == "__main__":
    main()
