"""
Service pour la gestion des classes et de leurs plans de frais.

Règles :
- Une classe est rattachée à l'année scolaire courante
- Le plan de frais « Scolarité » (montant FCFA) est créé/modifié avec elle
- Suppression refusée si la classe contient des élèves
  (l'historique des reçus doit rester cohérent)
"""

from typing import List, Optional

from app.config import format_euros
from app.data.repositories.audit_repository import AuditRepository
from app.data.repositories.class_repository import ClassRepository
from app.data.repositories.fee_plan_repository import FeePlanRepository
from app.data.repositories.school_year_repository import SchoolYearRepository
from app.data.repositories.student_repository import StudentRepository
from app.models.class_model import ClassModel
from app.services.exceptions import BusinessRuleError, NotFoundError, ValidationError
from app.services.student_service import StudentService


class ClassService:
    """CRUD des classes avec leur plan de frais « Scolarité »."""

    FEE_LABEL = "Scolarité"

    def __init__(
        self,
        class_repo: Optional[ClassRepository] = None,
        fee_plan_repo: Optional[FeePlanRepository] = None,
        student_repo: Optional[StudentRepository] = None,
        school_year_repo: Optional[SchoolYearRepository] = None,
        student_service: Optional[StudentService] = None,
        audit_repo: Optional[AuditRepository] = None,
    ):
        self.class_repo = class_repo or ClassRepository()
        self.fee_plan_repo = fee_plan_repo or FeePlanRepository()
        self.student_repo = student_repo or StudentRepository()
        self.school_year_repo = school_year_repo or SchoolYearRepository()
        self.audit_repo = audit_repo or AuditRepository()
        self.student_service = student_service or StudentService(
            student_repo=self.student_repo,
            class_repo=self.class_repo,
            school_year_repo=self.school_year_repo,
        )

    # ------------------------------------------------------------------
    # Lecture
    # ------------------------------------------------------------------

    def get_all_classes(self, school_year_id: Optional[int] = None):
        """Liste des classes de l'année demandée (défaut : courante), avec frais et effectif."""
        year = self._resolve_year(school_year_id)
        result = []
        for c in self.class_repo.get_all(year.id):
            fee = self._get_fee(c.id, year.id)
            students = self.student_repo.get_by_class(c.id)
            result.append({
                "class": c,
                "fee_int": fee.amount_int if fee else 0,
                "fee_formatted": format_euros(fee.amount_int) if fee else "—",
                "due_date": fee.due_date if fee else None,
                "nb_students": len(students),
            })
        return result

    def get_class(self, class_id: int):
        """Détail d'une classe (dict class/fee_int/...)."""
        year = self.student_service.get_current_school_year()
        c = self.class_repo.get_by_id(class_id)
        if not c:
            raise NotFoundError(f"Classe introuvable (ID: {class_id})")
        fee = self._get_fee(class_id, year.id)
        return {
            "class": c,
            "fee_int": fee.amount_int if fee else 0,
            "fee_formatted": format_euros(fee.amount_int) if fee else "—",
            "due_date": fee.due_date if fee else None,
            "nb_students": len(self.student_repo.get_by_class(class_id)),
        }

    def _resolve_year(self, school_year_id: Optional[int] = None):
        """Année demandée, ou l'année courante par défaut."""
        if school_year_id:
            year = self.school_year_repo.get_by_id(school_year_id)
            if year is not None:
                return year
        return self.student_service.get_current_school_year()

    def _get_fee(self, class_id: int, school_year_id: int):
        fees = self.fee_plan_repo.get_by_class(class_id, school_year_id)
        for f in fees:
            if f.label == self.FEE_LABEL:
                return f
        return fees[0] if fees else None

    # ------------------------------------------------------------------
    # Création / modification / suppression
    # ------------------------------------------------------------------

    def create_class(self, name: str, level: str, fee_fcfa: float,
                     due_date: Optional[str] = None) -> ClassModel:
        """
        Crée une classe avec son plan de frais « Scolarité ».

        Args:
            name: Nom complet (ex : « 6ème A »)
            level: Niveau (ex : « 6ème ») ; déduit du nom si vide
            fee_fcfa: Montant annuel en FCFA
            due_date: Échéance optionnelle (AAAA-MM-JJ)

        Raises:
            ValidationError: Données invalides
            BusinessRuleError: Nom déjà utilisé pour l'année courante
        """
        name = (name or "").strip()
        if not name:
            raise ValidationError("Le nom de la classe est obligatoire")
        level = (level or "").strip() or self._infer_level(name)
        if not level:
            raise ValidationError("Le niveau est obligatoire")

        fee_int = self._validate_fee(fee_fcfa)

        year = self.student_service.get_current_school_year()

        # Unicité du nom pour l'année courante
        existing = {c.name.lower() for c in self.class_repo.get_all(year.id)}
        if name.lower() in existing:
            raise BusinessRuleError(
                f"Une classe « {name} » existe déjà pour l'année {year.label}")

        class_model = ClassModel(
            name=name, level=level, school_year_id=year.id)
        class_id = self.class_repo.add(class_model)
        class_model.id = class_id

        from app.data.repositories.fee_plan_repository import FeePlan
        self.fee_plan_repo.add(FeePlan(
            class_id=class_id,
            school_year_id=year.id,
            label=self.FEE_LABEL,
            amount_int=fee_int,
            due_date=due_date or None,
        ))

        self.audit_repo.add(
            "Création", "Classe", class_id, name,
            f"Niveau : {level} — Frais : {format_euros(fee_int)}/an "
            f"({year.label})")
        return class_model

    def update_class(self, class_id: int, name: str, level: str,
                     fee_fcfa: float, due_date: Optional[str] = None) -> ClassModel:
        """
        Modifie une classe (nom, niveau) et son plan de frais.

        Raises:
            ValidationError: Données invalides
            BusinessRuleError: Nom déjà pris par une autre classe
            NotFoundError: Classe inexistante
        """
        class_model = self.class_repo.get_by_id(class_id)
        if not class_model:
            raise NotFoundError(f"Classe introuvable (ID: {class_id})")
        previous = {
            "name": class_model.name,
            "level": class_model.level,
        }
        previous_fee = self._get_fee(class_id, class_model.school_year_id)

        name = (name or "").strip()
        if not name:
            raise ValidationError("Le nom de la classe est obligatoire")
        level = (level or "").strip() or self._infer_level(name)
        fee_int = self._validate_fee(fee_fcfa)

        year = self.student_service.get_current_school_year()
        others = {c.name.lower(): c.id
                  for c in self.class_repo.get_all(year.id)}
        if name.lower() in others and others[name.lower()] != class_id:
            raise BusinessRuleError(
                f"Une autre classe porte déjà le nom « {name} »")

        class_model.name = name
        class_model.level = level
        if not self.class_repo.update(class_model):
            raise NotFoundError(f"Classe introuvable (ID: {class_id})")

        fee = self._get_fee(class_id, year.id)
        if fee:
            fee.amount_int = fee_int
            fee.due_date = due_date or None
            self.fee_plan_repo.update(fee)
        else:
            from app.data.repositories.fee_plan_repository import FeePlan
            self.fee_plan_repo.add(FeePlan(
                class_id=class_id, school_year_id=year.id,
                label=self.FEE_LABEL, amount_int=fee_int,
                due_date=due_date or None))

        changes = []
        if previous["name"] != name:
            changes.append(f"Nom : « {previous['name']} » → « {name} »")
        if previous["level"] != level:
            changes.append(f"Niveau : {previous['level']} → {level}")
        old_fee = previous_fee.amount_int if previous_fee else 0
        if old_fee != fee_int:
            changes.append(f"Frais : {format_euros(old_fee)} → {format_euros(fee_int)}")
        self.audit_repo.add(
            "Modification", "Classe", class_id, name,
            " ; ".join(changes) or "Enregistrement sans changement")
        return class_model

    def delete_class(self, class_id: int) -> bool:
        """
        Supprime une classe (et son plan de frais, en CASCADE).

        La suppression est refusée si la classe contient encore des élèves :
        déplacez-les d'abord vers une autre classe.

        Raises:
            BusinessRuleError: Si la classe contient des élèves
            NotFoundError: Classe inexistante
        """
        class_model = self.class_repo.get_by_id(class_id)
        if not class_model:
            raise NotFoundError(f"Classe introuvable (ID: {class_id})")

        students = self.student_repo.get_by_class(class_id)
        if students:
            raise BusinessRuleError(
                f"Impossible de supprimer « {class_model.name} » : "
                f"{len(students)} élève(s) y sont encore inscrits. "
                "Déplacez-les d'abord vers une autre classe.")

        deleted = self.class_repo.delete(class_id)
        if deleted:
            self.audit_repo.add(
                "Suppression", "Classe", class_id, class_model.name,
                f"Niveau : {class_model.level}")
        return deleted

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_fee(fee_fcfa) -> int:
        """Valide et convertit un montant FCFA en entier strictement positif."""
        try:
            fee_int = int(round(float(str(fee_fcfa).replace(" ", "").replace(",", "."))))
        except (TypeError, ValueError):
            raise ValidationError("Montant des frais invalide")
        if fee_int <= 0:
            raise ValidationError("Le montant des frais doit être strictement positif")
        return fee_int

    @staticmethod
    def _infer_level(name: str) -> str:
        """Déduit le niveau du nom de classe (« 6ème A » → « 6ème »)."""
        for lvl in ("6ème", "5ème", "4ème", "3ème", "2nde", "1ère", "Tle",
                    "CP1", "CP2", "CE1", "CE2", "CM1", "CM2"):
            if name.lower().startswith(lvl.lower()):
                return lvl
        return name.split()[0] if name.split() else ""
