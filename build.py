"""
Script de construction de l'exécutable avec PyInstaller

- DB seed et schéma SQL embarqués (--add-data)
- PySide6 et reportlab détectés automatiquement
"""

import subprocess
import sys

SEP = ";" if sys.platform == "win32" else ":"


def build_exe():
    """Construit l'exécutable EduPaie."""
    print("Construction de l'exécutable EduPaie...")

    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name=EduPaie",
        f"--add-data=data{SEP}data",                # DB seed embarquée
        f"--add-data=app/data{SEP}app/data",        # Schéma SQL
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=PySide6.QtWidgets",
        "--hidden-import=reportlab",
        "--hidden-import=reportlab.lib",
        "--hidden-import=reportlab.platypus",
        "main.py",
    ]

    try:
        subprocess.run(cmd, check=True)
        print("\n[OK] Exécutable créé dans dist/EduPaie.exe")
        print("     - DB de travail : %APPDATA%/EduPaie au premier lancement")
        print("     - Reçus PDF     : ~/Documents/EduPaie/Recus")
    except subprocess.CalledProcessError as e:
        print(f"\n[ERREUR] Échec de la construction : {e}")
        sys.exit(1)


if __name__ == "__main__":
    build_exe()
