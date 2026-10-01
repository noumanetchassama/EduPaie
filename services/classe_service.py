"""
Service pour la logique métier des classes
"""

from models.classe import Classe
from repositories.classe_repository import ClasseRepository
from repositories.eleve_repository import EleveRepository


class ClasseService:
    """Service contenant la logique métier pour les classes"""
    
    def __init__(self, classe_repo=None, eleve_repo=None):
        self.classe_repo = classe_repo if classe_repo else ClasseRepository()
        self.eleve_repo = eleve_repo if eleve_repo else EleveRepository()
    
    def create_classe(self, nom: str, niveau: str, annee_scolaire: str) -> Classe:
        """Crée une nouvelle classe avec validation"""
        if not nom or not nom.strip():
            raise ValueError("Le nom de la classe est obligatoire")
        if not niveau or not niveau.strip():
            raise ValueError("Le niveau est obligatoire")
        if not annee_scolaire or not annee_scolaire.strip():
            raise ValueError("L'année scolaire est obligatoire")
        
        classe = Classe(
            nom=nom.strip(),
            niveau=niveau.strip(),
            annee_scolaire=annee_scolaire.strip()
        )
        
        classe_id = self.classe_repo.add(classe)
        classe.id = classe_id
        return classe
    
    def update_classe(self, classe: Classe) -> bool:
        """Met à jour une classe avec validation"""
        if not classe.nom or not classe.nom.strip():
            raise ValueError("Le nom de la classe est obligatoire")
        
        return self.classe_repo.update(classe)
    
    def delete_classe(self, classe_id: int) -> bool:
        """Supprime une classe si elle n'a pas d'élèves"""
        # Vérifier si la classe a des élèves
        eleves = self.eleve_repo.get_all()
        for eleve in eleves:
            if eleve.classe == self.classe_repo.get_by_id(classe_id).nom:
                raise ValueError("Impossible de supprimer une classe qui contient des élèves")

        return self.classe_repo.delete(classe_id)
    
    def get_classe(self, classe_id: int) -> Classe:
        """Récupère une classe par son ID"""
        return self.classe_repo.get_by_id(classe_id)
    
    def get_all_classes(self) -> list[Classe]:
        """Récupère toutes les classes"""
        return self.classe_repo.get_all()
    
    def get_classes_by_annee(self, annee_scolaire: str) -> list[Classe]:
        """Récupère les classes d'une année scolaire"""
        return self.classe_repo.get_by_annee(annee_scolaire)
    
    def search_classes(self, query: str) -> list[Classe]:
        """Recherche des classes par nom ou niveau"""
        return self.classe_repo.search(query)
