"""
Live demo voor peer testing (Deel 9 — backend methods).

Gebruik: python run_demo.py
Vereist: MySQL met timaflu_schema.sql + timaflu_seed.sql geladen.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.acquisitie_service import AcquisitieService
from services.administratie_service import AdministratieService
from services.discount import calculate_order_discounts
from services.distributie_service import DistributieService
from services.inkoop_service import InkoopService
from services.verkoop_service import VerkoopService


def section(title: str) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def main() -> None:
    section("1. Klantkorting berekenen (verkoop)")
    print("Stappen: bestellingskorting → eerste bestelling 10% → klantenkorting (Tabel 1)")
    verkoop = VerkoopService()
    db_result = verkoop.bereken_korting_bestelling(
        "Apotheek De Linge",
        "Lindelaan 12, 5341 AB Oss",
        500,
    )
    out = verkoop.discount_to_dict(db_result)
    print(
        f"Invoer: klant + subtotaal €500 → totaal €{out['totaalbedrag']:.2f}, "
        f"gegeven korting €{out['gegeven_korting']:.2f} "
        f"(jaaromzet uit orders: €{out['jaaromzet_afgelopen_jaar']})"
    )
    print(out)

    section("2. Product niet op voorraad (inkoop)")
    inkoop = InkoopService()
    print("Invoer: productnaam → leveranciers (goedkoopst eerst, contact + telefoon)")
    for row in inkoop.leveranciers_voor_product("Ibuprofen 400 mg"):
        print(
            f"{row['leverancier']}: €{row['inkoopprijs']} — "
            f"{row['contactpersoon']} {row['telefoonnummer']}"
        )

    section("3. Klant niet betaald (administratie — klantnummer → factuur)")
    admin = AdministratieService()
    print(admin.generate_invoice_for_customer(4))

    section("4. Klant niet aanwezig (distributie)")
    dist = DistributieService()
    for slot in dist.get_schedule("2026-10-31"):
        print(f"{slot['levertijd']} — {slot['bedrijfsnaam']} — {slot['adres']}")

    section("5. Acquisitie — nog geen bestelling")
    acq = AcquisitieService()
    for visit in acq.get_acquisition_overview():
        print(f"{visit['bedrijfsnaam']}: {visit['contactpersoon']} ({visit['telefoonnummer']})")


if __name__ == "__main__":
    main()
