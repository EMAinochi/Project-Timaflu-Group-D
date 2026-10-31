"""Inkoop — timaflu_schema.sql (product, manufacturer, product_supplier, purchase_order)."""

from __future__ import annotations

from db.connection import db_cursor
from db.serialize import sanitize_row, sanitize_rows


class InkoopService:
    def _resolve_product(self, cur, product_name: str) -> dict | None:
        """Zoek product op exacte naam, bestelcode, of (deels) productnaam."""
        term = product_name.strip()
        if not term:
            return None
        cur.execute(
            """
            SELECT product_id, order_code, name, stock, minimum_stock
            FROM product
            WHERE name = %s OR order_code = %s
            LIMIT 1
            """,
            (term, term),
        )
        row = cur.fetchone()
        if row:
            return row
        cur.execute(
            """
            SELECT product_id, order_code, name, stock, minimum_stock
            FROM product
            WHERE name LIKE %s
            ORDER BY name
            LIMIT 1
            """,
            (f"%{term}%",),
        )
        return cur.fetchone()

    def products_below_minimum(self) -> list[dict]:
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT order_code AS bestelcode, name AS naam, stock AS voorraad,
                       minimum_stock AS minimum_voorraad, packaging_type AS magazijn_locatie
                FROM product
                WHERE stock < minimum_stock
                ORDER BY name
                """
            )
            return sanitize_rows(cur.fetchall())

    def leveranciers_voor_product(self, productnaam: str) -> list[dict]:
        """
        Productbeschrijving inkoop — invoer productnaam → leveranciers (goedkoopst eerst),
        met contactpersoon en telefoonnummer.
        """
        return self.get_suppliers_for_product(productnaam)

    def get_suppliers_for_product(self, product_name: str) -> list[dict]:
        with db_cursor() as cur:
            product = self._resolve_product(cur, product_name)
            if not product:
                return []
            cur.execute(
                """
                SELECT p.order_code AS bestelcode, p.name AS productnaam, p.stock AS voorraad,
                       m.manufacturer_id AS fabrikant_id, m.name AS leverancier,
                       m.contact_person AS contactpersoon, m.phone_number AS telefoonnummer,
                       a.street, a.house_number, a.postal_code, a.city AS plaats,
                       m.website, ps.purchase_price AS inkoopprijs
                FROM product p
                JOIN product_supplier ps ON ps.product_id = p.product_id
                JOIN manufacturer m ON m.manufacturer_id = ps.manufacturer_id
                JOIN address a ON a.address_id = m.address_id
                WHERE p.product_id = %s
                ORDER BY ps.purchase_price ASC, m.name ASC
                """,
                (product["product_id"],),
            )
            return sanitize_rows(cur.fetchall())

    def get_purchase_order(self, purchase_id: int) -> dict | None:
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT po.purchase_id AS inkooporder_id, po.quantity AS aantal, po.price AS prijs,
                       po.order_date AS orderdatum, p.name AS productnaam, p.order_code AS bestelcode,
                       m.name AS leverancier, m.manufacturer_id AS fabrikant_id
                FROM purchase_order po
                JOIN product p ON p.product_id = po.product_id
                JOIN manufacturer m ON m.manufacturer_id = po.manufacturer_id
                WHERE po.purchase_id = %s
                """,
                (purchase_id,),
            )
            return sanitize_row(cur.fetchone())

    def remove_supplier_from_product(
        self, product_name_or_code: str, manufacturer_id: int
    ) -> bool:
        """Verwijder koppeling leverancier ↔ product (productnaam of bestelcode)."""
        with db_cursor() as cur:
            product = self._resolve_product(cur, product_name_or_code)
            if not product:
                return False
            cur.execute(
                """
                DELETE FROM product_supplier
                WHERE product_id = %s AND manufacturer_id = %s
                """,
                (product["product_id"], manufacturer_id),
            )
            return cur.rowcount > 0

    def delete_product(self, product_name_or_code: str) -> dict:
        """
        Verwijder product uit assortiment.
        Mislukt als er nog verkooporderregels op het product staan.
        """
        with db_cursor() as cur:
            product = self._resolve_product(cur, product_name_or_code)
            if not product:
                return {"ok": False, "error": "Product niet gevonden"}
            pid = product["product_id"]
            cur.execute(
                "SELECT COUNT(*) AS cnt FROM order_line WHERE product_id = %s",
                (pid,),
            )
            if int(cur.fetchone()["cnt"]) > 0:
                return {
                    "ok": False,
                    "error": "Product kan niet worden verwijderd: er zijn nog orderregels",
                }
            cur.execute("DELETE FROM purchase_order WHERE product_id = %s", (pid,))
            cur.execute("DELETE FROM product WHERE product_id = %s", (pid,))
            if cur.rowcount:
                return {
                    "ok": True,
                    "bestelcode": product["order_code"],
                    "productnaam": product["name"],
                }
            return {"ok": False, "error": "Verwijderen mislukt"}

    def create_purchase_order(
        self, product_code: str, fabrikant_id: int, quantity: int
    ) -> dict | None:
        with db_cursor() as cur:
            cur.execute(
                "SELECT product_id FROM product WHERE order_code = %s",
                (product_code,),
            )
            product = cur.fetchone()
            if not product:
                return None
            cur.execute(
                """
                SELECT purchase_price FROM product_supplier
                WHERE product_id = %s AND manufacturer_id = %s
                """,
                (product["product_id"], fabrikant_id),
            )
            row = cur.fetchone()
            if not row:
                return None
            price = row["purchase_price"]
            cur.execute(
                """
                INSERT INTO purchase_order (order_date, product_id, manufacturer_id, quantity, price)
                VALUES (CURDATE(), %s, %s, %s, %s)
                """,
                (product["product_id"], fabrikant_id, quantity, price),
            )
            purchase_id = int(cur.lastrowid)
            cur.execute(
                "SELECT name, order_code FROM product WHERE product_id = %s",
                (product["product_id"],),
            )
            prod = cur.fetchone()
            cur.execute(
                "SELECT name FROM manufacturer WHERE manufacturer_id = %s",
                (fabrikant_id,),
            )
            fab = cur.fetchone()
            return sanitize_row(
                {
                    "inkooporder_id": purchase_id,
                    "bestelcode": prod["order_code"],
                    "productnaam": prod["name"],
                    "fabrikant_id": fabrikant_id,
                    "leverancier": fab["name"] if fab else "",
                    "aantal": quantity,
                    "prijs": float(price),
                }
            )
