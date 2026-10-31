-- Mock data for timaflu_schema.sql
CREATE DATABASE IF NOT EXISTS timaflu CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE timaflu;

-- Run timaflu_schema.sql first, then this file.

INSERT INTO address (street, house_number, postal_code, city) VALUES
('Lindelaan', '12', '5341 AB', 'Oss'),
('Markt', '3', '5211 AA', "'s-Hertogenbosch"),
('Noordweg', '88', '5223 BC', "'s-Hertogenbosch"),
('Zuidpark', '5', '5212 CD', "'s-Hertogenbosch"),
('Dorpsstraat', '1', '4811 AA', 'Breda'),
('Kerkstraat', '9', '5214 GH', "'s-Hertogenbosch"),
('Hoofdweg', '22', '5342 EF', 'Oss'),
('Parklaan', '4', '5224 IJ', "'s-Hertogenbosch"),
('Industrieweg', '1', '5345 AA', 'Oss'),
('Haven', '12', '5211 BB', "'s-Hertogenbosch"),
('Kanaalweg', '7', '5222 AA', "'s-Hertogenbosch"),
('Fabriekslaan', '3', '5346 BB', 'Oss'),
('Westlaan', '2', '5213 EF', "'s-Hertogenbosch"),
('Rivierdijk', '44', '5346 CD', 'Oss'),
('Magazijnweg', '1', '5345 AB', 'Oss');

INSERT INTO employee (name, department) VALUES
('Sanne Accountmanager', 'Acquisitie'),
('Koerier Jan', 'Distributie'),
('Koerier Eva', 'Distributie'),
('Spoed Express', 'Distributie');

INSERT INTO courier (employee_id, region, phone_number, available, external) VALUES
(2, 'Oss', '06-50101010', 1, 0),
(3, 'Den Bosch', '06-50202020', 1, 0),
(4, 'Landelijk', '0800-9999', 1, 1);

INSERT INTO customer (company_name, contact_person, phone_number, delivery_address_id, invoice_address_id,
    region, annual_turnover, one_time_discount, blocked) VALUES
('Apotheek De Linge', 'Sanne Visser', '06-11223344', 1, 1, 'Oss', 15000.00, 1, 0),
('Apotheek Centrum', 'Mark van Dijk', '06-22334455', 2, 2, 'Den Bosch', 8000.00, 0, 0),
('Apotheek Noord', 'Lisa Jansen', '06-33445566', 3, 3, 'Den Bosch', 22000.00, 0, 0),
('Apotheek Zuid', 'Peter Bakker', '06-44556677', 4, 4, 'Den Bosch', 12000.00, 0, 1),
('Apotheek De Vries', 'Jan de Vries', '076-5123456', 5, 5, 'Breda', 15000.00, 0, 0),
('Apotheek Smit', 'Emma Smit', '06-55667788', 6, 6, 'Den Bosch', 6000.00, 0, 0),
('Apotheek Jansen', 'Tom Jansen', '06-66778899', 7, 7, 'Oss', 9000.00, 0, 0),
('Apotheek Bakker', 'Nora Bakker', '06-77889900', 8, 8, 'Den Bosch', 11000.00, 0, 0);

INSERT INTO manufacturer (name, address_id, contact_person, phone_number, website) VALUES
('PharmaSupply BV', 9, 'Jan de Groot', '0412-555100', 'www.pharmasupply.nl'),
('MediGroothandel NL', 10, 'Eva Smit', '073-555200', 'www.medigroothandel.nl'),
('Benelux Farma', 11, 'Tom Kuipers', '088-555300', NULL),
('Genfarma BV', 12, 'Laura Peeters', '0413-555400', NULL);

INSERT INTO product (order_code, name, active_ingredients, packaging_type, units_per_bulk_pack,
    price_per_bulk_pack, short_description, minimum_order_qty, stock, minimum_stock) VALUES
('MF-1001', 'Paracetamol 500 mg', 'Paracetamol', 'Loc C17', 20, 12.50, 'Pijnstiller', 1, 120, 50),
('MF-2040', 'Ibuprofen 400 mg', 'Ibuprofen', 'Loc B04', 20, 10.00, 'Ontstekingsremmer', 1, 8, 25),
('MF-3012', 'Amoxicilline 500 mg', 'Amoxicilline', 'Loc A12', 10, 18.75, 'Antibioticum', 1, 45, 30),
('MF-4500', 'Omeprazol 20 mg', 'Omeprazol', 'Loc D02', 14, 22.00, 'Maagzuur', 1, 5, 20),
('MF-8801', 'Loratadine 10 mg', 'Loratadine', 'Loc C05', 30, 8.50, 'Anti-allergie', 1, 200, 40),
('MF-9900', 'Vitamine D3 1000 IE', 'Vitamine D3', 'Loc F08', 25, 14.00, 'Supplement', 1, 15, 35);

INSERT INTO product_supplier (product_id, manufacturer_id, purchase_price) VALUES
(2, 1, 7.50), (2, 2, 8.20), (2, 3, 7.90),
(4, 1, 14.00), (4, 2, 13.50),
(1, 1, 9.00), (1, 3, 8.80),
(3, 4, 18.40), (3, 2, 19.10),
(6, 1, 11.00), (6, 3, 10.50);

INSERT INTO invoice (customer_id, invoice_date, paid, reminder_count) VALUES
(4, '2026-10-20', 0, 1);

INSERT INTO orders (customer_id, invoice_id, order_date, delivery_date, day_part, urgent, status) VALUES
(1, NULL, '2026-10-28', '2026-10-29', 'MORNING', 0, 'SHIPPED'),
(8, NULL, '2026-10-27', '2026-10-28', 'AFTERNOON', 0, 'READY_FOR_DISTRIBUTION'),
(5, NULL, '2026-10-26', '2026-10-27', 'MORNING', 0, 'BEING_PICKED'),
(7, NULL, '2026-10-25', '2026-10-26', 'AFTERNOON', 0, 'BACKORDER'),
(6, NULL, '2026-10-30', '2026-10-31', 'MORNING', 1, 'BEING_PICKED'),
(2, NULL, '2026-10-29', '2026-10-30', 'AFTERNOON', 0, 'SHIPPED'),
(3, NULL, '2026-10-28', '2026-10-31', 'MORNING', 0, 'SHIPPED'),
(4, 1, '2025-10-01', '2025-10-05', 'MORNING', 0, 'DELIVERED'),
(1, NULL, '2026-10-22', '2026-10-23', 'AFTERNOON', 0, 'DELIVERED');

INSERT INTO order_line (order_id, product_id, quantity, price, backorder) VALUES
(1, 1, 20, 12.50, 0),
(1, 2, 20, 12.50, 1),
(2, 1, 12, 12.50, 0),
(2, 5, 8, 8.50, 0),
(3, 5, 40, 10.00, 0),
(3, 4, 25, 19.60, 0),
(4, 3, 11, 25.00, 0),
(5, 3, 10, 18.75, 0),
(5, 5, 15, 8.50, 0),
(5, 6, 8, 14.00, 0),
(5, 2, 2, 10.00, 1),
(6, 3, 16, 20.00, 0),
(7, 1, 30, 12.50, 0),
(7, 4, 10, 22.00, 0),
(8, 1, 50, 15.00, 0),
(9, 1, 15, 12.50, 0),
(9, 5, 20, 8.50, 0);

INSERT INTO delivery (order_id, courier_id, delivery_date, delivery_time, attempts, delivered, signed) VALUES
(2, 3, '2026-10-31', '09:30:00', 1, 0, 0),
(3, 2, '2026-10-31', '11:00:00', 2, 0, 0),
(1, 2, '2026-10-31', '14:00:00', 1, 0, 0),
(7, 3, '2026-10-31', '10:15:00', 1, 0, 0),
(5, 2, '2026-10-31', '08:45:00', 1, 0, 0);

INSERT INTO purchase_order (order_date, product_id, manufacturer_id, quantity, price) VALUES
('2026-10-29', 2, 1, 50, 7.50);

INSERT INTO visit (account_manager_id, company_name, contact_person, phone_number, address_id, visit_date, customer_id) VALUES
(1, 'Apotheek West', 'Mirjam Hoek', '06-77889900', 13, '2026-08-15', NULL),
(1, 'Apotheek Rivier', 'Chris Meijer', '06-88990011', 14, '2026-07-01', NULL),
(1, 'Apotheek De Linge', 'Sanne Visser', '06-11223344', 1, '2026-09-01', 1);
