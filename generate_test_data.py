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
        ("Dubois", "Marie", "6ème D", "Dubois Paul", "0623456789", "solde"),
        ("Bernard", "Pierre", "5ème A", "Bernard Jacques", "0634567890", "solde"),
        ("Petit", "Sophie", "4ème D", "Petit Michel", "0645678901", "solde"),
        ("Robert", "Lucas", "3ème A", "Robert Jean", "0656789012", "solde"),
        ("Richard", "Emma", "2nde A", "Richard Marc", "0667890123", "partiel"),
        ("Durand", "Thomas", "2nde D", "Durand Louis", "0678901234", "partiel"),
        ("Moreau", "Léa", "1ère A", "Moreau André", "0689012345", "partiel"),
        ("Simon", "Hugo", "1ère D", "Simon Philippe", "0690123456", "partiel"),
        ("Michel", "Chloé", "Tle A", "Michel Jean", "0701234567", "partiel"),
        ("Garcia", "Antoine", "Tle D", "Garcia Carlos", "0712345678", "partiel"),
        ("Roux", "Manon", "6ème D", "Roux Nicolas", "0745678901", "non_paye"),
        ("Fournier", "Nathan", "5ème D", "Fournier Olivier", "0756789012", "non_paye"),
        ("Lemoine", "Jade", "4ème A", "Lemoine Sébastien", "0767890123", "non_paye"),
        ("Martinez", "Sarah", "Tle A", "Martinez Juan", "0789012345", "non_paye"),
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
        target = due if status == "solde" else round(due * 0.6 / 500) * 500

        # Fractionner en 1 ou 2 paiements (multiples de 500 FCFA)
        if target <= 30000:
            amounts = [target]
        else:
            first = round(target / 2 / 500) * 500
            amounts = [first, target - first]
        paid = 0
        for j, amount in enumerate(amounts):
            paid_on = (today - timedelta(days=15 * (len(amounts) - 1 - j))) \
                .strftime("%Y-%m-%d")
            method = methods[(nb_payments) % len(methods)]
            try:
                payment_service.create_payment(
                    student_id=s.id, amount_euros=amount,
                    paid_on=paid_on, method=method)
                nb_payments += 1
                paid += amount
            except Exception as e:
                print(f"    ! Paiement refuse : {e}")

        balance = payment_service.balance_service.get_balance(s.id, year.id)
        statut = "Solde" if balance == 0 else "Partiel"
        print(f"    -> {statut} : {paid:,} FCFA payes, reste {balance:,} FCFA"
              .replace(",", " "))

    overview = payment_service.get_overview()
    print("\n=== Résumé ===")
    print(f"Eleves : {overview['nb_students']}")
    print(f"  Soldes          : {overview['nb_paid']}")
    print(f"  Partiels        : {overview['nb_partial']}")
    print(f"  Non payes       : {overview['nb_unpaid']}")
    print(f"Total encaisse   : {overview['total_paid_int']:,} FCFA".replace(",", " "))
    print(f"Total restant du : {overview['total_balance_int']:,} FCFA".replace(",", " "))
    print(f"Paiements crees  : {nb_payments}")
    print("\nDonnees de test generees avec succes !")


if __name__ == "__main__":
    main()
