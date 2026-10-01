"""
Repository du journal d'audit : enregistre et liste les opérations.

Chaque entrée trace : l'action (création, modification, suppression,
annulation), l'élément concerné (élève, paiement, classe, année scolaire),
un libellé lisible, des détails optionnels et l'utilisateur système.
"""

import getpass
from typing import List, Optional

from app.data.db import Database


class AuditRepository:
    """Accès aux données du journal d'audit."""

    def __init__(self, db: Optional[Database] = None):
        self.db = db if db is not None else Database()

    @staticmethod
    def _current_user() -> str:
        """Utilisateur système (aucune authentification dans l'application)."""
        try:
            return getpass.getuser() or "inconnu"
        except Exception:
            return "inconnu"

    def add(self, action: str, entity: str, entity_id: Optional[int] = None,
            entity_label: str = None, details: str = None) -> int:
        """
        Ajoute une entrée au journal d'audit.

        Args:
            action: Création / Modification / Suppression / Annulation
            entity: Élève / Paiement / Classe / Année scolaire
            entity_id: Identifiant de l'élément concerné
            entity_label: Libellé lisible (ex : « Jean Dupont », « REC-2024-000012 »)
            details: Précisions (motif, anciennes/nouvelles valeurs…)

        Returns:
            int: Identifiant de l'entrée créée
        """
        with self.db.transaction() as cursor:
            cursor.execute(
                """
                INSERT INTO audit_log
                    (action, entity, entity_id, entity_label, details, user)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (action, entity, entity_id, entity_label, details,
                 self._current_user()),
            )
            return cursor.lastrowid

    def get_all(self, limit: int = 500, entity: str = None,
                action: str = None) -> List[dict]:
        """
        Liste les entrées les plus récentes d'abord.

        Args:
            limit: Nombre maximum d'entrées retournées
            entity: Filtre sur l'élément (Élève / Paiement / Classe…)
            action: Filtre sur l'action

        Returns:
            Liste de dicts (id, action, entity, entity_label, details,
            user, created_at)
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        query = """
            SELECT id, action, entity, entity_id, entity_label, details,
                   user, created_at
            FROM audit_log
            WHERE 1 = 1
        """
        params = []
        if entity:
            query += " AND entity = ?"
            params.append(entity)
        if action:
            query += " AND action = ?"
            params.append(action)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        rows = cursor.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def count(self) -> int:
        """Nombre total d'entrées du journal."""
        conn = self.db.get_connection()
        return conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
