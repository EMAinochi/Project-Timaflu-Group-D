# Timaflu — Query-document (peer test Deel 10–12)

Database: **timaflu** (`timaflu_schema.sql`, `timaflu_seed.sql`).  
Queries komen overeen met schermen in de Flask-app (`Backend/templates/`).

**Volledige inleverversie** (alle schermen + screenshots + volledige output):  
[Documentatie/Timaflu-schermen-en-queries.md](Documentatie/Timaflu-schermen-en-queries.md)

---

## 1. Verkoop — klant zoeken

```sql
SELECT c.customer_id AS klantnummer, c.company_name AS bedrijfsnaam,
       c.contact_person AS contactpersoon, c.phone_number AS telefoonnummer,
       c.annual_turnover AS jaaromzet, c.one_time_discount AS eenmalige_korting
FROM customer c
WHERE c.company_name LIKE '%Apotheek%'
ORDER BY c.company_name;
```

**Output (8 rijen):**

| klantnummer | bedrijfsnaam | contactpersoon | telefoonnummer | jaaromzet |
|-------------|--------------|----------------|----------------|-----------|
| 8 | Apotheek Bakker | Nora Bakker | 06-77889900 | 11000.00 |
| 2 | Apotheek Centrum | Mark van Dijk | 06-22334455 | 8000.00 |
| 1 | Apotheek De Linge | Sanne Visser | 06-11223344 | 15000.00 |
| 5 | Apotheek De Vries | Jan de Vries | 076-5123456 | 15000.00 |
| 7 | Apotheek Jansen | Tom Jansen | 06-66778899 | 9000.00 |
| 3 | Apotheek Noord | Lisa Jansen | 06-33445566 | 22000.00 |
| 6 | Apotheek Smit | Emma Smit | 06-55667788 | 6000.00 |
| 4 | Apotheek Zuid | Peter Bakker | 06-44556677 | 12000.00 |

---

## 2. Verkoop — product / voorraad

```sql
SELECT p.product_id, p.order_code AS bestelcode, p.name AS naam,
       p.stock AS voorraad, p.minimum_stock AS minimum_voorraad,
       p.packaging_type AS magazijn_locatie, p.price_per_bulk_pack AS prijs
FROM product p
ORDER BY p.name;
```

**Output (6 rijen):**

| product_id | bestelcode | naam | voorraad | minimum_voorraad | magazijn_locatie | prijs |
|------------|------------|------|----------|------------------|------------------|-------|
| 3 | MF-3012 | Amoxicilline 500 mg | 41 | 30 | Loc A12 | 18.75 |
| 2 | MF-2040 | Ibuprofen 400 mg | 8 | 25 | Loc B04 | 10.00 |
| 5 | MF-8801 | Loratadine 10 mg | 200 | 40 | Loc C05 | 8.50 |
| 4 | MF-4500 | Omeprazol 20 mg | 5 | 20 | Loc D02 | 22.00 |
| 1 | MF-1001 | Paracetamol 500 mg | 120 | 50 | Loc C17 | 12.50 |
| 6 | MF-9900 | Vitamine D3 1000 IE | 15 | 35 | Loc F08 | 14.00 |

---

## 3. Verkoop — orders en orderregels

```sql
SELECT o.order_id AS ordernummer, c.company_name AS klant, o.status, o.urgent AS spoed
FROM orders o
JOIN customer c ON c.customer_id = o.customer_id
ORDER BY o.order_id;

SELECT ol.order_id, p.name AS product, ol.quantity AS aantal, ol.price, ol.backorder
FROM order_line ol
JOIN product p ON p.product_id = ol.product_id
WHERE ol.order_id = 5;
```

**Output orders (10 rijen):**

| ordernummer | klant | status | spoed |
|-------------|-------|--------|-------|
| 1 | Apotheek De Linge | SHIPPED | 0 |
| 2 | Apotheek Bakker | READY_FOR_DISTRIBUTION | 0 |
| 3 | Apotheek De Vries | BEING_PICKED | 0 |
| 4 | Apotheek Jansen | BACKORDER | 0 |
| 5 | Apotheek Smit | READY_FOR_DISTRIBUTION | 1 |
| 6 | Apotheek Centrum | SHIPPED | 0 |
| 7 | Apotheek Noord | SHIPPED | 0 |
| 8 | Apotheek Zuid | DELIVERED | 0 |
| 9 | Apotheek De Linge | DELIVERED | 0 |
| 10 | Apotheek Bakker | BEING_PICKED | 1 |

**Output orderregels order 5:**

| order_id | product | aantal | price | backorder |
|----------|---------|--------|-------|-----------|
| 5 | Amoxicilline 500 mg | 10 | 18.75 | 0 |
| 5 | Loratadine 10 mg | 15 | 8.50 | 0 |
| 5 | Vitamine D3 1000 IE | 8 | 14.00 | 0 |
| 5 | Ibuprofen 400 mg | 2 | 10.00 | 1 |

---

## 4. Inkoop — onder minimumvoorraad

```sql
SELECT p.name AS productnaam, p.stock AS voorraad, p.minimum_stock AS minimum
FROM product p
WHERE p.stock < p.minimum_stock
ORDER BY p.name;
```

**Output (3 rijen):**

| productnaam | voorraad | minimum |
|-------------|----------|---------|
| Ibuprofen 400 mg | 8 | 25 |
| Omeprazol 20 mg | 5 | 20 |
| Vitamine D3 1000 IE | 15 | 35 |

---

## 5. Inkoop — leveranciers per product (goedkoopst eerst)

```sql
SELECT p.name AS product, m.name AS leverancier, ps.purchase_price AS inkoopprijs,
       m.contact_person, m.phone_number AS telefoonnummer
FROM product p
JOIN product_supplier ps ON ps.product_id = p.product_id
JOIN manufacturer m ON m.manufacturer_id = ps.manufacturer_id
WHERE p.name LIKE '%Ibuprofen%'
ORDER BY ps.purchase_price ASC;
```

**Output (goedkoopst eerst):**

| product | leverancier | inkoopprijs | contact_person | telefoonnummer |
|---------|-------------|-------------|----------------|----------------|
| Ibuprofen 400 mg | PharmaSupply BV | 7.50 | Jan de Groot | 0412-555100 |
| Ibuprofen 400 mg | Benelux Farma | 7.90 | Tom Kuipers | 088-555300 |
| Ibuprofen 400 mg | MediGroothandel NL | 8.20 | Eva Smit | 073-555200 |

---

## 6. Orderpicking — wachtrij

```sql
SELECT o.order_id + 1020 AS ordernr_weergave, c.company_name AS klant,
       o.urgent AS spoed, o.status
FROM orders o
JOIN customer c ON c.customer_id = o.customer_id
WHERE o.status IN ('BEING_PICKED', 'BACKORDER', 'READY_FOR_DISTRIBUTION')
ORDER BY o.urgent DESC, o.order_id;
```

**Output (5 rijen, spoed bovenaan):**

| ordernr_weergave | klant | spoed | status |
|------------------|-------|-------|--------|
| 1025 | Apotheek Smit | 1 | READY_FOR_DISTRIBUTION |
| 1030 | Apotheek Bakker | 1 | BEING_PICKED |
| 1022 | Apotheek Bakker | 0 | READY_FOR_DISTRIBUTION |
| 1023 | Apotheek De Vries | 0 | BEING_PICKED |
| 1024 | Apotheek Jansen | 0 | BACKORDER |

---

## 7. Orderpicking — magazijnlocatie per regel

```sql
SELECT p.order_code, p.name, ol.quantity,
       p.packaging_type AS magazijn_locatie
FROM order_line ol
JOIN product p ON p.product_id = ol.product_id
WHERE ol.order_id = 5 AND ol.backorder = 0;
```

**Output (3 leverbare regels):**

| order_code | name | quantity | magazijn_locatie |
|------------|------|----------|------------------|
| MF-3012 | Amoxicilline 500 mg | 10 | Loc A12 |
| MF-8801 | Loratadine 10 mg | 15 | Loc C05 |
| MF-9900 | Vitamine D3 1000 IE | 8 | Loc F08 |

---

## 8. Orderpicking — deelorderstatus per gang

```sql
SELECT order_id, gang, status
FROM order_pick_gang
WHERE order_id = 5;
```

**Output:**

| order_id | gang | status |
|----------|------|--------|
| 5 | A | ROLLERBAAN |
| 5 | C | ROLLERBAAN |
| 5 | F | ROLLERBAAN |

---

## 9. Distributie — rooster op datum

```sql
SELECT d.delivery_id, d.delivery_time, c.company_name, c.phone_number,
       o.urgent AS spoed, o.day_part, d.delivered, d.attempts
FROM delivery d
JOIN orders o ON o.order_id = d.order_id
JOIN customer c ON c.customer_id = o.customer_id
WHERE d.delivery_date = '2026-10-31'
ORDER BY d.delivery_time;
```

**Output (5 stops op 2026-10-31):**

| delivery_id | delivery_time | company_name | phone_number | spoed | day_part | delivered | attempts |
|-------------|---------------|--------------|--------------|-------|----------|-----------|----------|
| 5 | 08:45:00 | Apotheek Smit | 06-55667788 | 1 | MORNING | 0 | 1 |
| 1 | 09:30:00 | Apotheek Bakker | 06-77889900 | 0 | AFTERNOON | 0 | 1 |
| 4 | 10:15:00 | Apotheek Noord | 06-33445566 | 0 | MORNING | 0 | 1 |
| 2 | 11:00:00 | Apotheek De Vries | 076-5123456 | 0 | MORNING | 0 | 2 |
| 3 | 14:00:00 | Apotheek De Linge | 06-11223344 | 0 | MORNING | 0 | 1 |

---

## 10. Administratie — afgeleverd zonder factuur

```sql
SELECT c.customer_id, c.company_name, COUNT(o.order_id) AS orders
FROM orders o
JOIN customer c ON c.customer_id = o.customer_id
WHERE o.status = 'DELIVERED' AND o.invoice_id IS NULL
GROUP BY c.customer_id, c.company_name;
```

**Output:** 0 rijen. Alle `DELIVERED`-orders hebben al een `invoice_id` (order 8 → factuur 1, order 9 → factuur 2). De filter `invoice_id IS NULL` sluit ze terecht uit.

---

## 11. Administratie — openstaande facturen

```sql
SELECT i.invoice_id, c.company_name, i.invoice_date, i.paid, i.reminder_count
FROM invoice i
JOIN customer c ON c.customer_id = i.customer_id
WHERE i.paid = 0;
```

**Output (2 openstaande facturen):**

| invoice_id | company_name | invoice_date | paid | reminder_count |
|------------|--------------|--------------|------|----------------|
| 1 | Apotheek Zuid | 2026-10-20 | 0 | 2 |
| 2 | Apotheek De Linge | 2026-10-31 | 0 | 0 |

---

## 12. Acquisitie — overzicht (≥ 1 maand, geen order)

```sql
SELECT v.company_name, v.contact_person, v.phone_number, v.visit_date
FROM visit v
WHERE v.customer_id IS NULL
  AND v.visit_date <= DATE_SUB(CURDATE(), INTERVAL 1 MONTH)
  AND NOT EXISTS (
      SELECT 1 FROM orders o
      JOIN customer c ON c.customer_id = o.customer_id
      WHERE c.company_name = v.company_name
  );
```

**Output (2 prospects; De Linge valt af omdat die al klant is):**

| company_name | contact_person | phone_number | visit_date |
|--------------|----------------|--------------|------------|
| Apotheek Rivier | Chris Meijer | 06-88990011 | 2026-07-01 |
| Apotheek West | Mirjam Hoek | 06-77889900 | 2026-08-15 |

---

## 13. Acquisitie — follow-up contactmomenten

```sql
SELECT v.company_name, f.follow_up_date, f.notes
FROM visit_follow_up f
JOIN visit v ON v.visit_id = f.visit_id
ORDER BY f.follow_up_date DESC;
```

**Output (2 follow-ups):**

| company_name | follow_up_date | notes |
|--------------|----------------|-------|
| Apotheek West | 2026-09-20 | Tweede bezoek: interesse in paracetamol en ibuprofen, nog geen bestelling. |
| Apotheek Rivier | 2026-08-12 | Telefonisch nagebeld; contactpersoon was afwezig, nieuwe afspraak gemaakt. |

---

## Traceability (Deel 12)

| Scherm | Template | Hoofdtabellen |
|--------|----------|---------------|
| Verkoop | `index.html` | `customer`, `product`, `orders`, `order_line` |
| Inkoop | `inkoop-2-2-*.html` | `product`, `product_supplier`, `manufacturer`, `purchase_order` |
| Orderpicking | `orderpicking.html` | `orders`, `order_line`, `product`, `order_pick_gang` |
| Distributie | `distributie.html` | `delivery`, `orders`, `customer`, `address` |
| Administratie | `administratie.html` | `invoice`, `orders`, `customer` |
| Acquisitie | `acquisition-6-22.html` | `visit`, `visit_follow_up`, `customer` |

Terminologie: **order** / **bestelling** → `orders`; **klant** → `customer`; **leverancier** → `manufacturer`.
