"""
Service pour la gestion des années scolaires.

Fonctionnalités :
- Liste des années scolaires (pour la consultation des années précédentes)
- Création d'une nouvelle année, avec recopie facultative des classes
  et de leurs frais de l'année courante
- Définition de l'année courante (où les nouveaux paiements sont enregistrés)
- Traçabilité dans le journal d'audit
"""

import re
from typing import Optional

from app.data.repositories.audit_repository import AuditRepository
from app.data.repositories.class_repository import ClassRepository
from app.data.repositories.fee_plan_repository import FeePlanRepository
from app.data.repositories.school_year_repository import SchoolYearRepository
from app.models.class_model import ClassModel
from app.models.school_year import SchoolYear
from app.services.exceptions import BusinessRuleError, ValidationError
from app.services.student_service import StudentService

LABEL_PATTERN = re.compile(r"^(\d{4})-(\d{4})$")


class SchoolYearService:
    """CRUD des années scolaires + recopie des classes d'une année à l'autre."""

    def __init__(
        self,
        student_service: Optional[StudentService] = None,
        school_year_repo: Optional[SchoolYearRepository] = None,
        class_repo: Optional[ClassRepository] = None,
        fee_plan_repo: Optional[FeePlanRepository] = None,
        audit_repo: Optional[AuditRepository] = None,
    ):
        self.student_service = student_service or StudentService()
        self.school_year_repo = school_year_repo or SchoolYearRepository()
        self.class_repo = class_repo or self.student_service.class_repo
        self.fee_plan_repo = fee_plan_repo or FeePlanRepository()
        self.audit_repo = audit_repo or AuditRepository()

    # ------------------------------------------------------------------
    # Lecture
    # ------------------------------------------------------------------

    def get_all(self):
        """Toutes les années scolaires (de la plus récente à la plus ancienne)."""
        return self.school_year_repo.get_all()

    def get_current(self):
        """Année scolaire courante (créée automatiquement si absente)."""
        return self.student_service.get_current_school_year()

    def get_by_id(self, year_id: int) -> Optional[SchoolYear]:
        return self.school_year_repo.get_by_id(year_id)

    # ------------------------------------------------------------------
    # Création / changement d'année courante
    # ------------------------------------------------------------------

    def create_school_year(self, label: str, copy_classes: bool = True,
                           set_current: bool = False) -> SchoolYear:
        """
        Crée une nouvelle année scolaire (format AAAA-AAAA).

        Args:
            label: Libellé au format AAAA-AAAA (ex : « 2025-2026 »)
            copy_classes: Recopie les classes (et leurs frais « Scolarité »)
                de l'année courante dans la nouvelle année
            set_current: Définit la nouvelle année comme courante
                (les nouveaux paiements y seront enregistrés)

        Raises:
            ValidationError: Format de libellé invalide
            BusinessRuleError: Libellé déjà utilisé
        """
        label = (label or "").strip()
        match = LABEL_PATTERN.match(label)
        if not match:
            raise ValidationError(
                "Le libellé doit être au format AAAA-AAAA (ex : 2025-2026).")
        start_year, end_year = int(match.group(1)), int(match.group(2))
        if end_year != start_year + 1:
            raise ValidationError(
                "L'année scolaire doit couvrir deux années consécutives "
                "(ex : 2025-2026).")

        current = self.get_current()

        year = SchoolYear(
            label=label,
            start_date=f"{start_year}-08-01",
            end_date=f"{end_year}-07-31",
            is_current=False,
        )
        try:
            year_id = self.school_year_repo.add(year)
        except Exception:
            raise BusinessRuleError(
                f"Une année scolaire « {label} » existe déjà.")

        copied = 0
        if copy_classes and current:
            copied = self._copy_classes(current.id, year_id)

        if set_current:
            self.school_year_repo.set_current(year_id)

        details = (f"{copied} classe(s) recopiée(s) depuis {current.label}"
                   if copy_classes and current and copied
                   else "Aucune classe recopiée")
        if set_current:
            details += " — définie comme année courante"
        self.audit_repo.add("Création", "Année scolaire", year_id, label, details)

        return self.school_year_repo.get_by_id(year_id)

    def set_current_year(self, year_id: int) -> bool:
        """
        Définit l'année scolaire courante (les nouveaux paiements y sont
        enregistrés). L'opération est journalisée.

        Raises:
            NotFoundError: Année inexistante
        """
        year = self.school_year_repo.get_by_id(year_id)
        if not year:
            from app.services.exceptions import NotFoundError
            raise NotFoundError(f"Année scolaire introuvable (ID: {year_id})")

        result = self.school_year_repo.set_current(year_id)
        if result:
            self.audit_repo.add(
                "Modification", "Année scolaire", year_id, year.label,
                "Définie comme année courante")
        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _copy_classes(self, from_year_id: int, to_year_id: int) -> int:
        """Recopie les classes et leurs frais « Scolarité » vers une année."""
        from app.data.repositories.fee_plan_repository import FeePlan

        copied = 0
        for c in self.class_repo.get_all(from_year_id):
            new_class_id = self.class_repo.add(ClassModel(
                name=c.name, level=c.level, school_year_id=to_year_id))
            for fee in self.fee_plan_repo.get_by_class(c.id, from_year_id):
                self.fee_plan_repo.add(FeePlan(
                    class_id=new_class_id,
                    school_year_id=to_year_id,
                    label=fee.label,
                    amount_int=fee.amount_int,
                    due_date=fee.due_date,
                ))
            copied += 1
        return copied
