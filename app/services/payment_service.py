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
from app.data.repositories.audit_repository import AuditRepository
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
        audit_repo: Optional[AuditRepository] = None,
    ):
        self.payment_repo = payment_repo or PaymentRepository()
        self.student_repo = student_repo or StudentRepository()
        self.school_year_repo = school_year_repo or SchoolYearRepository()
        self.fee_plan_repo = fee_plan_repo or FeePlanRepository()
        self.class_repo = class_repo or ClassRepository()
        self.audit_repo = audit_repo or AuditRepository()
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

        # Solde AVANT encaissement : le snapshot doit montrer la situation
        # avant/après ce paiement, or l'insertion est déjà faite au moment
        # où le snapshot est construit (sinon le montant est déduit deux fois).
        balance_before = self.balance_service.get_balance(
            student_id, school_year.id)

        # Numéro de reçu + insertion + snapshot : une seule transaction
        payment_id, receipt_no = self._insert_payment_atomic(
            student, school_year, amount_int, paid_on, method, reference,
            balance_before=balance_before,
        )

        self.audit_repo.add(
            "Création", "Paiement", payment_id, receipt_no,
            f"{format_euros(amount_int)} — {student.first_name} {student.last_name} "
            f"({self.MODES_PAIEMENT_LABELS.get(method, method)})")

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
                               method, reference, balance_before=None):
        """
        Insère le paiement, incrémente le compteur de reçus et écrit le
        snapshot dans UNE SEULE transaction SQLite.

        Args:
            balance_before: solde restant AVANT ce paiement (calculé hors
                transaction, sinon l'insertion déjà faite fausserait le
                « solde avant » du reçu).
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
                student, school_year, amount_int, paid_on, method, reference,
                receipt_no, balance_before=balance_before,
            )
            import json

            cursor.execute(
                "INSERT INTO receipt_snapshot (payment_id, snapshot_json) VALUES (?, ?)",
                (payment_id, json.dumps(snapshot, ensure_ascii=False)),
            )

        return payment_id, receipt_no

    def _build_receipt_snapshot(self, student, school_year, amount_int, paid_on,
                                method, reference, receipt_no,
                                balance_before=None) -> dict:
        """
        Construit le dictionnaire du snapshot du reçu (figé à l'émission).

        Args:
            balance_before: solde restant AVANT ce paiement ; calculé par
                défaut (à n'utiliser que si le paiement n'est pas encore
                enregistré en base).
        """
        from app.config import SCHOOL_ADDRESS, SCHOOL_EMAIL, SCHOOL_NAME, SCHOOL_PHONE

        class_obj = self.class_repo.get_by_id(student.class_id)
        class_name = class_obj.name if class_obj else "Classe inconnue"

        if balance_before is None:
            balance_before = self.balance_service.get_balance(
                student.id, school_year.id)
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

    def update_payment(
        self,
        payment_id: int,
        amount_euros: float,
        paid_on: str,
        method: str,
        reference: Optional[str] = None,
    ) -> Payment:
        """
        Modifie un paiement existant avec validation du solde.

        Le montant ne doit pas faire passer le solde de l'élève en négatif
        (on exclut le paiement lui-même du calcul). Le snapshot du reçu est
        régénéré pour refléter la correction, et le numéro de reçu est
        conservé.

        Raises:
            ValidationError: Si les données sont invalides
            BusinessRuleError: Si le solde deviendrait négatif
            NotFoundError: Si le paiement n'existe pas
        """
        payment = self.payment_repo.get_by_id(payment_id)
        if not payment:
            raise NotFoundError(f"Paiement introuvable (ID: {payment_id})")
        if payment.is_cancelled:
            raise BusinessRuleError(
                "Impossible de modifier un paiement annulé. Annulez-le ou "
                "réenregistrez un nouveau paiement.")

        student = self.student_repo.get_by_id(payment.student_id)
        if not student:
            raise NotFoundError(f"Élève introuvable (ID: {payment.student_id})")

        school_year = self.student_service.get_current_school_year()

        # Validations identiques à la création
        try:
            amount_euros = float(str(amount_euros).replace(",", "."))
        except (TypeError, ValueError):
            raise ValidationError("Montant invalide")
        if amount_euros <= 0:
            raise ValidationError("Le montant doit être strictement positif")
        amount_int = int(round(amount_euros))

        if method not in self.MODES_PAIEMENT:
            raise ValidationError(f"Mode de paiement invalide : {method}")

        try:
            paid_date = datetime.strptime(paid_on, DATE_FORMAT).date()
        except (TypeError, ValueError):
            raise ValidationError(f"Format de date invalide (attendu : {DATE_FORMAT})")
        if paid_date > date.today():
            raise ValidationError("La date de paiement ne peut pas être dans le futur")

        # Solde en excluant le paiement en cours de modification
        year = self.school_year_repo.get_by_id(payment.school_year_id)
        other_paid = self.payment_repo.get_total_by_student(
            payment.student_id, payment.school_year_id)
        balance_before = self.fee_plan_repo.get_total_by_class(
            student.class_id, payment.school_year_id) - (other_paid - payment.amount_int)
        if amount_int > balance_before:
            raise BusinessRuleError(
                f"Le montant ({format_euros(amount_int)}) dépasserait le solde "
                f"restant ({format_euros(balance_before)}) après modification.")

        # Mise à jour + snapshot régénéré (numéro de reçu inchangé),
        # en UNE seule écriture : le snapshot est mis à jour avec le
        # paiement dans la même transaction.
        previous = {
            "amount_int": payment.amount_int,
            "paid_on": payment.paid_on,
            "method": payment.method,
            "reference": payment.reference,
        }
        snapshot = self._build_receipt_snapshot(
            student, year, amount_int, paid_on, method, reference,
            payment.receipt_no, balance_before=balance_before)
        payment.amount_int = amount_int
        payment.paid_on = paid_on
        payment.method = method
        payment.reference = reference
        updated = self.payment_repo.update(payment, snapshot=snapshot)
        if not updated:
            raise NotFoundError(f"Paiement introuvable (ID: {payment_id})")

        changes = []
        if previous["amount_int"] != amount_int:
            changes.append(f"Montant : {format_euros(previous['amount_int'])} → "
                           f"{format_euros(amount_int)}")
        if previous["paid_on"] != paid_on:
            changes.append(f"Date : {previous['paid_on']} → {paid_on}")
        if previous["method"] != method:
            changes.append(
                f"Mode : {self.MODES_PAIEMENT_LABELS.get(previous['method'], previous['method'])} "
                f"→ {self.MODES_PAIEMENT_LABELS.get(method, method)}")
        if previous["reference"] != reference:
            changes.append("Référence")
        self.audit_repo.add(
            "Modification", "Paiement", payment.id, payment.receipt_no,
            " ; ".join(changes) or "Enregistrement sans changement")
        return payment

    def delete_payment(self, payment_id: int) -> bool:
        """
        Supprime définitivement un paiement (réservé aux corrections).

        L'annulation (cancel_payment) est à privilégier : elle conserve la
        trace du reçu. La suppression est ici pour les saisies fantaisistes
        ou les demandes de la direction.

        Raises:
            NotFoundError: Si le paiement n'existe pas
        """
        payment = self.payment_repo.get_by_id(payment_id)
        if not payment:
            raise NotFoundError(f"Paiement introuvable (ID: {payment_id})")
        deleted = self.payment_repo.delete(payment_id)
        if deleted:
            self.audit_repo.add(
                "Suppression", "Paiement", payment_id, payment.receipt_no,
                f"{format_euros(payment.amount_int)} du {payment.paid_on}")
        return deleted

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

        cancelled = self.payment_repo.cancel(payment_id, reason.strip())
        if cancelled:
            self.audit_repo.add(
                "Annulation", "Paiement", payment_id, payment.receipt_no,
                f"Motif : {reason.strip()}")
        return cancelled

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

    def get_overview(self, school_year_id: Optional[int] = None) -> dict:
        """
        Calcule les statistiques globales pour le tableau de bord :
        nombre d'élèves, total encaissé, total restant dû, nombre d'élèves
        non soldés, et le détail par élève (dû / payé / solde / statut).

        Args:
            school_year_id: Année scolaire à consulter (défaut : année
                courante). Pour une année antérieure, la classe de l'élève
                est retrouvée par son nom dans cette année.

        Returns:
            dict avec clés :
                school_year, nb_students, total_due_int, total_paid_int,
                total_balance_int, nb_paid, nb_partial, nb_unpaid,
                nb_not_settled, students (liste de dicts)
        """
        school_year = self._resolve_school_year(school_year_id)
        # Les élèves archivés (is_active = 0) sont exclus : ils ne sont
        # plus suivis et leurs paiements ne comptent plus dans les totaux.
        students = self.student_repo.get_all(active_only=True)
        year_classes = self.class_repo.get_all(school_year.id)
        classes = {c.id: c.name for c in year_classes}
        class_id_by_name = {c.name: c.id for c in year_classes}
        # Nom de la classe actuelle de chaque élève (toutes années)
        all_classes = {c.id: c.name for c in self.class_repo.get_all()}

        total_due = 0
        total_paid = 0
        nb_paid = 0
        nb_partial = 0
        nb_unpaid = 0
        student_rows = []

        for s in students:
            # Classe de l'élève pour l'année consultée (par nom) ; un élève
            # sans classe connue cette année-là et sans paiement n'est pas
            # affiché (il n'était pas suivi cette année-là).
            class_id_year = class_id_by_name.get(all_classes.get(s.class_id, ""))
            total_paid_s = self.payment_repo.get_total_by_student(s.id, school_year.id)
            if class_id_year is None and total_paid_s == 0:
                continue

            total_due_s = self.fee_plan_repo.get_total_by_class(
                class_id_year, school_year.id) if class_id_year else 0
            balance = total_due_s - total_paid_s

            if total_due_s == 0:
                # Aucun plan de frais cette année-là : soldé si des paiements
                # existent, sinon non payé (aligné sur BalanceService.get_status)
                status = (BalanceService.STATUS_SOLD if total_paid_s > 0
                          else BalanceService.STATUS_UNPAID)
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
                "class_name": all_classes.get(s.class_id, "—"),
                "school_year": school_year.label,
                "total_due_int": total_due_s,
                "total_paid_int": total_paid_s,
                "balance_int": balance,
                "status": status,
            })

        return {
            "school_year": school_year,
            "nb_students": len(student_rows),
            "total_due_int": total_due,
            "total_paid_int": total_paid,
            "total_balance_int": total_due - total_paid,
            "nb_paid": nb_paid,
            "nb_partial": nb_partial,
            "nb_unpaid": nb_unpaid,
            "nb_not_settled": nb_partial + nb_unpaid,
            "students": student_rows,
        }

    def _resolve_school_year(self, school_year_id: Optional[int] = None):
        """Année demandée, ou l'année courante par défaut."""
        if school_year_id:
            year = self.school_year_repo.get_by_id(school_year_id)
            if year is not None:
                return year
        return self.student_service.get_current_school_year()
