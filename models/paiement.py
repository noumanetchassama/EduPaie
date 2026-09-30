"""
Modèle Paiement
"""


class Paiement:
    """Classe représentant un paiement"""
    
    def __init__(self, id=None, eleve_id=None, montant=0.0, date_paiement="", 
                 mode_paiement="", numero_recu=""):
        self.id = id
        self.eleve_id = eleve_id
        self.montant = montant
        self.date_paiement = date_paiement
        self.mode_paiement = mode_paiement
        self.numero_recu = numero_recu
    
    def __repr__(self):
        return f"Paiement(id={self.id}, eleve_id={self.eleve_id}, montant={self.montant}, recu='{self.numero_recu}')"
    
    def to_dict(self):
        """Convertit le paiement en dictionnaire"""
        return {
            'id': self.id,
            'eleve_id': self.eleve_id,
            'montant': self.montant,
            'date_paiement': self.date_paiement,
            'mode_paiement': self.mode_paiement,
            'numero_recu': self.numero_recu
        }
    
    @classmethod
    def from_dict(cls, data):
        """Crée un paiement depuis un dictionnaire"""
        return cls(
            id=data.get('id'),
            eleve_id=data.get('eleve_id'),
            montant=data.get('montant', 0.0),
            date_paiement=data.get('date_paiement', ''),
            mode_paiement=data.get('mode_paiement', ''),
            numero_recu=data.get('numero_recu', '')
        )
