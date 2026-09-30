"""
Classe représentant une classe scolaire
"""


class Classe:
    """Représente une classe scolaire"""
    
    def __init__(self, id=None, nom=None, niveau=None, annee_scolaire=None):
        self.id = id
        self.nom = nom
        self.niveau = niveau
        self.annee_scolaire = annee_scolaire
    
    def __repr__(self):
        return f"Classe(id={self.id}, nom='{self.nom}', niveau='{self.niveau}')"
