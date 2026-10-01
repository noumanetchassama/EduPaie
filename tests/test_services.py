"""
Tests de la couche services : élèves, soldes, paiements, reçus.

Chaque test tourne sur une base SQLite temporaire isolée
(variable d'environnement EDUPAIE_DB).
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.data.db import Database  # noqa: E402
from app.services.balance_service import BalanceService  # noqa: E402
from app.services.exceptions import BusinessRuleError, ValidationError  # noqa: E402
from app.services.payment_service import PaymentService  # noqa: E402
from app.services.receipt_service import ReceiptService  # noqa: E402
from app.services.student_service import StudentService  # noqa: E402


@pytest.fixture(scope="module")
def db(tmp_path_factory):
    """Base de données isolée pour ce module de tests."""
    tmp = tmp_path_factory.mktemp("db")
    os.environ["EDUPAIE_DB"] = str(tmp / "test.db")
    Database.reset_instance()
    database = Database()
    database.initialize_schema()
    yield database
    Database.reset_instance()


@pytest.fixture()
def services(db):
    """Services frais, réinitialisés entre les tests."""
    return (
        StudentService(),
        PaymentService(),
        BalanceService(),
    )


def make_student(student_service, name="Dupont", first="Jean", class_name="6ème A"):
    classes = {c.name: c.id for c in student_service.get_all_classes()}
    return student_service.create_student(
        last_name=name, first_name=first, class_id=classes[class_name])


# ======================================================================
# Élèves
# ======================================================================

class TestStudents:
    def test_create_student_auto_matricule(self, services):
        student_service, _, _ = services
        s = make_student(student_service)
        assert s.id > 0
        assert s.matricule  # généré automatiquement

    def test_create_student_duplicate_matricule(self, services):
        student_service, _, _ = services
        s = make_student(student_service, name="Martin")
        with pytest.raises(BusinessRuleError):
            student_service.create_student(
                last_name="Autre", first_name="X",
                class_id=s.class_id, matricule=s.matricule)

    def test_name_validation(self, services):
        student_service, _, _ = services
        classes = {c.name: c.id for c in student_service.get_all_classes()}
        with pytest.raises(ValidationError):
            student_service.create_student(
                last_name="Dup0nt!", first_name="Jean",
                class_id=classes["6ème A"])

    def test_delete_student_with_payments_blocked(self, services):
        student_service, payment_service, _ = services
        s = make_student(student_service, name="Garcia", first="Antoine")
        payment_service.create_payment(
            student_id=s.id, amount_euros=50.0,
            paid_on="2025-06-01", method="especes")
        with pytest.raises(BusinessRuleError):
            student_service.delete_student(s.id)

    def test_delete_student_without_payments(self, services):
        student_service, _, _ = services
        s = make_student(student_service, name="Roux", first="Manon")
        assert student_service.delete_student(s.id) is True


# ======================================================================
# Soldes et statuts
# ======================================================================

class TestBalances:
    def test_status_unpaid_without_payment(self, services):
        student_service, _, balance_service = services
        s = make_student(student_service, name="Petit", first="Sophie")
        year = student_service.get_current_school_year()
        info = balance_service.get_balance_info(s.id, year.id)
        assert info["status"] == "Non payé"  # bug d'origine corrigé
        assert info["total_due_int"] > 0
        assert info["balance_int"] == info["total_due_int"]

    def test_status_partial_then_sold(self, services):
        student_service, payment_service, balance_service = services
        s = make_student(student_service, name="Bernard", first="Pierre")
        year = student_service.get_current_school_year()

        payment_service.create_payment(
            student_id=s.id, amount_euros=100.0,
            paid_on="2025-06-01", method="especes")
        info = balance_service.get_balance_info(s.id, year.id)
        assert info["status"] == "Partiellement payé"

        total_due = info["total_due_int"]
        payment_service.create_payment(
            student_id=s.id, amount_euros=total_due / 100 - 100.0,
            paid_on="2025-06-02", method="cheque")
        info = balance_service.get_balance_info(s.id, year.id)
        assert info["balance_int"] == 0
        assert info["status"] == "Soldé"


# ======================================================================
# Paiements
# ======================================================================

class TestPayments:
    def test_payment_exceeding_balance_refused(self, services):
        student_service, payment_service, _ = services
        s = make_student(student_service, name="Durand", first="Thomas")
        with pytest.raises(BusinessRuleError):
            payment_service.create_payment(
                student_id=s.id, amount_euros=99999.0,
                paid_on="2025-06-01", method="especes")

    def test_negative_or_zero_amount_refused(self, services):
        student_service, payment_service, _ = services
        s = make_student(student_service, name="Moreau", first="Léa")
        for bad in (0.0, -10.0):
            with pytest.raises(ValidationError):
                payment_service.create_payment(
                    student_id=s.id, amount_euros=bad,
                    paid_on="2025-06-01", method="especes")

    def test_future_date_refused(self, services):
        student_service, payment_service, _ = services
        s = make_student(student_service, name="Simon", first="Hugo")
        with pytest.raises(ValidationError):
            payment_service.create_payment(
                student_id=s.id, amount_euros=10.0,
                paid_on="2099-01-01", method="especes")

    def test_invalid_method_refused(self, services):
        student_service, payment_service, _ = services
        s = make_student(student_service, name="Michel", first="Chloé")
        with pytest.raises(ValidationError):
            payment_service.create_payment(
                student_id=s.id, amount_euros=10.0,
                paid_on="2025-06-01", method="crypto")

    def test_receipt_numbers_are_sequential_and_unique(self, services):
        student_service, payment_service, _ = services
        s = make_student(student_service, name="Lemoine", first="Jade")
        p1 = payment_service.create_payment(
            student_id=s.id, amount_euros=10.0,
            paid_on="2025-06-01", method="especes")
        p2 = payment_service.create_payment(
            student_id=s.id, amount_euros=10.0,
            paid_on="2025-06-01", method="especes")
        assert p1.receipt_no != p2.receipt_no
        # Numéros séquentiels REC-AAAA-NNNNNN
        n1 = int(p1.receipt_no.split("-")[-1])
        n2 = int(p2.receipt_no.split("-")[-1])
        assert n2 == n1 + 1

    def test_cancel_payment_restores_balance(self, services):
        student_service, payment_service, balance_service = services
        s = make_student(student_service, name="Fournier", first="Nathan")
        year = student_service.get_current_school_year()
        p = payment_service.create_payment(
            student_id=s.id, amount_euros=50.0,
            paid_on="2025-06-01", method="virement")
        before = balance_service.get_balance(s.id, year.id)
        payment_service.cancel_payment(p.id, "Erreur de saisie")
        after = balance_service.get_balance(s.id, year.id)
        assert after == before + 5000  # solde restauré (+50 €)
        with pytest.raises(BusinessRuleError):
            payment_service.cancel_payment(p.id, "Déjà annulé")

    def test_overview_counts(self, services):
        student_service, payment_service, _ = services
        overview = payment_service.get_overview()
        assert overview["nb_students"] >= 1
        assert overview["total_paid_int"] > 0
        assert overview["nb_paid"] + overview["nb_partial"] \
            + overview["nb_unpaid"] == overview["nb_students"]


# ======================================================================
# Reçus (PDF)
# ======================================================================

class TestReceipts:
    def test_generate_pdf_from_snapshot(self, services, tmp_path):
        student_service, payment_service, _ = services
        s = make_student(student_service, name="Martinez", first="Sarah")
        p = payment_service.create_payment(
            student_id=s.id, amount_euros=75.0,
            paid_on="2025-06-01", method="cheque")

        receipt_service = ReceiptService(payment_service=payment_service)
        out = tmp_path / "recu_test.pdf"
        path = receipt_service.generate_receipt_pdf(p, output_path=str(out))
        assert Path(path).exists()
        assert Path(path).stat().st_size > 1000
        # Un PDF commence par %PDF
        assert Path(path).read_bytes()[:4] == b"%PDF"

    def test_snapshot_immutable_after_new_payment(self, services):
        """Le snapshot d'un reçu ne change pas après d'autres paiements."""
        student_service, payment_service, _ = services
        s = make_student(student_service, name="Lopez", first="Enzo")
        p1 = payment_service.create_payment(
            student_id=s.id, amount_euros=30.0,
            paid_on="2025-06-01", method="especes")
        snap1 = payment_service.get_payment_snapshot(p1.id)

        payment_service.create_payment(
            student_id=s.id, amount_euros=30.0,
            paid_on="2025-06-02", method="especes")

        snap1_again = payment_service.get_payment_snapshot(p1.id)
        assert snap1 == snap1_again
        assert "Solde restant" in snap1["balance"]["after_formatted"] or \
            snap1["balance"]["after_euros"] >= 0
