"""
Service pour le journal d'audit.

Fournit à l'interface la liste filtrable des opérations enregistrées
(qui a créé, modifié, supprimé ou annulé élèves, paiements, classes et
années scolaires) sans exposer le repository directement.
"""

from typing import List, Optional

from app.data.repositories.audit_repository import AuditRepository

# Filtres proposés à l'interface
ENTITY_FILTERS = {
    "Tous les éléments": None,
    "Élèves": "Élève",
    "Paiements": "Paiement",
    "Classes": "Classe",
    "Années scolaires": "Année scolaire",
}

ACTION_FILTERS = {
    "Toutes les actions": None,
    "Créations": "Création",
    "Modifications": "Modification",
    "Suppressions": "Suppression",
    "Archivages": "Archivage",
    "Annulations": "Annulation",
}


class AuditService:
    """Accès en lecture au journal d'audit."""

    def __init__(self, audit_repo: Optional[AuditRepository] = None):
        self.audit_repo = audit_repo or AuditRepository()

    def get_entries(self, limit: int = 500, entity: Optional[str] = None,
                    action: Optional[str] = None) -> List[dict]:
        """
        Liste les entrées du journal, les plus récentes d'abord.

        Args:
            limit: Nombre maximum d'entrées
            entity: Filtre sur l'élément (Élève / Paiement / Classe / …)
            action: Filtre sur l'action (Création / Modification / …)

        Returns:
            Liste de dicts (id, action, entity, entity_label, details,
            user, created_at)
        """
        return self.audit_repo.get_all(limit=limit, entity=entity, action=action)

    def count(self) -> int:
        """Nombre total d'entrées enregistrées."""
        return self.audit_repo.count()
