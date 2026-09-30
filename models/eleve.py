"""
Classe représentant un élève
"""


class Eleve:
    """Représente un élève"""
    
    def __init__(self, id=None, nom=None, prenom=None, classe_id=None, annee_scolaire=None, montant_du=None):
        self.id = id
        self.nom = nom
        self.prenom = prenom
        self.classe_id = classe_id
        self.annee_scolaire = annee_scolaire
        self.montant_du = montant_du
    
    def __repr__(self):
        return f"Eleve(id={self.id}, nom='{self.nom}', prenom='{self.prenom}', classe_id={self.classe_id})"
    
    def to_dict(self):
        """Convertit l'élève en dictionnaire"""
        return {
            'id': self.id,
            'nom': self.nom,
            'prenom': self.prenom,
            'classe_id': self.classe_id,
            'annee_scolaire': self.annee_scolaire,
            'montant_du': self.montant_du
        }
    
    @classmethod
    def from_dict(cls, data):
        """Crée un élève depuis un dictionnaire"""
        return cls(
            id=data.get('id'),
            nom=data.get('nom', ''),
            prenom=data.get('prenom', ''),
            classe_id=data.get('classe_id'),
            annee_scolaire=data.get('annee_scolaire', ''),
            montant_du=data.get('montant_du', 0.0)
        )
