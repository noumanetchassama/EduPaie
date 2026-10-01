"""
Repository pour la gestion des classes (DAO).

Ce fichier contient uniquement les accès aux données SQLite.
Aucune logique d'interface graphique ne doit se trouver ici.
"""

from typing import Optional

from models.classe import Classe
from utils.database import Database


class ClasseRepository:
    """Repository pour les opérations CRUD sur les classes."""

    def __init__(self, db=None):
        self.db = db if db is not None else Database()

    def add(self, classe: Classe) -> int:
        """
        Ajoute une classe dans la base de données.

        Returns:
            int: Identifiant de la classe créée.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO classes (nom, niveau, annee_scolaire)
                VALUES (?, ?, ?)
                """,
                (classe.nom, classe.niveau, classe.annee_scolaire)
            )

            conn.commit()
            return cursor.lastrowid

        except Exception:
            conn.rollback()
            raise

    def get_by_id(self, classe_id: int) -> Optional[Classe]:
        """
        Récupère une classe à partir de son identifiant.

        Returns:
            Classe | None: La classe trouvée ou None si elle n'existe pas.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, nom, niveau, annee_scolaire, date_creation
            FROM classes
            WHERE id = ?
            """,
            (classe_id,)
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_classe(row)

    def get_all(self) -> list[Classe]:
        """Récupère toutes les classes."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, nom, niveau, annee_scolaire, date_creation
            FROM classes
            ORDER BY nom COLLATE NOCASE
            """
        )

        rows = cursor.fetchall()
        return [self._row_to_classe(row) for row in rows]

    def update(self, classe: Classe) -> bool:
        """
        Met à jour les informations d'une classe.

        Returns:
            bool: True si une ligne a été modifiée, sinon False.
        """
        if classe.id is None:
            raise ValueError("Impossible de modifier une classe sans identifiant.")

        conn = self.db.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE classes
                SET nom = ?, niveau = ?, annee_scolaire = ?
                WHERE id = ?
                """,
                (classe.nom, classe.niveau, classe.annee_scolaire, classe.id)
            )

            conn.commit()
            return cursor.rowcount > 0

        except Exception:
            conn.rollback()
            raise

    def delete(self, classe_id: int) -> bool:
        """
        Supprime une classe.

        Returns:
            bool: True si la classe a été supprimée, sinon False.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                DELETE FROM classes
                WHERE id = ?
                """,
                (classe_id,)
            )

            conn.commit()
            return cursor.rowcount > 0

        except Exception:
            conn.rollback()
            raise

    def search(self, query: str) -> list[Classe]:
        """
        Recherche une classe par nom ou niveau.
        """
        if query is None:
            return []

        query = query.strip()

        if not query:
            return self.get_all()

        conn = self.db.get_connection()
        cursor = conn.cursor()

        search_pattern = f"%{query}%"

        cursor.execute(
            """
            SELECT id, nom, niveau, annee_scolaire, date_creation
            FROM classes
            WHERE nom LIKE ? OR niveau LIKE ?
            ORDER BY nom COLLATE NOCASE
            """,
            (search_pattern, search_pattern)
        )

        rows = cursor.fetchall()
        return [self._row_to_classe(row) for row in rows]

    def get_by_annee(self, annee_scolaire: str) -> list[Classe]:
        """Récupère les classes d'une année scolaire."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, nom, niveau, annee_scolaire, date_creation
            FROM classes
            WHERE annee_scolaire = ?
            ORDER BY nom COLLATE NOCASE
            """,
            (annee_scolaire,)
        )

        rows = cursor.fetchall()
        return [self._row_to_classe(row) for row in rows]

    @staticmethod
    def _row_to_classe(row) -> Classe:
        """
        Transforme une ligne SQLite en objet Classe.
        """
        return Classe(
            id=row["id"],
            nom=row["nom"],
            niveau=row["niveau"],
            annee_scolaire=row["annee_scolaire"]
        )