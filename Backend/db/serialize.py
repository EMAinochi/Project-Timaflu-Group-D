"""Convert MySQL row types for JSON responses."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Any


def _value(v: Any) -> Any:
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    if isinstance(v, time):
        return v.strftime("%H:%M")
    if isinstance(v, timedelta):
        return str(v)
    return v


def sanitize_row(row: dict | None) -> dict | None:
    if row is None:
        return None
    return {k: _value(v) for k, v in row.items()}


def sanitize_rows(rows: list[dict]) -> list[dict]:
    return [sanitize_row(r) for r in rows]
