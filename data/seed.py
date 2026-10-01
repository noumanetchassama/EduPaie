"""
Script de génération de la base de données seed pour EduPaie

Crée data/edupaie_seed.db (embarquée dans l'exécutable) avec :
- 1 année scolaire courante
- 5 classes avec plans de frais
- 20 élèves avec des paiements variés (soldés, partiels, non payés)
- Paiements avec numéros de reçus et snapshots JSON conformes
  (mêmes clés que PaymentService._build_receipt_snapshot)
"""

import json
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

SEED_DB_PATH = Path(__file__).parent / "edupaie_seed.db"

SCHOOL = {
    "name": "Groupe Scolaire Exemple",
    "address": "123 Rue de l'École",
    "phone": "01 23 45 67 89",
    "email": "contact@ecole-exemple.fr",
}

# (nom, niveau, frais annuels en cents)
CLASSES = [
    ("6ème A", "6ème", 50000),
    ("6ème B", "6ème", 50000),
    ("5ème A", "5ème", 55000),
    ("4ème A", "4ème", 60000),
    ("3ème A", "3ème", 65000),
]

# (matricule, nom, prénom, classe, naissance, parent, tel, email, statut)
STUDENTS = [
    ("MAT001", "Martin", "Jean", "6ème A", "2012-05-15", "Martin Pierre", "0612345678", "martin.pere@email.com", "solde"),
    ("MAT002", "Dubois", "Marie", "6ème A", "2012-08-20", "Dubois Paul", "0623456789", "dubois.paul@email.com", "solde"),
    ("MAT003", "Bernard", "Pierre", "5ème A", "2011-03-10", "Bernard Jacques", "0634567890", "bernard.jacques@email.com", "solde"),
    ("MAT004", "Petit", "Sophie", "4ème A", "2010-11-25", "Petit Michel", "0645678901", "petit.michel@email.com", "solde"),
    ("MAT005", "Robert", "Lucas", "3ème A", "2009-07-08", "Robert Jean", "0656789012", "robert.jean@email.com", "solde"),
    ("MAT006", "Richard", "Emma", "6ème B", "2012-02-14", "Richard Marc", "0667890123", "richard.marc@email.com", "partiel"),
    ("MAT007", "Durand", "Thomas", "6ème B", "2012-09-30", "Durand Louis", "0678901234", "durand.louis@email.com", "partiel"),
    ("MAT008", "Moreau", "Léa", "5ème A", "2011-06-18", "Moreau André", "0689012345", "moreau.andre@email.com", "partiel"),
    ("MAT009", "Simon", "Hugo", "4ème A", "2010-04-05", "Simon Philippe", "0690123456", "simon.philippe@email.com", "partiel"),
    ("MAT010", "Michel", "Chloé", "3ème A", "2009-12-22", "Michel Jean", "0701234567", "michel.jean@email.com", "partiel"),
    ("MAT011", "Garcia", "Antoine", "6ème A", "2012-01-08", "Garcia Carlos", "0712345678", "garcia.carlos@email.com", "partiel"),
    ("MAT012", "David", "Camille", "5ème A", "2011-10-17", "David Alain", "0723456789", "david.alain@email.com", "partiel"),
    ("MAT013", "Bertrand", "Maxime", "4ème A", "2010-05-29", "Bertrand François", "0734567890", "bertrand.francois@email.com", "partiel"),
    ("MAT014", "Roux", "Manon", "6ème B", "2012-07-03", "Roux Nicolas", "0745678901", "roux.nicolas@email.com", "non_paye"),
    ("MAT015", "Fournier", "Nathan", "5ème A", "2011-02-11", "Fournier Olivier", "0756789012", "fournier.olivier@email.com", "non_paye"),
    ("MAT016", "Lemoine", "Jade", "4ème A", "2010-08-19", "Lemoine Sébastien", "0767890123", "lemoine.sebastien@email.com", "non_paye"),
    ("MAT017", "Garcia", "Louis", "3ème A", "2009-03-27", "Garcia Manuel", "0778901234", "garcia.manuel@email.com", "non_paye"),
    ("MAT018", "Martinez", "Sarah", "6ème A", "2012-11-12", "Martinez Juan", "0789012345", "martinez.juan@email.com", "non_paye"),
    ("MAT019", "Lopez", "Enzo", "5ème A", "2011-06-05", "Lopez Pedro", "0790123456", "lopez.pedro@email.com", "non_paye"),
    ("MAT020", "Sanchez", "Lina", "4ème A", "2010-09-24", "Sanchez Carlos", "0801234567", "sanchez.carlos@email.com", "non_paye"),
]

METHODS = ["especes", "cheque", "virement", "mobile_money"]
METHOD_LABELS = {
    "especes": "Espèces", "cheque": "Chèque",
    "virement": "Virement", "mobile_money": "Mobile Money",
}


def fmt(cents: int) -> str:
    return f"{cents / 100:,.2f}".replace(",", " ").replace(".", ",") + " €"


def make_snapshot(receipt_no, paid_on, method, matricule, last_name, first_name,
                  class_name, year_label, amount_int, balance_before):
    """Snapshot identique en structure à celui de PaymentService."""
    balance_after = balance_before - amount_int
    return {
        "receipt_no": receipt_no,
        "receipt_date": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "school": dict(SCHOOL),
        "student": {
            "matricule": matricule,
            "last_name": last_name,
            "first_name": first_name,
            "class": class_name,
            "school_year": year_label,
        },
        "payment": {
            "amount_euros": amount_int / 100,
            "amount_formatted": fmt(amount_int),
            "paid_on": paid_on,
            "method": METHOD_LABELS.get(method, method),
            "reference": None,
        },
        "balance": {
            "before_euros": balance_before / 100,
            "before_formatted": fmt(balance_before),
            "after_euros": balance_after / 100,
            "after_formatted": fmt(balance_after),
        },
    }


def create_seed_database():
    """Crée la base de données seed complète."""
    if SEED_DB_PATH.exists():
        SEED_DB_PATH.unlink()
        print(f"[OK] DB existante supprimée : {SEED_DB_PATH}")

    conn = sqlite3.connect(str(SEED_DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")

    schema_path = Path(__file__).parent.parent / "app" / "data" / "schema.sql"
    if not schema_path.exists():
        print(f"[ERREUR] Schéma introuvable : {schema_path}")
        sys.exit(1)
    with open(schema_path, "r", encoding="utf-8") as f:
        cursor.executescript(f.read())
    conn.commit()
    print("[OK] Schéma créé")

    cursor.execute("SELECT id, label FROM school_year WHERE is_current = 1")
    year = cursor.fetchone()
    school_year_id = year["id"]
    year_label = year["label"]
    print(f"[OK] Année scolaire courante : {year_label} (ID {school_year_id})")

    # Classes + plans de frais (le schéma crée déjà des classes par défaut :
    # on les réutilise si elles existent, et on force les montants de démo)
    class_ids = {}
    for name, level, amount_int in CLASSES:
        cursor.execute(
            "SELECT id FROM class WHERE name = ? AND school_year_id = ?",
            (name, school_year_id),
        )
        row = cursor.fetchone()
        if row:
            class_ids[name] = row["id"]
        else:
            cursor.execute(
                "INSERT INTO class (name, level, school_year_id) VALUES (?, ?, ?)",
                (name, level, school_year_id),
            )
            class_ids[name] = cursor.lastrowid

        cursor.execute(
            "SELECT id FROM fee_plan WHERE class_id = ? AND school_year_id = ? "
            "AND label = 'Scolarité'",
            (class_ids[name], school_year_id),
        )
        fee_row = cursor.fetchone()
        if fee_row:
            cursor.execute(
                "UPDATE fee_plan SET amount_int = ? WHERE id = ?",
                (amount_int, fee_row["id"]),
            )
        else:
            cursor.execute(
                """
                INSERT INTO fee_plan (class_id, school_year_id, label, amount_int, due_date)
                VALUES (?, ?, 'Scolarité', ?, '2025-06-30')
                """,
                (class_ids[name], school_year_id, amount_int),
            )
    conn.commit()
    print(f"[OK] {len(CLASSES)} classes avec plans de frais")

    # Année du numéro de reçu : première année du libellé
    receipt_year = int(year_label[:4])
    cursor.execute(
        "INSERT OR IGNORE INTO receipt_counter (year, last_number) VALUES (?, 0)",
        (receipt_year,),
    )

    payment_counter = 0
    nb_payments = 0

    for matricule, last_name, first_name, class_name, birth, parent, phone, email, status in STUDENTS:
        cursor.execute(
            """
            INSERT INTO student (
                matricule, last_name, first_name, birth_date,
                class_id, parent_name, parent_phone, parent_email, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (matricule, last_name, first_name, birth,
             class_ids[class_name], parent, phone, email),
        )
        student_id = cursor.lastrowid

        cursor.execute(
            "SELECT amount_int FROM fee_plan WHERE class_id = ? AND school_year_id = ?",
            (class_ids[class_name], school_year_id),
        )
        amount_due = cursor.fetchone()["amount_int"]
        balance = amount_due

        payments_plan = []
        if status == "solde":
            # 1 ou 2 paiements couvrant la totalité
            if amount_due >= 60000:
                first = amount_due // 2
                payments_plan = [first, amount_due - first]
            else:
                payments_plan = [amount_due]
        elif status == "partiel":
            total = int(amount_due * (0.5 + (abs(hash(matricule)) % 3) * 0.1))
            first = total // 2
            payments_plan = [first, total - first]

        for i, amount_int in enumerate(payments_plan):
            payment_counter += 1
            receipt_no = f"REC-{receipt_year}-{payment_counter:06d}"
            paid_on = (datetime.now() - timedelta(days=30 * (len(payments_plan) - 1 - i))) \
                .strftime("%Y-%m-%d")
            method = METHODS[(payment_counter - 1) % len(METHODS)]
            balance_before = balance
            balance -= amount_int

            cursor.execute(
                """
                INSERT INTO payment (
                    student_id, school_year_id, amount_int, paid_on,
                    method, receipt_no, status
                ) VALUES (?, ?, ?, ?, ?, ?, 'valide')
                """,
                (student_id, school_year_id, amount_int, paid_on,
                 method, receipt_no),
            )
            payment_id = cursor.lastrowid

            snapshot = make_snapshot(
                receipt_no, paid_on, method, matricule, last_name, first_name,
                class_name, year_label, amount_int, balance_before)
            cursor.execute(
                "INSERT INTO receipt_snapshot (payment_id, snapshot_json) VALUES (?, ?)",
                (payment_id, json.dumps(snapshot, ensure_ascii=False)),
            )
            nb_payments += 1

        label = {"solde": "Soldé", "partiel": "Partiel", "non_paye": "Non payé"}[status]
        print(f"  {last_name} {first_name} ({class_name}) : {label}")

    cursor.execute(
        "UPDATE receipt_counter SET last_number = ? WHERE year = ?",
        (payment_counter, receipt_year),
    )

    conn.commit()
    conn.close()

    print(f"\n[OK] Base seed créée : {SEED_DB_PATH}")
    print(f"[OK] {len(STUDENTS)} élèves, {nb_payments} paiements")


if __name__ == "__main__":
    create_seed_database()
