from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

if __name__ == "__main__" and __package__ is None:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from centrix.config_service import get_config, set_config
from centrix.control import set_safe_mode
from centrix.db import init_schema


@dataclass
class RiskLimits:
    max_daily_loss: Optional[float]
    max_order_size: Optional[float]


@dataclass
class DummyOrder:
    symbol: str
    side: str
    quantity: float


def _parse_optional_float(value: Optional[str]) -> Optional[float]:
    """Convert a string to float; return None if missing or invalid."""
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def load_risk_limits() -> RiskLimits:
    """Load risk limits from config storage."""
    max_daily_loss = _parse_optional_float(get_config("risk.max_daily_loss"))
    max_order_size = _parse_optional_float(get_config("risk.max_order_size"))
    return RiskLimits(max_daily_loss=max_daily_loss, max_order_size=max_order_size)


def check_order_against_limits(order: DummyOrder, limits: RiskLimits) -> Tuple[bool, Optional[str]]:
    """Return whether the order is allowed and an optional reason when blocked."""
    if limits.max_order_size is not None and order.quantity > limits.max_order_size:
        return (
            False,
            f"order quantity {order.quantity} exceeds max_order_size {limits.max_order_size}",
        )

    # max_daily_loss placeholder for future implementation
    return True, None


def evaluate_order(order: DummyOrder) -> bool:
    """Evaluate an order against current limits; enable safe_mode if blocked."""
    limits = load_risk_limits()
    allowed, reason = check_order_against_limits(order, limits)

    if allowed:
        print(
            f"Order erlaubt: symbol={order.symbol}, side={order.side}, quantity={order.quantity}"
        )
        return True

    print(f"Order blockiert: {reason}; Safe-Mode aktiviert")
    set_safe_mode(True)
    return False


if __name__ == "__main__":
    # Simple self-test with dummy orders and limits
    init_schema()
    set_config("risk.max_order_size", "1000", value_type="float")

    small_order = DummyOrder(symbol="AAPL", side="buy", quantity=100)
    large_order = DummyOrder(symbol="AAPL", side="buy", quantity=1500)

    evaluate_order(small_order)
    evaluate_order(large_order)
