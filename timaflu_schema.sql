-- Timaflu – MySQL schema derived from Klassendiagram Timaflu (Visio / class diagram)
-- Normalized: Address as entity; Courier extends Employee; Invoice–Order 0..1 : 1..*

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS purchase_invoice;
DROP TABLE IF EXISTS purchase_order;
DROP TABLE IF EXISTS product_supplier;
DROP TABLE IF EXISTS order_pick_gang;
DROP TABLE IF EXISTS visit_follow_up;
DROP TABLE IF EXISTS delivery;
DROP TABLE IF EXISTS order_line;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS invoice;
DROP TABLE IF EXISTS visit;
DROP TABLE IF EXISTS product;
DROP TABLE IF EXISTS manufacturer;
DROP TABLE IF EXISTS customer;
DROP TABLE IF EXISTS courier;
DROP TABLE IF EXISTS employee;
DROP TABLE IF EXISTS address;

SET FOREIGN_KEY_CHECKS = 1;

-- «datatype» Address
CREATE TABLE address (
    address_id     INT UNSIGNED NOT NULL AUTO_INCREMENT,
    street         VARCHAR(255) NOT NULL,
    house_number   VARCHAR(20)  NOT NULL,
    postal_code    VARCHAR(20)  NOT NULL,
    city           VARCHAR(100) NOT NULL,
    PRIMARY KEY (address_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Employee (+ Courier generalization)
CREATE TABLE employee (
    employee_id    INT UNSIGNED NOT NULL AUTO_INCREMENT,
    name           VARCHAR(255) NOT NULL,
    department     VARCHAR(100) NOT NULL,
    PRIMARY KEY (employee_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE courier (
    employee_id    INT UNSIGNED NOT NULL,
    region         VARCHAR(100) NOT NULL,
    phone_number   VARCHAR(30)  NULL,
    available      TINYINT(1)   NOT NULL DEFAULT 0,
    external       TINYINT(1)   NOT NULL DEFAULT 0,
    PRIMARY KEY (employee_id),
    CONSTRAINT fk_courier_employee
        FOREIGN KEY (employee_id) REFERENCES employee (employee_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE customer (
    customer_id         INT UNSIGNED NOT NULL AUTO_INCREMENT,
    company_name        VARCHAR(255) NOT NULL,
    contact_person      VARCHAR(255) NOT NULL,
    phone_number        VARCHAR(30)  NOT NULL,
    delivery_address_id INT UNSIGNED NOT NULL,
    invoice_address_id  INT UNSIGNED NOT NULL,
    region              VARCHAR(100) NOT NULL,
    annual_turnover     DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    one_time_discount   TINYINT(1)     NOT NULL DEFAULT 0,
    blocked             TINYINT(1)     NOT NULL DEFAULT 0,
    PRIMARY KEY (customer_id),
    CONSTRAINT fk_customer_delivery_address
        FOREIGN KEY (delivery_address_id) REFERENCES address (address_id),
    CONSTRAINT fk_customer_invoice_address
        FOREIGN KEY (invoice_address_id) REFERENCES address (address_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE manufacturer (
    manufacturer_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    name            VARCHAR(255) NOT NULL,
    address_id      INT UNSIGNED NOT NULL,
    contact_person  VARCHAR(255) NOT NULL,
    phone_number    VARCHAR(30)  NOT NULL,
    website         VARCHAR(255) NULL,
    PRIMARY KEY (manufacturer_id),
    CONSTRAINT fk_manufacturer_address
        FOREIGN KEY (address_id) REFERENCES address (address_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE product (
    product_id           INT UNSIGNED NOT NULL AUTO_INCREMENT,
    order_code           VARCHAR(50)  NOT NULL,
    name                 VARCHAR(255) NOT NULL,
    active_ingredients   TEXT         NULL,
    packaging_type       VARCHAR(100) NOT NULL,
    units_per_bulk_pack  INT UNSIGNED NOT NULL DEFAULT 1,
    price_per_bulk_pack  DECIMAL(12, 2) NOT NULL,
    short_description    VARCHAR(500) NULL,
    long_description     TEXT         NULL,
    minimum_order_qty    INT UNSIGNED NOT NULL DEFAULT 1,
    stock                INT          NOT NULL DEFAULT 0,
    minimum_stock        INT UNSIGNED NOT NULL DEFAULT 0,
    PRIMARY KEY (product_id),
    UNIQUE KEY uq_product_order_code (order_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE product_supplier (
    product_id      INT UNSIGNED NOT NULL,
    manufacturer_id INT UNSIGNED NOT NULL,
    purchase_price  DECIMAL(12, 2) NOT NULL,
    PRIMARY KEY (product_id, manufacturer_id),
    CONSTRAINT fk_ps_product
        FOREIGN KEY (product_id) REFERENCES product (product_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_ps_manufacturer
        FOREIGN KEY (manufacturer_id) REFERENCES manufacturer (manufacturer_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE visit (
    visit_id            INT UNSIGNED NOT NULL AUTO_INCREMENT,
    account_manager_id  INT UNSIGNED NOT NULL,
    company_name        VARCHAR(255) NOT NULL,
    contact_person      VARCHAR(255) NOT NULL,
    phone_number        VARCHAR(30)  NOT NULL,
    address_id          INT UNSIGNED NOT NULL,
    visit_date          DATE         NOT NULL,
    customer_id         INT UNSIGNED NULL,
    PRIMARY KEY (visit_id),
    CONSTRAINT fk_visit_account_manager
        FOREIGN KEY (account_manager_id) REFERENCES employee (employee_id),
    CONSTRAINT fk_visit_address
        FOREIGN KEY (address_id) REFERENCES address (address_id),
    CONSTRAINT fk_visit_customer
        FOREIGN KEY (customer_id) REFERENCES customer (customer_id)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE visit_follow_up (
    follow_up_id   INT UNSIGNED NOT NULL AUTO_INCREMENT,
    visit_id       INT UNSIGNED NOT NULL,
    follow_up_date DATE         NOT NULL,
    notes          VARCHAR(500) NULL,
    PRIMARY KEY (follow_up_id),
    CONSTRAINT fk_visit_follow_up_visit
        FOREIGN KEY (visit_id) REFERENCES visit (visit_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE invoice (
    invoice_id        INT UNSIGNED NOT NULL AUTO_INCREMENT,
    customer_id       INT UNSIGNED NOT NULL,
    invoice_date      DATE         NOT NULL,
    vat_rate          DECIMAL(4, 4) NOT NULL DEFAULT 0.0900,
    paid              TINYINT(1)    NOT NULL DEFAULT 0,
    reminder_count    INT UNSIGNED  NOT NULL DEFAULT 0,
    payment_plan      TINYINT(1)    NOT NULL DEFAULT 0,
    collection_agency TINYINT(1)    NOT NULL DEFAULT 0,
    PRIMARY KEY (invoice_id),
    CONSTRAINT fk_invoice_customer
        FOREIGN KEY (customer_id) REFERENCES customer (customer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- «enumeration» OrderStatus, DayPart on Order
CREATE TABLE orders (
    order_id       INT UNSIGNED NOT NULL AUTO_INCREMENT,
    customer_id    INT UNSIGNED NOT NULL,
    invoice_id     INT UNSIGNED NULL,
    order_date     DATE         NOT NULL,
    delivery_date  DATE         NOT NULL,
    day_part       ENUM('MORNING', 'AFTERNOON') NOT NULL,
    urgent         TINYINT(1)   NOT NULL DEFAULT 0,
    status         ENUM(
        'BEING_PICKED',
        'BACKORDER',
        'READY_FOR_DISTRIBUTION',
        'SHIPPED',
        'DELIVERED',
        'NOT_DELIVERED'
    ) NOT NULL DEFAULT 'BEING_PICKED',
    extra_charges  DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    charge_note    VARCHAR(500)   NULL,
    PRIMARY KEY (order_id),
    CONSTRAINT fk_orders_customer
        FOREIGN KEY (customer_id) REFERENCES customer (customer_id),
    CONSTRAINT fk_orders_invoice
        FOREIGN KEY (invoice_id) REFERENCES invoice (invoice_id)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE order_line (
    order_line_id       INT UNSIGNED NOT NULL AUTO_INCREMENT,
    order_id            INT UNSIGNED NOT NULL,
    product_id          INT UNSIGNED NOT NULL,
    quantity            INT UNSIGNED NOT NULL,
    price               DECIMAL(12, 2) NOT NULL,
    delivered_quantity  INT UNSIGNED NOT NULL DEFAULT 0,
    backorder           TINYINT(1)   NOT NULL DEFAULT 0,
    PRIMARY KEY (order_line_id),
    CONSTRAINT fk_order_line_order
        FOREIGN KEY (order_id) REFERENCES orders (order_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_order_line_product
        FOREIGN KEY (product_id) REFERENCES product (product_id),
    UNIQUE KEY uq_order_line_order_product (order_id, product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE order_pick_gang (
    order_id    INT UNSIGNED NOT NULL,
    gang        CHAR(1)      NOT NULL,
    status      ENUM('BEZIG', 'VERZAMELD', 'ROLLERBAAN') NOT NULL DEFAULT 'BEZIG',
    PRIMARY KEY (order_id, gang),
    CONSTRAINT fk_order_pick_gang_order
        FOREIGN KEY (order_id) REFERENCES orders (order_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE delivery (
    delivery_id  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    order_id     INT UNSIGNED NOT NULL,
    courier_id   INT UNSIGNED NULL,
    delivery_date DATE        NOT NULL,
    delivery_time TIME        NULL,
    attempts     INT UNSIGNED NOT NULL DEFAULT 1,
    delivered    TINYINT(1)   NOT NULL DEFAULT 0,
    signed       TINYINT(1)   NOT NULL DEFAULT 0,
    PRIMARY KEY (delivery_id),
    CONSTRAINT fk_delivery_order
        FOREIGN KEY (order_id) REFERENCES orders (order_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_delivery_courier
        FOREIGN KEY (courier_id) REFERENCES courier (employee_id)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE purchase_order (
    purchase_id     INT UNSIGNED NOT NULL AUTO_INCREMENT,
    order_date      DATE         NOT NULL,
    product_id      INT UNSIGNED NOT NULL,
    manufacturer_id INT UNSIGNED NOT NULL,
    quantity        INT UNSIGNED NOT NULL,
    price           DECIMAL(12, 2) NOT NULL,
    PRIMARY KEY (purchase_id),
    CONSTRAINT fk_purchase_order_product
        FOREIGN KEY (product_id) REFERENCES product (product_id),
    CONSTRAINT fk_purchase_order_manufacturer
        FOREIGN KEY (manufacturer_id) REFERENCES manufacturer (manufacturer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE purchase_invoice (
    invoice_number    VARCHAR(50)  NOT NULL,
    purchase_order_id INT UNSIGNED NOT NULL,
    amount            DECIMAL(12, 2) NOT NULL,
    paid              TINYINT(1)     NOT NULL DEFAULT 0,
    PRIMARY KEY (purchase_order_id),
    UNIQUE KEY uq_purchase_invoice_number (invoice_number),
    CONSTRAINT fk_purchase_invoice_order
        FOREIGN KEY (purchase_order_id) REFERENCES purchase_order (purchase_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Helpful indexes for frontend / backend queries
CREATE INDEX idx_orders_customer ON orders (customer_id);
CREATE INDEX idx_orders_status ON orders (status);
CREATE INDEX idx_orders_delivery_date ON orders (delivery_date);
CREATE INDEX idx_delivery_courier_date ON delivery (courier_id, delivery_date);
CREATE INDEX idx_invoice_customer_paid ON invoice (customer_id, paid);
CREATE INDEX idx_product_stock ON product (stock, minimum_stock);
CREATE INDEX idx_visit_date ON visit (visit_date);
