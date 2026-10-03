"""
Repository pour la gestion des plans de frais (FeePlan)

Ce fichier contient uniquement les accès aux données SQLite.
Aucune logique d'interface graphique ne doit se trouver ici.
"""

import sqlite3
from typing import Optional, List
from app.data.db import Database
from app.services.exceptions import DatabaseError


class FeePlan:
    """Modèle simple pour un plan de frais (pour éviter créer un fichier modèle séparé)"""

    def __init__(
        self,
        id: Optional[int] = None,
        class_id: Optional[int] = None,
        school_year_id: Optional[int] = None,
        label: Optional[str] = None,
        amount_int: int = 0,
        due_date: Optional[str] = None,
        created_at: Optional[str] = None
    ):
        self.id = id
        self.class_id = class_id
        self.school_year_id = school_year_id
        self.label = label
        self.amount_int = amount_int  # Montant en cents
        self.due_date = due_date
        self.created_at = created_at

    def __repr__(self):
        return f"FeePlan(id={self.id}, label='{self.label}', amount_int={self.amount_int})"


class FeePlanRepository:
    """Repository pour les opérations CRUD sur les plans de frais."""

    def __init__(self, db: Optional[Database] = None):
        self.db = db if db is not None else Database()

    def add(self, fee_plan: FeePlan) -> int:
        """
        Ajoute un plan de frais dans la base de données.

        Args:
            fee_plan: Objet FeePlan à ajouter

        Returns:
            int: Identifiant du plan de frais créé

        Raises:
            DatabaseError: En cas d'erreur de base de données
        """
        with self.db.transaction() as cursor:
            try:
                cursor.execute(
                    """
                    INSERT INTO fee_plan (class_id, school_year_id, label, amount_int, due_date)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        fee_plan.class_id,
                        fee_plan.school_year_id,
                        fee_plan.label,
                        fee_plan.amount_int,
                        fee_plan.due_date
                    )
                )
                return cursor.lastrowid
            except sqlite3.IntegrityError as e:
                raise DatabaseError(f"Erreur d'intégrité : {e}")

    def get_by_id(self, fee_id: int) -> Optional[FeePlan]:
        """
        Récupère un plan de frais à partir de son identifiant.

        Args:
            fee_id: Identifiant du plan de frais

        Returns:
            FeePlan | None: Le plan de frais trouvé ou None s'il n'existe pas
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, class_id, school_year_id, label, amount_int, due_date, created_at
            FROM fee_plan
            WHERE id = ?
            """,
            (fee_id,)
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_fee_plan(row)

    def get_by_class(self, class_id: int, school_year_id: int = None) -> List[FeePlan]:
        """
        Récupère les plans de frais d'une classe.

        Args:
            class_id: Identifiant de la classe
            school_year_id: Identifiant de l'année scolaire (optionnel)

        Returns:
            List[FeePlan]: Liste des plans de frais
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        if school_year_id:
            cursor.execute(
                """
                SELECT id, class_id, school_year_id, label, amount_int, due_date, created_at
                FROM fee_plan
                WHERE class_id = ? AND school_year_id = ?
                ORDER BY due_date
                """,
                (class_id, school_year_id)
            )
        else:
            cursor.execute(
                """
                SELECT id, class_id, school_year_id, label, amount_int, due_date, created_at
                FROM fee_plan
                WHERE class_id = ?
                ORDER BY due_date
                """,
                (class_id,)
            )

        rows = cursor.fetchall()
        return [self._row_to_fee_plan(row) for row in rows]

    def get_total_by_class(self, class_id: int, school_year_id: int = None) -> int:
        """
        Calcule le total des frais dus pour une classe (en cents).

        Args:
            class_id: Identifiant de la classe
            school_year_id: Identifiant de l'année scolaire (optionnel)

        Returns:
            int: Total en cents
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        if school_year_id:
            cursor.execute(
                """
                SELECT COALESCE(SUM(amount_int), 0) as total
                FROM fee_plan
                WHERE class_id = ? AND school_year_id = ?
                """,
                (class_id, school_year_id)
            )
        else:
            cursor.execute(
                """
                SELECT COALESCE(SUM(amount_int), 0) as total
                FROM fee_plan
                WHERE class_id = ?
                """,
                (class_id,)
            )

        row = cursor.fetchone()
        return row['total'] if row else 0

    def get_all(self, school_year_id: int = None) -> List[FeePlan]:
        """
        Récupère tous les plans de frais.

        Args:
            school_year_id: Identifiant de l'année scolaire (optionnel)

        Returns:
            List[FeePlan]: Liste des plans de frais
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        if school_year_id:
            cursor.execute(
                """
                SELECT id, class_id, school_year_id, label, amount_int, due_date, created_at
                FROM fee_plan
                WHERE school_year_id = ?
                ORDER BY class_id, due_date
                """,
                (school_year_id,)
            )
        else:
            cursor.execute(
                """
                SELECT id, class_id, school_year_id, label, amount_int, due_date, created_at
                FROM fee_plan
                ORDER BY class_id, due_date
                """
            )

        rows = cursor.fetchall()
        return [self._row_to_fee_plan(row) for row in rows]

    def update(self, fee_plan: FeePlan) -> bool:
        """
        Met à jour les informations d'un plan de frais.

        Args:
            fee_plan: Objet FeePlan avec les nouvelles valeurs

        Returns:
            bool: True si une ligne a été modifiée, sinon False

        Raises:
            DatabaseError: En cas d'erreur de base de données
        """
        if fee_plan.id is None:
            raise ValueError("Impossible de modifier un plan de frais sans identifiant.")

        with self.db.transaction() as cursor:
            try:
                cursor.execute(
                    """
                    UPDATE fee_plan
                    SET class_id = ?, school_year_id = ?, label = ?, amount_int = ?, due_date = ?
                    WHERE id = ?
                    """,
                    (
                        fee_plan.class_id,
                        fee_plan.school_year_id,
                        fee_plan.label,
                        fee_plan.amount_int,
                        fee_plan.due_date,
                        fee_plan.id
                    )
                )
                return cursor.rowcount > 0
            except sqlite3.IntegrityError as e:
                raise DatabaseError(f"Erreur d'intégrité : {e}")

    def delete(self, fee_id: int) -> bool:
        """
        Supprime un plan de frais.

        Args:
            fee_id: Identifiant du plan de frais

        Returns:
            bool: True si le plan de frais a été supprimé, sinon False
        """
        with self.db.transaction() as cursor:
            cursor.execute(
                """
                DELETE FROM fee_plan
                WHERE id = ?
                """,
                (fee_id,)
            )
            return cursor.rowcount > 0

    @staticmethod
    def _row_to_fee_plan(row) -> FeePlan:
        """
        Transforme une ligne SQLite en objet FeePlan.
        """
        return FeePlan(
            id=row["id"],
            class_id=row["class_id"],
            school_year_id=row["school_year_id"],
            label=row["label"],
            amount_int=row["amount_int"],
            due_date=row["due_date"],
            created_at=row["created_at"]
        )
