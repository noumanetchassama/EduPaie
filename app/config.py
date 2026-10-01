"""
Configuration de l'application EduPaie

Contient :
- resource_path() : pour accéder aux ressources embarquées par PyInstaller
- Chemins utilisateur : pour DB de travail, logs et PDFs
- Configuration monnaie et école
"""

import os
import sys
from pathlib import Path


# ============================================================
# GESTION DES RESSOURCES EMBARQUÉES (PyInstaller)
# ============================================================

def resource_path(relative_path: str) -> str:
    """
    Retourne le chemin absolu vers une ressource.

    En développement : chemin relatif au dossier du script
    Avec PyInstaller --onefile : chemin dans sys._MEIPASS (dossier temporaire)

    Args:
        relative_path: Chemin relatif depuis la racine du projet

    Returns:
        Chemin absolu vers la ressource
    """
    try:
        # PyInstaller crée un dossier temporaire sys._MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # En développement, base_path est le dossier du script
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)


# ============================================================
# CHEMINS UTILISATEUR (données persistantes)
# ============================================================

def get_appdata_path() -> Path:
    """
    Retourne le chemin du dossier Application Data de l'utilisateur.

    Windows : %APPDATA%/EduPaie
    Linux/macOS : ~/.config/EduPaie

    Returns:
        Path: Chemin du dossier de données utilisateur
    """
    if sys.platform == 'win32':
        base = Path(os.environ.get('APPDATA', os.path.expanduser('~')))
    else:
        base = Path(os.path.expanduser('~/.config'))

    app_path = base / 'EduPaie'
    app_path.mkdir(parents=True, exist_ok=True)
    return app_path


def get_documents_path() -> Path:
    """
    Retourne le chemin du dossier Documents de l'utilisateur.

    Windows : %USERPROFILE%/Documents/EduPaie
    Linux/macOS : ~/Documents/EduPaie

    Returns:
        Path: Chemin du dossier Documents/EduPaie
    """
    if sys.platform == 'win32':
        base = Path(os.path.expanduser('~/Documents'))
    else:
        base = Path(os.path.expanduser('~/Documents'))

    docs_path = base / 'EduPaie'
    docs_path.mkdir(parents=True, exist_ok=True)
    return docs_path


# Chemin de la base de données de travail (dans APPDATA)
DB_PATH = get_appdata_path() / 'edupaie.db'

# Chemin de la base de données modèle (embarquée)
SEED_DB_PATH = resource_path('data/edupaie_seed.db')

# Chemin du dossier des reçus PDF (dans Documents)
RECEIPTS_FOLDER = get_documents_path() / 'Recus'
RECEIPTS_FOLDER.mkdir(parents=True, exist_ok=True)

# Chemin du fichier de logs (dans APPDATA)
LOG_FILE = get_appdata_path() / 'edupaie.log'


# ============================================================
# CONFIGURATION MONNAIE
# ============================================================

CURRENCY_CODE = 'EUR'  # Code ISO de la monnaie
CURRENCY_SYMBOL = '€'   # Symbole affiché
CURRENCY_SUBUNIT = 100  # Nombre de sous-unités par unité (100 cents = 1 euro)

# Nom de l'école (personnalisable)
SCHOOL_NAME = "École Exemple"
SCHOOL_ADDRESS = "123 Rue de l'École"
SCHOOL_PHONE = "01 23 45 67 89"
SCHOOL_EMAIL = "contact@ecole-exemple.fr"


# ============================================================
# FONCTIONS DE CONVERSION MONNAIE
# ============================================================

def euros_to_cents(euros: float) -> int:
    """
    Convertit un montant en euros en cents (entier).

    Attention : évite les erreurs d'arrondi float en multipliant par 100
    et en arrondissant à l'entier le plus proche.

    Args:
        euros: Montant en euros (ex: 12.50)

    Returns:
        int: Montant en cents (ex: 1250)
    """
    return int(round(euros * CURRENCY_SUBUNIT))


def cents_to_euros(cents: int) -> float:
    """
    Convertit un montant en cents en euros.

    Args:
        cents: Montant en cents (ex: 1250)

    Returns:
        float: Montant en euros (ex: 12.50)
    """
    return cents / CURRENCY_SUBUNIT


def format_euros(cents: int) -> str:
    """
    Formate un montant en cents pour l'affichage.

    Args:
        cents: Montant en cents (ex: 1250)

    Returns:
        str: Montant formaté (ex: "12,50 €")
    """
    euros = cents / CURRENCY_SUBUNIT
    return f"{euros:.2f} {CURRENCY_SYMBOL}"
