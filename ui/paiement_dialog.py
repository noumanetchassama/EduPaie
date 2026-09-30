"""
Dialogue d'enregistrement de paiement
"""

from datetime import datetime
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                                QDoubleSpinBox, QComboBox, QDateEdit, 
                                QPushButton, QMessageBox)
from PySide6.QtCore import Qt, QDate
from services.paiement_service import PaiementService
from services.eleve_service import EleveService
from models.eleve import Eleve


class PaiementDialog(QDialog):
    """Dialogue pour enregistrer un paiement"""
    
    def __init__(self, parent=None, eleve=None):
        super().__init__(parent)
        self.eleve = eleve
        self.paiement_service = PaiementService()
        self.eleve_service = EleveService()
        
        self.setWindowTitle("Enregistrer un paiement")
        self.setMinimumWidth(450)
        self.setup_ui()
        
        if eleve:
            self.load_eleve_info()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Informations de l'élève
        layout.addWidget(QLabel("Élève"))
        self.eleve_label = QLabel("-")
        self.eleve_label.setStyleSheet("font-weight: bold; padding: 5px;")
        layout.addWidget(self.eleve_label)
        
        # Sélection de l'élève (si non fourni)
        if not self.eleve:
            layout.addWidget(QLabel("Sélectionner un élève *"))
            self.eleve_combo = QComboBox()
            self.load_eleves()
            layout.addWidget(self.eleve_combo)
        
        # Solde restant
        layout.addWidget(QLabel("Solde restant avant paiement"))
        self.solde_label = QLabel("0.00 €")
        self.solde_label.setStyleSheet("font-weight: bold; color: blue; padding: 5px;")
        layout.addWidget(self.solde_label)
        
        # Montant du paiement
        layout.addWidget(QLabel("Montant du paiement (€) *"))
        self.montant_spin = QDoubleSpinBox()
        self.montant_spin.setRange(0.01, 100000)
        self.montant_spin.setDecimals(2)
        self.montant_spin.setValue(0)
        layout.addWidget(self.montant_spin)
        
        # Date du paiement
        layout.addWidget(QLabel("Date du paiement *"))
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        layout.addWidget(self.date_edit)
        
        # Mode de paiement
        layout.addWidget(QLabel("Mode de paiement *"))
        self.mode_combo = QComboBox()
        for mode in PaiementService.MODES_PAIEMENT:
            self.mode_combo.addItem(PaiementService.MODES_PAIEMENT_LABELS[mode], mode)
        layout.addWidget(self.mode_combo)
        
        # Boutons
        button_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("Annuler")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton("Enregistrer le paiement")
        self.save_btn.clicked.connect(self.validate_and_save)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
        
        # Connexion des signaux
        if self.eleve:
            self.montant_spin.valueChanged.connect(self.update_solde_info)
    
    def load_eleves(self):
        """Charge la liste des élèves dans le combo"""
        eleves = self.eleve_service.get_all_eleves()
        for eleve in eleves:
            self.eleve_combo.addItem(
                f"{eleve.nom} {eleve.prenom} ({eleve.classe})", 
                eleve.id
            )
        self.eleve_combo.currentIndexChanged.connect(self.on_eleve_changed)
    
    def load_eleve_info(self):
        """Affiche les informations de l'élève"""
        if self.eleve:
            self.eleve_label.setText(f"{self.eleve.nom} {self.eleve.prenom} - {self.eleve.classe}")
            self.update_solde_info()
    
    def on_eleve_changed(self):
        """Met à jour les infos quand l'élève change"""
        if hasattr(self, 'eleve_combo'):
            eleve_id = self.eleve_combo.currentData()
            if eleve_id:
                self.eleve = self.eleve_service.get_eleve(eleve_id)
                self.eleve_label.setText(f"{self.eleve.nom} {self.eleve.prenom} - {self.eleve.classe}")
                self.update_solde_info()
    
    def update_solde_info(self):
        """Met à jour l'affichage du solde"""
        if self.eleve:
            try:
                solde = self.paiement_service.get_solde(self.eleve.id)
                self.solde_label.setText(f"{solde:.2f} €")
                self.montant_spin.setMaximum(solde)
            except ValueError:
                self.solde_label.setText("Erreur")
    
    def validate_and_save(self):
        """Valide et enregistre le paiement"""
        # Récupérer l'élève
        if hasattr(self, 'eleve_combo'):
            eleve_id = self.eleve_combo.currentData()
            if not eleve_id:
                QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un élève")
                return
            self.eleve = self.eleve_service.get_eleve(eleve_id)
        
        if not self.eleve:
            QMessageBox.warning(self, "Erreur", "Aucun élève sélectionné")
            return
        
        montant = self.montant_spin.value()
        date_paiement = self.date_edit.date().toString("yyyy-MM-dd")
        mode_paiement = self.mode_combo.currentData()
        
        # Validation
        if montant <= 0:
            QMessageBox.warning(self, "Erreur", "Le montant doit être supérieur à 0")
            return
        
        try:
            paiement = self.paiement_service.create_paiement(
                self.eleve.id, montant, date_paiement, mode_paiement
            )
            QMessageBox.information(
                self, 
                "Succès", 
                f"Paiement enregistré avec succès\n\n"
                f"Numéro de reçu: {paiement.numero_recu}\n"
                f"Montant: {montant:.2f} €\n"
                f"Solde restant: {self.paiement_service.get_solde(self.eleve.id):.2f} €"
            )
            self.accept()
        except ValueError as e:
            QMessageBox.critical(self, "Erreur", str(e))
    
    def get_paiement(self):
        """Retourne le paiement créé"""
        return self.paiement
