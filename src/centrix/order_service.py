from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Optional, Tuple

if __name__ == "__main__" and __package__ is None:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from centrix.control import get_safe_mode, set_safe_mode
from centrix.db import get_connection
from centrix.ib_client import create_ib_client, connect_ib, disconnect_ib, submit_market_order
from centrix.order_model import NewOrder, OrderRecord
from centrix.risk import DummyOrder, check_order_against_limits, load_risk_limits


def _now_ts() -> int:
    return int(time.time())


def create_order_proposal(new_order: NewOrder) -> int:
    """Insert a proposed order into the orders table and return its id."""
    ts = _now_ts()
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO orders (symbol, side, quantity, status, created_at, updated_at, error_message)
            VALUES (?, ?, ?, 'proposed', ?, ?, NULL)
            """,
            (new_order.symbol, new_order.side, new_order.quantity, ts, ts),
        )
        return int(cursor.lastrowid)


def get_order(order_id: int) -> Optional[OrderRecord]:
    """Fetch an order by id."""
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM orders WHERE id = ?",
            (order_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return OrderRecord.from_row(row)


def update_order_status(order_id: int, status: str, error_message: Optional[str] = None) -> None:
    """Update order status and optional error message."""
    ts = _now_ts()
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE orders
            SET status = ?, updated_at = ?, error_message = ?
            WHERE id = ?
            """,
            (status, ts, error_message, order_id),
        )


def check_risk(order_id: int) -> Tuple[bool, str]:
    """Evaluate risk limits for an order; update status if blocked."""
    order = get_order(order_id)
    if order is None:
        return False, "order not found"

    dummy = DummyOrder(symbol=order.symbol, side=order.side, quantity=order.quantity)
    limits = load_risk_limits()
    allowed, reason = check_order_against_limits(dummy, limits)

    if not allowed:
        update_order_status(order_id, "risk_blocked", error_message=reason)
        set_safe_mode(True)
        return False, reason or "risk blocked"

    return True, ""


def execute_order(order_id: int) -> bool:
    """Execute an order end-to-end for Phase 5 (paper)."""
    order = get_order(order_id)
    if order is None:
        return False

    if get_safe_mode():
        update_order_status(order_id, "failed", error_message="Safe-Mode active")
        return False

    allowed, reason = check_risk(order_id)
    if not allowed:
        return False

    client = create_ib_client()

    connected = connect_ib(client)
    if not connected:
        update_order_status(order_id, "failed", error_message="IB connection failed")
        return False

    try:
        update_order_status(order_id, "executing")
        success, err = submit_market_order(client, order.symbol, order.side, order.quantity)
        if success:
            update_order_status(order_id, "executed", error_message=None)
            return True
        update_order_status(order_id, "failed", error_message=err or "IB order failed")
        return False
    except Exception as exc:  # safety net to avoid crashes
        update_order_status(order_id, "failed", error_message=str(exc))
        return False
    finally:
        disconnect_ib(client)
