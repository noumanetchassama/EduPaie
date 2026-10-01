"""
Script de génération de données de seed pour EduPaie

Crée une base de données avec :
- 1 année scolaire courante
- 5 classes
- 20 élèves avec des paiements variés (soldés, partiels, non payés)
- Plans de frais par classe
- Paiements avec numéros de reçus

La DB générée est prête à être embarquée dans l'exécutable.
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Chemin de la DB seed à générer
SEED_DB_PATH = Path(__file__).parent / 'edupaie_seed.db'


def create_seed_database():
    """Crée la base de données seed avec toutes les données"""

    # Supprimer la DB existante si elle existe
    if SEED_DB_PATH.exists():
        SEED_DB_PATH.unlink()
        print(f"[OK] DB existante supprimee : {SEED_DB_PATH}")

    # Créer la DB
    conn = sqlite3.connect(str(SEED_DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Activer les foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")

    print("Creation du schema...")

    # Lire et exécuter le schéma
    schema_path = Path(__file__).parent.parent / 'app' / 'data' / 'schema.sql'
    if not schema_path.exists():
        print(f"[ERREUR] Schema introuvable : {schema_path}")
        sys.exit(1)

    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    cursor.executescript(schema_sql)
    conn.commit()

    print("[OK] Schema cree")

    # ========================================
    # DONNÉES DE TEST
    # ========================================

    print("\nGénération des données de test...")

    # Année scolaire (déjà créée par le schéma)
    cursor.execute("SELECT id FROM school_year WHERE is_current = 1")
    school_year = cursor.fetchone()
    school_year_id = school_year['id']
    print(f"[OK] Année scolaire courante : ID {school_year_id}")

    # Classes
    classes_data = [
        ("6ème A", "6ème"),
        ("6ème B", "6ème"),
        ("5ème A", "5ème"),
        ("4ème A", "4ème"),
        ("3ème A", "3ème"),
    ]

    class_ids = {}
    for name, level in classes_data:
        cursor.execute(
            "INSERT INTO class (name, level, school_year_id) VALUES (?, ?, ?)",
            (name, level, school_year_id)
        )
        class_id = cursor.lastrowid
        class_ids[name] = class_id
        print(f"[OK] Classe creee : {name} (ID: {class_id})")

    # Plans de frais par classe (en cents)
    # 6ème : 500€, 5ème : 550€, 4ème : 600€, 3ème : 650€
    fee_plans = [
        ("6ème A", "Scolarité", 50000),
        ("6ème B", "Scolarité", 50000),
        ("5ème A", "Scolarité", 55000),
        ("4ème A", "Scolarité", 60000),
        ("3ème A", "Scolarité", 65000),
    ]

    for class_name, label, amount_int in fee_plans:
        cursor.execute(
            """
            INSERT INTO fee_plan (class_id, school_year_id, label, amount_int, due_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (class_ids[class_name], school_year_id, label, amount_int, "2024-09-30")
        )
        print(f"[OK] Plan de frais : {class_name} - {label} ({amount_int/100:.0f}€)")

    # Élèves (20 élèves)
    students_data = [
        # Élèves soldés (5)
        ("MAT001", "Martin", "Jean", "6ème A", "2012-05-15", "Martin Pierre", "0612345678", "martin.pere@email.com", "solde"),
        ("MAT002", "Dubois", "Marie", "6ème A", "2012-08-20", "Dubois Paul", "0623456789", "dubois.paul@email.com", "solde"),
        ("MAT003", "Bernard", "Pierre", "5ème A", "2011-03-10", "Bernard Jacques", "0634567890", "bernard.jacques@email.com", "solde"),
        ("MAT004", "Petit", "Sophie", "4ème A", "2010-11-25", "Petit Michel", "0645678901", "petit.michel@email.com", "solde"),
        ("MAT005", "Robert", "Lucas", "3ème A", "2009-07-08", "Robert Jean", "0656789012", "robert.jean@email.com", "solde"),

        # Élèves partiellement payés (8)
        ("MAT006", "Richard", "Emma", "6ème B", "2012-02-14", "Richard Marc", "0667890123", "richard.marc@email.com", "partiel"),
        ("MAT007", "Durand", "Thomas", "6ème B", "2012-09-30", "Durand Louis", "0678901234", "durand.louis@email.com", "partiel"),
        ("MAT008", "Moreau", "Léa", "5ème A", "2011-06-18", "Moreau André", "0689012345", "moreau.andre@email.com", "partiel"),
        ("MAT009", "Simon", "Hugo", "4ème A", "2010-04-05", "Simon Philippe", "0690123456", "simon.philippe@email.com", "partiel"),
        ("MAT010", "Michel", "Chloé", "3ème A", "2009-12-22", "Michel Jean", "0701234567", "michel.jean@email.com", "partiel"),
        ("MAT011", "Garcia", "Antoine", "6ème A", "2012-01-08", "Garcia Carlos", "0712345678", "garcia.carlos@email.com", "partiel"),
        ("MAT012", "David", "Camille", "5ème A", "2011-10-17", "David Alain", "0723456789", "david.alain@email.com", "partiel"),
        ("MAT013", "Bertrand", "Maxime", "4ème A", "2010-05-29", "Bertrand François", "0734567890", "bertrand.francois@email.com", "partiel"),

        # Élèves non payés (7)
        ("MAT014", "Roux", "Manon", "6ème B", "2012-07-03", "Roux Nicolas", "0745678901", "roux.nicolas@email.com", "non_paye"),
        ("MAT015", "Fournier", "Nathan", "5ème A", "2011-02-11", "Fournier Olivier", "0756789012", "fournier.olivier@email.com", "non_paye"),
        ("MAT016", "Lemoine", "Jade", "4ème A", "2010-08-19", "Lemoine Sébastien", "0767890123", "lemoine.sebastien@email.com", "non_paye"),
        ("MAT017", "Garcia", "Louis", "3ème A", "2009-03-27", "Garcia Manuel", "0778901234", "garcia.manuel@email.com", "non_paye"),
        ("MAT018", "Martinez", "Sarah", "6ème A", "2012-11-12", "Martinez Juan", "0789012345", "martinez.juan@email.com", "non_paye"),
        ("MAT019", "Lopez", "Enzo", "5ème A", "2011-06-05", "Lopez Pedro", "0790123456", "lopez.pedro@email.com", "non_paye"),
        ("MAT020", "Sanchez", "Lina", "4ème A", "2010-09-24", "Sanchez Carlos", "0801234567", "sanchez.carlos@email.com", "non_paye"),
    ]

    student_ids = {}
    payment_counter = 1

    for matricule, last_name, first_name, class_name, birth_date, parent_name, parent_phone, parent_email, status in students_data:
        # Créer l'élève
        cursor.execute(
            """
            INSERT INTO student (
                matricule, last_name, first_name, birth_date,
                class_id, parent_name, parent_phone, parent_email, is_active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (matricule, last_name, first_name, birth_date,
             class_ids[class_name], parent_name, parent_phone, parent_email)
        )
        student_id = cursor.lastrowid
        student_ids[matricule] = student_id

        # Récupérer le montant dû pour cette classe
        cursor.execute(
            """
            SELECT amount_int FROM fee_plan
            WHERE class_id = ? AND school_year_id = ?
            """,
            (class_ids[class_name], school_year_id)
        )
        fee = cursor.fetchone()
        amount_due = fee['amount_int'] if fee else 50000

        # Créer les paiements selon le statut
        if status == "solde":
            # Payer tout en 1 ou 2 fois
            nb_paiements = 2 if amount_due > 55000 else 1
            amount_per_payment = amount_due // nb_paiements

            for i in range(nb_paiements):
                date_paiement = (datetime.now() - timedelta(days=30*i)).strftime("%Y-%m-%d")
                mode = ['especes', 'cheque', 'virement', 'mobile_money'][i % 4]

                receipt_no = f"REC-2024-{payment_counter:06d}"
                cursor.execute(
                    """
                    INSERT INTO payment (
                        student_id, school_year_id, amount_int, paid_on,
                        method, receipt_no, status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, 'valide')
                    """,
                    (student_id, school_year_id, amount_per_payment, date_paiement, mode, receipt_no)
                )

                # Snapshot
                snapshot = {
                    'receipt_no': receipt_no,
                    'student_name': f"{last_name} {first_name}",
                    'class': class_name,
                    'amount': amount_per_payment / 100,
                    'date': date_paiement,
                    'method': mode
                }
                cursor.execute(
                    "INSERT INTO receipt_snapshot (payment_id, snapshot_json) VALUES (?, ?)",
                    (cursor.lastrowid, str(snapshot))
                )

                payment_counter += 1

            print(f"  Élève {last_name} {first_name} : Soldé ({nb_paiements} paiements)")

        elif status == "partiel":
            # Payer 50-70%
            pourcentage = 0.5 + (hash(matricule) % 3) * 0.1
            amount_paid = int(amount_due * pourcentage)

            nb_paiements = 2
            amount_per_payment = amount_paid // nb_paiements

            for i in range(nb_paiements):
                date_paiement = (datetime.now() - timedelta(days=15*i)).strftime("%Y-%m-%d")
                mode = ['especes', 'cheque', 'virement', 'mobile_money'][i % 4]

                receipt_no = f"REC-2024-{payment_counter:06d}"
                cursor.execute(
                    """
                    INSERT INTO payment (
                        student_id, school_year_id, amount_int, paid_on,
                        method, receipt_no, status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, 'valide')
                    """,
                    (student_id, school_year_id, amount_per_payment, date_paiement, mode, receipt_no)
                )

                payment_counter += 1

            print(f"  Élève {last_name} {first_name} : Partiel ({amount_paid/100:.0f}€/{amount_due/100:.0f}€)")

        else:  # non_paye
            print(f"  Élève {last_name} {first_name} : Non payé")

    # Mettre à jour le compteur de reçus
    cursor.execute(
        "UPDATE receipt_counter SET last_number = ? WHERE year = 2024",
        (payment_counter - 1,)
    )

    conn.commit()
    conn.close()

    print(f"\n[OK] Base de données seed créée : {SEED_DB_PATH}")
    print(f"[OK] {len(students_data)} élèves créés")
    print(f"[OK] {payment_counter - 1} paiements créés")


if __name__ == "__main__":
    create_seed_database()
