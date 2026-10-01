"""
Fenêtre principale de l'application
"""

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTabWidget
from PySide6.QtCore import Qt

# Utiliser la nouvelle Database
try:
    from app.data.db import Database
except ImportError:
    from utils.database import Database

from ui.eleves_page import EleveListWidget
from ui.dashboard import DashboardWidget


class MainWindow(QMainWindow):
    """Fenêtre principale d'EduPaie"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("EduPaie - Système de Gestion des Paiements Scolaires")
        self.setMinimumSize(1200, 800)

        # Initialiser la base de données
        self.db = Database()
        # Note: le schéma est déjà initialisé par main.py

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Onglets
        self.tabs = QTabWidget()

        # Onglet Tableau de bord
        self.dashboard_widget = DashboardWidget()
        self.tabs.addTab(self.dashboard_widget, "Tableau de bord")

        # Onglet Élèves
        self.eleve_widget = EleveListWidget()
        self.tabs.addTab(self.eleve_widget, "Élèves")

        layout.addWidget(self.tabs)
