"""Verkoop — klant zoeken en korting berekenen (timaflu_schema.sql)."""

from __future__ import annotations

from db.connection import db_cursor
from db.mappers import (
    customer_discount_pct,
    day_part_db,
    map_customer,
    map_product,
    order_status_nl,
    turnover_tier_label,
)
from db.serialize import sanitize_row, sanitize_rows
from services.discount import DiscountResult, calculate_order_discounts, discount_pct_from_turnover


class VerkoopService:
    def _load_addresses(self, cur, delivery_id: int, invoice_id: int) -> tuple[dict, dict]:
        cur.execute("SELECT * FROM address WHERE address_id = %s", (delivery_id,))
        delivery = cur.fetchone()
        cur.execute("SELECT * FROM address WHERE address_id = %s", (invoice_id,))
        invoice = cur.fetchone()
        return delivery, invoice

    def search_customers(self, name: str) -> list[dict]:
        pattern = f"%{name.strip()}%"
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT c.*, a.city AS aflever_plaats
                FROM customer c
                JOIN address a ON a.address_id = c.delivery_address_id
                WHERE c.company_name LIKE %s OR c.contact_person LIKE %s
                ORDER BY c.company_name
                """,
                (pattern, pattern),
            )
            rows = cur.fetchall()
            out = []
            for row in rows:
                turnover = self._year_purchase_turnover(cur, row["customer_id"])
                pct = customer_discount_pct(turnover)
                out.append(
                    sanitize_row(
                        {
                            "klantnummer": row["customer_id"],
                            "bedrijfsnaam": row["company_name"],
                            "telefoonnummer": row["phone_number"],
                            "aflever_plaats": row["aflever_plaats"],
                            "klantkorting": pct,
                            "eenmalige_korting": row["one_time_discount"],
                        }
                    )
                )
            return out

    def get_customer(self, customer_id: int) -> dict | None:
        with db_cursor() as cur:
            cur.execute("SELECT * FROM customer WHERE customer_id = %s", (customer_id,))
            row = cur.fetchone()
            if not row:
                return None
            delivery, invoice = self._load_addresses(
                cur, row["delivery_address_id"], row["invoice_address_id"]
            )
            turnover = self._year_purchase_turnover(cur, customer_id)
            mapped = map_customer(row, delivery, invoice)
            mapped["jaaromzet"] = turnover
            mapped["klantkorting"] = customer_discount_pct(turnover)
            mapped["klantkorting_tekst"] = (
                f"{mapped['klantkorting']:.0f}% ({turnover_tier_label(turnover)})"
            )
            mapped["eerste_bestelling"] = self._is_first_order(cur, customer_id)
            return mapped

    def get_medicijn(self, bestelcode: str) -> dict | None:
        with db_cursor() as cur:
            cur.execute(
                "SELECT * FROM product WHERE order_code = %s",
                (bestelcode.strip(),),
            )
            row = cur.fetchone()
            return map_product(row) if row else None

    def list_orders(self, limit: int = 20) -> list[dict]:
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT o.order_id AS ordernummer, o.status, o.urgent AS spoed,
                       o.delivery_date AS bezorgdatum, o.day_part AS dagdeel,
                       c.company_name AS bedrijfsnaam, c.customer_id AS klantnummer
                FROM orders o
                JOIN customer c ON c.customer_id = o.customer_id
                ORDER BY o.order_date DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = sanitize_rows(cur.fetchall())
            for r in rows:
                r["status"] = order_status_nl(r["status"])
            return rows

    def _is_first_order(self, cur, customer_id: int) -> bool:
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM orders WHERE customer_id = %s",
            (customer_id,),
        )
        return int(cur.fetchone()["cnt"]) == 0

    def _year_purchase_turnover(self, cur, customer_id: int) -> float:
        """Jaaromzet = som orderregels (aangekochte producten) in het lopende jaar."""
        cur.execute(
            """
            SELECT COALESCE(SUM(ol.quantity * ol.price), 0) AS omzet
            FROM orders o
            JOIN order_line ol ON ol.order_id = o.order_id
            WHERE o.customer_id = %s
              AND YEAR(o.order_date) = YEAR(CURDATE())
            """,
            (customer_id,),
        )
        return float(cur.fetchone()["omzet"])

    def bereken_korting_bestelling(
        self,
        klantnaam: str,
        klantadres: str,
        subtotaal: float,
    ) -> DiscountResult:
        """Productbeschrijving: invoer klantnaam, klantadres, optelsom → korting + totaal."""
        return self.calculate_discount(klantnaam, klantadres, subtotaal)

    def calculate_discount(
        self,
        klantnaam: str,
        klantadres: str,
        subtotal: float,
        klantnummer: int | None = None,
    ) -> DiscountResult:
        with db_cursor() as cur:
            if klantnummer is not None:
                cur.execute(
                    "SELECT * FROM customer WHERE customer_id = %s",
                    (klantnummer,),
                )
            else:
                cur.execute(
                    """
                    SELECT c.* FROM customer c
                    JOIN address a ON a.address_id = c.delivery_address_id
                    WHERE c.company_name = %s
                      AND CONCAT(a.street, ' ', a.house_number, ', ', a.postal_code, ' ', a.city) = %s
                    LIMIT 1
                    """,
                    (klantnaam.strip(), klantadres.strip()),
                )
            klant = cur.fetchone()
            if not klant:
                return calculate_order_discounts(
                    subtotal,
                    is_first_order=True,
                    has_one_time_discount=False,
                    customer_discount_pct=5.0,
                )

            kid = klant["customer_id"]
            turnover = self._year_purchase_turnover(cur, kid)
            first = self._is_first_order(cur, kid)
            result = calculate_order_discounts(
                subtotal,
                is_first_order=first,
                has_one_time_discount=bool(klant["one_time_discount"]),
                annual_turnover=turnover,
            )
            result.customer_turnover = turnover  # type: ignore[attr-defined]
            return result

    def discount_to_dict(self, result: DiscountResult) -> dict:
        total_discount = (
            result.order_discount
            + result.first_order_discount
            + result.customer_discount
        )
        turnover = getattr(result, "customer_turnover", None)
        return {
            "subtotaal": float(result.subtotal),
            "bestelkorting": float(result.order_discount),
            "bestellingskorting": float(result.order_discount),
            "bestelkorting_pct": float(result.order_discount_pct * 100),
            "eerste_bestelling_korting": float(result.first_order_discount),
            "eenmalige_korting": float(result.first_order_discount),
            "klantkorting": float(result.customer_discount),
            "klantenkorting": float(result.customer_discount),
            "klantkorting_pct": float(result.customer_discount_pct * 100),
            "totaal": float(result.total),
            "totaalbedrag": float(result.total),
            "totaal_korting": float(total_discount),
            "gegeven_korting": float(total_discount),
            "eerste_bestelling": result.is_first_order,
            "jaaromzet_afgelopen_jaar": turnover,
        }

    def create_order(
        self,
        klantnummer: int,
        lines: list[dict],
        bezorgdatum: str,
        dagdeel: str,
        spoed: bool,
    ) -> dict:
        with db_cursor() as cur:
            cur.execute(
                "SELECT * FROM customer WHERE customer_id = %s",
                (klantnummer,),
            )
            klant = cur.fetchone()
            if not klant:
                raise ValueError("Klant niet gevonden")

            subtotal = sum(float(l["aantal"]) * float(l["prijs"]) for l in lines)
            first = self._is_first_order(cur, klantnummer)
            turnover = self._year_purchase_turnover(cur, klantnummer)
            discounts = calculate_order_discounts(
                subtotal,
                is_first_order=first,
                has_one_time_discount=bool(klant["one_time_discount"]),
                annual_turnover=turnover,
            )

            has_leverbaar = any(l.get("status") == "leverbaar" for l in lines)
            has_backorder = any(l.get("status") == "backorder" for l in lines)
            if has_backorder and not has_leverbaar:
                status = "BACKORDER"
            else:
                status = "BEING_PICKED"

            cur.execute(
                """
                INSERT INTO orders (
                    customer_id, order_date, delivery_date, day_part, urgent, status
                ) VALUES (%s, CURDATE(), %s, %s, %s, %s)
                """,
                (
                    klantnummer,
                    bezorgdatum,
                    day_part_db(dagdeel),
                    int(spoed),
                    status,
                ),
            )
            order_id = cur.lastrowid

            for line in lines:
                cur.execute(
                    "SELECT product_id, stock FROM product WHERE order_code = %s",
                    (line["bestelcode"],),
                )
                product = cur.fetchone()
                if not product:
                    continue
                backorder = 1 if line.get("status") == "backorder" else 0
                cur.execute(
                    """
                    INSERT INTO order_line (order_id, product_id, quantity, price, backorder)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        order_id,
                        product["product_id"],
                        int(line["aantal"]),
                        float(line["prijs"]),
                        backorder,
                    ),
                )
                if not backorder:
                    cur.execute(
                        """
                        UPDATE product SET stock = GREATEST(0, stock - %s)
                        WHERE product_id = %s
                        """,
                        (int(line["aantal"]), product["product_id"]),
                    )

            return sanitize_row(
                {
                    "ordernummer": order_id,
                    "status": order_status_nl(status),
                    "totaalbedrag": float(discounts.total),
                    "backorder_only": bool(has_backorder and not has_leverbaar),
                }
            )
