"""
Gestion de la connexion à la base de données SQLite

Fonctionnalités :
- PRAGMA foreign_keys = ON à chaque connexion
- Gestion des transactions explicites
- Singleton pattern
- Support du nouveau schéma avec argent en entiers
"""

import sqlite3
import sys
from pathlib import Path
from contextlib import contextmanager

# Import de la configuration
try:
    from app.config import DB_PATH, SEED_DB_PATH
except ImportError:
    # Fallback pour compatibilité avec l'ancien code
    DB_PATH = Path("database/edupaie.db")
    SEED_DB_PATH = Path("database/edupaie.db")


class Database:
    """
    Classe singleton pour la connexion à la base de données.

    Assure que foreign_keys sont activés et gère les transactions.
    """

    _instance = None
    _connection = None

    def __new__(cls, db_path=None):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._db_path = db_path if db_path else DB_PATH
        return cls._instance

    def get_connection(self):
        """
        Retourne la connexion à la base de données.

        Active PRAGMA foreign_keys = ON à chaque connexion.
        """
        if self._connection is None:
            self._connection = sqlite3.connect(
                str(self._db_path),
                check_same_thread=False  # Permet l'utilisation multi-thread
            )
            self._connection.row_factory = sqlite3.Row

            # IMPORTANT : Activer les foreign keys
            cursor = self._connection.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute("PRAGMA journal_mode = WAL")  # Mode Write-Ahead Logging pour meilleure performance
            self._connection.commit()

        return self._connection

    def close(self):
        """Ferme la connexion à la base de données"""
        if self._connection:
            self._connection.close()
            self._connection = None

    @contextmanager
    def transaction(self):
        """
        Context manager pour les transactions explicites.

        Usage :
            with db.transaction():
                # Opérations DB
                cursor.execute("INSERT INTO ...")
                cursor.execute("UPDATE ...")
                # Si une exception est levée, rollback automatique
                # Sinon, commit automatique
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Début de transaction explicite
            cursor.execute("BEGIN")
            yield cursor
            # Commit si tout s'est bien passé
            conn.commit()
        except Exception:
            # Rollback en cas d'erreur
            conn.rollback()
            raise

    def initialize_schema(self, schema_path=None):
        """
        Initialise le schéma de la base de données depuis un fichier SQL.

        Args:
            schema_path: Chemin vers le fichier schema.sql
        """
        if schema_path is None:
            # Utiliser le nouveau schéma par défaut
            try:
                from app.config import resource_path
                schema_path = resource_path('app/data/schema.sql')
            except ImportError:
                schema_path = 'database/schema.sql'

        if not Path(schema_path).exists():
            raise FileNotFoundError(f"Fichier schéma introuvable : {schema_path}")

        conn = self.get_connection()
        cursor = conn.cursor()

        # Lire et exécuter le schéma
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        # Exécuter le schéma
        cursor.executescript(schema_sql)
        conn.commit()

    def get_version(self) -> int:
        """
        Retourne la version du schéma (PRAGMA user_version).

        Returns:
            int: Version du schéma (0 si non initialisé)
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA user_version")
        return cursor.fetchone()[0]

    def set_version(self, version: int):
        """
        Définit la version du schéma (PRAGMA user_version).

        Args:
            version: Numéro de version
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA user_version = {version}")
        conn.commit()
