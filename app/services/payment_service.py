"""
Service pour la logique métier des paiements

Fonctionnalités :
- Validation des paiements
- Génération atomique du numéro de reçu
- Création de snapshot pour ré-impression identique
- Annulation de paiements
"""

from datetime import datetime
from typing import Optional, List
from app.models.payment import Payment
from app.models.student import Student
from app.data.repositories.payment_repository import PaymentRepository
from app.data.repositories.student_repository import StudentRepository
from app.data.repositories.school_year_repository import SchoolYearRepository
from app.data.repositories.fee_plan_repository import FeePlanRepository, FeePlan
from app.config import format_euros, cents_to_euros
from app.services.exceptions import ValidationError, BusinessRuleError, NotFoundError


class PaymentService:
    """Service contenant la logique métier pour les paiements"""

    MODES_PAIEMENT = ['especes', 'cheque', 'virement', 'mobile_money']
    MODES_PAIEMENT_LABELS = {
        'especes': 'Espèces',
        'cheque': 'Chèque',
        'virement': 'Virement',
        'mobile_money': 'Mobile Money'
    }

    def __init__(
        self,
        payment_repo: Optional[PaymentRepository] = None,
        student_repo: Optional[StudentRepository] = None,
        school_year_repo: Optional[SchoolYearRepository] = None,
        fee_plan_repo: Optional[FeePlanRepository] = None
    ):
        self.payment_repo = payment_repo if payment_repo else PaymentRepository()
        self.student_repo = student_repo if student_repo else StudentRepository()
        self.school_year_repo = school_year_repo if school_year_repo else SchoolYearRepository()
        self.fee_plan_repo = fee_plan_repo if fee_plan_repo else FeePlanRepository()

    def create_payment(
        self,
        student_id: int,
        amount_euros: float,
        paid_on: str,
        method: str,
        reference: str = None,
        allow_overpayment: bool = False
    ) -> Payment:
        """
        Crée un nouveau paiement avec validation et numérotation atomique du reçu.

        Cette opération est atomique : paiement + numéro de reçu + snapshot
        sont créés dans une seule transaction.

        Args:
            student_id: Identifiant de l'élève
            amount_euros: Montant en euros
            paid_on: Date du paiement (YYYY-MM-DD)
            method: Mode de paiement
            reference: Référence (optionnel)
            allow_overpayment: Si True, autorise les paiements supérieurs au solde

        Returns:
            Payment: Le paiement créé

        Raises:
            ValidationError: Si les données sont invalides
            BusinessRuleError: Si une règle métier est violée
            NotFoundError: Si l'élève n'existe pas
        """
        # Validation de l'élève
        student = self.student_repo.get_by_id(student_id)
        if not student:
            raise NotFoundError(f"Élève introuvable (ID: {student_id})")

        # Récupérer l'année scolaire courante
        school_year = self.school_year_repo.get_current()
        if not school_year:
            raise BusinessRuleError("Aucune année scolaire courante définie")

        # Validation du montant
        if amount_euros <= 0:
            raise ValidationError("Le montant doit être positif")

        # Conversion en cents
        amount_int = int(round(amount_euros * 100))

        # Validation du mode de paiement
        if method not in self.MODES_PAIEMENT:
            raise ValidationError(f"Mode de paiement invalide : {method}")

        # Validation de la date
        try:
            paid_date = datetime.strptime(paid_on, '%Y-%m-%d').date()
            today = datetime.now().date()
            if paid_date > today:
                raise ValidationError("La date de paiement ne peut pas être dans le futur")
        except ValueError:
            raise ValidationError("Format de date invalide (attendu: YYYY-MM-DD)")

        # Validation du solde (sauf si overpayment autorisé)
        if not allow_overpayment:
            balance_service = BalanceService(
                self.payment_repo, self.fee_plan_repo, self.student_repo
            )
            balance = balance_service.get_balance(student_id, school_year.id)
            if amount_int > balance:
                raise BusinessRuleError(
                    f"Le montant ({format_euros(amount_int)}) dépasse le solde restant ({format_euros(balance)})"
                )

        # Génération atomique du numéro de reçu
        receipt_no = self._generate_receipt_number(school_year.label[:4])

        # Création du snapshot pour ré-impression identique
        snapshot = self._create_receipt_snapshot(
            student, school_year, amount_int, paid_on, method, reference, receipt_no
        )

        # Création du paiement dans une transaction atomique
        payment = Payment(
            student_id=student_id,
            school_year_id=school_year.id,
            amount_int=amount_int,
            paid_on=paid_on,
            method=method,
            reference=reference,
            receipt_no=receipt_no,
            status='valide'
        )

        payment_id = self.payment_repo.add(payment, snapshot)
        payment.id = payment_id

        return payment

    def _generate_receipt_number(self, year_str: str) -> str:
        """
        Génère un numéro de reçu unique de manière atomique.

        Format : REC-AAAA-NNNNNN
        - AAAA : Année (ex: 2024)
        - NNNNNN : Numéro séquentiel sur 6 chiffres

        L'incrémentation du compteur est atomique (faite dans la même transaction
        que l'insertion du paiement).

        Args:
            year_str: Année sous forme de string (ex: "2024-2025" → "2024")

        Returns:
            str: Numéro de reçu unique
        """
        year = int(year_str[:4])

        # Incrémentation atomique du compteur
        # Cette méthode est appelée dans la transaction du paiement
        next_number = self.payment_repo.increment_receipt_counter(year)

        # Formatage : REC-2024-000001
        return f"REC-{year}-{next_number:06d}"

    def _create_receipt_snapshot(
        self,
        student: Student,
        school_year,
        amount_int: int,
        paid_on: str,
        method: str,
        reference: str,
        receipt_no: str
    ) -> dict:
        """
        Crée un snapshot figé du reçu pour ré-impression identique.

        Le snapshot contient toutes les données nécessaires pour ré-imprimer
        le reçu à l'identique, même si les données de l'élève changent.

        Args:
            student: Objet Student
            school_year: Objet SchoolYear
            amount_int: Montant en cents
            paid_on: Date de paiement
            method: Mode de paiement
            reference: Référence
            receipt_no: Numéro de reçu

        Returns:
            dict: Snapshot JSON
        """
        # Récupérer la classe de l'élève
        # (à adapter quand ClassRepository sera créé)
        class_name = "Classe inconnue"  # TODO: récupérer depuis class_id

        # Calculer le solde avant et après
        balance_service = BalanceService(
            self.payment_repo, self.fee_plan_repo, self.student_repo
        )
        balance_before = balance_service.get_balance(student.id, school_year.id)
        balance_after = balance_before - amount_int

        # Configuration de l'école
        from app.config import SCHOOL_NAME, SCHOOL_ADDRESS, SCHOOL_PHONE

        snapshot = {
            'receipt_no': receipt_no,
            'receipt_date': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'school': {
                'name': SCHOOL_NAME,
                'address': SCHOOL_ADDRESS,
                'phone': SCHOOL_PHONE
            },
            'student': {
                'matricule': student.matricule,
                'last_name': student.last_name,
                'first_name': student.first_name,
                'class': class_name,
                'school_year': school_year.label
            },
            'payment': {
                'amount_euros': cents_to_euros(amount_int),
                'amount_formatted': format_euros(amount_int),
                'paid_on': paid_on,
                'method': self.MODES_PAIEMENT_LABELS.get(method, method),
                'reference': reference
            },
            'balance': {
                'before_euros': cents_to_euros(balance_before),
                'before_formatted': format_euros(balance_before),
                'after_euros': cents_to_euros(balance_after),
                'after_formatted': format_euros(balance_after)
            }
        }

        return snapshot

    def cancel_payment(self, payment_id: int, reason: str) -> bool:
        """
        Annule un paiement (soft delete).

        Le paiement n'est pas supprimé physiquement, mais marqué comme annulé.
        L'historique et la numérotation restent intacts.

        Args:
            payment_id: Identifiant du paiement
            reason: Motif de l'annulation

        Returns:
            bool: True si le paiement a été annulé

        Raises:
            ValidationError: Si le motif est vide
            NotFoundError: Si le paiement n'existe pas
        """
        if not reason or not reason.strip():
            raise ValidationError("Le motif d'annulation est obligatoire")

        payment = self.payment_repo.get_by_id(payment_id)
        if not payment:
            raise NotFoundError(f"Paiement introuvable (ID: {payment_id})")

        if payment.status == 'annule':
            raise BusinessRuleError("Ce paiement est déjà annulé")

        return self.payment_repo.cancel(payment_id, reason.strip())

    def get_payment_by_receipt(self, receipt_no: str) -> Optional[Payment]:
        """
        Récupère un paiement par son numéro de reçu.

        Args:
            receipt_no: Numéro de reçu

        Returns:
            Payment | None: Le paiement trouvé ou None
        """
        return self.payment_repo.get_by_receipt_no(receipt_no)

    def get_payment_snapshot(self, payment_id: int) -> Optional[dict]:
        """
        Récupère le snapshot d'un reçu pour ré-impression.

        Args:
            payment_id: Identifiant du paiement

        Returns:
            dict | None: Snapshot JSON ou None
        """
        return self.payment_repo.get_snapshot(payment_id)

    def get_student_payments(
        self,
        student_id: int,
        school_year_id: int = None,
        valid_only: bool = True
    ) -> List[Payment]:
        """
        Récupère les paiements d'un élève.

        Args:
            student_id: Identifiant de l'élève
            school_year_id: Identifiant de l'année scolaire (optionnel)
            valid_only: Si True, ne retourne que les paiements valides

        Returns:
            List[Payment]: Liste des paiements
        """
        return self.payment_repo.get_by_student(student_id, school_year_id, valid_only)

    def get_all_payments(
        self,
        school_year_id: int = None,
        valid_only: bool = True
    ) -> List[Payment]:
        """
        Récupère tous les paiements.

        Args:
            school_year_id: Identifiant de l'année scolaire (optionnel)
            valid_only: Si True, ne retourne que les paiements valides

        Returns:
            List[Payment]: Liste des paiements
        """
        return self.payment_repo.get_all(school_year_id, valid_only)
