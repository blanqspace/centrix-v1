from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import sqlite3


@dataclass
class NewOrder:
    symbol: str
    side: str
    quantity: float


@dataclass
class OrderRecord:
    id: int
    symbol: str
    side: str
    quantity: float
    status: str
    error_message: Optional[str]

    @staticmethod
    def from_row(row: sqlite3.Row) -> "OrderRecord":
        return OrderRecord(
            id=row["id"],
            symbol=row["symbol"],
            side=row["side"],
            quantity=row["quantity"],
            status=row["status"],
            error_message=row["error_message"],
        )
