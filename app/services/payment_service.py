"""
Service pour la logique métier des paiements

Fonctionnalités :
- Validation des paiements (montant, date, mode, solde)
- Génération atomique du numéro de reçu (compteur en base)
- Snapshot figé pour ré-impression identique
- Annulation (soft delete) de paiements
- Statistiques globales pour le tableau de bord
"""

from datetime import date, datetime
from typing import List, Optional

from app.config import format_euros
from app.data.repositories.class_repository import ClassRepository
from app.data.repositories.fee_plan_repository import FeePlanRepository
from app.data.repositories.payment_repository import PaymentRepository
from app.data.repositories.school_year_repository import SchoolYearRepository
from app.data.repositories.student_repository import StudentRepository
from app.models.payment import Payment
from app.services.balance_service import BalanceService
from app.services.exceptions import BusinessRuleError, NotFoundError, ValidationError
from app.services.student_service import StudentService

DATE_FORMAT = "%Y-%m-%d"


class PaymentService:
    """Service contenant la logique métier pour les paiements"""

    MODES_PAIEMENT = ["especes", "cheque", "virement", "mobile_money"]
    MODES_PAIEMENT_LABELS = {
        "especes": "Espèces",
        "cheque": "Chèque",
        "virement": "Virement",
        "mobile_money": "Mobile Money",
    }

    def __init__(
        self,
        payment_repo: Optional[PaymentRepository] = None,
        student_repo: Optional[StudentRepository] = None,
        school_year_repo: Optional[SchoolYearRepository] = None,
        fee_plan_repo: Optional[FeePlanRepository] = None,
        class_repo: Optional[ClassRepository] = None,
    ):
        self.payment_repo = payment_repo or PaymentRepository()
        self.student_repo = student_repo or StudentRepository()
        self.school_year_repo = school_year_repo or SchoolYearRepository()
        self.fee_plan_repo = fee_plan_repo or FeePlanRepository()
        self.class_repo = class_repo or ClassRepository()
        self.student_service = StudentService(
            student_repo=self.student_repo,
            class_repo=self.class_repo,
            payment_repo=self.payment_repo,
            school_year_repo=self.school_year_repo,
        )
        self.balance_service = BalanceService(
            payment_repo=self.payment_repo,
            fee_plan_repo=self.fee_plan_repo,
            student_repo=self.student_repo,
        )

    # ------------------------------------------------------------------
    # Création
    # ------------------------------------------------------------------

    def create_payment(
        self,
        student_id: int,
        amount_euros: float,
        paid_on: str,
        method: str,
        reference: Optional[str] = None,
        allow_overpayment: bool = False,
    ) -> Payment:
        """
        Crée un nouveau paiement avec validation et numérotation atomique du reçu.

        Cette opération est atomique : paiement + numéro de reçu + snapshot
        sont créés dans une seule transaction.

        Args:
            student_id: Identifiant de l'élève
            amount_euros: Montant en euros
            paid_on: Date du paiement (AAAA-MM-JJ)
            method: Mode de paiement (especes / cheque / virement / mobile_money)
            reference: Référence (n° de chèque, transaction...) optionnelle
            allow_overpayment: Si True, autorise un montant supérieur au solde
                (l'interface doit avoir averti l'utilisateur explicitement)

        Raises:
            ValidationError: Si les données sont invalides
            BusinessRuleError: Si le montant dépasse le solde restant
            NotFoundError: Si l'élève n'existe pas
        """
        student = self.student_repo.get_by_id(student_id)
        if not student:
            raise NotFoundError(f"Élève introuvable (ID: {student_id})")

        school_year = self.student_service.get_current_school_year()

        if amount_euros is None:
            raise ValidationError("Le montant est obligatoire")
        try:
            amount_euros = float(str(amount_euros).replace(",", "."))
        except (TypeError, ValueError):
            raise ValidationError("Montant invalide")
        if amount_euros <= 0:
            raise ValidationError("Le montant doit être strictement positif")

        amount_int = int(round(amount_euros))  # FCFA entiers

        if method not in self.MODES_PAIEMENT:
            raise ValidationError(f"Mode de paiement invalide : {method}")

        try:
            paid_date = datetime.strptime(paid_on, DATE_FORMAT).date()
        except (TypeError, ValueError):
            raise ValidationError(f"Format de date invalide (attendu : {DATE_FORMAT})")
        if paid_date > date.today():
            raise ValidationError("La date de paiement ne peut pas être dans le futur")

        if not allow_overpayment:
            balance = self.balance_service.get_balance(student_id, school_year.id)
            if amount_int > balance:
                raise BusinessRuleError(
                    f"Le montant ({format_euros(amount_int)}) dépasse le solde "
                    f"restant ({format_euros(balance)}). "
                    "Un paiement ne peut pas rendre le solde négatif."
                )

        # Numéro de reçu + insertion + snapshot : une seule transaction
        payment_id, receipt_no = self._insert_payment_atomic(
            student, school_year, amount_int, paid_on, method, reference
        )

        payment = Payment(
            id=payment_id,
            student_id=student_id,
            school_year_id=school_year.id,
            amount_int=amount_int,
            paid_on=paid_on,
            method=method,
            reference=reference,
            receipt_no=receipt_no,
            status="valide",
        )
        return payment

    def _insert_payment_atomic(self, student, school_year, amount_int, paid_on,
                               method, reference):
        """
        Insère le paiement, incrémente le compteur de reçus et écrit le
        snapshot dans UNE SEULE transaction SQLite.
        """
        year = int(school_year.label[:4])
        receipt_no = None
        payment_id = None

        with self.payment_repo.db.transaction() as cursor:
            # 1. Incrément atomique du compteur de reçus
            cursor.execute(
                "UPDATE receipt_counter SET last_number = last_number + 1 WHERE year = ?",
                (year,),
            )
            row = cursor.execute(
                "SELECT last_number FROM receipt_counter WHERE year = ?", (year,)
            ).fetchone()
            if row is None:
                cursor.execute(
                    "INSERT INTO receipt_counter (year, last_number) VALUES (?, 1)",
                    (year,),
                )
                number = 1
            else:
                number = row["last_number"]
            receipt_no = f"REC-{year}-{number:06d}"

            # 2. Insertion du paiement
            cursor.execute(
                """
                INSERT INTO payment (
                    student_id, school_year_id, amount_int, paid_on,
                    method, reference, receipt_no, status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 'valide')
                """,
                (
                    student.id,
                    school_year.id,
                    amount_int,
                    paid_on,
                    method,
                    reference,
                    receipt_no,
                ),
            )
            payment_id = cursor.lastrowid

            # 3. Snapshot figé pour ré-impression identique
            snapshot = self._build_receipt_snapshot(
                student, school_year, amount_int, paid_on, method, reference, receipt_no
            )
            import json

            cursor.execute(
                "INSERT INTO receipt_snapshot (payment_id, snapshot_json) VALUES (?, ?)",
                (payment_id, json.dumps(snapshot, ensure_ascii=False)),
            )

        return payment_id, receipt_no

    def _build_receipt_snapshot(self, student, school_year, amount_int, paid_on,
                                method, reference, receipt_no) -> dict:
        """Construit le dictionnaire de snapshot du reçu (figé à l'émission)."""
        from app.config import SCHOOL_ADDRESS, SCHOOL_EMAIL, SCHOOL_NAME, SCHOOL_PHONE

        class_obj = self.class_repo.get_by_id(student.class_id)
        class_name = class_obj.name if class_obj else "Classe inconnue"

        balance_before = self.balance_service.get_balance(student.id, school_year.id)
        balance_after = balance_before - amount_int

        return {
            "receipt_no": receipt_no,
            "receipt_date": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "school": {
                "name": SCHOOL_NAME,
                "address": SCHOOL_ADDRESS,
                "phone": SCHOOL_PHONE,
                "email": SCHOOL_EMAIL,
            },
            "student": {
                "matricule": student.matricule,
                "last_name": student.last_name,
                "first_name": student.first_name,
                "class": class_name,
                "school_year": school_year.label,
            },
            "payment": {
                "amount_int": amount_int,
                "amount_formatted": format_euros(amount_int),
                "paid_on": paid_on,
                "method": self.MODES_PAIEMENT_LABELS.get(method, method),
                "reference": reference,
            },
            "balance": {
                "before_int": balance_before,
                "before_formatted": format_euros(balance_before),
                "after_int": balance_after,
                "after_formatted": format_euros(balance_after),
            },
        }

    # ------------------------------------------------------------------
    # Annulation / consultation
    # ------------------------------------------------------------------

    def cancel_payment(self, payment_id: int, reason: str) -> bool:
        """
        Annule un paiement (soft delete).

        L'historique et la numérotation restent intacts ; le paiement annulé
        n'est plus compté dans les soldes.

        Raises:
            ValidationError: Si le motif est vide
            NotFoundError: Si le paiement n'existe pas
            BusinessRuleError: Si le paiement est déjà annulé
        """
        if not reason or not reason.strip():
            raise ValidationError("Le motif d'annulation est obligatoire")

        payment = self.payment_repo.get_by_id(payment_id)
        if not payment:
            raise NotFoundError(f"Paiement introuvable (ID: {payment_id})")
        if payment.is_cancelled:
            raise BusinessRuleError("Ce paiement est déjà annulé")

        return self.payment_repo.cancel(payment_id, reason.strip())

    def get_payment_by_receipt(self, receipt_no: str) -> Optional[Payment]:
        """Récupère un paiement par son numéro de reçu."""
        return self.payment_repo.get_by_receipt_no(receipt_no)

    def get_payment(self, payment_id: int) -> Optional[Payment]:
        """Récupère un paiement par son identifiant."""
        return self.payment_repo.get_by_id(payment_id)

    def get_payment_snapshot(self, payment_id: int) -> Optional[dict]:
        """Récupère le snapshot d'un reçu pour ré-impression identique."""
        return self.payment_repo.get_snapshot(payment_id)

    def get_student_payments(
        self,
        student_id: int,
        school_year_id: Optional[int] = None,
        valid_only: bool = True,
    ) -> List[Payment]:
        """Récupère les paiements d'un élève (triés du plus récent au plus ancien)."""
        return self.payment_repo.get_by_student(student_id, school_year_id, valid_only)

    def get_all_payments(
        self, school_year_id: Optional[int] = None, valid_only: bool = True
    ) -> List[Payment]:
        """Récupère tous les paiements."""
        return self.payment_repo.get_all(school_year_id, valid_only)

    # ------------------------------------------------------------------
    # Statistiques globales (tableau de bord)
    # ------------------------------------------------------------------

    def get_overview(self) -> dict:
        """
        Calcule les statistiques globales pour le tableau de bord :
        nombre d'élèves, total encaissé, total restant dû, nombre d'élèves
        non soldés, et le détail par élève (dû / payé / solde / statut).

        Returns:
            dict avec clés :
                school_year, nb_students, total_due_int, total_paid_int,
                total_balance_int, nb_paid, nb_partial, nb_unpaid,
                nb_not_settled, students (liste de dicts)
        """
        school_year = self.student_service.get_current_school_year()
        students = self.student_repo.get_all(active_only=False)
        classes = {c.id: c.name for c in self.class_repo.get_all(school_year.id)}

        total_due = 0
        total_paid = 0
        nb_paid = 0
        nb_partial = 0
        nb_unpaid = 0
        student_rows = []

        for s in students:
            total_due_s = self.fee_plan_repo.get_total_by_class(s.class_id, school_year.id)
            total_paid_s = self.payment_repo.get_total_by_student(s.id, school_year.id)
            balance = total_due_s - total_paid_s

            if total_due_s == 0:
                status = BalanceService.STATUS_UNPAID
            elif balance == 0:
                status = BalanceService.STATUS_SOLD
            elif total_paid_s > 0:
                status = BalanceService.STATUS_PARTIAL
            else:
                status = BalanceService.STATUS_UNPAID

            total_due += total_due_s
            total_paid += total_paid_s
            if status == BalanceService.STATUS_SOLD:
                nb_paid += 1
            elif status == BalanceService.STATUS_PARTIAL:
                nb_partial += 1
            else:
                nb_unpaid += 1

            student_rows.append({
                "student": s,
                "class_name": classes.get(s.class_id, "—"),
                "school_year": school_year.label,
                "total_due_int": total_due_s,
                "total_paid_int": total_paid_s,
                "balance_int": balance,
                "status": status,
            })

        return {
            "school_year": school_year,
            "nb_students": len(students),
            "total_due_int": total_due,
            "total_paid_int": total_paid,
            "total_balance_int": total_due - total_paid,
            "nb_paid": nb_paid,
            "nb_partial": nb_partial,
            "nb_unpaid": nb_unpaid,
            "nb_not_settled": nb_partial + nb_unpaid,
            "students": student_rows,
        }
