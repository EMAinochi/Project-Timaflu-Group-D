# Timaflu — Group D

Webapplicatie voor verkoop, inkoop, orderpicking, distributie, administratie en acquisitie.  
**Stack:** Python (Flask), MySQL, HTML/CSS (server-rendered templates, geen frontend JavaScript).

Na een `git pull` volg je onderstaande stappen op je eigen machine.

> **`app.py` staat in `Backend/`, niet in de projectroot.**  
> `python app.py` en `pip install -r requirements.txt` altijd uitvoeren **nadat** je `cd Backend` hebt gedaan (en bij voorkeur met geactiveerde venv).  
> Typ `app.py` niet in de Python-interactive (`>>>`) — sluit die met `exit()` en start de server via de terminal.

---

## Vereisten

| Software | Versie |
|----------|--------|
| Python | 3.11 of nieuwer |
| MySQL | 8.x (lokaal draaiend) |
| Git | (repo al gekloond) |

Optioneel: [MySQL Workbench](https://dev.mysql.com/downloads/workbench/) of de `mysql` CLI om de database te laden.

---

## 1. Repository

Je hebt de code al lokaal (bijv. `Project-Timaflu-Group-D`). Open een terminal in die map.

Bij updates later:

```bash
git pull
```

Als `timaflu_schema.sql` is gewijzigd, laad schema + seed opnieuw (zie stap 3).

---

## 2. Python-backend installeren

```powershell
cd Backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

**macOS / Linux:**

```bash
cd Backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Pas **`Backend/.env`** aan met jouw MySQL-gegevens:

```env
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=jouw_wachtwoord
MYSQL_DATABASE=timaflu
```

---

## 3. Database aanmaken en vullen

Gebruik de bestanden in de **project root** (niet `verkoopProducten.sql` — dat is een oud los script).

Vanuit de **project root**:

**Windows (PowerShell), met wachtwoord:**

```powershell
cd ..
Get-Content timaflu_schema.sql | mysql -u root -p
Get-Content timaflu_seed.sql | mysql -u root -p
```

**Of één regel per bestand (cmd):**

```cmd
mysql -u root -p < timaflu_schema.sql
mysql -u root -p < timaflu_seed.sql
```

**macOS / Linux:**

```bash
mysql -u root -p < timaflu_schema.sql
mysql -u root -p < timaflu_seed.sql
```

Dit maakt database `timaflu` aan met tabellen en demodata.

---

## 4. Applicatie starten

Met geactiveerde venv in **`Backend`**:

```bash
python app.py
```

Open in de browser:

**http://127.0.0.1:5000/**

- Startpagina = **Verkoop**
- Navigatie: Inkoop, Orderpicking, Bezorgen, Administratie, Acquisitie

Health check (API): **http://127.0.0.1:5000/api/health**

Poort wijzigen (optioneel): zet `PORT=8080` in `.env` of in de omgeving.

---

## 5. Peer test / demo (Deel 9)

Zonder browser — alleen de vijf verplichte backend-methodes:

```bash
cd Backend
.venv\Scripts\activate   # of source .venv/bin/activate
python run_demo.py
```

SQL-voorbeelden: **`timaflu_queries.md`**.  
Inleverdocument schermen + queries + output: **`Documentatie/Timaflu-schermen-en-queries.md`**.

---

## Mapstructuur (kort)

| Pad | Inhoud |
|-----|--------|
| `Backend/` | Flask-app (`app.py`), services, Jinja-templates |
| `Backend/templates/` | HTML-pagina’s (worden door Flask geserveerd) |
| `Frontend Website/styles.css` | Globale styling (via Flask) |
| `timaflu_schema.sql` / `timaflu_seed.sql` | Database |
| `Schermontwerpen/` | Wireframes desktop + mobiel |
| `Backend/README.md` | Uitgebreide API-endpointlijst |

---

## Veelvoorkomende problemen

**`Can't connect to MySQL server`**  
MySQL-service starten; host/poort/user/wachtwoord in `Backend/.env` controleren.

**Lege pagina’s of SQL-fouten in de terminal**  
Schema + seed opnieuw laden (stap 3). Controleer of database `timaflu` bestaat.

**Poort 5000 in gebruik**  
Andere poort via `PORT` in `.env`, of het andere proces stoppen.

**Na `git pull` werkt iets niet meer**  
Opnieuw `pip install -r requirements.txt` en indien nodig database opnieuw seeden.

---

## Meer documentatie

- API-endpoints: [Backend/README.md](Backend/README.md)
- Scherm ↔ wireframe: [Schermontwerpen/README.md](Schermontwerpen/README.md)
- Schermen + queries + output: [Documentatie/Timaflu-schermen-en-queries.md](Documentatie/Timaflu-schermen-en-queries.md)
