"""Orderpicking — orders + order_line + product (wireframe 3.2.1)."""

from __future__ import annotations

import re

from db.connection import db_cursor
from db.serialize import sanitize_row, sanitize_rows

ORDER_DISPLAY_OFFSET = 1020
GANG_BINS = {"A": "BAK-0012", "C": "BAK-0031", "F": "BAK-0032", "B": "BAK-0020", "D": "BAK-0040"}

GANG_STATUS_NL = {
    "BEZIG": "Bezig",
    "VERZAMELD": "Verzameld",
    "ROLLERBAAN": "Op rollerbaan",
}


def display_order_number(order_id: int) -> int:
    return ORDER_DISPLAY_OFFSET + int(order_id)


def resolve_order_id(value: int) -> int:
    if value >= 1000:
        return value - ORDER_DISPLAY_OFFSET
    return value


def _gang_from_location(magazijn_locatie: str) -> str:
    loc = (magazijn_locatie or "").strip()
    match = re.search(r"Loc\s+([A-Za-z])", loc, re.I)
    if match:
        return match.group(1).upper()
    if loc:
        return loc[0].upper()
    return "A"


def picking_status_nl(status: str) -> str:
    return {
        "BEING_PICKED": "Wordt verzameld",
        "BACKORDER": "In wachtrij",
        "READY_FOR_DISTRIBUTION": "Klaar voor distributie",
    }.get(status, status.replace("_", " ").capitalize())


class OrderpickingService:
    def open_orders(self) -> list[dict]:
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT o.order_id, o.status, o.urgent AS spoed,
                       c.company_name AS bedrijfsnaam
                FROM orders o
                JOIN customer c ON c.customer_id = o.customer_id
                WHERE o.status IN (
                    'BEING_PICKED', 'BACKORDER', 'READY_FOR_DISTRIBUTION'
                )
                ORDER BY o.urgent DESC, FIELD(o.order_id, 3, 4, 2), o.order_id ASC
                """
            )
            rows = sanitize_rows(cur.fetchall())
            for r in rows:
                oid = int(r["order_id"])
                r["ordernummer"] = display_order_number(oid)
                r["status"] = picking_status_nl(r["status"])
            return rows

    def order_lines(self, order_id: int) -> list[dict]:
        order_id = resolve_order_id(order_id)
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT p.order_code AS bestelcode, p.name AS naam, ol.quantity AS aantal,
                       ol.backorder AS is_backorder,
                       p.packaging_type AS magazijn_locatie
                FROM order_line ol
                JOIN product p ON p.product_id = ol.product_id
                WHERE ol.order_id = %s
                ORDER BY ol.backorder, p.name
                """,
                (order_id,),
            )
            rows = sanitize_rows(cur.fetchall())
            for r in rows:
                r["status"] = "backorder" if r.get("is_backorder") else "leverbaar"
                loc = r.get("magazijn_locatie") or ""
                r["locatie_code"] = loc.replace("Loc ", "").strip() if loc else "—"
            return rows

    def _gang_codes_for_order(self, lines: list[dict]) -> list[str]:
        gangs: set[str] = set()
        for line in lines:
            if line.get("status") != "leverbaar":
                continue
            gangs.add(_gang_from_location(line.get("magazijn_locatie") or ""))
        return sorted(gangs)

    def _ensure_gang_rows(self, cur, order_id: int, gang_codes: list[str]) -> None:
        for gang in gang_codes:
            cur.execute(
                """
                INSERT IGNORE INTO order_pick_gang (order_id, gang, status)
                VALUES (%s, %s, 'BEZIG')
                """,
                (order_id, gang),
            )

    def _load_gang_statuses(self, cur, order_id: int) -> dict[str, str]:
        cur.execute(
            "SELECT gang, status FROM order_pick_gang WHERE order_id = %s",
            (order_id,),
        )
        return {r["gang"]: r["status"] for r in cur.fetchall()}

    def _build_gangs(self, gang_codes: list[str], statuses: dict[str, str]) -> list[dict]:
        out: list[dict] = []
        for gang in gang_codes:
            raw = statuses.get(gang, "BEZIG")
            out.append(
                {
                    "gang": gang,
                    "robot": f"Robot {gang}",
                    "bakken": GANG_BINS.get(gang, f"BAK-{gang}01"),
                    "status": GANG_STATUS_NL.get(raw, raw),
                    "status_code": raw,
                }
            )
        return out

    def get_order_detail(self, order_id: int) -> dict | None:
        order_id = resolve_order_id(order_id)
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT o.order_id, o.status, o.urgent AS spoed,
                       c.company_name AS bedrijfsnaam
                FROM orders o
                JOIN customer c ON c.customer_id = o.customer_id
                WHERE o.order_id = %s
                """,
                (order_id,),
            )
            order = cur.fetchone()
            if not order:
                return None

            raw_status = order["status"]
            lines = self.order_lines(order_id)
            gang_codes = self._gang_codes_for_order(lines)
            if gang_codes:
                self._ensure_gang_rows(cur, order_id, gang_codes)
            statuses = self._load_gang_statuses(cur, order_id)
            gangs = self._build_gangs(gang_codes, statuses)

            backorder = [
                {**l, "melding": "Verkoop is gemeld"}
                for l in lines
                if l.get("status") == "backorder"
            ]

            all_done = bool(gang_codes) and all(
                statuses.get(g, "BEZIG") in ("VERZAMELD", "ROLLERBAAN") for g in gang_codes
            )

            order["ordernummer"] = display_order_number(order["order_id"])
            order["status"] = picking_status_nl(raw_status)
            order["raw_status"] = raw_status
            order["kan_compleet"] = all_done and raw_status in ("BEING_PICKED", "BACKORDER")
            return sanitize_row(
                {**order, "regels": lines, "gangs": gangs, "backorder": backorder}
            )

    def set_gang_status(self, order_id: int, gang: str, status: str) -> bool:
        order_id = resolve_order_id(order_id)
        gang = gang.strip().upper()[:1]
        if status not in GANG_STATUS_NL:
            return False
        with db_cursor() as cur:
            cur.execute(
                """
                INSERT INTO order_pick_gang (order_id, gang, status)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE status = VALUES(status)
                """,
                (order_id, gang, status),
            )
            return cur.rowcount > 0

    def mark_order_ready(self, order_id: int) -> bool:
        order_id = resolve_order_id(order_id)
        detail = self.get_order_detail(order_id)
        if not detail or not detail.get("kan_compleet"):
            return False
        with db_cursor() as cur:
            cur.execute(
                """
                UPDATE orders SET status = 'READY_FOR_DISTRIBUTION'
                WHERE order_id = %s
                  AND status IN ('BEING_PICKED', 'BACKORDER')
                """,
                (order_id,),
            )
            return cur.rowcount > 0

    def update_order_status(self, order_id: int, status: str) -> bool:
        order_id = resolve_order_id(order_id)
        with db_cursor() as cur:
            cur.execute(
                "UPDATE orders SET status = %s WHERE order_id = %s",
                (status, order_id),
            )
            return cur.rowcount > 0
