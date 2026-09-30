"""
Service pour la logique métier des élèves
"""

from models.eleve import Eleve
from repositories.eleve_repository import EleveRepository
from repositories.paiement_repository import PaiementRepository


class EleveService:
    """Service contenant la logique métier pour les élèves"""
    
    def __init__(self, eleve_repo=None, paiement_repo=None):
        self.eleve_repo = eleve_repo if eleve_repo else EleveRepository()
        self.paiement_repo = paiement_repo if paiement_repo else PaiementRepository()
    
    def create_eleve(self, nom: str, prenom: str, classe: str, 
                     annee_scolaire: str, montant_du: float) -> Eleve:
        """Crée un nouvel élève avec validation"""
        # Validation
        if not nom or not nom.strip():
            raise ValueError("Le nom est obligatoire")
        if not prenom or not prenom.strip():
            raise ValueError("Le prénom est obligatoire")
        if not classe or not classe.strip():
            raise ValueError("La classe est obligatoire")
        if not annee_scolaire or not annee_scolaire.strip():
            raise ValueError("L'année scolaire est obligatoire")
        if montant_du <= 0:
            raise ValueError("Le montant dû doit être positif")
        
        eleve = Eleve(
            nom=nom.strip(),
            prenom=prenom.strip(),
            classe=classe.strip(),
            annee_scolaire=annee_scolaire.strip(),
            montant_du=montant_du
        )
        
        eleve_id = self.eleve_repo.add(eleve)
        eleve.id = eleve_id
        return eleve
    
    def update_eleve(self, eleve: Eleve) -> Eleve:
        """Met à jour un élève avec validation"""
        # Validation
        if not eleve.nom or not eleve.nom.strip():
            raise ValueError("Le nom est obligatoire")
        if not eleve.prenom or not eleve.prenom.strip():
            raise ValueError("Le prénom est obligatoire")
        if not eleve.classe or not eleve.classe.strip():
            raise ValueError("La classe est obligatoire")
        if not eleve.annee_scolaire or not eleve.annee_scolaire.strip():
            raise ValueError("L'année scolaire est obligatoire")
        if eleve.montant_du <= 0:
            raise ValueError("Le montant dû doit être positif")
        
        # Nettoyage
        eleve.nom = eleve.nom.strip()
        eleve.prenom = eleve.prenom.strip()
        eleve.classe = eleve.classe.strip()
        eleve.annee_scolaire = eleve.annee_scolaire.strip()
        
        success = self.eleve_repo.update(eleve)
        if not success:
            raise ValueError("Élève non trouvé ou mise à jour échouée")
        
        return eleve
    
    def delete_eleve(self, eleve_id: int) -> bool:
        """Supprime un élève après vérification qu'il n'a pas de paiements"""
        # Vérifier s'il y a des paiements
        paiements = self.paiement_repo.get_by_eleve(eleve_id)
        if paiements:
            raise ValueError("Impossible de supprimer un élève ayant des paiements enregistrés")
        
        return self.eleve_repo.delete(eleve_id)
    
    def get_eleve(self, eleve_id: int) -> Eleve:
        """Récupère un élève par son ID"""
        return self.eleve_repo.get_by_id(eleve_id)
    
    def get_all_eleves(self) -> list[Eleve]:
        """Récupère tous les élèves"""
        return self.eleve_repo.get_all()
    
    def search_eleves(self, query: str) -> list[Eleve]:
        """Recherche des élèves par nom, prénom ou classe"""
        return self.eleve_repo.search(query)
    
    def filter_eleves_by_classe(self, classe: str) -> list[Eleve]:
        """Filtre les élèves par classe"""
        return self.eleve_repo.filter_by_classe(classe)
    
    def get_all_classes(self) -> list[str]:
        """Récupère la liste de toutes les classes"""
        return self.eleve_repo.get_classes()
