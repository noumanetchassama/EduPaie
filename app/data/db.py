"""
Gestion de la connexion à la base de données SQLite (singleton)

Fonctionnalités :
- PRAGMA foreign_keys = ON et WAL à chaque connexion
- Transactions explicites (context manager)
- Schéma initialisé depuis app/data/schema.sql
- Migration légère : ajoute les colonnes manquantes si une base existante est détectée
"""

import logging
import sqlite3
from datetime import date
from pathlib import Path
from contextlib import contextmanager

from app.config import DB_PATH, SCHEMA_PATH


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
            cls._instance._db_path = Path(db_path) if db_path else Path(DB_PATH)
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Réinitialise le singleton (utile pour les tests)."""
        if cls._connection is not None:
            cls._connection.close()
        cls._instance = None
        cls._connection = None

    def get_connection(self):
        """
        Retourne la connexion à la base de données.

        Active PRAGMA foreign_keys = ON et le mode WAL à chaque création.
        """
        if self._connection is None:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            self._connection = sqlite3.connect(
                str(self._db_path),
                check_same_thread=False
            )
            self._connection.row_factory = sqlite3.Row

            cursor = self._connection.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute("PRAGMA journal_mode = WAL")
            cursor.execute("PRAGMA synchronous = NORMAL")
            self._connection.commit()

        return self._connection

    def close(self):
        """Ferme la connexion à la base de données."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    @contextmanager
    def transaction(self):
        """
        Context manager pour les transactions explicites.

        Usage :
            with db.transaction() as cursor:
                cursor.execute("INSERT INTO ...")
                # Si une exception est levée, rollback automatique
                # Sinon, commit automatique
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("BEGIN")
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def initialize_schema(self, schema_path=None):
        """
        Initialise la base de données avec le schéma SQL.

        Args:
            schema_path: Chemin vers le fichier schema.sql (optionnel)

        Raises:
            FileNotFoundError: Si le fichier schéma est introuvable
        """
        if schema_path is None:
            schema_path = SCHEMA_PATH

        schema_file = Path(schema_path)
        if not schema_file.exists():
            raise FileNotFoundError(f"Fichier schéma introuvable : {schema_file}")

        conn = self.get_connection()
        cursor = conn.cursor()
        self._backup_existing_database(conn)

        # Détection AVANT l'exécution du schéma : une base « legacy » en
        # euros (montants stockés en centimes) doit être convertie en FCFA.
        # Une base neuve n'a pas encore de table fee_plan → pas de migration.
        legacy_euro = self._detect_legacy_euro(cursor)

        with open(schema_file, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        # Exécute le schéma (les instructions sont idempotentes : IF NOT EXISTS)
        cursor.executescript(schema_sql)
        conn.commit()

        # Migrations
        self._migrate_if_needed(cursor)
        if legacy_euro:
            cursor.execute(
                "UPDATE fee_plan SET amount_int = amount_int * 100")
            cursor.execute(
                "UPDATE payment SET amount_int = amount_int * 100")
            logging.warning(
                "Base ancienne en euros convertie en FCFA (montants x 100)")
        # Garde-fou anti double-migration
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)")
        cursor.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES ('fcfa_v2', '1')")
        conn.commit()

    def _backup_existing_database(self, conn):
        """Crée une sauvegarde quotidienne avant toute modification du schéma."""
        existing_table = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' "
            "AND name NOT LIKE 'sqlite_%' LIMIT 1"
        ).fetchone()
        if existing_table is None:
            return

        backup_dir = self._db_path.parent / "backups"
        backup_path = backup_dir / (
            f"{self._db_path.stem}_{date.today():%Y%m%d}.sqlite3")
        temp_path = backup_path.with_name(f".{backup_path.name}.tmp")

        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
            if not backup_path.exists():
                backup_connection = sqlite3.connect(str(temp_path))
                try:
                    conn.backup(backup_connection)
                finally:
                    backup_connection.close()
                temp_path.replace(backup_path)
                logging.info("Sauvegarde de la base créée : %s", backup_path)
        except Exception:
            logging.exception("Impossible de sauvegarder la base : %s", self._db_path)
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass

        backups = sorted(
            backup_dir.glob(f"{self._db_path.stem}_????????.sqlite3"),
            reverse=True,
        )
        for obsolete in backups[14:]:
            try:
                obsolete.unlink()
            except OSError:
                logging.warning("Impossible de supprimer l'ancienne sauvegarde : %s",
                                obsolete)

    @staticmethod
    def _detect_legacy_euro(cursor) -> bool:
        """
        True si la base existante contient des montants en centimes d'euro
        (500 €-650 € typiques → 50000-65000 en base, divisibles par 100).
        Ne s'applique qu'aux bases créées avant l'adoption du FCFA.
        """
        tables = {r[0] for r in cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        if "fee_plan" not in tables or "payment" not in tables:
            return False
        if "meta" in tables:
            cursor.execute("SELECT value FROM meta WHERE key = 'fcfa_v2'")
            if cursor.fetchone() is not None:
                return False  # déjà traité
        cursor.execute(
            "SELECT MIN(amount_int), MAX(amount_int) FROM fee_plan")
        mn, mx = cursor.fetchone()
        if mn is None or mx is None:
            return False
        if not (10000 <= mn and mx <= 100000):
            return False
        # Tous les montants doivent être des centimes ronds (multiple de 100)
        cursor.execute(
            "SELECT COUNT(*) FROM fee_plan WHERE amount_int % 100 != 0")
        if cursor.fetchone()[0] > 0:
            return False
        return True

    @staticmethod
    def _migrate_if_needed(cursor):
        """
        Migration légère : ajoute les colonnes manquantes sur une base existante.

        SQLite ne permet pas d'utiliser ADD COLUMN si la colonne existe déjà,
        on vérifie donc le contenu de PRAGMA table_info avant.
        """
        def columns(table):
            return {row[1] for row in cursor.execute(f"PRAGMA table_info({table})")}

        if "payment" in {r[0] for r in cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}:  # noqa: E501
            cols = columns("payment")
            if "status" not in cols:
                cursor.execute(
                    "ALTER TABLE payment ADD COLUMN status TEXT DEFAULT 'valide'")
            if "cancel_reason" not in cols:
                cursor.execute("ALTER TABLE payment ADD COLUMN cancel_reason TEXT")
            if "cancel_date" not in cols:
                cursor.execute("ALTER TABLE payment ADD COLUMN cancel_date DATE")
            if "reference" not in cols:
                cursor.execute("ALTER TABLE payment ADD COLUMN reference TEXT")

        if "student" in {r[0] for r in cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}:  # noqa: E501
            cols = columns("student")
            if "is_active" not in cols:
                cursor.execute(
                    "ALTER TABLE student ADD COLUMN is_active BOOLEAN DEFAULT 1")



    def get_version(self) -> int:
        """Retourne la version du schéma (PRAGMA user_version)."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA user_version")
        return cursor.fetchone()[0]

    def set_version(self, version: int):
        """Définit la version du schéma (PRAGMA user_version)."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA user_version = {version}")
        conn.commit()
