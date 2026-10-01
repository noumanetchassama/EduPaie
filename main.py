"""
EduPaie - Application de gestion des paiements scolaires
Point d'entrée principal

Fonctionnalités :
- Excepthook global pour capturer toutes les exceptions
- Logging dans fichier (APPDATA/EduPaie/edupaie.log)
- Copie de la DB seed au premier lancement
- Initialisation du schéma de base de données
"""

import sys
import logging
import shutil
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt

# Configuration de l'application
try:
    from app.config import DB_PATH, SEED_DB_PATH, LOG_FILE
    from app.data.db import Database
except ImportError:
    # Fallback pour compatibilité avec l'ancien code
    DB_PATH = Path("database/edupaie.db")
    SEED_DB_PATH = Path("database/edupaie.db")
    LOG_FILE = Path("edupaie.log")

from ui.main_window import MainWindow


def setup_logging():
    """
    Configure le logging de l'application.

    Les logs sont écrits dans APPDATA/EduPaie/edupaie.log
    """
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    logging.info("EduPaie démarré")


def handle_exception(exc_type, exc_value, exc_traceback):
    """
    Gestionnaire global d'exceptions.

    Capture toutes les exceptions non gérées, les log et affiche
    un message à l'utilisateur.
    """
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logging.error("Exception non gérée", exc_info=(exc_type, exc_value, exc_traceback))

    # Afficher un message à l'utilisateur (si QApplication existe)
    if QApplication.instance():
        error_msg = f"Une erreur inattendue s'est produite :\n\n{str(exc_value)}\n\n"
        error_msg += f"Les détails ont été enregistrés dans :\n{LOG_FILE}"

        QMessageBox.critical(
            None,
            "Erreur",
            error_msg
        )


def copy_seed_db_if_needed():
    """
    Copie la DB seed vers l'emplacement de travail si elle n'existe pas.

    La DB seed est embarquée avec l'exécutable (sys._MEIPASS)
    et copiée dans APPDATA/EduPaie au premier lancement.
    """
    if DB_PATH.exists():
        logging.info(f"DB de travail existante : {DB_PATH}")
        return

    logging.info("Premier lancement : copie de la DB seed...")

    try:
        # Copier la DB seed vers l'emplacement de travail
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SEED_DB_PATH, DB_PATH)
        logging.info(f"DB seed copiée vers {DB_PATH}")
    except Exception as e:
        logging.error(f"Erreur lors de la copie de la DB seed : {e}")
        # Si la copie échoue, créer une DB vide
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        DB_PATH.touch()
        logging.warning("DB vide créée suite à l'erreur de copie")


def initialize_database():
    """
    Initialise la base de données avec le schéma.

    Crée les tables si elles n'existent pas.
    """
    try:
        db = Database()
        db.initialize_schema()
        logging.info("Base de données initialisée")
    except Exception as e:
        logging.error(f"Erreur lors de l'initialisation de la DB : {e}")
        raise


def main():
    # Configuration de l'excepthook global
    sys.excepthook = handle_exception

    # Configuration du logging
    setup_logging()

    # Copie de la DB seed si nécessaire
    copy_seed_db_if_needed()

    # Initialisation de la base de données
    initialize_database()

    # Création de l'application Qt
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Création et affichage de la fenêtre principale
    try:
        window = MainWindow()
        window.show()
        logging.info("Fenêtre principale affichée")
    except Exception as e:
        logging.error(f"Erreur lors de la création de la fenêtre : {e}")
        QMessageBox.critical(
            None,
            "Erreur de démarrage",
            f"Impossible de démarrer l'application :\n\n{str(e)}"
        )
        sys.exit(1)

    # Boucle d'événements
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
