"""
Script de construction de l'exécutable avec PyInstaller
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
        "--add-data=database;database",
        "--add-data=resources;resources",
        "main.py"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("\n✓ Exécutable créé avec succès dans le dossier dist/")
        print("✓ Le fichier se nomme: EduPaie.exe")
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Erreur lors de la construction: {e}")
        sys.exit(1)


if __name__ == "__main__":
    build_exe()
