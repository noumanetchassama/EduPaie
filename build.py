"""
Script de construction de l'exécutable EduPaie avec PyInstaller

Produit un fichier exécutable standalone (Windows) qui ne nécessite
pas d'installation Python préalable.
"""

import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path


def validate_executable(path: Path):
    """Refuse de publier un fichier qui n'est pas un exécutable PE Windows."""
    with path.open("rb") as executable:
        header = executable.read(64)
        if len(header) < 64 or header[:2] != b"MZ":
            raise RuntimeError("L'exécutable généré n'a pas d'en-tête Windows valide.")

        pe_offset = struct.unpack_from("<I", header, 0x3C)[0]
        executable.seek(pe_offset)
        pe_header = executable.read(6)

    if len(pe_header) != 6 or pe_header[:4] != b"PE\0\0":
        raise RuntimeError("La signature PE de l'exécutable généré est invalide.")

    machine = struct.unpack_from("<H", pe_header, 4)[0]
    if machine not in (0x014C, 0x8664, 0xAA64):
        raise RuntimeError(f"Architecture PE Windows non reconnue : 0x{machine:04X}.")


def build_exe():
    """Construit l'exécutable avec PyInstaller."""

    # Vérifier PyInstaller dans le même environnement Python que l'application.
    try:
        import PyInstaller
    except ImportError:
        print("Installation de PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller>=6.0"])

    try:
        # Construire hors du dossier synchronisé, puis publier le fichier complet.
        with tempfile.TemporaryDirectory(prefix="edupaie-build-") as temp_dir:
            build_root = Path(temp_dir)
            staged_dist = build_root / "dist"
            work_dir = build_root / "work"
            dist_dir = Path.cwd() / "dist"

            cmd = [
                sys.executable,
                "-m",
                "PyInstaller",
                "--noconfirm",
                "--clean",
                "--name=EduPaie",
                "--onefile",
                "--windowed",
                "--icon=NONE",
                "--add-data=app/data/schema.sql;app/data",
                "--hidden-import=PySide6.QtCore",
                "--hidden-import=PySide6.QtGui",
                "--hidden-import=PySide6.QtWidgets",
                f"--distpath={staged_dist}",
                f"--workpath={work_dir}",
                "main.py",
            ]

            print("Construction de l'exécutable Windows...")
            subprocess.check_call(cmd)

            built_exe = staged_dist / "EduPaie.exe"
            validate_executable(built_exe)

            dist_dir.mkdir(exist_ok=True)
            published_temp = dist_dir / ".EduPaie.exe.tmp"
            try:
                shutil.copy2(built_exe, published_temp)
                validate_executable(published_temp)
                published_temp.replace(dist_dir / "EduPaie.exe")
            finally:
                published_temp.unlink(missing_ok=True)

        print("\n[OK] Construction réussie !")
        print(f"Exécutable créé et vérifié : {dist_dir / 'EduPaie.exe'}")
    except subprocess.CalledProcessError as e:
        print(f"\n[ERREUR] Erreur de construction : {e}")
        sys.exit(1)
    except (OSError, RuntimeError) as e:
        print(f"\n[ERREUR] Exécutable non publié : {e}")
        sys.exit(1)


if __name__ == "__main__":
    build_exe()
