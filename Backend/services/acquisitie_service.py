"""Acquisitie — visit + customer (timaflu_schema.sql)."""

from __future__ import annotations

from datetime import date

from db.connection import db_cursor
from db.mappers import format_address
from db.serialize import sanitize_rows


class AcquisitieService:
    def register_visit(
        self,
        bedrijfsnaam: str,
        contactpersoon: str,
        telefoonnummer: str,
        straat: str,
        postcode: str,
        plaats: str,
        bezoekdatum: date | str,
    ) -> dict:
        if isinstance(bezoekdatum, str):
            bezoekdatum = date.fromisoformat(bezoekdatum)

        with db_cursor() as cur:
            cur.execute(
                """
                INSERT INTO address (street, house_number, postal_code, city)
                VALUES (%s, '', %s, %s)
                """,
                (straat, postcode, plaats),
            )
            address_id = cur.lastrowid
            cur.execute(
                "SELECT employee_id FROM employee WHERE department = 'Acquisitie' LIMIT 1"
            )
            mgr = cur.fetchone()
            account_manager_id = mgr["employee_id"] if mgr else 1
            cur.execute(
                """
                INSERT INTO visit (
                    account_manager_id, company_name, contact_person, phone_number,
                    address_id, visit_date, customer_id
                ) VALUES (%s, %s, %s, %s, %s, %s, NULL)
                """,
                (
                    account_manager_id,
                    bedrijfsnaam,
                    contactpersoon,
                    telefoonnummer,
                    address_id,
                    bezoekdatum,
                ),
            )
            return {"bezoek_id": cur.lastrowid, "status": "bezoek toegevoegd"}

    def get_acquisition_overview(self) -> list[dict]:
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT v.visit_id AS bezoek_id, v.company_name AS bedrijfsnaam,
                       v.contact_person AS contactpersoon, v.phone_number AS telefoonnummer,
                       v.visit_date AS bezoekdatum, v.customer_id AS klantnummer,
                       a.street, a.house_number, a.postal_code, a.city
                FROM visit v
                JOIN address a ON a.address_id = v.address_id
                WHERE v.customer_id IS NULL
                  AND v.visit_date <= DATE_SUB(CURDATE(), INTERVAL 1 MONTH)
                  AND NOT EXISTS (
                      SELECT 1 FROM customer c WHERE c.company_name = v.company_name
                  )
                  AND NOT EXISTS (
                      SELECT 1 FROM orders o
                      JOIN customer c ON c.customer_id = o.customer_id
                      WHERE c.company_name = v.company_name
                  )
                ORDER BY v.visit_date
                """
            )
            rows = cur.fetchall()
            return sanitize_rows(
                [
                    {
                        **r,
                        "adres": format_address(
                            r["street"], r.get("house_number") or "", r["postal_code"], r["city"]
                        ),
                    }
                    for r in rows
                ]
            )

    def create_customer_with_incentive(self, visit_id: int) -> dict | None:
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT v.*, a.street, a.postal_code, a.city
                FROM visit v
                JOIN address a ON a.address_id = v.address_id
                WHERE v.visit_id = %s
                """,
                (visit_id,),
            )
            visit = cur.fetchone()
            if not visit:
                return None

            cur.execute(
                """
                INSERT INTO address (street, house_number, postal_code, city)
                VALUES (%s, '', %s, %s)
                """,
                (visit["street"], visit["postal_code"], visit["city"]),
            )
            inv_id = cur.lastrowid
            cur.execute(
                """
                INSERT INTO customer (
                    company_name, contact_person, phone_number,
                    delivery_address_id, invoice_address_id, region,
                    annual_turnover, one_time_discount, blocked
                ) VALUES (%s, %s, %s, %s, %s, %s, 0, 1, 0)
                """,
                (
                    visit["company_name"],
                    visit["contact_person"],
                    visit["phone_number"],
                    visit["address_id"],
                    inv_id,
                    "Onbekend",
                ),
            )
            customer_id = cur.lastrowid
            cur.execute(
                "UPDATE visit SET customer_id = %s WHERE visit_id = %s",
                (customer_id, visit_id),
            )
            return {
                "klantnummer": customer_id,
                "eenmalige_korting_pct": 10,
                "bedrijfsnaam": visit["company_name"],
            }

    def register_follow_up(
        self,
        visit_id: int,
        follow_up_date: date | str,
        notes: str = "",
    ) -> dict | None:
        if isinstance(follow_up_date, str):
            follow_up_date = date.fromisoformat(follow_up_date)
        with db_cursor() as cur:
            cur.execute("SELECT visit_id FROM visit WHERE visit_id = %s", (visit_id,))
            if not cur.fetchone():
                return None
            cur.execute(
                """
                INSERT INTO visit_follow_up (visit_id, follow_up_date, notes)
                VALUES (%s, %s, %s)
                """,
                (visit_id, follow_up_date, (notes or "").strip()[:500] or None),
            )
            return {"follow_up_id": cur.lastrowid, "status": "follow-up geregistreerd"}

    def get_contact_history(self, limit: int = 20) -> list[dict]:
        """Bezoeken + follow-ups voor potentiële klanten (nog geen order)."""
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT v.visit_id AS bezoek_id, v.company_name AS bedrijfsnaam,
                       v.contact_person AS contactpersoon, v.visit_date AS bezoekdatum,
                       (SELECT COUNT(*) FROM visit_follow_up f WHERE f.visit_id = v.visit_id)
                           AS follow_up_count,
                       (SELECT MAX(f.follow_up_date) FROM visit_follow_up f WHERE f.visit_id = v.visit_id)
                           AS laatste_follow_up
                FROM visit v
                WHERE v.customer_id IS NULL
                  AND NOT EXISTS (
                      SELECT 1 FROM orders o
                      JOIN customer c ON c.customer_id = o.customer_id
                      WHERE c.company_name = v.company_name
                  )
                ORDER BY v.visit_date DESC, v.visit_id DESC
                LIMIT %s
                """,
                (limit,),
            )
            return sanitize_rows(cur.fetchall())

    def get_follow_ups_for_visit(self, visit_id: int) -> list[dict]:
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT follow_up_id, follow_up_date AS datum, notes AS notitie
                FROM visit_follow_up
                WHERE visit_id = %s
                ORDER BY follow_up_date DESC
                """,
                (visit_id,),
            )
            return sanitize_rows(cur.fetchall())
