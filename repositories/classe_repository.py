"""
Repository pour la gestion des élèves (DAO).

Ce fichier contient uniquement les accès aux données SQLite.
Aucune logique d'interface graphique ne doit se trouver ici.
"""

from typing import Optional

from models.eleve import Eleve
from utils.database import Database


class EleveRepository:
    """Repository pour les opérations CRUD sur les élèves."""

    def __init__(self, db=None):
        self.db = db if db is not None else Database()

    # ==========================================================
    # AJOUTER
    # ==========================================================

    def add(self, eleve: Eleve) -> int:
        """
        Ajoute un élève dans la base de données.

        Returns:
            int: Identifiant de l'élève créé.
        """

        conn = self.db.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO eleves (
                    nom,
                    prenom,
                    classe,
                    annee_scolaire,
                    montant_total
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    eleve.nom,
                    eleve.prenom,
                    eleve.classe,
                    eleve.annee_scolaire,
                    eleve.montant_total,
                )
            )

            conn.commit()

            return cursor.lastrowid

        except Exception:
            conn.rollback()
            raise

    # ==========================================================
    # RECHERCHER PAR ID
    # ==========================================================

    def get_by_id(self, eleve_id: int) -> Optional[Eleve]:
        """
        Récupère un élève à partir de son identifiant.

        Returns:
            Eleve | None: L'élève trouvé ou None s'il n'existe pas.
        """

        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                nom,
                prenom,
                classe,
                annee_scolaire,
                montant_total,
                date_creation
            FROM eleves
            WHERE id = ?
            """,
            (eleve_id,)
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_eleve(row)

    # ==========================================================
    # RÉCUPÉRER TOUS LES ÉLÈVES
    # ==========================================================

    def get_all(self) -> list[Eleve]:
        """Récupère tous les élèves."""

        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                nom,
                prenom,
                classe,
                annee_scolaire,
                montant_total,
                date_creation
            FROM eleves
            ORDER BY nom COLLATE NOCASE, prenom COLLATE NOCASE
            """
        )

        rows = cursor.fetchall()

        return [self._row_to_eleve(row) for row in rows]

    # ==========================================================
    # MODIFIER
    # ==========================================================

    def update(self, eleve: Eleve) -> bool:
        """
        Met à jour les informations d'un élève.

        Returns:
            bool: True si une ligne a été modifiée, sinon False.
        """

        if eleve.id is None:
            raise ValueError(
                "Impossible de modifier un élève sans identifiant."
            )

        conn = self.db.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE eleves
                SET
                    nom = ?,
                    prenom = ?,
                    classe = ?,
                    annee_scolaire = ?,
                    montant_total = ?
                WHERE id = ?
                """,
                (
                    eleve.nom,
                    eleve.prenom,
                    eleve.classe,
                    eleve.annee_scolaire,
                    eleve.montant_total,
                    eleve.id,
                )
            )

            conn.commit()

            return cursor.rowcount > 0

        except Exception:
            conn.rollback()
            raise

    # ==========================================================
    # SUPPRIMER
    # ==========================================================

    def delete(self, eleve_id: int) -> bool:
        """
        Supprime un élève.

        Returns:
            bool: True si l'élève a été supprimé, sinon False.
        """

        conn = self.db.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                DELETE FROM eleves
                WHERE id = ?
                """,
                (eleve_id,)
            )

            conn.commit()

            return cursor.rowcount > 0

        except Exception:
            conn.rollback()
            raise

    # ==========================================================
    # RECHERCHE
    # ==========================================================

    def search(self, query: str) -> list[Eleve]:
        """
        Recherche un élève par :
        - nom
        - prénom
        - classe
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
            SELECT
                id,
                nom,
                prenom,
                classe,
                annee_scolaire,
                montant_total,
                date_creation
            FROM eleves
            WHERE
                nom LIKE ?
                OR prenom LIKE ?
                OR classe LIKE ?
            ORDER BY
                nom COLLATE NOCASE,
                prenom COLLATE NOCASE
            """,
            (
                search_pattern,
                search_pattern,
                search_pattern,
            )
        )

        rows = cursor.fetchall()

        return [self._row_to_eleve(row) for row in rows]

    # ==========================================================
    # FILTRER PAR CLASSE
    # ==========================================================

    def filter_by_classe(self, classe: str) -> list[Eleve]:
        """Récupère les élèves d'une classe."""

        if classe is None:
            return []

        classe = classe.strip()

        if not classe:
            return self.get_all()

        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                nom,
                prenom,
                classe,
                annee_scolaire,
                montant_total,
                date_creation
            FROM eleves
            WHERE classe = ?
            ORDER BY
                nom COLLATE NOCASE,
                prenom COLLATE NOCASE
            """,
            (classe,)
        )

        rows = cursor.fetchall()

        return [self._row_to_eleve(row) for row in rows]

    # ==========================================================
    # RÉCUPÉRER LES CLASSES
    # ==========================================================

    def get_classes(self) -> list[str]:
        """Récupère la liste des classes uniques."""

        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT DISTINCT classe
            FROM eleves
            WHERE classe IS NOT NULL
              AND TRIM(classe) != ''
            ORDER BY classe COLLATE NOCASE
            """
        )

        rows = cursor.fetchall()

        return [row["classe"] for row in rows]

    # ==========================================================
    # CONVERSION SQLITE -> OBJET ELEVE
    # ==========================================================

    @staticmethod
    def _row_to_eleve(row) -> Eleve:
        """
        Transforme une ligne SQLite en objet Eleve.

        Le projet utilise une connexion SQLite configurée
        avec sqlite3.Row afin d'accéder aux colonnes par leur nom.
        """

        return Eleve(
            id=row["id"],
            nom=row["nom"],
            prenom=row["prenom"],
            classe=row["classe"],
            annee_scolaire=row["annee_scolaire"],
            montant_total=row["montant_total"],
            date_creation=row["date_creation"],
        )