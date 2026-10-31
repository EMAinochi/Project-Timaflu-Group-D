"""Distributie — delivery + orders + customer (timaflu_schema.sql)."""

from __future__ import annotations

from datetime import date

from db.connection import db_cursor
from db.mappers import day_part_nl, format_address
from db.serialize import sanitize_rows


class DistributieService:
    def rooster_voor_datum(self, datum: date | str) -> list[dict]:
        """Productbeschrijving distributie — invoer datum → rooster met klantgegevens."""
        return self.get_schedule(datum)

    @staticmethod
    def _status_label(row: dict) -> str:
        if row.get("order_status") == "NOT_DELIVERED":
            return "Niet afgeleverd"
        if row.get("afgeleverd"):
            return "Afgeleverd"
        if int(row.get("pogingen") or 0) > 1:
            return "Later vandaag"
        return "Gepland"

    def get_schedule(self, schedule_date: date | str) -> list[dict]:
        if isinstance(schedule_date, str):
            schedule_date = date.fromisoformat(schedule_date)

        with db_cursor() as cur:
            cur.execute(
                """
                SELECT d.delivery_id AS levering_id,
                       TIME_FORMAT(d.delivery_time, '%H:%i') AS levertijd,
                       d.attempts AS pogingen, d.delivered AS afgeleverd,
                       o.order_id AS ordernummer, o.urgent AS spoed, o.day_part,
                       o.status AS order_status,
                       c.company_name AS bedrijfsnaam, c.contact_person AS contactpersoon,
                       c.phone_number AS telefoonnummer,
                       a.street, a.house_number, a.postal_code, a.city,
                       e.name AS koerier
                FROM delivery d
                JOIN orders o ON o.order_id = d.order_id
                JOIN customer c ON c.customer_id = o.customer_id
                JOIN address a ON a.address_id = c.delivery_address_id
                LEFT JOIN employee e ON e.employee_id = d.courier_id
                WHERE d.delivery_date = %s
                ORDER BY d.delivery_time
                """,
                (schedule_date,),
            )
            rows = cur.fetchall()
            out = []
            for row in rows:
                out.append(
                    {
                        **row,
                        "adres": format_address(
                            row["street"],
                            row["house_number"],
                            row["postal_code"],
                            row["city"],
                        ),
                        "dagdeel": day_part_nl(row["day_part"]),
                        "klantnaam": row["bedrijfsnaam"],
                        "terugkomen_zelfde_dag": int(row["pogingen"]) > 1
                        and not row["afgeleverd"]
                        and row["order_status"] != "NOT_DELIVERED",
                        "is_terugkeer": int(row["pogingen"]) > 1,
                    }
                )
                item = out[-1]
                item["status_label"] = self._status_label(item)
            return sanitize_rows(out)

    def mark_customer_absent(self, delivery_id: int) -> bool:
        with db_cursor() as cur:
            cur.execute(
                """
                UPDATE delivery
                SET attempts = attempts + 1,
                    delivered = 0,
                    delivery_time = ADDTIME(delivery_time, '02:00:00')
                WHERE delivery_id = %s
                """,
                (delivery_id,),
            )
            return cur.rowcount > 0

    def mark_delivery_attempt(self, delivery_id: int, customer_present: bool) -> bool:
        with db_cursor() as cur:
            if customer_present:
                cur.execute(
                    """
                    UPDATE delivery SET delivered = 1, signed = 1
                    WHERE delivery_id = %s
                    """,
                    (delivery_id,),
                )
                cur.execute(
                    """
                    UPDATE orders o
                    JOIN delivery d ON d.order_id = o.order_id
                    SET o.status = 'DELIVERED'
                    WHERE d.delivery_id = %s
                    """,
                    (delivery_id,),
                )
            else:
                cur.execute(
                    """
                    UPDATE delivery
                    SET delivered = 0, attempts = attempts + 1
                    WHERE delivery_id = %s
                    """,
                    (delivery_id,),
                )
                cur.execute(
                    """
                    UPDATE orders o
                    JOIN delivery d ON d.order_id = o.order_id
                    SET o.status = 'NOT_DELIVERED'
                    WHERE d.delivery_id = %s
                    """,
                    (delivery_id,),
                )
            return cur.rowcount > 0
