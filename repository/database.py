"""
Gestion de la connexion à la base de données SQLite
"""

import sqlite3
import os


class Database:
    """Classe singleton pour la connexion à la base de données"""
    
    _instance = None
    _connection = None
    
    def __new__(cls, db_path='edupaie.db'):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._db_path = db_path
        return cls._instance
    
    def get_connection(self):
        """Retourne la connexion à la base de données"""
        if self._connection is None:
            self._connection = sqlite3.connect(self._db_path)
            self._connection.row_factory = sqlite3.Row
        return self._connection
    
    def close(self):
        """Ferme la connexion à la base de données"""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def initialize_schema(self):
        """Initialise le schéma de la base de données"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Table élèves
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS eleves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                prenom TEXT NOT NULL,
                classe TEXT NOT NULL,
                annee_scolaire TEXT NOT NULL,
                montant_du REAL NOT NULL,
                date_creation DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table paiements
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS paiements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                eleve_id INTEGER NOT NULL,
                montant REAL NOT NULL,
                date_paiement DATETIME NOT NULL,
                mode_paiement TEXT NOT NULL,
                numero_recu TEXT NOT NULL UNIQUE,
                FOREIGN KEY (eleve_id) REFERENCES eleves(id)
            )
        ''')
        
        conn.commit()
