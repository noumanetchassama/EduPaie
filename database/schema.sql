-- Schéma de la base de données EduPaie

-- Table élèves
CREATE TABLE IF NOT EXISTS eleves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    prenom TEXT NOT NULL,
    classe TEXT NOT NULL,
    annee_scolaire TEXT NOT NULL,
    montant_du REAL NOT NULL,
    date_creation DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Table paiements
CREATE TABLE IF NOT EXISTS paiements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    eleve_id INTEGER NOT NULL,
    montant REAL NOT NULL,
    date_paiement DATETIME NOT NULL,
    mode_paiement TEXT NOT NULL,
    numero_recu TEXT NOT NULL UNIQUE,
    FOREIGN KEY (eleve_id) REFERENCES eleves(id)
);

-- Index pour optimiser les recherches
CREATE INDEX IF NOT EXISTS idx_eleves_classe ON eleves(classe);
CREATE INDEX IF NOT EXISTS idx_paiements_eleve ON paiements(eleve_id);
CREATE INDEX IF NOT EXISTS idx_paiements_date ON paiements(date_paiement);
