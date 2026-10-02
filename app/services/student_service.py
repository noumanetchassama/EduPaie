"""
Service pour la logique métier des étudiants

Fonctionnalités :
- Validation des données d'étudiant
- Génération du matricule unique
- CRUD complet avec règles métier
"""

import re
from datetime import datetime
from typing import List, Optional

from app.data.repositories.audit_repository import AuditRepository
from app.data.repositories.class_repository import ClassRepository
from app.data.repositories.payment_repository import PaymentRepository
from app.data.repositories.school_year_repository import SchoolYearRepository
from app.data.repositories.student_repository import StudentRepository
from app.models.student import Student
from app.services.exceptions import BusinessRuleError, NotFoundError, ValidationError


class StudentService:
    """Service contenant la logique métier pour les étudiants"""

    def __init__(
        self,
        student_repo: Optional[StudentRepository] = None,
        class_repo: Optional[ClassRepository] = None,
        payment_repo: Optional[PaymentRepository] = None,
        school_year_repo: Optional[SchoolYearRepository] = None,
        audit_repo: Optional[AuditRepository] = None,
    ):
        self.student_repo = student_repo or StudentRepository()
        self.class_repo = class_repo or ClassRepository()
        self.payment_repo = payment_repo or PaymentRepository()
        self.school_year_repo = school_year_repo or SchoolYearRepository()
        self.audit_repo = audit_repo or AuditRepository()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def get_current_school_year(self):
        """
        Retourne l'année scolaire courante.

        Si aucune n'est définie, l'année contenant la date du jour est
        automatiquement marquée comme courante (2025-2026 entre août et juillet).

        Raises:
            BusinessRuleError: Si aucune année scolaire n'existe
        """
        year = self.school_year_repo.get_current()
        if year:
            return year

        years = self.school_year_repo.get_all()
        if not years:
            raise BusinessRuleError(
                "Aucune année scolaire définie. Créez-en une pour démarrer.")

        today = datetime.now()
        # Année scolaire : de septembre (8) à juillet (6) de l'année suivante
        start = today.year if today.month >= 8 else today.year - 1
        label = f"{start}-{start + 1}"
        for y in years:
            if y.label == label:
                self.school_year_repo.set_current(y.id)
                return y

        # Aucune ne correspond : prendre la plus récente
        self.school_year_repo.set_current(years[0].id)
        return years[0]

    def get_all_classes(self, school_year_id: Optional[int] = None):
        """Retourne la liste des classes (objet ClassModel)."""
        if school_year_id is None:
            school_year_id = self.get_current_school_year().id
        return self.class_repo.get_all(school_year_id)

    def get_class_names(self, school_year_id: Optional[int] = None) -> List[str]:
        """Retourne les noms de classes pour les filtres de l'interface."""
        return [c.name for c in self.get_all_classes(school_year_id)]

    def find_class_by_name(self, name: str):
        """Retourne la classe portant ce nom (année courante), ou None."""
        classes = self.get_all_classes()
        for c in classes:
            if c.name.lower() == (name or "").strip().lower():
                return c
        return None

    def generate_matricule(self, class_id: int) -> str:
        """
        Génère un matricule unique de la forme AAAA-CLASSE-NNNN
        (ex: 2025-6EMEA-0007), en comptant les élèves existants.
        """
        year = datetime.now().year
        class_obj = self.class_repo.get_by_id(class_id)
        code = "CLAS"
        if class_obj and class_obj.name:
            code = re.sub(r"[^A-Z0-9]", "",
                          class_obj.name.upper().replace("È", "E").replace("É", "E"))
            code = code[:6] if code else "CLAS"

        counter = 1
        while True:
            candidate = f"{year}-{code}-{counter:04d}"
            if not self.student_repo.get_by_matricule(candidate):
                return candidate
            counter += 1

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create_student(
        self,
        last_name: str,
        first_name: str,
        class_id: int,
        matricule: Optional[str] = None,
        birth_date: Optional[str] = None,
        parent_name: Optional[str] = None,
        parent_phone: Optional[str] = None,
        parent_email: Optional[str] = None,
    ) -> Student:
        """
        Crée un nouvel étudiant avec validation.

        Le matricule est généré automatiquement s'il n'est pas fourni.

        Raises:
            ValidationError: Si les données sont invalides
            BusinessRuleError: Si une règle métier est violée
            NotFoundError: Si la classe n'existe pas
        """
        if not last_name or not last_name.strip():
            raise ValidationError("Le nom est obligatoire")
        if not first_name or not first_name.strip():
            raise ValidationError("Le prénom est obligatoire")
        if class_id is None:
            raise ValidationError("La classe est obligatoire")

        last_name = last_name.strip()
        first_name = first_name.strip()
        if not self._validate_name(last_name):
            raise ValidationError("Le nom contient des caractères invalides")
        if not self._validate_name(first_name):
            raise ValidationError("Le prénom contient des caractères invalides")

        class_obj = self.class_repo.get_by_id(class_id)
        if not class_obj:
            raise NotFoundError(f"Classe introuvable (ID: {class_id})")

        if birth_date and not self._validate_date(birth_date):
            raise ValidationError("Format de date de naissance invalide (attendu : AAAA-MM-JJ)")
        if parent_phone and not self._validate_phone(parent_phone):
            raise ValidationError("Format de téléphone invalide")
        if parent_email and not self._validate_email(parent_email):
            raise ValidationError("Format d'email invalide")

        if matricule:
            matricule = matricule.strip()
            if len(matricule) < 3:
                raise ValidationError("Le matricule doit contenir au moins 3 caractères")
            existing = self.student_repo.get_by_matricule(matricule)
            if existing:
                raise BusinessRuleError(f"Le matricule '{matricule}' est déjà utilisé")
        else:
            matricule = self.generate_matricule(class_id)

        student = Student(
            matricule=matricule,
            last_name=last_name,
            first_name=first_name,
            birth_date=birth_date or None,
            class_id=class_id,
            parent_name=parent_name.strip() if parent_name else None,
            parent_phone=parent_phone.strip() if parent_phone else None,
            parent_email=parent_email.strip().lower() if parent_email else None,
            is_active=True,
        )

        student_id = self.student_repo.add(student)
        student.id = student_id

        self.audit_repo.add(
            "Création", "Élève", student.id,
            f"{student.first_name} {student.last_name} ({student.matricule})",
            f"Classe : {class_obj.name}")
        return student

    def update_student(self, student: Student) -> Student:
        """
        Met à jour un étudiant avec validation.

        Raises:
            ValidationError: Si les données sont invalides
            BusinessRuleError: Si le matricule est déjà utilisé
            NotFoundError: Si l'étudiant ou la classe n'existe pas
        """
        if student.id is None:
            raise ValidationError("Impossible de modifier un étudiant sans identifiant")

        previous = self.student_repo.get_by_id(student.id)

        if not student.last_name or not student.last_name.strip():
            raise ValidationError("Le nom est obligatoire")
        if not student.first_name or not student.first_name.strip():
            raise ValidationError("Le prénom est obligatoire")
        if not self._validate_name(student.last_name.strip()):
            raise ValidationError("Le nom contient des caractères invalides")
        if not self._validate_name(student.first_name.strip()):
            raise ValidationError("Le prénom contient des caractères invalides")
        if not student.class_id:
            raise ValidationError("La classe est obligatoire")

        class_obj = self.class_repo.get_by_id(student.class_id)
        if not class_obj:
            raise NotFoundError(f"Classe introuvable (ID: {student.class_id})")

        if student.birth_date and not self._validate_date(student.birth_date):
            raise ValidationError("Format de date de naissance invalide (attendu : AAAA-MM-JJ)")
        if student.parent_phone and not self._validate_phone(student.parent_phone):
            raise ValidationError("Format de téléphone invalide")
        if student.parent_email and not self._validate_email(student.parent_email):
            raise ValidationError("Format d'email invalide")

        if student.matricule:
            student.matricule = student.matricule.strip()
            existing = self.student_repo.get_by_matricule(student.matricule)
            if existing and existing.id != student.id:
                raise BusinessRuleError(
                    f"Le matricule '{student.matricule}' est déjà utilisé")

        student.last_name = student.last_name.strip()
        student.first_name = student.first_name.strip()
        student.parent_name = student.parent_name.strip() if student.parent_name else None
        student.parent_phone = student.parent_phone.strip() if student.parent_phone else None
        student.parent_email = student.parent_email.strip().lower() if student.parent_email else None

        success = self.student_repo.update(student)
        if not success:
            raise NotFoundError(f"Étudiant introuvable (ID: {student.id})")

        self._audit_update(student, previous)
        return student

    def _audit_update(self, student: Student, previous: Optional[Student]):
        """Journalise les champs réellement modifiés d'un élève."""
        if previous is None:
            changes = []
        else:
            mapping = [
                ((previous.last_name or ""), (student.last_name or ""), "nom"),
                ((previous.first_name or ""), (student.first_name or ""), "prénom"),
                ((previous.matricule or ""), (student.matricule or ""), "matricule"),
                ((previous.birth_date or ""), (student.birth_date or ""), "date de naissance"),
                (previous.class_id, student.class_id, "classe"),
                ((previous.parent_name or ""), (student.parent_name or ""), "parent"),
                ((previous.parent_phone or ""), (student.parent_phone or ""), "téléphone parent"),
                ((previous.parent_email or ""), (student.parent_email or ""), "email parent"),
                (previous.is_active, student.is_active, "statut d'activité"),
            ]
            changes = [label for old, new, label in mapping if old != new]
        details = ("Champs modifiés : " + ", ".join(changes)) if changes \
            else "Enregistrement sans changement"
        self.audit_repo.add(
            "Modification", "Élève", student.id,
            f"{student.first_name} {student.last_name} ({student.matricule})",
            details)

    def move_student(self, student_id: int, new_class_id: int) -> Student:
        """
        Déplace un élève vers une autre classe (transfert).

        Les paiements déjà enregistrés sont conservés ; le total dû est
        recalculé à partir des frais de la nouvelle classe.

        Raises:
            NotFoundError: Élève ou classe inexistante
            BusinessRuleError: L'élève est déjà dans cette classe
        """
        student = self.student_repo.get_by_id(student_id)
        if not student:
            raise NotFoundError(f"Étudiant introuvable (ID: {student_id})")

        new_class = self.class_repo.get_by_id(new_class_id)
        if not new_class:
            raise NotFoundError(f"Classe introuvable (ID: {new_class_id})")
        if new_class.id == student.class_id:
            raise BusinessRuleError(
                f"L'élève est déjà inscrit en « {new_class.name} ».")

        old_class = self.class_repo.get_by_id(student.class_id)
        old_name = old_class.name if old_class else "?"

        student.class_id = new_class.id
        success = self.student_repo.update(student)
        if not success:
            raise NotFoundError(f"Étudiant introuvable (ID: {student_id})")

        self.audit_repo.add(
            "Modification", "Élève", student.id,
            f"{student.first_name} {student.last_name} ({student.matricule})",
            f"Transfert de classe : « {old_name} » → « {new_class.name} »")
        return student

    def get_class_for_year(self, student: Student, school_year_id: int):
        """
        Retourne la classe de l'élève pour l'année scolaire donnée.

        Les élèves étant rattachés à la classe de leur inscription, la
        consultation d'une année antérieure apparie la classe par son NOM
        (les classes sont recréées à l'identique chaque année).
        Retourne None si aucune classe équivalente n'existe cette année-là.
        """
        if not student or not student.class_id:
            return None
        current = self.class_repo.get_by_id(student.class_id)
        if not current:
            return None
        if current.school_year_id == school_year_id:
            return current
        for c in self.class_repo.get_all(school_year_id):
            if c.name == current.name:
                return c
        return None

    def delete_student(self, student_id: int) -> bool:
        """
        Supprime un étudiant.

        La suppression est bloquée s'il existe des paiements (même annulés),
        afin de préserver l'historique des reçus émis.

        Raises:
            BusinessRuleError: Si l'étudiant a des paiements
            NotFoundError: Si l'étudiant n'existe pas
        """
        student = self.student_repo.get_by_id(student_id)
        if not student:
            raise NotFoundError(f"Étudiant introuvable (ID: {student_id})")

        payments = self.payment_repo.get_by_student(student_id, valid_only=False)
        if payments:
            raise BusinessRuleError(
                "Impossible de supprimer un élève ayant des paiements enregistrés "
                "(l'historique des reçus doit être conservé).")

        deleted = self.student_repo.delete(student_id)
        if deleted:
            class_obj = self.class_repo.get_by_id(student.class_id)
            self.audit_repo.add(
                "Suppression", "Élève", student_id,
                f"{student.first_name} {student.last_name} ({student.matricule})",
                f"Classe au moment de la suppression : "
                f"{class_obj.name if class_obj else '?'}")
        return deleted

    def count_payments(self, student_id: int) -> int:
        """Nombre de paiements enregistrés pour un élève (annulés inclus)."""
        return len(self.payment_repo.get_by_student(student_id, valid_only=False))

    def archive_student(self, student_id: int) -> bool:
        """
        Archive un élève (is_active = False) : il disparaît des listes et
        du tableau de bord, tandis que ses paiements et reçus restent
        consultables (l'historique financier est intouché).

        Retourne False si l'élève était déjà archivé.

        Raises:
            NotFoundError: Si l'élève n'existe pas
        """
        student = self.student_repo.get_by_id(student_id)
        if not student:
            raise NotFoundError(f"Étudiant introuvable (ID: {student_id})")
        if not student.is_active:
            return False

        student.is_active = False
        if not self.student_repo.update(student):
            raise NotFoundError(f"Étudiant introuvable (ID: {student_id})")

        class_obj = self.class_repo.get_by_id(student.class_id)
        self.audit_repo.add(
            "Archivage", "Élève", student_id,
            f"{student.first_name} {student.last_name} ({student.matricule})",
            "Élève archivé (paiements et reçus conservés) — classe : "
            f"{class_obj.name if class_obj else '?'}")
        return True

    def get_student(self, student_id: int) -> Optional[Student]:
        """Récupère un étudiant par son identifiant."""
        return self.student_repo.get_by_id(student_id)

    def get_all_students(self, active_only: bool = False) -> List[Student]:
        """Récupère tous les étudiants."""
        return self.student_repo.get_all(active_only)

    def search_students(self, query: str, active_only: bool = False) -> List[Student]:
        """Recherche des étudiants par nom, prénom ou matricule."""
        return self.student_repo.search(query, active_only)

    def get_students_by_class(self, class_id: int, active_only: bool = False) -> List[Student]:
        """Récupère les étudiants d'une classe."""
        return self.student_repo.get_by_class(class_id, active_only)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_name(name: str) -> bool:
        """Nom : lettres, espaces, tirets et apostrophes uniquement."""
        if not name:
            return False
        return all(c.isalpha() or c.isspace() or c in "-'" for c in name)

    @staticmethod
    def _validate_date(date_str: str) -> bool:
        """Valide une date au format AAAA-MM-JJ."""
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _validate_phone(phone: str) -> bool:
        """Téléphone : 10 à 15 chiffres après nettoyage."""
        digits = re.sub(r"[^\d]", "", phone)
        return 10 <= len(digits) <= 15

    @staticmethod
    def _validate_email(email: str) -> bool:
        """Valide une adresse email simple."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None
