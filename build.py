"""
Script de construction de l'exécutable avec PyInstaller

Utilise la nouvelle architecture avec :
- DB seed embarquée
- Schéma SQL embarqué
- Configuration resource_path()
"""

import os
import subprocess
import sys


def build_exe():
    """Construit l'exécutable avec PyInstaller"""

    print("Construction de l'exécutable EduPaie...")

    # Commande PyInstaller
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name=EduPaie",
        "--add-data=data;data",  # DB seed
        "--add-data=app/data;app/data",  # Schéma SQL et migrations
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=PySide6.QtWidgets",
        "--hidden-import=reportlab",
        "--hidden-import=reportlab.lib",
        "--hidden-import=reportlab.platypus",
        "main.py"
    ]

    try:
        subprocess.run(cmd, check=True)
        print("\n✓ Exécutable créé avec succès dans le dossier dist/")
        print("✓ Le fichier se nomme: EduPaie.exe")
        print("\nNote: La DB de travail sera créée dans %APPDATA%/EduPaie au premier lancement")
        print("      Les reçus PDF seront sauvegardés dans Documents/EduPaie/Recus")
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Erreur lors de la construction: {e}")
        sys.exit(1)


if __name__ == "__main__":
    build_exe()
