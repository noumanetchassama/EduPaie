"""
Repository pour la gestion des paiements (DAO)
"""

from models.paiement import Paiement
from repository.database import Database


class PaiementRepository:
    """Repository pour les opérations sur les paiements"""
    
    def __init__(self, db=None):
        self.db = db if db else Database()
    
    def add(self, paiement: Paiement) -> int:
        """Ajoute un paiement et retourne son ID"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO paiements (eleve_id, montant, date_paiement, mode_paiement, numero_recu)
            VALUES (?, ?, ?, ?, ?)
        ''', (paiement.eleve_id, paiement.montant, paiement.date_paiement,
              paiement.mode_paiement, paiement.numero_recu))
        
        conn.commit()
        return cursor.lastrowid
    
    def get_by_id(self, paiement_id: int) -> Paiement:
        """Récupère un paiement par son ID"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM paiements WHERE id = ?', (paiement_id,))
        row = cursor.fetchone()
        
        if row:
            return Paiement(
                id=row['id'],
                eleve_id=row['eleve_id'],
                montant=row['montant'],
                date_paiement=row['date_paiement'],
                mode_paiement=row['mode_paiement'],
                numero_recu=row['numero_recu']
            )
        return None
    
    def get_by_eleve(self, eleve_id: int) -> list[Paiement]:
        """Récupère tous les paiements d'un élève"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM paiements 
            WHERE eleve_id = ? 
            ORDER BY date_paiement DESC
        ''', (eleve_id,))
        
        rows = cursor.fetchall()
        return [Paiement(
            id=row['id'],
            eleve_id=row['eleve_id'],
            montant=row['montant'],
            date_paiement=row['date_paiement'],
            mode_paiement=row['mode_paiement'],
            numero_recu=row['numero_recu']
        ) for row in rows]
    
    def get_by_recu(self, numero_recu: str) -> Paiement:
        """Récupère un paiement par son numéro de reçu"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM paiements WHERE numero_recu = ?', (numero_recu,))
        row = cursor.fetchone()
        
        if row:
            return Paiement(
                id=row['id'],
                eleve_id=row['eleve_id'],
                montant=row['montant'],
                date_paiement=row['date_paiement'],
                mode_paiement=row['mode_paiement'],
                numero_recu=row['numero_recu']
            )
        return None
    
    def get_all(self) -> list[Paiement]:
        """Récupère tous les paiements"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM paiements ORDER BY date_paiement DESC')
        rows = cursor.fetchall()
        
        return [Paiement(
            id=row['id'],
            eleve_id=row['eleve_id'],
            montant=row['montant'],
            date_paiement=row['date_paiement'],
            mode_paiement=row['mode_paiement'],
            numero_recu=row['numero_recu']
        ) for row in rows]
    
    def get_total_by_eleve(self, eleve_id: int) -> float:
        """Calcule le total des paiements pour un élève"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COALESCE(SUM(montant), 0) as total 
            FROM paiements 
            WHERE eleve_id = ?
        ''', (eleve_id,))
        
        row = cursor.fetchone()
        return row['total'] if row else 0.0
    
    def delete(self, paiement_id: int) -> bool:
        """Supprime un paiement"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM paiements WHERE id = ?', (paiement_id,))
        conn.commit()
        return cursor.rowcount > 0
