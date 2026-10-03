-- ============================================================
-- SCHÉMA DE LA BASE DE DONNÉES EDUPAIE
-- Version: 1
-- ============================================================
-- Ce schéma suit les exigences du projet :
-- - Argent stocké en entiers (cents)
-- - Foreign keys activées
-- - Numérotation atomique des reçus
-- - Snapshot pour ré-impression identique
-- - Annulation au lieu de suppression
-- Toutes les instructions sont idempotentes (IF NOT EXISTS / OR IGNORE)
-- ============================================================

-- ============================================================
-- TABLE DES ANNÉES SCOLAIRES
-- ============================================================
CREATE TABLE IF NOT EXISTS school_year (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT NOT NULL UNIQUE,              -- Ex: "2024-2025"
    start_date DATE NOT NULL,                -- Date de début
    end_date DATE NOT NULL,                  -- Date de fin
    is_current BOOLEAN DEFAULT 0 CHECK(is_current IN (0, 1))
);

CREATE INDEX IF NOT EXISTS idx_school_year_current ON school_year(is_current) WHERE is_current = 1;

-- Année scolaire courante par défaut
INSERT OR IGNORE INTO school_year (label, start_date, end_date, is_current)
VALUES ('2024-2025', '2024-09-01', '2025-07-31', 1);

-- ============================================================
-- TABLE DES CLASSES
-- ============================================================
CREATE TABLE IF NOT EXISTS class (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                      -- Ex: "6ème A"
    level TEXT NOT NULL,                     -- Ex: "6ème"
    school_year_id INTEGER NOT NULL,
    date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (school_year_id) REFERENCES school_year(id) ON DELETE RESTRICT,
    UNIQUE(name, school_year_id)
);

CREATE INDEX IF NOT EXISTS idx_class_name ON class(name COLLATE NOCASE);

-- Classes par défaut : du 6ème au Tle, séries A et D (rattachées à l'année courante)
INSERT OR IGNORE INTO class (name, level, school_year_id)
SELECT '6ème A', '6ème', id FROM school_year WHERE is_current = 1;
INSERT OR IGNORE INTO class (name, level, school_year_id)
SELECT '6ème D', '6ème', id FROM school_year WHERE is_current = 1;
INSERT OR IGNORE INTO class (name, level, school_year_id)
SELECT '5ème A', '5ème', id FROM school_year WHERE is_current = 1;
INSERT OR IGNORE INTO class (name, level, school_year_id)
SELECT '5ème D', '5ème', id FROM school_year WHERE is_current = 1;
INSERT OR IGNORE INTO class (name, level, school_year_id)
SELECT '4ème A', '4ème', id FROM school_year WHERE is_current = 1;
INSERT OR IGNORE INTO class (name, level, school_year_id)
SELECT '4ème D', '4ème', id FROM school_year WHERE is_current = 1;
INSERT OR IGNORE INTO class (name, level, school_year_id)
SELECT '3ème A', '3ème', id FROM school_year WHERE is_current = 1;
INSERT OR IGNORE INTO class (name, level, school_year_id)
SELECT '3ème D', '3ème', id FROM school_year WHERE is_current = 1;
INSERT OR IGNORE INTO class (name, level, school_year_id)
SELECT '2nde A', '2nde', id FROM school_year WHERE is_current = 1;
INSERT OR IGNORE INTO class (name, level, school_year_id)
SELECT '2nde D', '2nde', id FROM school_year WHERE is_current = 1;
INSERT OR IGNORE INTO class (name, level, school_year_id)
SELECT '1ère A', '1ère', id FROM school_year WHERE is_current = 1;
INSERT OR IGNORE INTO class (name, level, school_year_id)
SELECT '1ère D', '1ère', id FROM school_year WHERE is_current = 1;
INSERT OR IGNORE INTO class (name, level, school_year_id)
SELECT 'Tle A', 'Tle', id FROM school_year WHERE is_current = 1;
INSERT OR IGNORE INTO class (name, level, school_year_id)
SELECT 'Tle D', 'Tle', id FROM school_year WHERE is_current = 1;

-- ============================================================
-- TABLE DES ÉLÈVES
-- ============================================================
CREATE TABLE IF NOT EXISTS student (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    matricule TEXT UNIQUE NOT NULL,          -- Numéro unique d'élève
    last_name TEXT NOT NULL,                 -- Nom de famille
    first_name TEXT NOT NULL,                -- Prénom
    birth_date DATE,                         -- Date de naissance
    class_id INTEGER NOT NULL,               -- FK vers class
    parent_name TEXT,                        -- Nom du parent/tuteur
    parent_phone TEXT,                       -- Téléphone du parent
    parent_email TEXT,                       -- Email du parent
    is_active BOOLEAN DEFAULT 1 CHECK(is_active IN (0, 1)),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (class_id) REFERENCES class(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_student_last_name ON student(last_name COLLATE NOCASE, first_name COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_student_class ON student(class_id);
CREATE INDEX IF NOT EXISTS idx_student_matricule ON student(matricule);

-- ============================================================
-- TABLE DES PLANS DE FRAIS (montants dus par classe/année)
-- ============================================================
CREATE TABLE IF NOT EXISTS fee_plan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id INTEGER NOT NULL,
    school_year_id INTEGER NOT NULL,
    label TEXT NOT NULL,                     -- Ex: "Scolarité", "Cantine"
    amount_int INTEGER NOT NULL CHECK(amount_int > 0),  -- Montant en cents
    due_date DATE,                           -- Date d'échéance
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (class_id) REFERENCES class(id) ON DELETE CASCADE,
    FOREIGN KEY (school_year_id) REFERENCES school_year(id) ON DELETE CASCADE,
    UNIQUE(class_id, school_year_id, label)
);

CREATE INDEX IF NOT EXISTS idx_fee_plan_class ON fee_plan(class_id, school_year_id);

-- Plans de frais par défaut (FCFA par an) : 6ème 50 000, 5ème 55 000,
-- 4ème 60 000, 3ème 65 000, 2nde 75 000, 1ère 85 000, Tle 95 000
INSERT OR IGNORE INTO fee_plan (class_id, school_year_id, label, amount_int, due_date)
SELECT c.id, c.school_year_id, 'Scolarité', 50000, '2025-06-30'
FROM class c WHERE c.level = '6ème';
INSERT OR IGNORE INTO fee_plan (class_id, school_year_id, label, amount_int, due_date)
SELECT c.id, c.school_year_id, 'Scolarité', 55000, '2025-06-30'
FROM class c WHERE c.level = '5ème';
INSERT OR IGNORE INTO fee_plan (class_id, school_year_id, label, amount_int, due_date)
SELECT c.id, c.school_year_id, 'Scolarité', 60000, '2025-06-30'
FROM class c WHERE c.level = '4ème';
INSERT OR IGNORE INTO fee_plan (class_id, school_year_id, label, amount_int, due_date)
SELECT c.id, c.school_year_id, 'Scolarité', 65000, '2025-06-30'
FROM class c WHERE c.level = '3ème';
INSERT OR IGNORE INTO fee_plan (class_id, school_year_id, label, amount_int, due_date)
SELECT c.id, c.school_year_id, 'Scolarité', 75000, '2025-06-30'
FROM class c WHERE c.level = '2nde';
INSERT OR IGNORE INTO fee_plan (class_id, school_year_id, label, amount_int, due_date)
SELECT c.id, c.school_year_id, 'Scolarité', 85000, '2025-06-30'
FROM class c WHERE c.level = '1ère';
INSERT OR IGNORE INTO fee_plan (class_id, school_year_id, label, amount_int, due_date)
SELECT c.id, c.school_year_id, 'Scolarité', 95000, '2025-06-30'
FROM class c WHERE c.level = 'Tle';

-- ============================================================
-- TABLE DES PAIEMENTS
-- ============================================================
CREATE TABLE IF NOT EXISTS payment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    school_year_id INTEGER NOT NULL,
    amount_int INTEGER NOT NULL CHECK(amount_int > 0),  -- Montant en cents
    paid_on DATE NOT NULL,                   -- Date du paiement
    method TEXT NOT NULL CHECK(method IN ('especes', 'cheque', 'virement', 'mobile_money')),
    reference TEXT,                          -- Référence (n° chèque, etc.)
    receipt_no TEXT NOT NULL UNIQUE,         -- Numéro de reçu unique
    status TEXT DEFAULT 'valide' CHECK(status IN ('valide', 'annule')),
    cancel_reason TEXT,                      -- Motif d'annulation
    cancel_date DATE,                        -- Date d'annulation
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE RESTRICT,
    FOREIGN KEY (school_year_id) REFERENCES school_year(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_payment_student ON payment(student_id);
CREATE INDEX IF NOT EXISTS idx_payment_date ON payment(paid_on DESC);
CREATE INDEX IF NOT EXISTS idx_payment_receipt ON payment(receipt_no);

-- ============================================================
-- TABLE DES SNAPSHOTS DE REÇUS (pour ré-impression identique)
-- ============================================================
CREATE TABLE IF NOT EXISTS receipt_snapshot (
    payment_id INTEGER PRIMARY KEY,
    snapshot_json TEXT NOT NULL,             -- Snapshot JSON du reçu figé
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (payment_id) REFERENCES payment(id) ON DELETE CASCADE
);

-- ============================================================
-- TABLE COMPTEUR DE REÇUS (numérotation atomique par année)
-- ============================================================
CREATE TABLE IF NOT EXISTS receipt_counter (
    year INTEGER PRIMARY KEY,                -- Année (ex: 2024)
    last_number INTEGER NOT NULL DEFAULT 0   -- Dernier numéro utilisé
);

-- ============================================================
-- TABLE JOURNAL D'AUDIT (traçabilité des opérations)
-- ============================================================
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,                    -- Création / Modification / Suppression / Annulation
    entity TEXT NOT NULL,                    -- Élève / Paiement / Classe / Année scolaire
    entity_id INTEGER,                       -- Identifiant de l'élément
    entity_label TEXT,                       -- Libellé lisible (nom, n° de reçu…)
    details TEXT,                            -- Détails (motif, anciennes/nouvelles valeurs…)
    user TEXT,                               -- Utilisateur système ayant opéré
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_log(entity, entity_id);

-- Compteurs de reçus pré-initialisés (année scolaire en cours + suivante)
INSERT OR IGNORE INTO receipt_counter (year, last_number) VALUES (2024, 0);
INSERT OR IGNORE INTO receipt_counter (year, last_number) VALUES (2025, 0);
