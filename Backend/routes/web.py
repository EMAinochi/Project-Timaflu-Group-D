"""Server-rendered HTML routes (no frontend JavaScript)."""

from __future__ import annotations

from datetime import date

from flask import Blueprint, redirect, render_template, request, session, url_for

from services.acquisitie_service import AcquisitieService
from services.administratie_service import AdministratieService
from services.distributie_service import DistributieService
from services.inkoop_service import InkoopService
from services.orderpicking_service import (
    OrderpickingService,
    display_order_number,
    resolve_order_id,
)
from services.verkoop_service import VerkoopService
from web_helpers import distributie_dagregel, distributie_datum, euro, pct, today_iso

web = Blueprint("web", __name__)

verkoop_svc = VerkoopService()
inkoop_svc = InkoopService()
orderpicking_svc = OrderpickingService()
distributie_svc = DistributieService()
acquisitie_svc = AcquisitieService()
administratie_svc = AdministratieService()


def _cart_lines() -> list[dict]:
    return session.get("order_lines", [])


def _cart_subtotal(lines: list[dict]) -> float:
    return sum(float(l["aantal"]) * float(l["prijs"]) for l in lines)


def _clear_cart() -> None:
    session.pop("order_lines", None)
    session.pop("klantnummer", None)


@web.route("/")
@web.route("/index.html")
def verkoop_page():
    q = request.args.get("q", "Apotheek").strip()
    klantnummer = request.args.get("klant", type=int) or session.get("klantnummer")
    if klantnummer:
        session["klantnummer"] = klantnummer

    klanten = verkoop_svc.search_customers(q) if q else []
    klant = verkoop_svc.get_customer(klantnummer) if klantnummer else None

    product = None
    bestelcode = request.args.get("bestelcode", "").strip()
    aantal = request.args.get("aantal", "4")
    if (
        request.method == "GET"
        and klantnummer
        and "bestelcode" in request.args
        and not request.args.get("_at")
    ):
        return redirect(
            url_for(
                "web.verkoop_page",
                klant=klantnummer,
                q=q,
                bestelcode=bestelcode,
                aantal=aantal,
                _at="bestelling",
            )
            + "#bestelling"
        )
    if bestelcode:
        product = verkoop_svc.get_medicijn(bestelcode)

    lines = _cart_lines()
    subtotal = _cart_subtotal(lines)
    totals = None
    if klant and lines:
        result = verkoop_svc.calculate_discount(
            klant["bedrijfsnaam"],
            klant["afleveradres"],
            subtotal,
            klantnummer=klant["klantnummer"],
        )
        totals = verkoop_svc.discount_to_dict(result)

    saved = session.pop("saved_order", None)
    nieuw = request.args.get("nieuw") == "1"

    return render_template(
        "index.html",
        active="verkoop",
        q=q,
        nieuw=nieuw,
        klanten=klanten,
        klant=klant,
        product=product,
        bestelcode=bestelcode or "MF-3012",
        aantal=aantal,
        lines=lines,
        totals=totals,
        subtotal=subtotal,
        saved=saved,
        euro=euro,
        pct=pct,
    )


@web.post("/index.html/regel")
def verkoop_add_line():
    klantnummer = request.form.get("klantnummer", type=int)
    if klantnummer:
        session["klantnummer"] = klantnummer
    bestelcode = request.form.get("bestelcode", "").strip()
    aantal = request.form.get("aantal", type=int) or 1
    status = request.form.get("status", "leverbaar")
    medicijn = verkoop_svc.get_medicijn(bestelcode)
    if medicijn:
        lines = _cart_lines()
        lines.append(
            {
                "bestelcode": medicijn["bestelcode"],
                "naam": medicijn["naam"],
                "aantal": aantal,
                "prijs": medicijn["prijs"],
                "status": status,
            }
        )
        session["order_lines"] = lines
    q = request.form.get("q", "Apotheek")
    url = url_for(
        "web.verkoop_page",
        klant=klantnummer,
        q=q,
        bestelcode=bestelcode,
        aantal=aantal,
    )
    return redirect(f"{url}#bestelling")


@web.post("/index.html/opslaan")
def verkoop_save_order():
    klantnummer = request.form.get("klantnummer", type=int)
    lines = _cart_lines()
    if not klantnummer or not lines:
        return redirect(url_for("web.verkoop_page"))
    bezorgdatum = request.form.get("bezorgdatum") or today_iso()
    dagdeel = request.form.get("dagdeel", "ochtend")
    spoed = request.form.get("spoed") == "1"
    saved = verkoop_svc.create_order(klantnummer, lines, bezorgdatum, dagdeel, spoed)
    session["saved_order"] = saved
    _clear_cart()
    q = request.form.get("q", "Apotheek")
    return redirect(f"{url_for('web.verkoop_page', klant=klantnummer, q=q)}#afronden")


@web.post("/index.html/reset")
def verkoop_reset_cart():
    _clear_cart()
    return redirect(url_for("web.verkoop_page", q=request.form.get("q", "Apotheek")))


@web.post("/index.html/annuleren")
def verkoop_annuleren():
    session.pop("klantnummer", None)
    _clear_cart()
    return redirect(url_for("web.verkoop_page", q=request.form.get("q", "Apotheek")))


@web.post("/index.html/afzien")
def verkoop_afzien():
    _clear_cart()
    klantnummer = request.form.get("klantnummer", type=int)
    q = request.form.get("q", "Apotheek")
    return redirect(f"{url_for('web.verkoop_page', klant=klantnummer, q=q)}#bestelling")


@web.route("/inkoop-2-2-1.html")
def inkoop_minimum():
    products = inkoop_svc.products_below_minimum()
    msg = request.args.get("msg", "")
    return render_template(
        "inkoop-2-2-1.html",
        active="inkoop-min",
        products=products,
        msg=msg,
    )


@web.route("/inkoop-2-2-2.html")
def inkoop_suppliers():
    product = request.args.get("product", "")
    code = request.args.get("code", "")
    msg = request.args.get("msg", "")
    err = request.args.get("err", "")
    suppliers = inkoop_svc.get_suppliers_for_product(product or code)
    title_product = (
        suppliers[0]["productnaam"]
        if suppliers
        else (product or code or "Product")
    )
    bestelcode = suppliers[0]["bestelcode"] if suppliers else code
    return render_template(
        "inkoop-2-2-2.html",
        active="inkoop-sup",
        suppliers=suppliers,
        title_product=title_product,
        product_query=product or code,
        bestelcode=bestelcode,
        msg=msg,
        err=err,
        euro=euro,
    )


@web.route("/inkoop-leveranciers.html")
def inkoop_leveranciers_page():
    """Alias — productnaam → leveranciers (productbeschrijving inkoop)."""
    return inkoop_suppliers()


@web.post("/inkoop-2-2-2.html/zoek")
def inkoop_search_product():
    productnaam = request.form.get("productnaam", "").strip()
    return redirect(
        url_for("web.inkoop_suppliers", product=productnaam)
    )


@web.post("/inkoop-2-2-2.html/remove-supplier")
def inkoop_remove_supplier():
    product = request.form.get("productnaam", "") or request.form.get("product", "")
    fabrikant_id = request.form.get("fabrikant_id", type=int) or 0
    ok = inkoop_svc.remove_supplier_from_product(product, fabrikant_id)
    if ok:
        return redirect(
            url_for("web.inkoop_suppliers", product=product, msg="Leverancier verwijderd")
        )
    return redirect(
        url_for("web.inkoop_suppliers", product=product, err="Leverancier niet gevonden")
    )


@web.post("/inkoop-2-2-2.html/delete-product")
def inkoop_delete_product():
    product = request.form.get("productnaam", "") or request.form.get("product", "")
    result = inkoop_svc.delete_product(product)
    if result.get("ok"):
        return redirect(url_for("web.inkoop_minimum", msg="Product verwijderd"))
    return redirect(
        url_for(
            "web.inkoop_suppliers",
            product=product,
            err=result.get("error", "Verwijderen mislukt"),
        )
    )


@web.post("/inkoop-2-2-2.html/order")
def inkoop_place_order():
    created = inkoop_svc.create_purchase_order(
        request.form.get("bestelcode", ""),
        request.form.get("fabrikant_id", type=int) or 0,
        request.form.get("aantal", type=int) or 50,
    )
    if not created or not created.get("inkooporder_id"):
        return redirect(
            url_for(
                "web.inkoop_suppliers",
                product=request.form.get("productnaam", ""),
                err="Inkooporder kon niet worden aangemaakt.",
            )
        )
    return redirect(url_for("web.inkoop_confirm", id=created["inkooporder_id"]))


@web.route("/inkoop-2-2-3.html")
def inkoop_confirm():
    order_id = request.args.get("id", type=int)
    order = inkoop_svc.get_purchase_order(order_id) if order_id else None
    return render_template(
        "inkoop-2-2-3.html",
        active="inkoop-sup",
        order=order,
        euro=euro,
    )


@web.route("/administratie.html")
def administratie_page():
    klantnummer = request.args.get("klantnummer", type=int)
    factuur = None
    error = None
    if klantnummer is not None:
        factuur = administratie_svc.generate_invoice_for_customer(klantnummer)
        if not factuur:
            error = "Geen open (onbetaalde) factuur voor dit klantnummer."
    msg = request.args.get("msg")
    err_arg = request.args.get("error")
    if err_arg == "geen-orders":
        error = error or "Geen afgeleverde orders zonder factuur voor deze klant."
    return render_template(
        "administratie.html",
        active="administratie",
        klantnummer=klantnummer,
        factuur=factuur,
        error=error,
        msg=msg,
        week_label=administratie_svc.week_label(),
        pending=administratie_svc.get_delivered_without_invoice(),
        unpaid=administratie_svc.get_unpaid_invoice_overview(),
        euro=euro,
        pct=pct,
    )


@web.post("/administratie.html")
def administratie_post():
    klantnummer = request.form.get("klantnummer", type=int)
    return redirect(url_for("web.administratie_page", klantnummer=klantnummer))


@web.post("/administratie.html/<int:invoice_id>/herinnering")
def administratie_herinnering(invoice_id: int):
    administratie_svc.send_reminder(invoice_id)
    kn = request.form.get("klantnummer", type=int)
    return redirect(url_for("web.administratie_page", klantnummer=kn) if kn else url_for("web.administratie_page"))


@web.post("/administratie.html/<int:invoice_id>/betaald")
def administratie_betaald(invoice_id: int):
    administratie_svc.register_payment(invoice_id)
    return redirect(url_for("web.administratie_page"))


@web.post("/administratie.html/<int:klantnummer>/factuur-aanmaken")
def administratie_factuur_aanmaken(klantnummer: int):
    created = administratie_svc.create_week_invoice(klantnummer)
    if created:
        return redirect(
            url_for(
                "web.administratie_page",
                klantnummer=klantnummer,
                msg=f"factuur-{created['factuurnummer']}",
            )
        )
    return redirect(url_for("web.administratie_page", error="geen-orders"))


@web.route("/orderpicking.html")
def orderpicking_page():
    orders = orderpicking_svc.open_orders()
    raw = request.args.get("order", type=int)
    if raw is not None:
        order_id = resolve_order_id(raw)
    elif orders:
        order_id = int(orders[0]["order_id"])
    else:
        order_id = None
    detail = orderpicking_svc.get_order_detail(order_id) if order_id else None
    selected = display_order_number(order_id) if order_id else None
    return render_template(
        "orderpicking.html",
        active="orderpicking",
        orders=orders,
        detail=detail,
        selected_order=selected,
        msg=request.args.get("msg"),
    )


@web.post("/orderpicking.html/<int:order_ref>/gang/<gang>/status")
def orderpicking_gang_status(order_ref: int, gang: str):
    status = request.form.get("status", "VERZAMELD")
    orderpicking_svc.set_gang_status(order_ref, gang, status)
    num = display_order_number(resolve_order_id(order_ref))
    return redirect(url_for("web.orderpicking_page", order=num, msg="gang"))


@web.post("/orderpicking.html/<int:order_ref>/compleet")
def orderpicking_compleet(order_ref: int):
    ok = orderpicking_svc.mark_order_ready(order_ref)
    num = display_order_number(resolve_order_id(order_ref))
    if ok:
        return redirect(url_for("web.orderpicking_page", msg="compleet"))
    return redirect(url_for("web.orderpicking_page", order=num, msg="compleet-mislukt"))


@web.route("/distributie.html")
def distributie_page():
    datum = request.args.get("datum") or distributie_datum()
    stops = distributie_svc.get_schedule(datum)
    if not stops and datum != "2026-10-31":
        datum = "2026-10-31"
        stops = distributie_svc.get_schedule(datum)
    stop_id = request.args.get("stop", type=int)
    active_stop = None
    if stops:
        if stop_id:
            active_stop = next((s for s in stops if s["levering_id"] == stop_id), stops[0])
        else:
            active_stop = stops[0]
    delivered = sum(1 for s in stops if s.get("afgeleverd"))
    total = len(stops)
    progress_pct = int(round(100 * delivered / total)) if total else 0
    open_stops = [s for s in stops if not s.get("afgeleverd") and s.get("order_status") != "NOT_DELIVERED"]
    next_stop = open_stops[0] if open_stops else None
    spoed_open = sum(
        1 for s in open_stops if s.get("spoed")
    )
    koerier_naam = (stops[0].get("koerier") or "Koerier").split()[0] if stops else "Koerier"
    return render_template(
        "distributie.html",
        active="distributie",
        datum=datum,
        dagregel=distributie_dagregel(datum),
        stops=stops,
        active_stop=active_stop,
        delivered=delivered,
        total=total,
        progress_pct=progress_pct,
        next_stop=next_stop,
        spoed_open=spoed_open,
        koerier_naam=koerier_naam,
        euro=euro,
    )


def _dist_redirect():
    datum = request.form.get("datum", today_iso())
    stop = request.form.get("stop", type=int)
    if stop:
        return redirect(url_for("web.distributie_page", datum=datum, stop=stop))
    return redirect(url_for("web.distributie_page", datum=datum))


@web.post("/distributie.html/<int:levering_id>/afgeleverd")
def distributie_delivered(levering_id: int):
    distributie_svc.mark_delivery_attempt(levering_id, True)
    return _dist_redirect()


@web.post("/distributie.html/<int:levering_id>/niet-aanwezig")
def distributie_absent(levering_id: int):
    distributie_svc.mark_customer_absent(levering_id)
    return _dist_redirect()


@web.post("/distributie.html/<int:levering_id>/niet-afgeleverd")
def distributie_niet_afgeleverd(levering_id: int):
    """Tweede bezoek: klant nog steeds niet bereikbaar."""
    distributie_svc.mark_delivery_attempt(levering_id, False)
    return _dist_redirect()


@web.route("/acquisition-6-22.html")
def acquisition_page():
    visits = acquisitie_svc.get_acquisition_overview()
    history = acquisitie_svc.get_contact_history()
    return render_template(
        "acquisition-6-22.html",
        active="acquisitie",
        visits=visits,
        history=history,
        msg=request.args.get("msg"),
        today=today_iso(),
    )


@web.route("/acquisition-6-21.html")
@web.route("/acquisition-6-23.html")
def acquisition_legacy_redirect():
    return redirect(url_for("web.acquisition_page"))


@web.post("/acquisition-6-22.html/bezoek")
def acquisition_add_visit():
    acquisitie_svc.register_visit(
        bedrijfsnaam=request.form.get("bedrijfsnaam", "").strip(),
        contactpersoon=request.form.get("contactpersoon", "").strip(),
        telefoonnummer=request.form.get("telefoonnummer", "").strip(),
        straat=request.form.get("straat", "").strip(),
        postcode=request.form.get("postcode", "").strip(),
        plaats=request.form.get("plaats", "").strip(),
        bezoekdatum=request.form.get("bezoekdatum") or today_iso(),
    )
    return redirect(url_for("web.acquisition_page", msg="bezoek"))


@web.post("/acquisition-6-22.html/<int:bezoek_id>/follow-up")
def acquisition_follow_up(bezoek_id: int):
    acquisitie_svc.register_follow_up(
        bezoek_id,
        request.form.get("follow_up_datum") or today_iso(),
        request.form.get("notitie", ""),
    )
    return redirect(url_for("web.acquisition_page", msg="follow-up"))


@web.post("/acquisition-6-22.html/<int:bezoek_id>/klant")
def acquisition_create_customer(bezoek_id: int):
    result = acquisitie_svc.create_customer_with_incentive(bezoek_id)
    if result:
        return redirect(
            url_for(
                "web.acquisition_page",
                msg=f"klant-{result['klantnummer']}",
            )
        )
    return redirect(url_for("web.acquisition_page", msg="klant-mislukt"))


@web.route("/styles.css")
def styles_css():
    from flask import current_app, send_from_directory

    return send_from_directory(current_app.config["FRONTEND_DIR"], "styles.css")
