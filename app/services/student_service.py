"""
Service pour la logique métier des étudiants

Fonctionnalités :
- Validation des données d'étudiant
- Génération du matricule unique
- Création, modification, suppression
"""

import re
from typing import Optional, List
from app.models.student import Student
from app.data.repositories.student_repository import StudentRepository
from app.data.repositories.class_repository import ClassRepository
from app.config import euros_to_cents
from app.services.exceptions import ValidationError, BusinessRuleError, NotFoundError


class StudentService:
    """Service contenant la logique métier pour les étudiants"""

    def __init__(
        self,
        student_repo: Optional[StudentRepository] = None,
        class_repo: Optional[ClassRepository] = None
    ):
        self.student_repo = student_repo if student_repo else StudentRepository()
        self.class_repo = class_repo if class_repo else ClassRepository()

    def create_student(
        self,
        matricule: str,
        last_name: str,
        first_name: str,
        class_id: int,
        birth_date: str = None,
        parent_name: str = None,
        parent_phone: str = None,
        parent_email: str = None
    ) -> Student:
        """
        Crée un nouvel étudiant avec validation.

        Args:
            matricule: Matricule unique
            last_name: Nom de famille
            first_name: Prénom
            class_id: Identifiant de la classe
            birth_date: Date de naissance (optionnel)
            parent_name: Nom du parent (optionnel)
            parent_phone: Téléphone du parent (optionnel)
            parent_email: Email du parent (optionnel)

        Returns:
            Student: L'étudiant créé

        Raises:
            ValidationError: Si les données sont invalides
            BusinessRuleError: Si une règle métier est violée
        """
        # Validation du matricule
        if not matricule or not matricule.strip():
            raise ValidationError("Le matricule est obligatoire")

        matricule = matricule.strip()
        if len(matricule) < 3:
            raise ValidationError("Le matricule doit contenir au moins 3 caractères")

        # Vérifier l'unicité du matricule
        existing = self.student_repo.get_by_matricule(matricule)
        if existing:
            raise BusinessRuleError(f"Le matricule '{matricule}' est déjà utilisé")

        # Validation du nom
        if not last_name or not last_name.strip():
            raise ValidationError("Le nom est obligatoire")
        if not self._validate_name(last_name):
            raise ValidationError("Le nom contient des caractères invalides")

        # Validation du prénom
        if not first_name or not first_name.strip():
            raise ValidationError("Le prénom est obligatoire")
        if not self._validate_name(first_name):
            raise ValidationError("Le prénom contient des caractères invalides")

        # Validation de la classe
        if class_id is None:
            raise ValidationError("La classe est obligatoire")

        class_obj = self.class_repo.get_by_id(class_id)
        if not class_obj:
            raise NotFoundError(f"Classe introuvable (ID: {class_id})")

        # Validation de la date de naissance
        if birth_date:
            if not self._validate_date(birth_date):
                raise ValidationError("Format de date invalide (attendu: YYYY-MM-DD)")

        # Validation du téléphone
        if parent_phone and not self._validate_phone(parent_phone):
            raise ValidationError("Format de téléphone invalide")

        # Validation de l'email
        if parent_email and not self._validate_email(parent_email):
            raise ValidationError("Format d'email invalide")

        # Création de l'étudiant
        student = Student(
            matricule=matricule,
            last_name=last_name.strip(),
            first_name=first_name.strip(),
            birth_date=birth_date,
            class_id=class_id,
            parent_name=parent_name.strip() if parent_name else None,
            parent_phone=parent_phone.strip() if parent_phone else None,
            parent_email=parent_email.strip().lower() if parent_email else None,
            is_active=True
        )

        student_id = self.student_repo.add(student)
        student.id = student_id

        return student

    def update_student(self, student: Student) -> Student:
        """
        Met à jour un étudiant avec validation.

        Args:
            student: Objet Student avec les nouvelles valeurs

        Returns:
            Student: L'étudiant mis à jour

        Raises:
            ValidationError: Si les données sont invalides
            BusinessRuleError: Si une règle métier est violée
        """
        if student.id is None:
            raise ValidationError("Impossible de modifier un étudiant sans identifiant")

        # Validation du matricule (si modifié)
        if student.matricule:
            student.matricule = student.matricule.strip()
            existing = self.student_repo.get_by_matricule(student.matricule)
            if existing and existing.id != student.id:
                raise BusinessRuleError(f"Le matricule '{student.matricule}' est déjà utilisé")

        # Validation du nom
        if not student.last_name or not student.last_name.strip():
            raise ValidationError("Le nom est obligatoire")
        if not self._validate_name(student.last_name):
            raise ValidationError("Le nom contient des caractères invalides")

        # Validation du prénom
        if not student.first_name or not student.first_name.strip():
            raise ValidationError("Le prénom est obligatoire")
        if not self._validate_name(student.first_name):
            raise ValidationError("Le prénom contient des caractères invalides")

        # Validation de la classe
        if student.class_id:
            class_obj = self.class_repo.get_by_id(student.class_id)
            if not class_obj:
                raise NotFoundError(f"Classe introuvable (ID: {student.class_id})")

        # Validation de la date de naissance
        if student.birth_date and not self._validate_date(student.birth_date):
            raise ValidationError("Format de date invalide (attendu: YYYY-MM-DD)")

        # Validation du téléphone
        if student.parent_phone and not self._validate_phone(student.parent_phone):
            raise ValidationError("Format de téléphone invalide")

        # Validation de l'email
        if student.parent_email and not self._validate_email(student.parent_email):
            raise ValidationError("Format d'email invalide")

        # Nettoyage des données
        student.last_name = student.last_name.strip()
        student.first_name = student.first_name.strip()
        student.parent_name = student.parent_name.strip() if student.parent_name else None
        student.parent_phone = student.parent_phone.strip() if student.parent_phone else None
        student.parent_email = student.parent_email.strip().lower() if student.parent_email else None

        success = self.student_repo.update(student)
        if not success:
            raise NotFoundError(f"Étudiant introuvable (ID: {student.id})")

        return student

    def delete_student(self, student_id: int) -> bool:
        """
        Supprime un étudiant.

        Vérifie d'abord qu'il n'a pas de paiements.

        Args:
            student_id: Identifiant de l'étudiant

        Returns:
            bool: True si l'étudiant a été supprimé

        Raises:
            BusinessRuleError: Si l'étudiant a des paiements
        """
        # TODO: Vérifier s'il y a des paiements
        # Pour l'instant, on laisse le repository gérer la contrainte FK

        return self.student_repo.delete(student_id)

    def get_student(self, student_id: int) -> Optional[Student]:
        """
        Récupère un étudiant par son identifiant.

        Args:
            student_id: Identifiant de l'étudiant

        Returns:
            Student | None: L'étudiant trouvé ou None
        """
        return self.student_repo.get_by_id(student_id)

    def get_all_students(self, active_only: bool = False) -> List[Student]:
        """
        Récupère tous les étudiants.

        Args:
            active_only: Si True, ne retourne que les étudiants actifs

        Returns:
            List[Student]: Liste des étudiants
        """
        return self.student_repo.get_all(active_only)

    def search_students(self, query: str, active_only: bool = False) -> List[Student]:
        """
        Recherche des étudiants par nom, prénom ou matricule.

        Args:
            query: Terme de recherche
            active_only: Si True, ne retourne que les étudiants actifs

        Returns:
            List[Student]: Liste des étudiants correspondants
        """
        return self.student_repo.search(query, active_only)

    def get_students_by_class(self, class_id: int, active_only: bool = False) -> List[Student]:
        """
        Récupère les étudiants d'une classe.

        Args:
            class_id: Identifiant de la classe
            active_only: Si True, ne retourne que les étudiants actifs

        Returns:
            List[Student]: Liste des étudiants de la classe
        """
        return self.student_repo.get_by_class(class_id, active_only)

    def generate_matricule(self, class_id: int, counter: int) -> str:
        """
        Génère un matricule unique basé sur la classe et un compteur.

        Format : AAAA-CCCC-NNNN
        - AAAA : Année courante
        - CCCC : Code de la classe
        - NNNN : Numéro séquentiel

        Args:
            class_id: Identifiant de la classe
            counter: Compteur

        Returns:
            str: Matricule généré
        """
        from datetime import datetime

        year = datetime.now().year
        class_obj = self.class_repo.get_by_id(class_id)
        class_code = class_obj.name.replace(' ', '').upper()[:4] if class_obj else "CLAS"

        return f"{year}-{class_code}-{counter:04d}"

    @staticmethod
    def _validate_name(name: str) -> bool:
        """
        Valide un nom (lettres, espaces, tirets, apostrophes uniquement).

        Args:
            name: Nom à valider

        Returns:
            bool: True si valide
        """
        if not name:
            return False
        return all(c.isalpha() or c.isspace() or c in "-'" for c in name)

    @staticmethod
    def _validate_date(date_str: str) -> bool:
        """
        Valide une date au format YYYY-MM-DD.

        Args:
            date_str: Date à valider

        Returns:
            bool: True si valide
        """
        try:
            from datetime import datetime
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    @staticmethod
    def _validate_phone(phone: str) -> bool:
        """
        Valide un numéro de téléphone.

        Accepte les formats avec espaces, points, tirets.

        Args:
            phone: Téléphone à valider

        Returns:
            bool: True si valide
        """
        # Nettoyer : garder uniquement les chiffres
        digits = re.sub(r'[^\d]', '', phone)
        return len(digits) >= 10 and len(digits) <= 15

    @staticmethod
    def _validate_email(email: str) -> bool:
        """
        Valide une adresse email.

        Args:
            email: Email à valider

        Returns:
            bool: True si valide
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
