"""
Repository pour la gestion des années scolaires (SchoolYear)

Ce fichier contient uniquement les accès aux données SQLite.
Aucune logique d'interface graphique ne doit se trouver ici.
"""

import sqlite3
from typing import Optional, List
from app.models.school_year import SchoolYear
from app.data.db import Database
from app.services.exceptions import DatabaseError


class SchoolYearRepository:
    """Repository pour les opérations CRUD sur les années scolaires."""

    def __init__(self, db: Optional[Database] = None):
        self.db = db if db is not None else Database()

    def add(self, school_year: SchoolYear) -> int:
        """
        Ajoute une année scolaire dans la base de données.

        Args:
            school_year: Objet SchoolYear à ajouter

        Returns:
            int: Identifiant de l'année scolaire créée

        Raises:
            DatabaseError: En cas d'erreur de base de données
        """
        with self.db.transaction() as cursor:
            try:
                cursor.execute(
                    """
                    INSERT INTO school_year (label, start_date, end_date, is_current)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        school_year.label,
                        school_year.start_date,
                        school_year.end_date,
                        1 if school_year.is_current else 0
                    )
                )
                return cursor.lastrowid
            except sqlite3.IntegrityError as e:
                raise DatabaseError(f"Erreur d'intégrité : {e}")

    def get_by_id(self, year_id: int) -> Optional[SchoolYear]:
        """
        Récupère une année scolaire à partir de son identifiant.

        Args:
            year_id: Identifiant de l'année scolaire

        Returns:
            SchoolYear | None: L'année scolaire trouvée ou None si elle n'existe pas
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, label, start_date, end_date, is_current
            FROM school_year
            WHERE id = ?
            """,
            (year_id,)
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_school_year(row)

    def get_current(self) -> Optional[SchoolYear]:
        """
        Récupère l'année scolaire courante.

        Returns:
            SchoolYear | None: L'année scolaire courante ou None
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, label, start_date, end_date, is_current
            FROM school_year
            WHERE is_current = 1
            LIMIT 1
            """
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_school_year(row)

    def get_all(self) -> List[SchoolYear]:
        """
        Récupère toutes les années scolaires.

        Returns:
            List[SchoolYear]: Liste des années scolaires
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, label, start_date, end_date, is_current
            FROM school_year
            ORDER BY start_date DESC
            """
        )

        rows = cursor.fetchall()
        return [self._row_to_school_year(row) for row in rows]

    def update(self, school_year: SchoolYear) -> bool:
        """
        Met à jour les informations d'une année scolaire.

        Args:
            school_year: Objet SchoolYear avec les nouvelles valeurs

        Returns:
            bool: True si une ligne a été modifiée, sinon False

        Raises:
            DatabaseError: En cas d'erreur de base de données
        """
        if school_year.id is None:
            raise ValueError("Impossible de modifier une année scolaire sans identifiant.")

        with self.db.transaction() as cursor:
            try:
                cursor.execute(
                    """
                    UPDATE school_year
                    SET label = ?, start_date = ?, end_date = ?, is_current = ?
                    WHERE id = ?
                    """,
                    (
                        school_year.label,
                        school_year.start_date,
                        school_year.end_date,
                        1 if school_year.is_current else 0,
                        school_year.id
                    )
                )
                return cursor.rowcount > 0
            except sqlite3.IntegrityError as e:
                raise DatabaseError(f"Erreur d'intégrité : {e}")

    def set_current(self, year_id: int) -> bool:
        """
        Définit une année scolaire comme courante.

        Désactive toutes les autres années.

        Args:
            year_id: Identifiant de l'année scolaire

        Returns:
            bool: True si l'opération a réussi
        """
        with self.db.transaction() as cursor:
            # Désactiver toutes les années
            cursor.execute("UPDATE school_year SET is_current = 0")

            # Activer l'année demandée
            cursor.execute(
                """
                UPDATE school_year
                SET is_current = 1
                WHERE id = ?
                """,
                (year_id,)
            )

            return cursor.rowcount > 0

    def delete(self, year_id: int) -> bool:
        """
        Supprime une année scolaire.

        Args:
            year_id: Identifiant de l'année scolaire

        Returns:
            bool: True si l'année scolaire a été supprimée, sinon False

        Raises:
            DatabaseError: Si l'année a des données liées (contrainte FK)
        """
        with self.db.transaction() as cursor:
            try:
                cursor.execute(
                    """
                    DELETE FROM school_year
                    WHERE id = ?
                    """,
                    (year_id,)
                )
                return cursor.rowcount > 0
            except sqlite3.IntegrityError as e:
                raise DatabaseError("Impossible de supprimer une année scolaire contenant des données")

    @staticmethod
    def _row_to_school_year(row) -> SchoolYear:
        """
        Transforme une ligne SQLite en objet SchoolYear.
        """
        return SchoolYear(
            id=row["id"],
            label=row["label"],
            start_date=row["start_date"],
            end_date=row["end_date"],
            is_current=bool(row["is_current"])
        )
