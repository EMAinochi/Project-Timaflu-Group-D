# Timaflu — Query-document (peer test Deel 10–12)

Database: **timaflu** (`timaflu_schema.sql`, `timaflu_seed.sql`).  
Queries komen overeen met schermen in de Flask-app (`Backend/templates/`).

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

**Voorbeeldoutput (seed):**

| klantnummer | bedrijfsnaam      | jaaromzet |
|-------------|-------------------|-----------|
| 1           | Apotheek De Linge | 15000.00  |
| 8           | Apotheek Bakker   | 11000.00  |
| 2           | Apotheek Centrum  | 8000.00   |
| …           | …                 | …         |

---

## 2. Verkoop — product / voorraad

```sql
SELECT p.product_id, p.order_code AS bestelcode, p.name AS naam,
       p.stock AS voorraad, p.minimum_stock AS minimum_voorraad,
       p.packaging_type AS magazijn_locatie, p.price_per_bulk_pack AS prijs
FROM product p
ORDER BY p.name;
```

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

---

## 4. Inkoop — onder minimumvoorraad

```sql
SELECT p.name AS productnaam, p.stock AS voorraad, p.minimum_stock AS minimum
FROM product p
WHERE p.stock < p.minimum_stock
ORDER BY p.name;
```

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

**Voorbeeldoutput:** PharmaSupply €7,50 → Benelux €7,90 → MediGroothandel €8,20.

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

---

## 7. Orderpicking — magazijnlocatie per regel

```sql
SELECT p.order_code, p.name, ol.quantity,
       p.packaging_type AS magazijn_locatie
FROM order_line ol
JOIN product p ON p.product_id = ol.product_id
WHERE ol.order_id = 5 AND ol.backorder = 0;
```

---

## 8. Orderpicking — deelorderstatus per gang

```sql
SELECT order_id, gang, status
FROM order_pick_gang
WHERE order_id = 5;
```

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

---

## 10. Administratie — afgeleverd zonder factuur

```sql
SELECT c.customer_id, c.company_name, COUNT(o.order_id) AS orders
FROM orders o
JOIN customer c ON c.customer_id = o.customer_id
WHERE o.status = 'DELIVERED' AND o.invoice_id IS NULL
GROUP BY c.customer_id, c.company_name;
```

---

## 11. Administratie — openstaande facturen

```sql
SELECT i.invoice_id, c.company_name, i.invoice_date, i.paid, i.reminder_count
FROM invoice i
JOIN customer c ON c.customer_id = i.customer_id
WHERE i.paid = 0;
```

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

---

## 13. Acquisitie — follow-up contactmomenten

```sql
SELECT v.company_name, f.follow_up_date, f.notes
FROM visit_follow_up f
JOIN visit v ON v.visit_id = f.visit_id
ORDER BY f.follow_up_date DESC;
```

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
