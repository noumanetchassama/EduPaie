"""
Service pour le calcul des soldes et statuts de paiement

Fonctionnalités :
- Calcul du total dû (somme des fee_plan)
- Calcul du total payé (somme des paiements valides)
- Calcul du solde restant
- Détermination du statut (Soldé, Partiel, Impayé, En retard)
"""

from datetime import datetime
from typing import Optional
from app.data.repositories.payment_repository import PaymentRepository
from app.data.repositories.fee_plan_repository import FeePlanRepository
from app.data.repositories.student_repository import StudentRepository
from app.config import format_euros
from app.services.exceptions import NotFoundError


class BalanceService:
    """Service pour le calcul des soldes et statuts"""

    # Statuts de paiement
    STATUS_SOLD = "Soldé"
    STATUS_PARTIAL = "Partiellement payé"
    STATUS_UNPAID = "Non payé"
    STATUS_LATE = "En retard"

    def __init__(
        self,
        payment_repo: Optional[PaymentRepository] = None,
        fee_plan_repo: Optional[FeePlanRepository] = None,
        student_repo: Optional[StudentRepository] = None
    ):
        self.payment_repo = payment_repo if payment_repo else PaymentRepository()
        self.fee_plan_repo = fee_plan_repo if fee_plan_repo else FeePlanRepository()
        self.student_repo = student_repo if student_repo else StudentRepository()

    def get_balance(self, student_id: int, school_year_id: int) -> int:
        """
        Calcule le solde restant pour un élève (en cents).

        Solde = Total dû - Total payé

        Args:
            student_id: Identifiant de l'élève
            school_year_id: Identifiant de l'année scolaire

        Returns:
            int: Solde en cents (positif = dette, négatif = trop-perçu)

        Raises:
            NotFoundError: Si l'élève n'existe pas
        """
        student = self.student_repo.get_by_id(student_id)
        if not student:
            raise NotFoundError(f"Élève introuvable (ID: {student_id})")

        # Total dû : somme des fee_plan de sa classe
        total_due = self.fee_plan_repo.get_total_by_class(student.class_id, school_year_id)

        # Total payé : somme des paiements valides
        total_paid = self.payment_repo.get_total_by_student(student_id, school_year_id, valid_only=True)

        # Solde = dû - payé
        return total_due - total_paid

    def get_total_due(self, student_id: int, school_year_id: int) -> int:
        """
        Calcule le total dû pour un élève (en cents).

        Args:
            student_id: Identifiant de l'élève
            school_year_id: Identifiant de l'année scolaire

        Returns:
            int: Total dû en cents
        """
        student = self.student_repo.get_by_id(student_id)
        if not student:
            raise NotFoundError(f"Élève introuvable (ID: {student_id})")

        return self.fee_plan_repo.get_total_by_class(student.class_id, school_year_id)

    def get_total_paid(self, student_id: int, school_year_id: int) -> int:
        """
        Calcule le total payé pour un élève (en cents).

        Ne compte que les paiements valides (non annulés).

        Args:
            student_id: Identifiant de l'élève
            school_year_id: Identifiant de l'année scolaire

        Returns:
            int: Total payé en cents
        """
        return self.payment_repo.get_total_by_student(student_id, school_year_id, valid_only=True)

    def get_status(self, student_id: int, school_year_id: int) -> str:
        """
        Détermine le statut de paiement d'un élève.

        Statuts possibles :
        - "Soldé" : solde = 0
        - "Partiellement payé" : 0 < payé < dû
        - "Non payé" : payé = 0
        - "En retard" : solde > 0 et échéance dépassée

        Args:
            student_id: Identifiant de l'élève
            school_year_id: Identifiant de l'année scolaire

        Returns:
            str: Statut de paiement
        """
        balance = self.get_balance(student_id, school_year_id)
        total_due = self.get_total_due(student_id, school_year_id)
        total_paid = self.get_total_paid(student_id, school_year_id)

        # Vérifier si en retard (échéance dépassée)
        if balance > 0 and self._is_overdue(student_id, school_year_id):
            return self.STATUS_LATE

        # Déterminer le statut
        if balance == 0:
            return self.STATUS_SOLD
        elif total_paid > 0:
            return self.STATUS_PARTIAL
        else:
            return self.STATUS_UNPAID

    def _is_overdue(self, student_id: int, school_year_id: int) -> bool:
        """
        Vérifie si l'élève est en retard (échéance dépassée).

        Un élève est en retard si :
        - Il a un solde > 0
        - Au moins un fee_plan a une due_date passée

        Args:
            student_id: Identifiant de l'élève
            school_year_id: Identifiant de l'année scolaire

        Returns:
            bool: True si en retard
        """
        student = self.student_repo.get_by_id(student_id)
        if not student:
            return False

        # Récupérer les fee_plan de la classe
        fee_plans = self.fee_plan_repo.get_by_class(student.class_id, school_year_id)

        today = datetime.now().date()

        # Vérifier si une échéance est dépassée
        for fee_plan in fee_plans:
            if fee_plan.due_date:
                try:
                    due_date = datetime.strptime(fee_plan.due_date, '%Y-%m-%d').date()
                    if due_date < today:
                        return True
                except ValueError:
                    continue

        return False

    def get_balance_info(self, student_id: int, school_year_id: int) -> dict:
        """
        Retourne toutes les informations de solde pour un élève.

        Args:
            student_id: Identifiant de l'élève
            school_year_id: Identifiant de l'année scolaire

        Returns:
            dict: Dictionnaire avec total_due, total_paid, balance, status
        """
        total_due = self.get_total_due(student_id, school_year_id)
        total_paid = self.get_total_paid(student_id, school_year_id)
        balance = self.get_balance(student_id, school_year_id)
        status = self.get_status(student_id, school_year_id)

        return {
            'total_due_int': total_due,
            'total_due_formatted': format_euros(total_due),
            'total_paid_int': total_paid,
            'total_paid_formatted': format_euros(total_paid),
            'balance_int': balance,
            'balance_formatted': format_euros(balance),
            'status': status
        }
