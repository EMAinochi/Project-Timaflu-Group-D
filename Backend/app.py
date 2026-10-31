"""
Timaflu — Flask backend + server-rendered HTML (geen frontend JavaScript).

Start: python app.py
Open:  http://127.0.0.1:5000/
"""

from __future__ import annotations

import os
import sys
from datetime import date

from flask import Flask, jsonify, request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from routes.web import web
from services.acquisitie_service import AcquisitieService
from services.administratie_service import AdministratieService
from services.distributie_service import DistributieService
from services.inkoop_service import InkoopService
from services.orderpicking_service import OrderpickingService
from services.verkoop_service import VerkoopService

FRONTEND_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "Frontend Website")
)

app = Flask(__name__, template_folder="templates")
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "timaflu-dev-secret")
app.config["FRONTEND_DIR"] = FRONTEND_DIR
app.register_blueprint(web)

verkoop = VerkoopService()
inkoop = InkoopService()
administratie = AdministratieService()
distributie = DistributieService()
acquisitie = AcquisitieService()
orderpicking = OrderpickingService()


# --- JSON API (peer test / run_demo) ---
@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "service": "timaflu-backend"})


@app.get("/api/klanten")
def search_klanten():
    return jsonify(verkoop.search_customers(request.args.get("q", "")))


@app.get("/api/klanten/<int:klantnummer>")
def get_klant(klantnummer: int):
    klant = verkoop.get_customer(klantnummer)
    if not klant:
        return jsonify({"error": "Klant niet gevonden"}), 404
    return jsonify(klant)


@app.get("/api/medicijn/<bestelcode>")
def get_medicijn(bestelcode: str):
    medicijn = verkoop.get_medicijn(bestelcode)
    if not medicijn:
        return jsonify({"error": "Product niet gevonden"}), 404
    return jsonify(medicijn)


def _korting_response():
    if request.method == "GET":
        data = request.args
    else:
        data = request.get_json(force=True, silent=True) or {}
    kn = data.get("klantnummer")
    if kn is not None and kn != "":
        kn = int(kn)
    else:
        kn = None
    result = verkoop.calculate_discount(
        klantnaam=data.get("klantnaam", ""),
        klantadres=data.get("klantadres", ""),
        subtotal=float(data.get("subtotaal", 0) or 0),
        klantnummer=kn,
    )
    return jsonify(verkoop.discount_to_dict(result))


@app.get("/api/verkoop/korting")
@app.post("/api/verkoop/korting")
def bereken_korting():
    return _korting_response()


@app.get("/api/inkoop/minimum-voorraad")
def minimum_voorraad():
    return jsonify(inkoop.products_below_minimum())


@app.get("/api/inkoop/leveranciers")
def inkoop_leveranciers():
    product = request.args.get("product", "") or request.args.get("productnaam", "")
    if not product.strip():
        return jsonify({"error": "productnaam verplicht"}), 400
    rows = inkoop.leveranciers_voor_product(product)
    return jsonify({"productnaam": product.strip(), "leveranciers": rows})


@app.delete("/api/inkoop/product/leverancier")
def inkoop_verwijder_leverancier():
    product = request.args.get("product", "") or request.args.get("productnaam", "")
    fabrikant_id = request.args.get("fabrikant_id", type=int)
    if not product.strip() or not fabrikant_id:
        return jsonify({"error": "productnaam en fabrikant_id verplicht"}), 400
    ok = inkoop.remove_supplier_from_product(product, fabrikant_id)
    if not ok:
        return jsonify({"error": "Leverancier niet gevonden op dit product"}), 404
    return jsonify({"ok": True})


@app.post("/api/inkoop/product/leverancier/verwijderen")
def inkoop_verwijder_leverancier_post():
    data = request.get_json(force=True, silent=True) or request.form
    product = data.get("productnaam") or data.get("product", "")
    fabrikant_id = data.get("fabrikant_id")
    if fabrikant_id is not None:
        fabrikant_id = int(fabrikant_id)
    if not str(product).strip() or not fabrikant_id:
        return jsonify({"error": "productnaam en fabrikant_id verplicht"}), 400
    ok = inkoop.remove_supplier_from_product(str(product), fabrikant_id)
    if not ok:
        return jsonify({"error": "Leverancier niet gevonden op dit product"}), 404
    return jsonify({"ok": True})


@app.delete("/api/inkoop/product")
def inkoop_verwijder_product():
    product = request.args.get("product", "") or request.args.get("productnaam", "")
    if not product.strip():
        return jsonify({"error": "productnaam verplicht"}), 400
    result = inkoop.delete_product(product)
    status = 200 if result.get("ok") else 409 if "orderregels" in result.get("error", "") else 404
    return jsonify(result), status


@app.post("/api/inkoop/product/verwijderen")
def inkoop_verwijder_product_post():
    data = request.get_json(force=True, silent=True) or request.form
    product = data.get("productnaam") or data.get("product", "")
    if not str(product).strip():
        return jsonify({"error": "productnaam verplicht"}), 400
    result = inkoop.delete_product(str(product))
    status = 200 if result.get("ok") else 409 if "orderregels" in result.get("error", "") else 404
    return jsonify(result), status


@app.get("/api/distributie/rooster")
def rooster():
    datum = request.args.get("datum", "")
    if not datum:
        return jsonify({"error": "datum verplicht"}), 400
    return jsonify(distributie.get_schedule(datum))


@app.get("/api/orderpicking/wachtrij")
def orderpicking_wachtrij():
    return jsonify(orderpicking.open_orders())


@app.get("/api/orderpicking/order/<int:order_ref>")
def orderpicking_detail(order_ref: int):
    detail = orderpicking.get_order_detail(order_ref)
    if not detail:
        return jsonify({"error": "Order niet gevonden"}), 404
    return jsonify(detail)


@app.get("/api/acquisitie/overzicht")
def acquisitie_overzicht():
    return jsonify(acquisitie.get_acquisition_overview())


@app.post("/api/acquisitie/bezoek")
def acquisitie_bezoek_registreren():
    data = request.get_json(silent=True) or {}
    try:
        result = acquisitie.register_visit(
            bedrijfsnaam=str(data.get("bedrijfsnaam", "")).strip(),
            contactpersoon=str(data.get("contactpersoon", "")).strip(),
            telefoonnummer=str(data.get("telefoonnummer", "")).strip(),
            straat=str(data.get("straat", "")).strip(),
            postcode=str(data.get("postcode", "")).strip(),
            plaats=str(data.get("plaats", "")).strip(),
            bezoekdatum=data.get("bezoekdatum") or date.today().isoformat(),
        )
    except (ValueError, TypeError):
        return jsonify({"error": "Ongeldige invoer"}), 400
    if not result.get("bezoek_id"):
        return jsonify({"error": "Bezoek niet opgeslagen"}), 400
    return jsonify(result), 201


@app.get("/api/administratie/factuur/<int:klantnummer>")
def factuur_klant(klantnummer: int):
    text = administratie.factuur_voor_klant_niet_betaald(klantnummer)
    if text is None:
        return jsonify({"error": "Geen open factuur"}), 404
    return jsonify({"klantnummer": klantnummer, "factuur": text})


@app.get("/api/administratie/openstaand")
def administratie_openstaand():
    return jsonify(administratie.get_unpaid_invoices())


@app.post("/api/administratie/factuur-aanmaken/<int:klantnummer>")
def administratie_factuur_aanmaken_api(klantnummer: int):
    created = administratie.create_week_invoice(klantnummer)
    if not created:
        return jsonify({"error": "Geen afgeleverde orders zonder factuur"}), 404
    return jsonify(created), 201


@app.post("/api/orderpicking/order/<int:order_ref>/gang/<gang>/status")
def orderpicking_gang_api(order_ref: int, gang: str):
    data = request.get_json(silent=True) or {}
    status = data.get("status") or request.form.get("status", "VERZAMELD")
    if not orderpicking.set_gang_status(order_ref, gang, status):
        return jsonify({"error": "Status niet bijgewerkt"}), 400
    return jsonify({"ok": True})


@app.post("/api/orderpicking/order/<int:order_ref>/compleet")
def orderpicking_compleet_api(order_ref: int):
    if not orderpicking.mark_order_ready(order_ref):
        return jsonify({"error": "Order niet compleet"}), 409
    return jsonify({"ok": True, "status": "READY_FOR_DISTRIBUTION"})


@app.post("/api/acquisitie/follow-up/<int:bezoek_id>")
def acquisitie_follow_up_api(bezoek_id: int):
    data = request.get_json(silent=True) or {}
    result = acquisitie.register_follow_up(
        bezoek_id,
        data.get("follow_up_datum") or date.today().isoformat(),
        str(data.get("notitie", "")),
    )
    if not result:
        return jsonify({"error": "Bezoek niet gevonden"}), 404
    return jsonify(result), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
