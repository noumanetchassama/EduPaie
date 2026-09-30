"""
Fenêtre principale de l'application
"""

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTabWidget
from PySide6.QtCore import Qt
from repository.database import Database
from ui.eleve_list_widget import EleveListWidget


class MainWindow(QMainWindow):
    """Fenêtre principale d'EduPaie"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EduPaie - Gestion des paiements scolaires")
        self.setMinimumSize(1000, 700)
        
        # Initialiser la base de données
        self.db = Database()
        self.db.initialize_schema()
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Onglets
        self.tabs = QTabWidget()
        
        # Onglet Élèves
        self.eleve_widget = EleveListWidget()
        self.tabs.addTab(self.eleve_widget, "Élèves")
        
        layout.addWidget(self.tabs)
