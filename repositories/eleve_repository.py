"""
Repository pour la gestion des élèves (DAO)
"""

from models.eleve import Eleve
from utils.database import Database


class EleveRepository:
    """Repository pour les opérations sur les élèves"""
    
    def __init__(self, db=None):
        self.db = db if db else Database()
    
    def add(self, eleve: Eleve) -> int:
        """Ajoute un élève et retourne son ID"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO eleves (nom, prenom, classe, annee_scolaire, montant_du)
            VALUES (?, ?, ?, ?, ?)
        ''', (eleve.nom, eleve.prenom, eleve.classe,
              eleve.annee_scolaire, eleve.montant_du))
        
        conn.commit()
        return cursor.lastrowid
    
    def get_by_id(self, eleve_id: int) -> Eleve:
        """Récupère un élève par son ID"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM eleves WHERE id = ?', (eleve_id,))
        row = cursor.fetchone()
        
        if row:
            return Eleve(
                id=row['id'],
                nom=row['nom'],
                prenom=row['prenom'],
                classe=row['classe'],
                annee_scolaire=row['annee_scolaire'],
                montant_du=row['montant_du']
            )
        return None
    
    def get_all(self) -> list[Eleve]:
        """Récupère tous les élèves"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM eleves ORDER BY nom, prenom')
        rows = cursor.fetchall()
        
        return [
            Eleve(
            id=row['id'],
            nom=row['nom'],
            prenom=row['prenom'],
            classe=row['classe'],
            annee_scolaire=row['annee_scolaire'],
            montant_du=row['montant_du']
        )
        for row in rows
        ]
    
    def update(self, eleve: Eleve) -> bool:
        """Met à jour un élève"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE eleves
            SET nom=?, prenom=?, classe=?, annee_scolaire=?, montant_du=?
            WHERE id=?
        ''', (eleve.nom, eleve.prenom, eleve.classe,
              eleve.annee_scolaire, eleve.montant_du, eleve.id))
        
        conn.commit()
        return cursor.rowcount > 0
    
    def delete(self, eleve_id: int) -> bool:
        """Supprime un élève"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM eleves WHERE id = ?', (eleve_id,))
        conn.commit()
        return cursor.rowcount > 0
    
    def search(self, query: str) -> list[Eleve]:
        """Recherche d'élèves par nom, prénom ou classe"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        search_pattern = f'%{query}%'
        cursor.execute('''
            SELECT * FROM eleves
            WHERE nom LIKE ? OR prenom LIKE ? OR classe LIKE ?
            ORDER BY nom, prenom
        ''', (search_pattern, search_pattern, search_pattern))

        rows = cursor.fetchall()
        return [Eleve(
            id=row['id'],
            nom=row['nom'],
            prenom=row['prenom'],
            classe=row['classe'],
            annee_scolaire=row['annee_scolaire'],
            montant_du=row['montant_du']
        ) for row in rows]
    
    def filter_by_classe(self, classe: str) -> list[Eleve]:
        """Filtre les élèves par classe"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM eleves
            WHERE classe = ?
            ORDER BY nom, prenom
        ''', (classe,))

        rows = cursor.fetchall()
        return [Eleve(
            id=row['id'],
            nom=row['nom'],
            prenom=row['prenom'],
            classe=row['classe'],
            annee_scolaire=row['annee_scolaire'],
            montant_du=row['montant_du']
        ) for row in rows]

    def get_classes(self) -> list[str]:
        """Récupère la liste des classes uniques"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT DISTINCT classe FROM eleves ORDER BY classe')
        rows = cursor.fetchall()
        return [row['classe'] for row in rows]
