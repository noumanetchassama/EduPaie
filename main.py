"""
EduPaie — Application de gestion des paiements scolaires
Point d'entrée principal

Séquencement :
1. Logging (APPDATA/EduPaie/edupaie.log)
2. Base de données : schéma initialisé/migré à chaque lancement,
   DB seed copiée au premier lancement si disponible
3. Thème professionnel éducatif (palette + stylesheet)
4. Fenêtre principale (navigation latérale)
"""

import logging
import shutil
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox

# Configuration (chemins, monnaie, école)
from app.config import DB_PATH, LOG_FILE, SEED_DB_PATH


def setup_logging():
    """Configure le logging fichier + console."""
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(LOG_FILE, encoding="utf-8"),
                logging.StreamHandler(sys.stdout),
            ],
        )
    except Exception:
        # Jamais bloquant : on garde au moins la console
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
    logging.info("EduPaie démarré")


def handle_exception(exc_type, exc_value, exc_traceback):
    """Gestionnaire global d'exceptions : log + message utilisateur."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logging.error("Exception non gérée", exc_info=(exc_type, exc_value, exc_traceback))

    if QApplication.instance():
        QMessageBox.critical(
            None,
            "Erreur",
            f"Une erreur inattendue s'est produite :\n\n{exc_value}\n\n"
            f"Les détails ont été enregistrés dans :\n{LOG_FILE}",
        )


def prepare_database():
    """
    Prépare la base de données de travail.

    - Initialise/migre systématiquement le schéma (idempotent)
    - Au premier lancement, si la DB de travail est vide et qu'une DB seed
      embarquée existe, les données de démonstration sont copiées d'abord.
    """
    from app.data.db import Database

    first_run = not DB_PATH.exists() or DB_PATH.stat().st_size == 0
    if first_run and Path(SEED_DB_PATH).exists():
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(SEED_DB_PATH, DB_PATH)
            logging.info(f"DB seed copiée vers {DB_PATH}")
        except Exception as e:
            logging.warning(f"Copie de la DB seed impossible ({e}) : "
                            "création d'une base vierge")

    db = Database()
    db.initialize_schema()
    logging.info(f"Base de données prête : {DB_PATH}")


def main():
    sys.excepthook = handle_exception
    setup_logging()

    try:
        prepare_database()
    except Exception as e:
        logging.error(f"Échec de l'initialisation de la base : {e}")
        QMessageBox.critical(
            None, "Erreur de base de données",
            f"Impossible d'initialiser la base de données :\n\n{e}")
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setApplicationName("EduPaie")
    app.setOrganizationName("EduPaie")
    app.setStyle("Fusion")

    from app.ui.theme import get_professional_palette, get_professional_stylesheet
    app.setPalette(get_professional_palette())
    app.setStyleSheet(get_professional_stylesheet())

    from app.ui.main_window import MainWindow
    try:
        window = MainWindow()
    except Exception as e:
        logging.error(f"Erreur lors de la création de la fenêtre : {e}")
        QMessageBox.critical(
            None, "Erreur de démarrage",
            f"Impossible de démarrer l'application :\n\n{e}")
        sys.exit(1)

    window.show()
    logging.info("Fenêtre principale affichée")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
