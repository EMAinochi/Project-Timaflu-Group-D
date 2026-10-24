-- Verkoopproducten Timaflu
-- Dit script gooit de verkooptabellen weg en maakt ze opnieuw aan.
-- Het kan dus vaker achter elkaar worden uitgevoerd.

CREATE DATABASE IF NOT EXISTS timaflu;

USE timaflu;


DROP TABLE IF EXISTS bestelregel;
DROP TABLE IF EXISTS bestelling;
DROP TABLE IF EXISTS klant;
DROP TABLE IF EXISTS medicijn;

CREATE TABLE medicijn (
    bestelcode VARCHAR(20) NOT NULL,
    naam VARCHAR(150) NOT NULL,
    PRIMARY KEY (bestelcode)
);

CREATE TABLE klant (
    klantnummer INT NOT NULL AUTO_INCREMENT,
    bedrijfsnaam VARCHAR(100) NOT NULL,
    voornaam VARCHAR(50) NOT NULL,
    tussenvoegsel VARCHAR(20) NULL,
    achternaam VARCHAR(50) NOT NULL,
    telefoonnummer VARCHAR(20) NOT NULL,
    aflever_straat VARCHAR(100) NOT NULL,
    aflever_postcode VARCHAR(7) NOT NULL,
    aflever_plaats VARCHAR(80) NOT NULL,
    betaal_straat VARCHAR(100) NOT NULL,
    betaal_postcode VARCHAR(7) NOT NULL,
    betaal_plaats VARCHAR(80) NOT NULL,
    -- 99.99
    klantkorting DECIMAL(4, 2) NOT NULL DEFAULT 5.00,
    eenmalige_korting TINYINT(1) NOT NULL DEFAULT 0,
    incassoblokkade TINYINT(1) NOT NULL DEFAULT 0,
    PRIMARY KEY (klantnummer),
    -- update/create controles
    CONSTRAINT chk_klant_klantkorting CHECK (klantkorting IN (5.00, 10.00, 15.00)),
    CONSTRAINT chk_klant_eenmalige_korting CHECK (eenmalige_korting IN (0, 1)),
    CONSTRAINT chk_klant_incassoblokkade CHECK (incassoblokkade IN (0, 1))
);

CREATE TABLE bestelling (
    ordernummer INT NOT NULL AUTO_INCREMENT,
    klantnummer INT NOT NULL,
    besteldatum DATE NOT NULL,
    bezorgdatum DATE NOT NULL,
    dagdeel ENUM('ochtend', 'middag') NULL,
    spoed TINYINT(1) NOT NULL DEFAULT 0,
    status ENUM('wordt verzameld', 'verstuurd', 'backorder', 'afgeleverd') NOT NULL DEFAULT 'wordt verzameld',
    subtotaal DECIMAL(10, 2) NOT NULL,
    bestelkorting DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    eenmalige_korting_bedrag DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    klantkorting_bedrag DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    totaalbedrag DECIMAL(10, 2) NOT NULL,
    PRIMARY KEY (ordernummer),
    -- fk aangeven
    CONSTRAINT fk_bestelling_klant
        FOREIGN KEY (klantnummer) REFERENCES klant (klantnummer),
	-- create/update checks
    CONSTRAINT chk_bestelling_spoed CHECK (spoed IN (0, 1)),
    CONSTRAINT chk_bestelling_bedragen CHECK (
        subtotaal >= 0
        AND bestelkorting >= 0
        AND eenmalige_korting_bedrag >= 0
        AND klantkorting_bedrag >= 0
        AND totaalbedrag >= 0
    )
);

CREATE TABLE bestelregel (
    bestelregelnummer INT NOT NULL AUTO_INCREMENT,
    ordernummer INT NOT NULL,
    bestelcode VARCHAR(20) NOT NULL,
    aantal INT NOT NULL,
    prijs DECIMAL(10, 2) NOT NULL,
    status ENUM('leverbaar', 'backorder') NOT NULL,
    PRIMARY KEY (bestelregelnummer),
    CONSTRAINT fk_bestelregel_bestelling
        FOREIGN KEY (ordernummer) REFERENCES bestelling (ordernummer),
    CONSTRAINT fk_bestelregel_medicijn
        FOREIGN KEY (bestelcode) REFERENCES medicijn (bestelcode),
    CONSTRAINT chk_bestelregel_aantal CHECK (aantal > 0),
    CONSTRAINT chk_bestelregel_prijs CHECK (prijs >= 0)
);
