"""Map timaflu_schema (English) rows to frontend/Dutch field names."""

from __future__ import annotations

from services.discount import discount_pct_from_turnover


def format_address(street: str, house_number: str, postal_code: str, city: str) -> str:
    return f"{street} {house_number}, {postal_code} {city}"


def customer_discount_pct(annual_turnover: float) -> float:
    return float(discount_pct_from_turnover(annual_turnover) * 100)


def turnover_tier_label(turnover: float) -> str:
    """Tekst zoals wireframe 1.2.2 (Tabel 1)."""
    if turnover >= 20000:
        return "jaaromzet € 20.000 of meer"
    if turnover >= 10000:
        return "jaaromzet € 10.000 tot € 20.000"
    return "jaaromzet onder € 10.000"


def map_customer(row: dict, delivery: dict, invoice_addr: dict) -> dict:
    turnover = float(row["annual_turnover"])
    pct = customer_discount_pct(turnover)
    return {
        "klantnummer": row["customer_id"],
        "bedrijfsnaam": row["company_name"],
        "contactpersoon": row["contact_person"],
        "telefoonnummer": row["phone_number"],
        "aflever_plaats": delivery["city"],
        "afleveradres": format_address(
            delivery["street"],
            delivery["house_number"],
            delivery["postal_code"],
            delivery["city"],
        ),
        "betaaladres": format_address(
            invoice_addr["street"],
            invoice_addr["house_number"],
            invoice_addr["postal_code"],
            invoice_addr["city"],
        ),
        "klantkorting": pct,
        "eenmalige_korting": row["one_time_discount"],
        "incassoblokkade": row["blocked"],
        "jaaromzet": turnover,
        "klantkorting_tekst": f"{pct:.0f}% (jaaromzet € {turnover:,.2f})".replace(",", "."),
    }


def map_product(row: dict) -> dict:
    return {
        "product_id": row["product_id"],
        "bestelcode": row["order_code"],
        "naam": row["name"],
        "voorraad": row["stock"],
        "minimum_voorraad": row["minimum_stock"],
        "magazijn_locatie": row.get("packaging_type", ""),
        "prijs": float(row["price_per_bulk_pack"]),
        "minimum_bestel": int(row["minimum_order_qty"]),
    }


def order_status_nl(status: str) -> str:
    return {
        "BEING_PICKED": "wordt verzameld",
        "BACKORDER": "backorder",
        "READY_FOR_DISTRIBUTION": "klaar voor distributie",
        "SHIPPED": "verstuurd",
        "DELIVERED": "afgeleverd",
        "NOT_DELIVERED": "niet afgeleverd",
    }.get(status, status)


def day_part_nl(day_part: str) -> str:
    return {"MORNING": "ochtend", "AFTERNOON": "middag"}.get(day_part, day_part)


def day_part_db(dagdeel: str) -> str:
    if dagdeel == "middag":
        return "AFTERNOON"
    return "MORNING"
