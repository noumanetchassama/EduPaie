"""
Génération de données de test pour EduPaie

Utilise la nouvelle architecture (app/) : les paiements passent par les
services réels, avec numéros de reçus et snapshots générés comme en
production. Lancez :  python generate_test_data.py
"""

import io
import os
import sys
from pathlib import Path

# Console Windows (cp1252) : éviter les UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Base de travail locale au projet (pas celle de l'utilisateur)
os.environ["EDUPAIE_DB"] = str(Path(__file__).parent / "database" / "edupaie.db")

sys.path.insert(0, str(Path(__file__).parent))

from app.data.db import Database  # noqa: E402
from app.services.payment_service import PaymentService  # noqa: E402
from app.services.student_service import StudentService  # noqa: E402


def main():
    db = Database()
    db.initialize_schema()

    student_service = StudentService()
    payment_service = PaymentService()

    year = student_service.get_current_school_year()
    classes = {c.name: c.id for c in student_service.get_all_classes()}
    if not classes:
        print("Aucune classe définie ; lancez d'abord le schéma (main.py).")
        sys.exit(1)

    # Élèves existants ? on ne duplique pas
    existing = student_service.get_all_students()
    if existing:
        print(f"La base contient déjà {len(existing)} élève(s). "
              "Supprimez database/edupaie.db pour régénérer un jeu complet.")
        return

    # (nom, prénom, classe, parent, téléphone, statut)
    students = [
        ("Martin", "Jean", "6ème A", "Martin Pierre", "0612345678", "solde"),
        ("Dubois", "Marie", "6ème A", "Dubois Paul", "0623456789", "solde"),
        ("Bernard", "Pierre", "5ème A", "Bernard Jacques", "0634567890", "solde"),
        ("Petit", "Sophie", "4ème A", "Petit Michel", "0645678901", "solde"),
        ("Robert", "Lucas", "3ème A", "Robert Jean", "0656789012", "solde"),
        ("Richard", "Emma", "6ème B", "Richard Marc", "0667890123", "partiel"),
        ("Durand", "Thomas", "6ème B", "Durand Louis", "0678901234", "partiel"),
        ("Moreau", "Léa", "5ème A", "Moreau André", "0689012345", "partiel"),
        ("Simon", "Hugo", "4ème A", "Simon Philippe", "0690123456", "partiel"),
        ("Michel", "Chloé", "3ème A", "Michel Jean", "0701234567", "partiel"),
        ("Garcia", "Antoine", "6ème A", "Garcia Carlos", "0712345678", "partiel"),
        ("Roux", "Manon", "6ème B", "Roux Nicolas", "0745678901", "non_paye"),
        ("Fournier", "Nathan", "5ème A", "Fournier Olivier", "0756789012", "non_paye"),
        ("Lemoine", "Jade", "4ème A", "Lemoine Sébastien", "0767890123", "non_paye"),
        ("Martinez", "Sarah", "6ème A", "Martinez Juan", "0789012345", "non_paye"),
    ]

    from datetime import date, timedelta

    today = date.today()
    methods = PaymentService.MODES_PAIEMENT
    nb_payments = 0

    for i, (last, first, class_name, parent, phone, status) in enumerate(students, 1):
        s = student_service.create_student(
            last_name=last, first_name=first,
            class_id=classes[class_name],
            parent_name=parent, parent_phone=phone,
        )
        print(f"{i:02d}. Eleve cree : {first} {last} ({class_name}) "
              f"[{s.matricule}]")

        if status == "non_paye":
            continue

        info = payment_service.balance_service.get_balance_info(s.id, year.id)
        due = info["total_due_int"]
        target = due if status == "solde" else int(due * 0.6)

        # Fractionner en 1 ou 2 paiements
        amounts = [target] if target <= 30000 else [target // 2, target - target // 2]
        paid = 0
        for j, amount_euros in enumerate(amounts):
            amount = amount_euros / 100
            paid_on = (today - timedelta(days=15 * (len(amounts) - 1 - j))) \
                .strftime("%Y-%m-%d")
            method = methods[(nb_payments) % len(methods)]
            try:
                payment_service.create_payment(
                    student_id=s.id, amount_euros=amount,
                    paid_on=paid_on, method=method)
                nb_payments += 1
                paid += amount_euros
            except Exception as e:
                print(f"    ! Paiement refusé : {e}")

        balance = payment_service.balance_service.get_balance(s.id, year.id)
        statut = "Solde" if balance == 0 else "Partiel"
        print(f"    -> {statut} : {paid / 100:.2f} EUR payes, "
              f"reste {balance / 100:.2f} EUR")

    overview = payment_service.get_overview()
    print("\n=== Résumé ===")
    print(f"Eleves : {overview['nb_students']}")
    print(f"  Soldes          : {overview['nb_paid']}")
    print(f"  Partiels        : {overview['nb_partial']}")
    print(f"  Non payes       : {overview['nb_unpaid']}")
    print(f"Total encaisse   : {overview['total_paid_int'] / 100:.2f} EUR")
    print(f"Total restant du : {overview['total_balance_int'] / 100:.2f} EUR")
    print(f"Paiements crees  : {nb_payments}")
    print("\nDonnees de test generees avec succes !")


if __name__ == "__main__":
    main()
