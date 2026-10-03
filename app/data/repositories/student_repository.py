"""
Repository pour la gestion des élèves (Student)

Ce fichier contient uniquement les accès aux données SQLite.
Aucune logique d'interface graphique ne doit se trouver ici.
"""

import sqlite3
from typing import Optional, List
from app.models.student import Student
from app.data.db import Database
from app.services.exceptions import DatabaseError


class StudentRepository:
    """Repository pour les opérations CRUD sur les élèves."""

    def __init__(self, db: Optional[Database] = None):
        self.db = db if db is not None else Database()

    def add(self, student: Student) -> int:
        """
        Ajoute un élève dans la base de données.

        Utilise une transaction explicite pour garantir l'intégrité.

        Args:
            student: Objet Student à ajouter

        Returns:
            int: Identifiant de l'élève créé

        Raises:
            DatabaseError: En cas d'erreur de base de données
        """
        with self.db.transaction() as cursor:
            try:
                cursor.execute(
                    """
                    INSERT INTO student (
                        matricule, last_name, first_name, birth_date,
                        class_id, parent_name, parent_phone, parent_email, is_active
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        student.matricule,
                        student.last_name,
                        student.first_name,
                        student.birth_date,
                        student.class_id,
                        student.parent_name,
                        student.parent_phone,
                        student.parent_email,
                        1 if student.is_active else 0
                    )
                )
                return cursor.lastrowid
            except sqlite3.IntegrityError as e:
                raise DatabaseError(f"Erreur d'intégrité : {e}")

    def get_by_id(self, student_id: int) -> Optional[Student]:
        """
        Récupère un élève à partir de son identifiant.

        Args:
            student_id: Identifiant de l'élève

        Returns:
            Student | None: L'élève trouvé ou None s'il n'existe pas
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, matricule, last_name, first_name, birth_date,
                   class_id, parent_name, parent_phone, parent_email,
                   is_active, created_at
            FROM student
            WHERE id = ?
            """,
            (student_id,)
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_student(row)

    def get_by_matricule(self, matricule: str) -> Optional[Student]:
        """
        Récupère un élève à partir de son matricule.

        Args:
            matricule: Matricule de l'élève

        Returns:
            Student | None: L'élève trouvé ou None s'il n'existe pas
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, matricule, last_name, first_name, birth_date,
                   class_id, parent_name, parent_phone, parent_email,
                   is_active, created_at
            FROM student
            WHERE matricule = ?
            """,
            (matricule,)
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_student(row)

    def get_all(self, active_only: bool = False) -> List[Student]:
        """
        Récupère tous les élèves.

        Args:
            active_only: Si True, ne retourne que les élèves actifs

        Returns:
            List[Student]: Liste des élèves
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        if active_only:
            cursor.execute(
                """
                SELECT id, matricule, last_name, first_name, birth_date,
                       class_id, parent_name, parent_phone, parent_email,
                       is_active, created_at
                FROM student
                WHERE is_active = 1
                ORDER BY last_name COLLATE NOCASE, first_name COLLATE NOCASE
                """
            )
        else:
            cursor.execute(
                """
                SELECT id, matricule, last_name, first_name, birth_date,
                       class_id, parent_name, parent_phone, parent_email,
                       is_active, created_at
                FROM student
                ORDER BY last_name COLLATE NOCASE, first_name COLLATE NOCASE
                """
            )

        rows = cursor.fetchall()
        return [self._row_to_student(row) for row in rows]

    def get_by_class(self, class_id: int, active_only: bool = False) -> List[Student]:
        """
        Récupère les élèves d'une classe.

        Args:
            class_id: Identifiant de la classe
            active_only: Si True, ne retourne que les élèves actifs

        Returns:
            List[Student]: Liste des élèves de la classe
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        if active_only:
            cursor.execute(
                """
                SELECT id, matricule, last_name, first_name, birth_date,
                       class_id, parent_name, parent_phone, parent_email,
                       is_active, created_at
                FROM student
                WHERE class_id = ? AND is_active = 1
                ORDER BY last_name COLLATE NOCASE, first_name COLLATE NOCASE
                """,
                (class_id,)
            )
        else:
            cursor.execute(
                """
                SELECT id, matricule, last_name, first_name, birth_date,
                       class_id, parent_name, parent_phone, parent_email,
                       is_active, created_at
                FROM student
                WHERE class_id = ?
                ORDER BY last_name COLLATE NOCASE, first_name COLLATE NOCASE
                """,
                (class_id,)
            )

        rows = cursor.fetchall()
        return [self._row_to_student(row) for row in rows]

    def update(self, student: Student) -> bool:
        """
        Met à jour les informations d'un élève.

        Args:
            student: Objet Student avec les nouvelles valeurs

        Returns:
            bool: True si une ligne a été modifiée, sinon False

        Raises:
            DatabaseError: En cas d'erreur de base de données
        """
        if student.id is None:
            raise ValueError("Impossible de modifier un élève sans identifiant.")

        with self.db.transaction() as cursor:
            try:
                cursor.execute(
                    """
                    UPDATE student
                    SET matricule = ?, last_name = ?, first_name = ?,
                        birth_date = ?, class_id = ?, parent_name = ?,
                        parent_phone = ?, parent_email = ?, is_active = ?
                    WHERE id = ?
                    """,
                    (
                        student.matricule,
                        student.last_name,
                        student.first_name,
                        student.birth_date,
                        student.class_id,
                        student.parent_name,
                        student.parent_phone,
                        student.parent_email,
                        1 if student.is_active else 0,
                        student.id
                    )
                )
                return cursor.rowcount > 0
            except sqlite3.IntegrityError as e:
                raise DatabaseError(f"Erreur d'intégrité : {e}")

    def delete(self, student_id: int) -> bool:
        """
        Supprime un élève (DELETE physique).

        Note: En production, il est préférable d'utiliser un soft delete
        (is_active = False) pour conserver l'historique.

        Args:
            student_id: Identifiant de l'élève

        Returns:
            bool: True si l'élève a été supprimé, sinon False

        Raises:
            DatabaseError: Si l'élève a des paiements (contrainte FK)
        """
        with self.db.transaction() as cursor:
            try:
                cursor.execute(
                    """
                    DELETE FROM student
                    WHERE id = ?
                    """,
                    (student_id,)
                )
                return cursor.rowcount > 0
            except sqlite3.IntegrityError as e:
                raise DatabaseError("Impossible de supprimer un élève ayant des paiements")

    def search(self, query: str, active_only: bool = False) -> List[Student]:
        """
        Recherche un élève par nom, prénom ou matricule.

        Args:
            query: Terme de recherche
            active_only: Si True, ne retourne que les élèves actifs

        Returns:
            List[Student]: Liste des élèves correspondants
        """
        if query is None:
            return []

        query = query.strip()

        if not query:
            return self.get_all(active_only)

        conn = self.db.get_connection()
        cursor = conn.cursor()

        search_pattern = f"%{query}%"

        if active_only:
            cursor.execute(
                """
                SELECT id, matricule, last_name, first_name, birth_date,
                       class_id, parent_name, parent_phone, parent_email,
                       is_active, created_at
                FROM student
                WHERE is_active = 1
                  AND (last_name LIKE ? OR first_name LIKE ? OR matricule LIKE ?)
                ORDER BY last_name COLLATE NOCASE, first_name COLLATE NOCASE
                """,
                (search_pattern, search_pattern, search_pattern)
            )
        else:
            cursor.execute(
                """
                SELECT id, matricule, last_name, first_name, birth_date,
                       class_id, parent_name, parent_phone, parent_email,
                       is_active, created_at
                FROM student
                WHERE last_name LIKE ? OR first_name LIKE ? OR matricule LIKE ?
                ORDER BY last_name COLLATE NOCASE, first_name COLLATE NOCASE
                """,
                (search_pattern, search_pattern, search_pattern)
            )

        rows = cursor.fetchall()
        return [self._row_to_student(row) for row in rows]

    @staticmethod
    def _row_to_student(row) -> Student:
        """
        Transforme une ligne SQLite en objet Student.

        Le projet utilise une connexion SQLite configurée
        avec sqlite3.Row afin d'accéder aux colonnes par leur nom.
        """
        return Student(
            id=row["id"],
            matricule=row["matricule"],
            last_name=row["last_name"],
            first_name=row["first_name"],
            birth_date=row["birth_date"],
            class_id=row["class_id"],
            parent_name=row["parent_name"],
            parent_phone=row["parent_phone"],
            parent_email=row["parent_email"],
            is_active=bool(row["is_active"]),
            created_at=row["created_at"]
        )
