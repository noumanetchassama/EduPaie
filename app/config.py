"""
Configuration de l'application EduPaie

Contient :
- resource_path() : accès aux ressources embarquées par PyInstaller (base = racine projet en dev)
- Chemins utilisateur : DB de travail, logs et reçus PDF
- Configuration monnaie (FCFA) et école
"""

import os
import sys
from pathlib import Path


# ============================================================
# GESTION DES RESSOURCES EMBARQUÉES (PyInstaller)
# ============================================================

def _base_path() -> Path:
    """
    Retourne le répertoire de base des ressources.

    - Avec PyInstaller (--onefile / --onedir) : sys._MEIPASS
    - En développement : la RACINE du projet (parent du package `app`)
    """
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass)
    # app/config.py -> racine du projet = parent du dossier `app`
    return Path(__file__).resolve().parent.parent


def resource_path(relative_path: str) -> str:
    """
    Retourne le chemin absolu vers une ressource.

    Args:
        relative_path: Chemin relatif depuis la racine du projet
                       (ex: 'app/data/schema.sql', 'data/edupaie_seed.db')

    Returns:
        Chemin absolu vers la ressource
    """
    return str(_base_path() / relative_path)


# ============================================================
# CHEMINS UTILISATEUR (données persistantes)
# ============================================================

def get_appdata_path() -> Path:
    """
    Retourne le dossier de données de l'utilisateur.

    Windows : %APPDATA%/EduPaie
    Linux/macOS : ~/.config/EduPaie
    """
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", os.path.expanduser("~")))
    else:
        base = Path(os.path.expanduser("~/.config"))

    app_path = base / "EduPaie"
    app_path.mkdir(parents=True, exist_ok=True)
    return app_path


def get_documents_path() -> Path:
    """
    Retourne le dossier Documents de l'utilisateur (sous-dossier EduPaie créé).
    """
    docs_path = Path(os.path.expanduser("~/Documents")) / "EduPaie"
    docs_path.mkdir(parents=True, exist_ok=True)
    return docs_path


# Chemin de la base de données de travail (dans APPDATA)
# Surcharge possible pour les tests : variable d'environnement EDUPAIE_DB
def _resolve_db_path() -> Path:
    env_db = os.environ.get("EDUPAIE_DB")
    if env_db:
        return Path(env_db)
    return get_appdata_path() / "edupaie.db"


DB_PATH = _resolve_db_path()

# Chemin de la base de données modèle (embarquée)
SEED_DB_PATH = resource_path(os.path.join("data", "edupaie_seed.db"))

# Chemin du fichier de schéma SQL (embarqué)
SCHEMA_PATH = resource_path(os.path.join("app", "data", "schema.sql"))

# Chemin du dossier des reçus PDF (dans Documents)
RECEIPTS_FOLDER = get_documents_path() / "Recus"
RECEIPTS_FOLDER.mkdir(parents=True, exist_ok=True)

# Chemin du fichier de logs (dans APPDATA)
LOG_FILE = get_appdata_path() / "edupaie.log"


# ============================================================
# CONFIGURATION MONNAIE — FCFA (XOF)
# ============================================================
# Le FCFA n'a pas de sous-unité en circulation : les montants sont
# stockés en entiers d'unités (pas de centimes, donc pas d'erreurs
# d'arrondi non plus).

CURRENCY_CODE = "XOF"
CURRENCY_SYMBOL = "FCFA"
CURRENCY_SUBUNIT = 1  # pas de centime en pratique
# Ancienne sous-unité euro ; conservée pour compatibilité, valeur neutre
CURRENCY_SUBUNIT_EUR = 1

# Nom de l'école (personnalisable)
SCHOOL_NAME = "Groupe Scolaire Exemple"
SCHOOL_ADDRESS = "123 Rue de l'École"
SCHOOL_PHONE = "01 23 45 67 89"
SCHOOL_EMAIL = "contact@ecole-exemple.fr"


# ============================================================
# FONCTIONS DE CONVERSION / FORMATAGE MONNAIE
# ============================================================

def euros_to_cents(euros: float) -> int:
    """
    Convertit un montant saisi (float) en entier d'unités FCFA.

    L'API historique est conservée (nom et usage) : le « centime » est
    aujourd'hui l'unité FCFA elle-même (pas de sous-unité).
    Ex: 25000.0 -> 25000
    """
    return int(round(float(euros)))


def cents_to_euros(cents: int) -> float:
    """
    Convertit un entier FCFA en float (compatibilité des services/vues).
    Ex: 25000 -> 25000.0
    """
    return float(cents)


def format_euros(cents: int) -> str:
    """
    Formate un montant en entier pour l'affichage.
    Ex: 250000 -> '250 000 FCFA'
    """
    return f"{int(cents):,}".replace(",", " ") + f" {CURRENCY_SYMBOL}"
