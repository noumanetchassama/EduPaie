"""
Tests de la couche services : élèves, soldes, paiements, reçus.

Chaque test tourne sur une base SQLite temporaire isolée
(variable d'environnement EDUPAIE_DB).
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.data.db import Database  # noqa: E402
from app.data.repositories.audit_repository import AuditRepository  # noqa: E402
from app.services.balance_service import BalanceService  # noqa: E402
from app.services.class_service import ClassService  # noqa: E402
from app.services.exceptions import BusinessRuleError, NotFoundError, ValidationError  # noqa: E402
from app.services.payment_service import PaymentService  # noqa: E402
from app.services.receipt_service import ReceiptService  # noqa: E402
from app.services.school_year_service import SchoolYearService  # noqa: E402
from app.services.student_service import StudentService  # noqa: E402


@pytest.fixture(scope="module")
def db(tmp_path_factory):
    """Base de données isolée pour ce module de tests.

    Le chemin est passé EXPLICITEMENT au singleton : la variable
    d'environnement EDUPAIE_DB est lue par app.config à l'import, donc
    définie trop tard pour les tests.
    """
    tmp = tmp_path_factory.mktemp("db")
    Database.reset_instance()
    database = Database(str(tmp / "test.db"))
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
            student_id=s.id, amount_euros=5000,
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
            student_id=s.id, amount_euros=10000,
            paid_on="2025-06-01", method="especes")
        info = balance_service.get_balance_info(s.id, year.id)
        assert info["status"] == "Partiellement payé"

        total_due = info["total_due_int"]
        payment_service.create_payment(
            student_id=s.id, amount_euros=total_due - 10000,
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
                student_id=s.id, amount_euros=9999999,
                paid_on="2025-06-01", method="especes")

    def test_negative_or_zero_amount_refused(self, services):
        student_service, payment_service, _ = services
        s = make_student(student_service, name="Moreau", first="Léa")
        for bad in (0, -10):
            with pytest.raises(ValidationError):
                payment_service.create_payment(
                    student_id=s.id, amount_euros=bad,
                    paid_on="2025-06-01", method="especes")

    def test_future_date_refused(self, services):
        student_service, payment_service, _ = services
        s = make_student(student_service, name="Simon", first="Hugo")
        with pytest.raises(ValidationError):
            payment_service.create_payment(
                student_id=s.id, amount_euros=10,
                paid_on="2099-01-01", method="especes")

    def test_invalid_method_refused(self, services):
        student_service, payment_service, _ = services
        s = make_student(student_service, name="Michel", first="Chloé")
        with pytest.raises(ValidationError):
            payment_service.create_payment(
                student_id=s.id, amount_euros=10,
                paid_on="2025-06-01", method="crypto")

    def test_receipt_numbers_are_sequential_and_unique(self, services):
        student_service, payment_service, _ = services
        s = make_student(student_service, name="Lemoine", first="Jade")
        p1 = payment_service.create_payment(
            student_id=s.id, amount_euros=10000,
            paid_on="2025-06-01", method="especes")
        p2 = payment_service.create_payment(
            student_id=s.id, amount_euros=10000,
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
            student_id=s.id, amount_euros=50000,
            paid_on="2025-06-01", method="virement")
        before = balance_service.get_balance(s.id, year.id)
        payment_service.cancel_payment(p.id, "Erreur de saisie")
        after = balance_service.get_balance(s.id, year.id)
        assert after == before + 50000  # solde restauré (+50 000 FCFA)
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
            student_id=s.id, amount_euros=20000,
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
            student_id=s.id, amount_euros=20000,
            paid_on="2025-06-01", method="especes")
        snap1 = payment_service.get_payment_snapshot(p1.id)

        payment_service.create_payment(
            student_id=s.id, amount_euros=10000,
            paid_on="2025-06-02", method="especes")

        snap1_again = payment_service.get_payment_snapshot(p1.id)
        assert snap1 == snap1_again
        assert "FCFA" in snap1["balance"]["after_formatted"]
        assert snap1["balance"]["after_int"] >= 0

    def test_update_payment_amount_and_balance(self, services):
        """Modification d'un paiement : solde et snapshot recalculés."""
        student_service, payment_service, balance_service = services
        s = make_student(student_service, name="David", first="Camille")
        year = student_service.get_current_school_year()
        p = payment_service.create_payment(
            student_id=s.id, amount_euros=10000,
            paid_on="2025-06-01", method="especes")

        payment_service.update_payment(
            payment_id=p.id, amount_euros=20000,
            paid_on="2025-06-05", method="cheque", reference="CHQ-77")

        updated = payment_service.get_payment(p.id)
        assert updated.amount_int == 20000
        assert updated.method == "cheque"
        assert updated.receipt_no == p.receipt_no  # numéro conservé
        assert balance_service.get_total_paid(s.id, year.id) == 20000

        snap = payment_service.get_payment_snapshot(p.id)
        assert snap["payment"]["amount_int"] == 20000  # snapshot régénéré

    def test_update_payment_exceeding_balance_refused(self, services):
        """La modification ne doit pas rendre le solde négatif."""
        student_service, payment_service, _ = services
        s = make_student(student_service, name="Bertrand", first="Maxime")
        p = payment_service.create_payment(
            student_id=s.id, amount_euros=10000,
            paid_on="2025-06-01", method="especes")
        with pytest.raises(BusinessRuleError):
            payment_service.update_payment(
                payment_id=p.id, amount_euros=9999999,
                paid_on="2025-06-02", method="especes")

    def test_delete_payment_removes_it(self, services):
        """Suppression définitive d'un paiement."""
        student_service, payment_service, _ = services
        s = make_student(student_service, name="Sanchez", first="Lina")
        p = payment_service.create_payment(
            student_id=s.id, amount_euros=10000,
            paid_on="2025-06-01", method="especes")
        assert payment_service.delete_payment(p.id) is True
        assert payment_service.get_payment(p.id) is None
        with pytest.raises(NotFoundError):
            payment_service.delete_payment(p.id)


# ======================================================================
# Classes (CRUD + frais)
# ======================================================================

class TestClasses:
    def test_create_class_with_fee(self, services):
        student_service, _, _ = services
        class_service = ClassService(student_service=student_service)
        c = class_service.create_class("6ème C", "6ème", 52000)
        info = class_service.get_class(c.id)
        assert info["class"].name == "6ème C"
        assert info["fee_int"] == 52000

    def test_create_duplicate_class_refused(self, services):
        student_service, _, _ = services
        class_service = ClassService(student_service=student_service)
        class_service.create_class("5ème Z", "5ème", 55000)
        with pytest.raises(BusinessRuleError):
            class_service.create_class("5ème Z", "5ème", 60000)

    def test_update_class_fee_applies_to_students(self, services):
        """Modifier les frais d'une classe recalcule les soldes des élèves."""
        student_service, _, balance_service = services
        class_service = ClassService(student_service=student_service)
        c = class_service.create_class("4ème Z", "4ème", 60000)
        s = student_service.create_student(
            last_name="Test", first_name="Frais", class_id=c.id)
        year = student_service.get_current_school_year()

        class_service.update_class(c.id, "4ème Z bis", "4ème", 65000)
        info = balance_service.get_balance_info(s.id, year.id)
        assert info["total_due_int"] == 65000

    def test_delete_class_with_students_refused(self, services):
        student_service, _, _ = services
        class_service = ClassService(student_service=student_service)
        c = class_service.create_class("3ème Z", "3ème", 65000)
        student_service.create_student(
            last_name="Test", first_name="Classe", class_id=c.id)
        with pytest.raises(BusinessRuleError):
            class_service.delete_class(c.id)

    def test_delete_empty_class(self, services):
        student_service, _, _ = services
        class_service = ClassService(student_service=student_service)
        c = class_service.create_class("2nde Z", "2nde", 75000)
        assert class_service.delete_class(c.id) is True


# ======================================================================
# Journal d'audit
# ======================================================================

class TestAudit:
    def test_student_lifecycle_audited(self, services):
        student_service, _, _ = services
        audit = AuditRepository()

        s = make_student(student_service, name="Traceur", first="Alice")
        entries = audit.get_all(entity="Élève", action="Création")
        assert any("Alice" in (e["entity_label"] or "") for e in entries)

        s.first_name = "Alicia"
        student_service.update_student(s)
        entries = audit.get_all(entity="Élève", action="Modification")
        assert any("Alicia" in (e["entity_label"] or "")
                   and "prénom" in (e["details"] or "") for e in entries)

        student_service.delete_student(s.id)
        entries = audit.get_all(entity="Élève", action="Suppression")
        assert any("Traceur" in (e["entity_label"] or "") for e in entries)

    def test_payment_lifecycle_audited(self, services):
        student_service, payment_service, _ = services
        audit = AuditRepository()
        s = make_student(student_service, name="Auditeur", first="Paul")

        p = payment_service.create_payment(
            student_id=s.id, amount_euros=10000,
            paid_on="2025-06-01", method="especes")
        entries = audit.get_all(entity="Paiement", action="Création")
        assert any(e["entity_label"] == p.receipt_no for e in entries)
        assert any("10 000" in (e["details"] or "") for e in entries)

        payment_service.update_payment(
            payment_id=p.id, amount_euros=15000,
            paid_on="2025-06-02", method="cheque")
        entries = audit.get_all(entity="Paiement", action="Modification")
        assert any(p.receipt_no in (e["entity_label"] or "")
                   and "Montant" in (e["details"] or "") for e in entries)

        payment_service.cancel_payment(p.id, "Erreur de saisie")
        entries = audit.get_all(entity="Paiement", action="Annulation")
        assert any("Erreur de saisie" in (e["details"] or "") for e in entries)

        payment_service.delete_payment(p.id)
        entries = audit.get_all(entity="Paiement", action="Suppression")
        assert any(e["entity_label"] == p.receipt_no for e in entries)

    def test_class_crud_audited(self, services):
        student_service, _, _ = services
        class_service = ClassService(student_service=student_service)
        audit = AuditRepository()

        c = class_service.create_class("6ème B", "6ème", 52000)
        entries = audit.get_all(entity="Classe", action="Création")
        assert any(e["entity_label"] == "6ème B" for e in entries)

        class_service.update_class(c.id, "6ème B bis", "6ème", 54000)
        entries = audit.get_all(entity="Classe", action="Modification")
        assert any("6ème B bis" in (e["entity_label"] or "")
                   and "Nom" in (e["details"] or "") for e in entries)

        class_service.delete_class(c.id)
        entries = audit.get_all(entity="Classe", action="Suppression")
        assert any(e["entity_label"] == "6ème B bis" for e in entries)

    def test_audit_filters_and_user(self, services):
        student_service, payment_service, _ = services
        audit = AuditRepository()
        s = make_student(student_service, name="Filtre", first="Zoé")
        payment_service.create_payment(
            student_id=s.id, amount_euros=10000,
            paid_on="2025-06-01", method="especes")

        only_students = audit.get_all(entity="Élève")
        assert all(e["entity"] == "Élève" for e in only_students)
        assert only_students
        assert all(e.get("user") for e in only_students)  # utilisateur renseigné
        assert audit.count() >= len(only_students)


class TestMoveStudent:
    def test_move_updates_class_and_due(self, services):
        student_service, payment_service, balance_service = services
        classes = {c.name: c.id for c in student_service.get_all_classes()}
        s = student_service.create_student(
            last_name="Transfere", first_name="Marc",
            class_id=classes["6ème A"])
        year = student_service.get_current_school_year()
        payment_service.create_payment(
            student_id=s.id, amount_euros=10000,
            paid_on="2025-06-01", method="especes")

        moved = student_service.move_student(s.id, classes["5ème A"])
        assert moved.class_id == classes["5ème A"]
        # Le total dû suit la nouvelle classe (55 000 FCFA en 5ème)
        assert balance_service.get_total_due(s.id, year.id) == 55000
        # Les paiements sont conservés
        assert balance_service.get_total_paid(s.id, year.id) == 10000

    def test_move_audited_as_transfert(self, services):
        student_service, _, _ = services
        audit = AuditRepository()
        classes = {c.name: c.id for c in student_service.get_all_classes()}
        s = student_service.create_student(
            last_name="Migrate", first_name="Nina", class_id=classes["6ème D"])
        student_service.move_student(s.id, classes["5ème D"])
        entries = audit.get_all(entity="Élève", action="Modification")
        assert any("Transfert" in (e["details"] or "")
                   and "6ème D" in (e["details"] or "")
                   and "5ème D" in (e["details"] or "") for e in entries)

    def test_move_to_same_class_refused(self, services):
        student_service, _, _ = services
        classes = {c.name: c.id for c in student_service.get_all_classes()}
        s = make_student(student_service, name="Sedentaire", first="Olivier")
        with pytest.raises(BusinessRuleError):
            student_service.move_student(s.id, classes["6ème A"])

    def test_move_unknown_student_refused(self, services):
        student_service, _, _ = services
        classes = {c.name: c.id for c in student_service.get_all_classes()}
        with pytest.raises(NotFoundError):
            student_service.move_student(999999, classes["6ème A"])


# ======================================================================
# Années scolaires (consultation des années précédentes)
# ======================================================================

class TestSchoolYears:
    def test_create_year_copies_classes(self, services):
        student_service, _, _ = services
        school_year_service = SchoolYearService(student_service=student_service)
        before = {c.name for c in student_service.get_all_classes()}

        new_year = school_year_service.create_school_year("2099-2100")
        assert new_year.id
        assert not new_year.is_current  # l'année courante ne change pas

        after = {c.name for c in student_service.get_all_classes()}
        assert before == after  # même noms de classes

    def test_create_duplicate_year_refused(self, services):
        student_service, _, _ = services
        school_year_service = SchoolYearService(student_service=student_service)
        school_year_service.create_school_year("2098-2099")
        with pytest.raises(BusinessRuleError):
            school_year_service.create_school_year("2098-2099")

    def test_invalid_label_refused(self, services):
        student_service, _, _ = services
        school_year_service = SchoolYearService(student_service=student_service)
        for bad in ("2025", "2099-2098", "abcd-efgh", ""):
            with pytest.raises(ValidationError):
                school_year_service.create_school_year(bad)

    def test_overview_per_year(self, services):
        """Le tableau de bord respecte l'année consultée."""
        student_service, payment_service, _ = services
        school_year_service = SchoolYearService(student_service=student_service)
        s = make_student(student_service, name="Annuel", first="Victor")
        payment_service.create_payment(
            student_id=s.id, amount_euros=10000,
            paid_on="2025-06-01", method="especes")

        current = student_service.get_current_school_year()
        overview_cur = payment_service.get_overview(current.id)
        row_cur = next(r for r in overview_cur["students"]
                       if r["student"].id == s.id)
        assert row_cur["total_paid_int"] == 10000

        # Nouvelle année : classes recopiées, aucun paiement (années futures
        # ou passées : l'élève apparaît si sa classe y existe)
        new_year = school_year_service.create_school_year("2097-2098")
        overview_new = payment_service.get_overview(new_year.id)
        assert overview_new["total_paid_int"] == 0
        row_new = next(r for r in overview_new["students"]
                       if r["student"].id == s.id)
        assert row_new["total_paid_int"] == 0
        assert row_new["total_due_int"] > 0  # frais recopiés

    def test_year_creation_audited(self, services):
        student_service, _, _ = services
        school_year_service = SchoolYearService(student_service=student_service)
        audit = AuditRepository()
        school_year_service.create_school_year("2096-2097")
        entries = audit.get_all(entity="Année scolaire", action="Création")
        assert any(e["entity_label"] == "2096-2097" for e in entries)

    def test_set_current_year(self, services):
        student_service, _, _ = services
        school_year_service = SchoolYearService(student_service=student_service)
        year = school_year_service.create_school_year("2095-2096")
        school_year_service.set_current_year(year.id)
        assert student_service.get_current_school_year().id == year.id
        # Retour à l'année d'origine pour ne pas perturber les autres tests
        others = [y for y in school_year_service.get_all() if y.id != year.id]
        school_year_service.set_current_year(others[0].id)
