"""
Script de construction de l'exécutable EduPaie avec PyInstaller

Produit un fichier exécutable standalone (Windows) qui ne nécessite
pas d'installation Python préalable.
"""

import os
import subprocess
import sys
from pathlib import Path


def build_exe():
    """Construit l'exécutable avec PyInstaller."""

    # Vérifier que PyInstaller est installé
    try:
        import PyInstaller
    except ImportError:
        print("Installation de PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller>=6.0"])

    # Créer le dossier dist s'il n'existe pas
    dist_dir = Path("dist")
    dist_dir.mkdir(exist_ok=True)

    # Commande PyInstaller
    cmd = [
        "pyinstaller",
        "--name=EduPaie",
        "--onefile",
        "--windowed",
        "--icon=NONE",
        "--add-data=app/data/schema.sql;app/data",
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=PySide6.QtWidgets",
        "main.py",
    ]

    print("Construction de l'exécutable...")
    print(f"Commande: {' '.join(cmd)}")

    try:
        subprocess.check_call(cmd)
        print("\n[OK] Construction reussie !")
        print(f"Executable cree: {dist_dir / 'EduPaie.exe'}")
    except subprocess.CalledProcessError as e:
        print(f"\n[ERREUR] Erreur lors de la construction: {e}")
        sys.exit(1)


if __name__ == "__main__":
    build_exe()
