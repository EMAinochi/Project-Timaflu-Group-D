# Timaflu Backend (Flask + MySQL)

Python-backend volgens **Productbeschrijving** en **Klassendiagram Timaflu.png**:

- Domeinclasses in `domain/` (methods grotendeels stubs; kernlogica in `services/`)
- Vijf verplichte processen volledig geïmplementeerd
- REST API via Flask voor koppeling met de frontend en peer tests

## Vereisten

- Python 3.11+
- MySQL 8 (database `timaflu`)

## Installatie

```bash
cd Backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Pas `.env` aan (MySQL-gebruiker/wachtwoord).

## Database

Gebruik **`timaflu_schema.sql`** en **`timaflu_seed.sql`** in de projectmap (klassendiagram).  
Query-document voor peer test: **`timaflu_queries.md`** (project root).

```bash
cd ..
mysql -u root -p < timaflu_schema.sql
mysql -u root -p < timaflu_seed.sql
```

## Starten

```bash
python app.py
```

Open de website (server-side HTML + CSS, **geen frontend JavaScript**):

**http://127.0.0.1:5000/**

Pagina’s gebruiken formulieren (GET/POST); data komt uit MySQL via Python.

Health check: `GET http://localhost:5000/api/health`

Na wijziging aan `sql/seed.sql`: opnieuw laden in MySQL (`schema.sql` + `seed.sql`).

## Peer test demo (Deel 9)

Zonder Flask, alleen de vijf verplichte methods:

```bash
python run_demo.py
```

## Belangrijkste endpoints

| Proces | Method | Endpoint |
|--------|--------|----------|
| Verkoop — korting | POST | `/api/verkoop/korting` |
| Inkoop — leveranciers | GET | `/api/inkoop/leveranciers?productnaam=...` |
| Inkoop — leverancier loskoppelen | DELETE/POST | `/api/inkoop/product/leverancier` |
| Inkoop — product verwijderen | DELETE/POST | `/api/inkoop/product` |
| Administratie — factuur | GET | `/api/administratie/factuur/<klantnummer>` |
| Distributie — rooster | GET | `/api/distributie/rooster?datum=YYYY-MM-DD` |
| Orderpicking — wachtrij | GET | `/api/orderpicking/wachtrij` |
| Orderpicking — detail | GET | `/api/orderpicking/order/<ordernummer>` (1025 of intern id) |
| Acquisitie — overzicht | GET | `/api/acquisitie/overzicht` |
| Acquisitie — bezoek | POST | `/api/acquisitie/bezoek` (JSON) |

### Korting berekenen (JSON)

```json
{
  "klantnaam": "Apotheek De Linge",
  "klantadres": "Lindelaan 12, 5341 AB Oss",
  "subtotaal": 500
}
```

Kortingsvolgorde: bestelkorting 5% (≥ €500) → 10% eerste/ eenmalige korting → klantkorting (5/10/15%).
