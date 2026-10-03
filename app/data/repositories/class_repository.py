"""
Repository pour la gestion des classes (ClassModel)

Ce fichier contient uniquement les accès aux données SQLite.
Aucune logique d'interface graphique ne doit se trouver ici.
"""

import sqlite3
from typing import Optional, List
from app.models.class_model import ClassModel
from app.data.db import Database
from app.services.exceptions import DatabaseError


class ClassRepository:
    """Repository pour les opérations CRUD sur les classes."""

    def __init__(self, db: Optional[Database] = None):
        self.db = db if db is not None else Database()

    def add(self, class_model: ClassModel) -> int:
        """
        Ajoute une classe dans la base de données.

        Args:
            class_model: Objet ClassModel à ajouter

        Returns:
            int: Identifiant de la classe créée

        Raises:
            DatabaseError: En cas d'erreur de base de données
        """
        with self.db.transaction() as cursor:
            try:
                cursor.execute(
                    """
                    INSERT INTO class (name, level, school_year_id)
                    VALUES (?, ?, ?)
                    """,
                    (class_model.name, class_model.level, class_model.school_year_id)
                )
                return cursor.lastrowid
            except sqlite3.IntegrityError as e:
                raise DatabaseError(f"Erreur d'intégrité : {e}")

    def get_by_id(self, class_id: int) -> Optional[ClassModel]:
        """
        Récupère une classe à partir de son identifiant.

        Args:
            class_id: Identifiant de la classe

        Returns:
            ClassModel | None: La classe trouvée ou None si elle n'existe pas
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, name, level, school_year_id, date_creation
            FROM class
            WHERE id = ?
            """,
            (class_id,)
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_class(row)

    def get_all(self, school_year_id: int = None) -> List[ClassModel]:
        """
        Récupère toutes les classes.

        Args:
            school_year_id: Identifiant de l'année scolaire (optionnel)

        Returns:
            List[ClassModel]: Liste des classes
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        if school_year_id:
            cursor.execute(
                """
                SELECT id, name, level, school_year_id, date_creation
                FROM class
                WHERE school_year_id = ?
                ORDER BY name COLLATE NOCASE
                """,
                (school_year_id,)
            )
        else:
            cursor.execute(
                """
                SELECT id, name, level, school_year_id, date_creation
                FROM class
                ORDER BY name COLLATE NOCASE
                """
            )

        rows = cursor.fetchall()
        return [self._row_to_class(row) for row in rows]

    def update(self, class_model: ClassModel) -> bool:
        """
        Met à jour les informations d'une classe.

        Args:
            class_model: Objet ClassModel avec les nouvelles valeurs

        Returns:
            bool: True si une ligne a été modifiée, sinon False

        Raises:
            DatabaseError: En cas d'erreur de base de données
        """
        if class_model.id is None:
            raise ValueError("Impossible de modifier une classe sans identifiant.")

        with self.db.transaction() as cursor:
            try:
                cursor.execute(
                    """
                    UPDATE class
                    SET name = ?, level = ?, school_year_id = ?
                    WHERE id = ?
                    """,
                    (class_model.name, class_model.level, class_model.school_year_id, class_model.id)
                )
                return cursor.rowcount > 0
            except sqlite3.IntegrityError as e:
                raise DatabaseError(f"Erreur d'intégrité : {e}")

    def delete(self, class_id: int) -> bool:
        """
        Supprime une classe.

        Args:
            class_id: Identifiant de la classe

        Returns:
            bool: True si la classe a été supprimée, sinon False

        Raises:
            DatabaseError: Si la classe a des élèves (contrainte FK)
        """
        with self.db.transaction() as cursor:
            try:
                cursor.execute(
                    """
                    DELETE FROM class
                    WHERE id = ?
                    """,
                    (class_id,)
                )
                return cursor.rowcount > 0
            except sqlite3.IntegrityError as e:
                raise DatabaseError("Impossible de supprimer une classe contenant des élèves")

    def search(self, query: str, school_year_id: int = None) -> List[ClassModel]:
        """
        Recherche une classe par nom ou niveau.

        Args:
            query: Terme de recherche
            school_year_id: Identifiant de l'année scolaire (optionnel)

        Returns:
            List[ClassModel]: Liste des classes correspondantes
        """
        if query is None:
            return []

        query = query.strip()

        if not query:
            return self.get_all(school_year_id)

        conn = self.db.get_connection()
        cursor = conn.cursor()

        search_pattern = f"%{query}%"

        if school_year_id:
            cursor.execute(
                """
                SELECT id, name, level, school_year_id, date_creation
                FROM class
                WHERE school_year_id = ?
                  AND (name LIKE ? OR level LIKE ?)
                ORDER BY name COLLATE NOCASE
                """,
                (school_year_id, search_pattern, search_pattern)
            )
        else:
            cursor.execute(
                """
                SELECT id, name, level, school_year_id, date_creation
                FROM class
                WHERE name LIKE ? OR level LIKE ?
                ORDER BY name COLLATE NOCASE
                """,
                (search_pattern, search_pattern)
            )

        rows = cursor.fetchall()
        return [self._row_to_class(row) for row in rows]

    @staticmethod
    def _row_to_class(row) -> ClassModel:
        """
        Transforme une ligne SQLite en objet ClassModel.
        """
        return ClassModel(
            id=row["id"],
            name=row["name"],
            level=row["level"],
            school_year_id=row["school_year_id"],
            date_creation=row["date_creation"]
        )
