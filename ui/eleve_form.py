"""
Formulaire d'ajout/modification d'élève
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                                QLineEdit, QDoubleSpinBox, QPushButton, 
                                QMessageBox)
from PySide6.QtCore import Qt
from models.eleve import Eleve


class EleveForm(QDialog):
    """Dialogue pour ajouter ou modifier un élève"""
    
    def __init__(self, parent=None, eleve=None):
        super().__init__(parent)
        self.eleve = eleve
        self.setWindowTitle("Ajouter un élève" if eleve is None else "Modifier un élève")
        self.setMinimumWidth(400)
        self.setup_ui()
        
        if eleve:
            self.load_eleve()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Nom
        layout.addWidget(QLabel("Nom *"))
        self.nom_edit = QLineEdit()
        self.nom_edit.setPlaceholderText("Nom de l'élève")
        layout.addWidget(self.nom_edit)
        
        # Prénom
        layout.addWidget(QLabel("Prénom *"))
        self.prenom_edit = QLineEdit()
        self.prenom_edit.setPlaceholderText("Prénom de l'élève")
        layout.addWidget(self.prenom_edit)
        
        # Classe
        layout.addWidget(QLabel("Classe *"))
        self.classe_edit = QLineEdit()
        self.classe_edit.setPlaceholderText("Ex: 6ème A, CM2, etc.")
        layout.addWidget(self.classe_edit)
        
        # Année scolaire
        layout.addWidget(QLabel("Année scolaire *"))
        self.annee_edit = QLineEdit()
        self.annee_edit.setPlaceholderText("Ex: 2024-2025")
        layout.addWidget(self.annee_edit)
        
        # Montant dû
        layout.addWidget(QLabel("Montant des frais de scolarité (€) *"))
        self.montant_spin = QDoubleSpinBox()
        self.montant_spin.setRange(0, 100000)
        self.montant_spin.setDecimals(2)
        self.montant_spin.setValue(0)
        layout.addWidget(self.montant_spin)
        
        # Boutons
        button_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("Annuler")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton("Enregistrer")
        self.save_btn.clicked.connect(self.validate_and_save)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
    
    def load_eleve(self):
        """Charge les données de l'élève dans le formulaire"""
        self.nom_edit.setText(self.eleve.nom)
        self.prenom_edit.setText(self.eleve.prenom)
        self.classe_edit.setText(self.eleve.classe)
        self.annee_edit.setText(self.eleve.annee_scolaire)
        self.montant_spin.setValue(self.eleve.montant_du)
    
    def validate_and_save(self):
        """Valide le formulaire et sauvegarde"""
        nom = self.nom_edit.text().strip()
        prenom = self.prenom_edit.text().strip()
        classe = self.classe_edit.text().strip()
        annee = self.annee_edit.text().strip()
        montant = self.montant_spin.value()
        
        # Validation
        if not nom:
            QMessageBox.warning(self, "Erreur", "Le nom est obligatoire")
            self.nom_edit.setFocus()
            return
        if not prenom:
            QMessageBox.warning(self, "Erreur", "Le prénom est obligatoire")
            self.prenom_edit.setFocus()
            return
        if not classe:
            QMessageBox.warning(self, "Erreur", "La classe est obligatoire")
            self.classe_edit.setFocus()
            return
        if not annee:
            QMessageBox.warning(self, "Erreur", "L'année scolaire est obligatoire")
            self.annee_edit.setFocus()
            return
        if montant <= 0:
            QMessageBox.warning(self, "Erreur", "Le montant doit être supérieur à 0")
            self.montant_spin.setFocus()
            return
        
        # Créer ou mettre à jour l'élève
        if self.eleve:
            self.eleve.nom = nom
            self.eleve.prenom = prenom
            self.eleve.classe = classe
            self.eleve.annee_scolaire = annee
            self.eleve.montant_du = montant
        else:
            self.eleve = Eleve(
                nom=nom,
                prenom=prenom,
                classe=classe,
                annee_scolaire=annee,
                montant_du=montant
            )
        
        self.accept()
    
    def get_eleve(self) -> Eleve:
        """Retourne l'élève du formulaire"""
        return self.eleve
