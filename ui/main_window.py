"""
Fenêtre principale de l'application
"""

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


class MainWindow(QMainWindow):
    """Fenêtre principale d'EduPaie"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EduPaie - Gestion des paiements scolaires")
        self.setMinimumSize(1000, 700)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Label temporaire
        label = QLabel("EduPaie - Application en cours de développement")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 18px; font-weight: bold; padding: 20px;")
        layout.addWidget(label)
