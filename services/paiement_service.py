"""
Service pour la logique métier des paiements
"""

from datetime import datetime
from models.paiement import Paiement
from models.eleve import Eleve
from repositories.paiement_repository import PaiementRepository
from repositories.eleve_repository import EleveRepository


class PaiementService:
    """Service contenant la logique métier pour les paiements"""
    
    MODES_PAIEMENT = ['especes', 'cheque', 'virement', 'mobile_money']
    MODES_PAIEMENT_LABELS = {
        'especes': 'Espèces',
        'cheque': 'Chèque',
        'virement': 'Virement',
        'mobile_money': 'Mobile Money'
    }
    
    def __init__(self, paiement_repo=None, eleve_repo=None):
        self.paiement_repo = paiement_repo if paiement_repo else PaiementRepository()
        self.eleve_repo = eleve_repo if eleve_repo else EleveRepository()
    
    def get_solde(self, eleve_id: int) -> float:
        """Calcule le solde restant pour un élève"""
        eleve = self.eleve_repo.get_by_id(eleve_id)
        if not eleve:
            raise ValueError("Élève non trouvé")
        
        total_paye = self.paiement_repo.get_total_by_eleve(eleve_id)
        return eleve.montant_du - total_paye
    
    def get_statut_paiement(self, eleve_id: int) -> str:
        """Retourne le statut de paiement d'un élève"""
        solde = self.get_solde(eleve_id)
        
        if solde <= 0:
            return "Soldé"
        elif solde > 0:
            return "Partiellement payé"
        else:
            return "Non payé"
    
    def create_paiement(self, eleve_id: int, montant: float, 
                       date_paiement: str, mode_paiement: str) -> Paiement:
        """Crée un nouveau paiement avec validation"""
        # Validation de l'élève
        eleve = self.eleve_repo.get_by_id(eleve_id)
        if not eleve:
            raise ValueError("Élève non trouvé")
        
        # Validation du montant
        if montant <= 0:
            raise ValueError("Le montant doit être positif")
        
        # Validation du mode de paiement
        if mode_paiement not in self.MODES_PAIEMENT:
            raise ValueError("Mode de paiement invalide")
        
        # Validation du solde
        solde_actuel = self.get_solde(eleve_id)
        if montant > solde_actuel:
            raise ValueError(
                f"Le montant ({montant:.2f}€) dépasse le solde restant ({solde_actuel:.2f}€)"
            )
        
        # Génération du numéro de reçu
        numero_recu = self._generer_numero_recu()
        
        # Création du paiement
        paiement = Paiement(
            eleve_id=eleve_id,
            montant=montant,
            date_paiement=date_paiement,
            mode_paiement=mode_paiement,
            numero_recu=numero_recu
        )
        
        paiement_id = self.paiement_repo.add(paiement)
        paiement.id = paiement_id
        return paiement
    
    def _generer_numero_recu(self) -> str:
        """Génère un numéro de reçu unique"""
        # Format: REC-YYYYMMDD-XXXXX
        date_str = datetime.now().strftime("%Y%m%d")
        
        # Compter les paiements du jour
        conn = self.paiement_repo.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) as count FROM paiements 
            WHERE date_paiement LIKE ?
        ''', (f"{date_str}%",))
        
        row = cursor.fetchone()
        count = row['count'] + 1
        
        return f"REC-{date_str}-{count:05d}"
    
    def get_paiements_eleve(self, eleve_id: int) -> list[Paiement]:
        """Récupère tous les paiements d'un élève"""
        return self.paiement_repo.get_by_eleve(eleve_id)
    
    def get_paiement_by_recu(self, numero_recu: str) -> Paiement:
        """Récupère un paiement par son numéro de reçu"""
        return self.paiement_repo.get_by_recu(numero_recu)
    
    def get_all_paiements(self) -> list[Paiement]:
        """Récupère tous les paiements"""
        return self.paiement_repo.get_all()
