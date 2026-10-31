"""Administratie — invoice + order_line (timaflu_schema.sql)."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from db.connection import db_cursor
from db.mappers import customer_discount_pct, format_address
from db.serialize import sanitize_row, sanitize_rows
from services.discount import calculate_order_discounts, discount_pct_from_turnover

_MONTHS_NL = (
    "januari",
    "februari",
    "maart",
    "april",
    "mei",
    "juni",
    "juli",
    "augustus",
    "september",
    "oktober",
    "november",
    "december",
)


class AdministratieService:
    TIMAFLU_NAME = "Timaflu"
    TIMAFLU_ADDRESS = "Magazijnweg 1, 5345 AB Oss"
    LINE_WIDTH = 66

    def _year_purchase_turnover(self, cur, customer_id: int) -> float:
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

    def week_label(self, ref: date | None = None) -> str:
        ref = ref or date.today()
        week = ref.isocalendar().week
        start = ref - timedelta(days=ref.weekday())
        end = start + timedelta(days=6)
        month = _MONTHS_NL[start.month - 1]
        if start.month == end.month:
            return (
                f"Wekelijkse administratie · Week {week} "
                f"({start.day} t/m {end.day} {month} {start.year})"
            )
        end_month = _MONTHS_NL[end.month - 1]
        return (
            f"Wekelijkse administratie · Week {week} "
            f"({start.day} {month} t/m {end.day} {end_month} {end.year})"
        )

    def format_factuurnummer(self, invoice_id: int, invoice_date: date) -> str:
        return f"F-{invoice_date.year}-{invoice_id:04d}"

    def _order_lines_subtotal(self, cur, order_ids: list[int]) -> Decimal:
        if not order_ids:
            return Decimal("0")
        placeholders = ",".join(["%s"] * len(order_ids))
        cur.execute(
            f"""
            SELECT COALESCE(SUM(ol.quantity * ol.price), 0) AS sub
            FROM order_line ol
            WHERE ol.order_id IN ({placeholders})
            """,
            tuple(order_ids),
        )
        return Decimal(str(cur.fetchone()["sub"]))

    def _bedrag_incl_btw_kortingen(
        self,
        cur,
        customer_id: int,
        one_time_discount: bool,
        subtotal: Decimal,
    ) -> tuple[float, float]:
        turnover = self._year_purchase_turnover(cur, customer_id)
        pct = float(customer_discount_pct(turnover))
        discounts = calculate_order_discounts(
            subtotal,
            is_first_order=False,
            has_one_time_discount=bool(one_time_discount),
            customer_discount_pct=pct,
        )
        after = (
            subtotal
            - discounts.order_discount
            - discounts.first_order_discount
            - discounts.customer_discount
        )
        btw = (after * Decimal("0.09")).quantize(Decimal("0.01"))
        total = float((after + btw).quantize(Decimal("0.01")))
        return total, pct

    def get_delivered_without_invoice(self) -> list[dict]:
        """Wireframe 5.2 — afgeleverde orders zonder factuur (per klant)."""
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT c.customer_id AS klantnummer, c.company_name AS bedrijfsnaam,
                       a.city AS plaats, c.one_time_discount, c.annual_turnover AS jaaromzet_vast,
                       GROUP_CONCAT(o.order_id) AS order_ids,
                       COUNT(DISTINCT o.order_id) AS orders,
                       COALESCE(SUM(ol.quantity), 0) AS producten
                FROM orders o
                JOIN customer c ON c.customer_id = o.customer_id
                JOIN address a ON a.address_id = c.delivery_address_id
                JOIN order_line ol ON ol.order_id = o.order_id
                WHERE o.status = 'DELIVERED' AND o.invoice_id IS NULL
                GROUP BY c.customer_id, c.company_name, a.city, c.one_time_discount
                ORDER BY c.company_name
                """
            )
            rows = cur.fetchall()
            out = []
            for row in rows:
                ids = [int(x) for x in str(row["order_ids"]).split(",") if x]
                sub = self._order_lines_subtotal(cur, ids)
                bedrag, korting = self._bedrag_incl_btw_kortingen(
                    cur,
                    row["klantnummer"],
                    row["one_time_discount"],
                    sub,
                )
                jaar_omzet = self._year_purchase_turnover(cur, row["klantnummer"])
                out.append(
                    sanitize_row(
                        {
                            "klantnummer": row["klantnummer"],
                            "bedrijfsnaam": row["bedrijfsnaam"],
                            "plaats": row["plaats"],
                            "orders": int(row["orders"]),
                            "producten": int(row["producten"]),
                            "korting_pct": korting,
                            "bedrag": bedrag,
                            "jaaromzet": jaar_omzet,
                        }
                    )
                )
            return out

    def create_week_invoice(self, customer_id: int) -> dict | None:
        """Weekfactuur: koppel alle afgeleverde orders zonder factuur aan nieuwe invoice."""
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT o.order_id
                FROM orders o
                WHERE o.customer_id = %s
                  AND o.status = 'DELIVERED'
                  AND o.invoice_id IS NULL
                """,
                (customer_id,),
            )
            order_ids = [r["order_id"] for r in cur.fetchall()]
            if not order_ids:
                return None

            inv_date = date.today()
            cur.execute(
                """
                INSERT INTO invoice (customer_id, invoice_date, paid, reminder_count)
                VALUES (%s, %s, 0, 0)
                """,
                (customer_id, inv_date),
            )
            invoice_id = int(cur.lastrowid)
            placeholders = ",".join(["%s"] * len(order_ids))
            cur.execute(
                f"""
                UPDATE orders SET invoice_id = %s
                WHERE order_id IN ({placeholders})
                """,
                (invoice_id, *order_ids),
            )
            return {
                "invoice_id": invoice_id,
                "factuurnummer": self.format_factuurnummer(invoice_id, inv_date),
                "klantnummer": customer_id,
                "orders": len(order_ids),
            }

    def get_unpaid_invoices(self) -> list[dict]:
        return self.get_unpaid_invoice_overview()

    def get_unpaid_invoice_overview(self) -> list[dict]:
        """Wireframe 5.2 — onbetaalde facturen met bedrag en herinneringsstatus."""
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT i.invoice_id, i.invoice_date, i.reminder_count, i.payment_plan,
                       i.collection_agency,
                       c.customer_id AS klantnummer, c.company_name AS bedrijfsnaam,
                       a.city AS plaats, c.one_time_discount
                FROM invoice i
                JOIN customer c ON c.customer_id = i.customer_id
                JOIN address a ON a.address_id = c.delivery_address_id
                WHERE i.paid = 0
                ORDER BY i.invoice_date
                """
            )
            rows = cur.fetchall()
            out = []
            today = date.today()
            for row in rows:
                cur.execute(
                    "SELECT order_id FROM orders WHERE invoice_id = %s",
                    (row["invoice_id"],),
                )
                order_ids = [r["order_id"] for r in cur.fetchall()]
                sub = self._order_lines_subtotal(cur, order_ids)
                bedrag, _ = self._bedrag_incl_btw_kortingen(
                    cur,
                    row["klantnummer"],
                    row["one_time_discount"],
                    sub,
                )
                inv_date = row["invoice_date"]
                if isinstance(inv_date, date):
                    days = (today - inv_date).days
                else:
                    days = 0
                weeks = max(1, (days + 6) // 7)
                status = self._reminder_status(
                    weeks,
                    int(row["reminder_count"]),
                    bool(row["payment_plan"]),
                    bool(row["collection_agency"]),
                )
                out.append(
                    sanitize_row(
                        {
                            "invoice_id": row["invoice_id"],
                            "factuurnummer": self.format_factuurnummer(
                                row["invoice_id"], inv_date
                            ),
                            "factuurdatum": inv_date,
                            "klantnummer": row["klantnummer"],
                            "bedrijfsnaam": row["bedrijfsnaam"],
                            "plaats": row["plaats"],
                            "bedrag": bedrag,
                            "weken_open": weeks,
                            "herinneringen": int(row["reminder_count"]),
                            "status_label": status["label"],
                            "status_muted": status["muted"],
                            "actie_label": status["actie"],
                            "actie_disabled": status["actie_disabled"],
                        }
                    )
                )
            return out

    def _reminder_status(
        self,
        weeks_open: int,
        reminder_count: int,
        payment_plan: bool,
        collection_agency: bool,
    ) -> dict:
        if collection_agency:
            return {
                "label": "Incasso",
                "muted": True,
                "actie": "Incassobureau",
                "actie_disabled": True,
            }
        if payment_plan:
            return {
                "label": "Regeling",
                "muted": True,
                "actie": "Regeling geaccepteerd",
                "actie_disabled": True,
            }
        if weeks_open >= 5:
            return {
                "label": f"{weeks_open} weken",
                "muted": True,
                "actie": "Regeling voorstellen",
                "actie_disabled": False,
            }
        if weeks_open >= 3:
            return {
                "label": "≥ 3 weken",
                "muted": True,
                "actie": "Regeling voorstellen",
                "actie_disabled": False,
            }
        if reminder_count >= 1 or weeks_open >= 2:
            return {
                "label": "2e herinnering",
                "muted": False,
                "actie": "2e herinnering",
                "actie_disabled": False,
            }
        return {
            "label": "1e herinnering",
            "muted": False,
            "actie": "1e herinnering",
            "actie_disabled": False,
        }

    def send_reminder(self, invoice_id: int) -> bool:
        with db_cursor() as cur:
            cur.execute(
                """
                UPDATE invoice
                SET reminder_count = LEAST(reminder_count + 1, 3)
                WHERE invoice_id = %s AND paid = 0
                """,
                (invoice_id,),
            )
            return cur.rowcount > 0

    def register_payment(self, invoice_id: int) -> bool:
        with db_cursor() as cur:
            cur.execute(
                "UPDATE invoice SET paid = 1 WHERE invoice_id = %s AND paid = 0",
                (invoice_id,),
            )
            return cur.rowcount > 0

    def factuur_voor_klant_niet_betaald(self, klantnummer: int) -> str | None:
        """Productbeschrijving administratie: invoer klantnummer → factuurtekst."""
        return self.generate_invoice_for_customer(klantnummer)

    def generate_invoice_for_customer(self, customer_id: int) -> str | None:
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT c.*, a.street, a.house_number, a.postal_code, a.city
                FROM customer c
                JOIN address a ON a.address_id = c.invoice_address_id
                WHERE c.customer_id = %s
                """,
                (customer_id,),
            )
            klant = cur.fetchone()
            if not klant:
                return None

            cur.execute(
                """
                SELECT invoice_id, invoice_date
                FROM invoice
                WHERE customer_id = %s AND paid = 0
                ORDER BY invoice_date DESC
                LIMIT 1
                """,
                (customer_id,),
            )
            factuur = cur.fetchone()
            if not factuur:
                return None

            cur.execute(
                """
                SELECT ol.quantity AS aantal, ol.price AS prijs,
                       p.order_code AS bestelcode, p.name AS naam
                FROM orders o
                JOIN order_line ol ON ol.order_id = o.order_id
                JOIN product p ON p.product_id = ol.product_id
                WHERE o.invoice_id = %s
                """,
                (factuur["invoice_id"],),
            )
            lines = cur.fetchall()
            if not lines:
                cur.execute(
                    """
                    SELECT ol.quantity AS aantal, ol.price AS prijs,
                           p.order_code AS bestelcode, p.name AS naam
                    FROM orders o
                    JOIN order_line ol ON ol.order_id = o.order_id
                    JOIN product p ON p.product_id = ol.product_id
                    WHERE o.customer_id = %s
                    ORDER BY o.order_id DESC
                    LIMIT 10
                    """,
                    (customer_id,),
                )
                lines = cur.fetchall()

            subtotal = sum(
                Decimal(str(r["aantal"])) * Decimal(str(r["prijs"])) for r in lines
            )
            klant_adres = format_address(
                klant["street"],
                klant["house_number"],
                klant["postal_code"],
                klant["city"],
            )
            klant_map = {
                "bedrijfsnaam": klant["company_name"],
                "eenmalige_korting": klant["one_time_discount"],
            }
            turnover = self._year_purchase_turnover(cur, customer_id)
            pct = float(discount_pct_from_turnover(Decimal(str(turnover))) * 100)

            return self._format_invoice(
                factuur["invoice_date"],
                factuur["invoice_id"],
                klant_map,
                klant_adres,
                lines,
                subtotal,
                pct,
            )

    def _format_invoice(
        self,
        invoice_date: date,
        invoice_number: int,
        klant: dict,
        klant_adres: str,
        lines: list[dict],
        subtotal: Decimal,
        customer_discount_pct: float,
    ) -> str:
        discounts = calculate_order_discounts(
            subtotal,
            is_first_order=False,
            has_one_time_discount=bool(klant["eenmalige_korting"]),
            customer_discount_pct=customer_discount_pct,
        )
        excl = subtotal
        btw = (excl * Decimal("0.09")).quantize(Decimal("0.01"))
        incl_btw = excl + btw
        after_order = excl - discounts.order_discount
        after_first = after_order - discounts.first_order_discount
        after_customer = after_first - discounts.customer_discount

        w = self.LINE_WIDTH
        nr = self.format_factuurnummer(invoice_number, invoice_date)
        header = (
            f"{invoice_date.strftime('%d-%m-%Y'):<40}{nr:>{w - 40}}\n"
            f"{'-' * w}\n"
            f"{self.TIMAFLU_NAME:<40}{klant['bedrijfsnaam']:>{w - 40}}\n"
            f"{self.TIMAFLU_ADDRESS:<40}{klant_adres:>{w - 40}}\n"
            f"{'-' * w}\n"
            f"{'Aantal':<16}{'prijs per eenheid':<24}{'regel totaal':>26}\n"
        )
        body_lines = []
        for row in lines:
            line_total = Decimal(str(row["aantal"])) * Decimal(str(row["prijs"]))
            body_lines.append(
                f"{row['aantal']:<16}{float(row['prijs']):>8.2f}{float(line_total):>34.2f}"
            )
        footer = (
            f"\n{'Totaal excl btw':>40} {float(excl):>16.2f}\n"
            f"{'9% btw':>40} {float(btw):>16.2f}\n"
            f"{'Totaal incl btw':>40} {float(incl_btw):>16.2f}\n"
            f"{'Bestellingskorting':>40} {float(discounts.order_discount):>16.2f}\n"
            f"{'Totaal incl bestellingskorting':>40} {float(after_order):>16.2f}\n"
            f"{'Eenmalige korting':>40} {float(discounts.first_order_discount):>16.2f}\n"
            f"{'Totaal incl eenmalige korting':>40} {float(after_first):>16.2f}\n"
            f"{'Klantenkorting':>40} {float(discounts.customer_discount):>16.2f}\n"
            f"{'Totaal incl klantenkorting':>40} {float(after_customer):>16.2f}\n"
        )
        return header + "\n".join(body_lines) + footer
