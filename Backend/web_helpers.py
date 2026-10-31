"""Helpers for server-rendered HTML pages."""

from __future__ import annotations

from datetime import date


def euro(amount: float | int) -> str:
    return f"€ {float(amount):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(value: float | int) -> str:
    return f"{float(value):.0f}%"


def today_iso() -> str:
    return date.today().isoformat()


def distributie_datum() -> str:
    """Seed leveringen use 2026-10-31; use today if data exists later."""
    return today_iso()


_DAG_NL = (
    "MAANDAG",
    "DINSDAG",
    "WOENSDAG",
    "DONDERDAG",
    "VRIJDAG",
    "ZATERDAG",
    "ZONDAG",
)
_MAAND_NL = (
    "JANUARI",
    "FEBRUARI",
    "MAART",
    "APRIL",
    "MEI",
    "JUNI",
    "JULI",
    "AUGUSTUS",
    "SEPTEMBER",
    "OKTOBER",
    "NOVEMBER",
    "DECEMBER",
)


def distributie_dagregel(iso_datum: str) -> str:
    d = date.fromisoformat(iso_datum)
    return f"{_DAG_NL[d.weekday()]} {d.day} {_MAAND_NL[d.month - 1]}"
