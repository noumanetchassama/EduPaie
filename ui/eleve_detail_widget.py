"""
Widget de détail d'un élève avec historique des paiements
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                QTableWidget, QTableWidgetItem, QPushButton, 
                                QMessageBox, QHeaderView, QFileDialog)
from PySide6.QtCore import Qt
from models.eleve import Eleve
from models.paiement import Paiement
from services.eleve_service import EleveService
from services.paiement_service import PaiementService
from services.recu_service import RecuService


class EleveDetailWidget(QWidget):
    """Widget affichant les détails d'un élève et l'historique de ses paiements"""
    
    def __init__(self, parent=None, eleve_id=None):
        super().__init__(parent)
        self.eleve_service = EleveService()
        self.paiement_service = PaiementService()
        self.recu_service = RecuService()
        self.eleve_id = eleve_id
        self.eleve = None
        self.setup_ui()
        
        if eleve_id:
            self.load_eleve()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Informations de l'élève
        info_layout = QVBoxLayout()
        self.info_label = QLabel("Aucun élève sélectionné")
        self.info_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        info_layout.addWidget(self.info_label)
        
        # Solde
        self.solde_label = QLabel("")
        self.solde_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        info_layout.addWidget(self.solde_label)
        
        layout.addLayout(info_layout)
        
        # Historique des paiements
        layout.addWidget(QLabel("Historique des paiements"))
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Date", "Montant (€)", "Mode", "N° Reçu", "Solde après (€)"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        # Boutons
        button_layout = QHBoxLayout()
        
        self.voir_recu_btn = QPushButton("Voir le reçu")
        self.voir_recu_btn.clicked.connect(self.voir_recu)
        self.voir_recu_btn.setEnabled(False)
        button_layout.addWidget(self.voir_recu_btn)
        
        self.imprimer_recu_btn = QPushButton("Imprimer le reçu (PDF)")
        self.imprimer_recu_btn.clicked.connect(self.imprimer_recu)
        self.imprimer_recu_btn.setEnabled(False)
        button_layout.addWidget(self.imprimer_recu_btn)
        
        button_layout.addStretch()
        
        self.refresh_btn = QPushButton("Actualiser")
        self.refresh_btn.clicked.connect(self.load_eleve)
        button_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(button_layout)
        
        # Connexion du signal de sélection
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
    
    def set_eleve(self, eleve_id: int):
        """Définit l'élève à afficher"""
        self.eleve_id = eleve_id
        self.load_eleve()
    
    def load_eleve(self):
        """Charge les informations de l'élève et ses paiements"""
        if not self.eleve_id:
            return
        
        self.eleve = self.eleve_service.get_eleve(self.eleve_id)
        if not self.eleve:
            QMessageBox.warning(self, "Erreur", "Élève non trouvé")
            return
        
        # Afficher les infos de l'élève
        self.info_label.setText(
            f"{self.eleve.nom} {self.eleve.prenom} - {self.eleve.classe} - {self.eleve.annee_scolaire}"
        )
        
        # Calculer et afficher le solde
        try:
            solde = self.paiement_service.get_solde(self.eleve_id)
            statut = self.paiement_service.get_statut_paiement(self.eleve_id)
            
            color = "green" if statut == "Soldé" else ("orange" if statut == "Partiellement payé" else "red")
            self.solde_label.setText(
                f"Solde restant: {solde:.2f} € - Statut: <span style='color: {color};'>{statut}</span>"
            )
        except Exception as e:
            self.solde_label.setText("Erreur de calcul du solde")
        
        # Charger les paiements
        self.load_paiements()
    
    def load_paiements(self):
        """Charge l'historique des paiements"""
        paiements = self.paiement_service.get_paiements_eleve(self.eleve_id)
        
        self.table.setRowCount(len(paiements))
        solde_cumule = self.eleve.montant_du
        
        for row, paiement in enumerate(paiements):
            self.table.setItem(row, 0, QTableWidgetItem(paiement.date_paiement))
            self.table.setItem(row, 1, QTableWidgetItem(f"{paiement.montant:.2f}"))
            
            mode_label = PaiementService.MODES_PAIEMENT_LABELS.get(paiement.mode_paiement, paiement.mode_paiement)
            self.table.setItem(row, 2, QTableWidgetItem(mode_label))
            self.table.setItem(row, 3, QTableWidgetItem(paiement.numero_recu))
            
            solde_cumule -= paiement.montant
            self.table.setItem(row, 4, QTableWidgetItem(f"{solde_cumule:.2f}"))
    
    def on_selection_changed(self):
        """Active/désactive les boutons selon la sélection"""
        has_selection = len(self.table.selectedItems()) > 0
        self.voir_recu_btn.setEnabled(has_selection)
        self.imprimer_recu_btn.setEnabled(has_selection)
    
    def voir_recu(self):
        """Affiche les détails du reçu sélectionné"""
        row = self.table.currentRow()
        if row < 0:
            return
        
        numero_recu = self.table.item(row, 3).text()
        paiement = self.paiement_service.get_paiement_by_recu(numero_recu)
        
        if paiement:
            solde_apres = float(self.table.item(row, 4).text())
            mode_label = PaiementService.MODES_PAIEMENT_LABELS.get(paiement.mode_paiement, paiement.mode_paiement)
            
            message = f"""
            <h3>Reçu de paiement</h3>
            <p><b>Numéro de reçu:</b> {paiement.numero_recu}</p>
            <p><b>Élève:</b> {self.eleve.nom} {self.eleve.prenom}</p>
            <p><b>Classe:</b> {self.eleve.classe}</p>
            <p><b>Date:</b> {paiement.date_paiement}</p>
            <p><b>Montant payé:</b> {paiement.montant:.2f} €</p>
            <p><b>Mode de paiement:</b> {mode_label}</p>
            <p><b>Solde après paiement:</b> {solde_apres:.2f} €</p>
            """
            
            QMessageBox.information(self, "Détails du reçu", message)
        else:
            QMessageBox.warning(self, "Erreur", "Reçu non trouvé")
    
    def imprimer_recu(self):
        """Génère et ouvre le PDF du reçu sélectionné"""
        row = self.table.currentRow()
        if row < 0:
            return
        
        numero_recu = self.table.item(row, 3).text()
        paiement = self.paiement_service.get_paiement_by_recu(numero_recu)
        
        if paiement:
            # Demander où sauvegarder le PDF
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Sauvegarder le reçu",
                f"recu_{numero_recu}.pdf",
                "Fichiers PDF (*.pdf)"
            )
            
            if file_path:
                try:
                    self.recu_service.generer_recu_pdf(paiement, self.eleve, file_path)
                    QMessageBox.information(
                        self, 
                        "Succès", 
                        f"Reçu généré avec succès:\n{file_path}"
                    )
                except Exception as e:
                    QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération du PDF: {str(e)}")
        else:
            QMessageBox.warning(self, "Erreur", "Reçu non trouvé")
