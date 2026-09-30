"""
Widget de tableau de bord avec statistiques globales
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                QTableWidget, QTableWidgetItem, QComboBox, 
                                QHeaderView, QFrame)
from PySide6.QtCore import Qt
from services.eleve_service import EleveService
from services.paiement_service import PaiementService


class DashboardWidget(QWidget):
    """Widget affichant le tableau de bord avec statistiques"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.eleve_service = EleveService()
        self.paiement_service = PaiementService()
        self.setup_ui()
        self.load_stats()
        self.load_eleves()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Statistiques globales
        stats_layout = QHBoxLayout()
        
        # Carte 1: Nombre d'élèves
        self.nb_eleves_card = self.create_stat_card("Nombre d'élèves", "0", "#3498db")
        stats_layout.addWidget(self.nb_eleves_card)
        
        # Carte 2: Total encaissé
        self.total_encaisse_card = self.create_stat_card("Total encaissé", "0 €", "#27ae60")
        stats_layout.addWidget(self.total_encaisse_card)
        
        # Carte 3: Total restant dû
        self.total_restant_card = self.create_stat_card("Total restant dû", "0 €", "#e74c3c")
        stats_layout.addWidget(self.total_restant_card)
        
        # Carte 4: Élèves non soldés
        self.non_soldes_card = self.create_stat_card("Élèves non soldés", "0", "#f39c12")
        stats_layout.addWidget(self.non_soldes_card)
        
        layout.addLayout(stats_layout)
        
        # Filtre par statut
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filtrer par statut:"))
        
        self.statut_combo = QComboBox()
        self.statut_combo.addItem("Tous les élèves")
        self.statut_combo.addItem("Soldés")
        self.statut_combo.addItem("Partiellement payés")
        self.statut_combo.addItem("Non payés")
        self.statut_combo.currentTextChanged.connect(self.on_filter_statut)
        filter_layout.addWidget(self.statut_combo)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Tableau des élèves avec statut
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["Nom", "Prénom", "Classe", "Année", "Montant dû (€)", "Payé (€)", "Solde (€)", "Statut"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
    
    def create_stat_card(self, title: str, value: str, color: str):
        """Crée une carte de statistique"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 10px;
                padding: 15px;
            }}
            QLabel {{
                color: white;
                font-weight: bold;
            }}
        """)
        card.setFixedHeight(100)
        
        layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px;")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet("font-size: 28px;")
        layout.addWidget(value_label)
        
        # Stocker la référence au label de valeur
        card.value_label = value_label
        
        return card
    
    def load_stats(self):
        """Charge les statistiques globales"""
        eleves = self.eleve_service.get_all_eleves()
        
        # Nombre d'élèves
        nb_eleves = len(eleves)
        self.nb_eleves_card.value_label.setText(str(nb_eleves))
        
        # Total encaissé et restant
        total_encaisse = 0.0
        total_restant = 0.0
        nb_non_soldes = 0
        
        for eleve in eleves:
            try:
                total_paye = self.paiement_service.paiement_repo.get_total_by_eleve(eleve.id)
                solde = eleve.montant_du - total_paye
                
                total_encaisse += total_paye
                total_restant += solde
                
                if solde > 0:
                    nb_non_soldes += 1
            except:
                total_restant += eleve.montant_du
                nb_non_soldes += 1
        
        self.total_encaisse_card.value_label.setText(f"{total_encaisse:.2f} €")
        self.total_restant_card.value_label.setText(f"{total_restant:.2f} €")
        self.non_soldes_card.value_label.setText(str(nb_non_soldes))
    
    def load_eleves(self):
        """Charge tous les élèves dans le tableau"""
        self.current_eleves = self.eleve_service.get_all_eleves()
        self.update_table()
    
    def update_table(self):
        """Met à jour le tableau avec les élèves filtrés"""
        statut_filter = self.statut_combo.currentText()
        
        # Filtrer par statut
        if statut_filter == "Tous les élèves":
            filtered_eleves = self.current_eleves
        else:
            filtered_eleves = []
            for eleve in self.current_eleves:
                try:
                    statut = self.paiement_service.get_statut_paiement(eleve.id)
                    if statut == statut_filter:
                        filtered_eleves.append(eleve)
                except:
                    if statut_filter == "Non payés":
                        filtered_eleves.append(eleve)
        
        self.table.setRowCount(len(filtered_eleves))
        
        for row, eleve in enumerate(filtered_eleves):
            self.table.setItem(row, 0, QTableWidgetItem(eleve.nom))
            self.table.setItem(row, 1, QTableWidgetItem(eleve.prenom))
            self.table.setItem(row, 2, QTableWidgetItem(eleve.classe))
            self.table.setItem(row, 3, QTableWidgetItem(eleve.annee_scolaire))
            self.table.setItem(row, 4, QTableWidgetItem(f"{eleve.montant_du:.2f}"))
            
            # Calculer le montant payé et le solde
            try:
                total_paye = self.paiement_service.paiement_repo.get_total_by_eleve(eleve.id)
                solde = eleve.montant_du - total_paye
                statut = self.paiement_service.get_statut_paiement(eleve.id)
            except:
                total_paye = 0
                solde = eleve.montant_du
                statut = "Non payé"
            
            self.table.setItem(row, 5, QTableWidgetItem(f"{total_paye:.2f}"))
            self.table.setItem(row, 6, QTableWidgetItem(f"{solde:.2f}"))
            
            # Statut avec couleur
            statut_item = QTableWidgetItem(statut)
            if statut == "Soldé":
                statut_item.setForeground(Qt.GlobalColor.green)
            elif statut == "Partiellement payé":
                statut_item.setForeground(Qt.GlobalColor.darkYellow)
            else:
                statut_item.setForeground(Qt.GlobalColor.red)
            self.table.setItem(row, 7, statut_item)
    
    def on_filter_statut(self, statut):
        """Filtre les élèves par statut"""
        self.update_table()
    
    def refresh(self):
        """Actualise les données"""
        self.load_stats()
        self.load_eleves()
