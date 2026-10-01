"""
Widget pour la liste des élèves avec recherche et filtre
Supporte la nouvelle architecture (app/services/) avec fallback vers l'ancienne
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                                QTableWidgetItem, QPushButton, QLineEdit,
                                QComboBox, QMessageBox, QHeaderView, QDialog, QLabel)
from PySide6.QtCore import Qt

# Essayer d'utiliser la nouvelle architecture
try:
    from app.models.student import Student
    from app.services.student_service import StudentService
    from app.services.payment_service import PaymentService
    from app.services.balance_service import BalanceService
    from app.config import format_euros, cents_to_euros
    NEW_ARCHITECTURE = True
    StudentModel = Student
    StudentServiceClass = StudentService
except ImportError:
    # Fallback vers l'ancienne architecture
    from models.eleve import Eleve
    from services.eleve_service import EleveService
    from services.paiement_service import PaiementService
    NEW_ARCHITECTURE = False
    StudentModel = Eleve
    StudentServiceClass = EleveService

from ui.eleve_form import EleveForm
from ui.paiement_dialog import PaiementDialog
from ui.eleve_details import EleveDetailWidget


class EleveListWidget(QWidget):
    """Widget affichant la liste des élèves avec recherche et filtre"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.eleve_service = StudentServiceClass()
        if NEW_ARCHITECTURE:
            self.paiement_service = PaymentService()
            self.balance_service = BalanceService()
        else:
            self.paiement_service = PaiementService()
        self.current_eleves = []
        self.setup_ui()
        self.load_eleves()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Barre de recherche et filtre
        search_layout = QHBoxLayout()
        
        search_layout.addWidget(QLabel("Rechercher:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Nom, prénom ou classe...")
        self.search_edit.textChanged.connect(self.on_search)
        search_layout.addWidget(self.search_edit)
        
        search_layout.addWidget(QLabel("Filtrer par classe:"))
        self.classe_combo = QComboBox()
        self.classe_combo.addItem("Toutes les classes")
        self.classe_combo.currentTextChanged.connect(self.on_filter_classe)
        search_layout.addWidget(self.classe_combo)
        
        layout.addLayout(search_layout)
        
        # Tableau des élèves
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["Nom", "Prénom", "Classe", "Année", "Montant dû (€)", "Payé (€)", "Solde (€)", "Statut"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        # Boutons d'action
        button_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("Ajouter un élève")
        self.add_btn.clicked.connect(self.add_eleve)
        button_layout.addWidget(self.add_btn)
        
        self.edit_btn = QPushButton("Modifier")
        self.edit_btn.clicked.connect(self.edit_eleve)
        self.edit_btn.setEnabled(False)
        button_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("Supprimer")
        self.delete_btn.clicked.connect(self.delete_eleve)
        self.delete_btn.setEnabled(False)
        button_layout.addWidget(self.delete_btn)
        
        self.paiement_btn = QPushButton("Enregistrer un paiement")
        self.paiement_btn.clicked.connect(self.enregistrer_paiement)
        self.paiement_btn.setEnabled(False)
        button_layout.addWidget(self.paiement_btn)
        
        self.detail_btn = QPushButton("Voir détails")
        self.detail_btn.clicked.connect(self.voir_details)
        self.detail_btn.setEnabled(False)
        button_layout.addWidget(self.detail_btn)
        
        button_layout.addStretch()
        
        self.refresh_btn = QPushButton("Actualiser")
        self.refresh_btn.clicked.connect(self.load_eleves)
        button_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(button_layout)
        
        # Connexion du signal de sélection
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
    
    def load_eleves(self):
        """Charge tous les élèves dans le tableau"""
        self.current_eleves = self.eleve_service.get_all_eleves()
        self.update_table()
        self.update_classe_filter()
    
    def update_table(self):
        """Met à jour le tableau avec les élèves courants"""
        self.table.setRowCount(len(self.current_eleves))

        for row, eleve in enumerate(self.current_eleves):
            # Adapter pour les deux architectures
            if NEW_ARCHITECTURE:
                nom = eleve.last_name
                prenom = eleve.first_name
                classe = str(eleve.class_id)  # Pour l'instant afficher l'ID
                annee = "2024-2025"  # TODO: récupérer depuis school_year
                montant_du = 0  # TODO: calculer depuis fee_plan
            else:
                nom = eleve.nom
                prenom = eleve.prenom
                classe = eleve.classe
                annee = eleve.annee_scolaire
                montant_du = eleve.montant_du

            self.table.setItem(row, 0, QTableWidgetItem(nom))
            self.table.setItem(row, 1, QTableWidgetItem(prenom))
            self.table.setItem(row, 2, QTableWidgetItem(classe))
            self.table.setItem(row, 3, QTableWidgetItem(annee))
            self.table.setItem(row, 4, QTableWidgetItem(f"{montant_du:.2f}"))

            # Calculer le montant payé et le solde
            try:
                if NEW_ARCHITECTURE:
                    # Utiliser BalanceService
                    balance_info = self.balance_service.get_balance_info(eleve.id, 1)  # TODO: school_year_id
                    total_paye = balance_info['total_paid_int']
                    solde = balance_info['balance_int']
                    statut = balance_info['status']
                    total_paye_euros = cents_to_euros(total_paye)
                    solde_euros = cents_to_euros(solde)
                else:
                    total_paye = self.paiement_service.paiement_repo.get_total_by_eleve(eleve.id)
                    solde = eleve.montant_du - total_paye
                    statut = self.paiement_service.get_statut_paiement(eleve.id)
                    total_paye_euros = total_paye
                    solde_euros = solde
            except:
                total_paye_euros = 0
                solde_euros = montant_du
                statut = "Non payé"

            self.table.setItem(row, 5, QTableWidgetItem(f"{total_paye_euros:.2f}"))
            self.table.setItem(row, 6, QTableWidgetItem(f"{solde_euros:.2f}"))

            # Statut avec couleur
            statut_item = QTableWidgetItem(statut)
            if statut == "Soldé":
                statut_item.setForeground(Qt.GlobalColor.green)
            elif statut == "Partiellement payé":
                statut_item.setForeground(Qt.GlobalColor.darkYellow)
            else:
                statut_item.setForeground(Qt.GlobalColor.red)
            self.table.setItem(row, 7, statut_item)
    
    def update_classe_filter(self):
        """Met à jour la liste des classes dans le filtre"""
        current_selection = self.classe_combo.currentText()
        self.classe_combo.clear()
        self.classe_combo.addItem("Toutes les classes")
        
        classes = self.eleve_service.get_all_classes()
        for classe in classes:
            self.classe_combo.addItem(classe)
        
        # Restaurer la sélection si possible
        index = self.classe_combo.findText(current_selection)
        if index >= 0:
            self.classe_combo.setCurrentIndex(index)
    
    def on_search(self, text):
        """Filtre les élèves selon la recherche"""
        classe_filter = self.classe_combo.currentText()
        
        if text and classe_filter != "Toutes les classes":
            # Recherche + filtre classe
            filtered = self.eleve_service.filter_eleves_by_classe(classe_filter)
            self.current_eleves = [e for e in filtered if 
                                   text.lower() in e.nom.lower() or 
                                   text.lower() in e.prenom.lower() or
                                   text.lower() in e.classe.lower()]
        elif text:
            # Recherche seulement
            self.current_eleves = self.eleve_service.search_eleves(text)
        elif classe_filter != "Toutes les classes":
            # Filtre classe seulement
            self.current_eleves = self.eleve_service.filter_eleves_by_classe(classe_filter)
        else:
            # Pas de filtre
            self.current_eleves = self.eleve_service.get_all_eleves()
        
        self.update_table()
    
    def on_filter_classe(self, classe):
        """Filtre les élèves par classe"""
        search_text = self.search_edit.text()
        
        if classe == "Toutes les classes":
            if search_text:
                self.current_eleves = self.eleve_service.search_eleves(search_text)
            else:
                self.current_eleves = self.eleve_service.get_all_eleves()
        else:
            filtered = self.eleve_service.filter_eleves_by_classe(classe)
            if search_text:
                self.current_eleves = [e for e in filtered if 
                                       search_text.lower() in e.nom.lower() or 
                                       search_text.lower() in e.prenom.lower()]
            else:
                self.current_eleves = filtered
        
        self.update_table()
    
    def on_selection_changed(self):
        """Active/désactive les boutons selon la sélection"""
        has_selection = len(self.table.selectedItems()) > 0
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
        self.paiement_btn.setEnabled(has_selection)
        self.detail_btn.setEnabled(has_selection)
    
    def add_eleve(self):
        """Ouvre le formulaire d'ajout d'élève"""
        dialog = EleveForm(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            eleve = dialog.get_eleve()
            try:
                self.eleve_service.create_eleve(
                    eleve.nom, eleve.prenom, eleve.classe,
                    eleve.annee_scolaire, eleve.montant_du
                )
                QMessageBox.information(self, "Succès", "Élève ajouté avec succès")
                self.load_eleves()
            except ValueError as e:
                QMessageBox.critical(self, "Erreur", str(e))
    
    def edit_eleve(self):
        """Ouvre le formulaire de modification d'élève"""
        row = self.table.currentRow()
        if row < 0:
            return
        
        eleve = self.current_eleves[row]
        dialog = EleveForm(self, eleve)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_eleve = dialog.get_eleve()
            try:
                self.eleve_service.update_eleve(updated_eleve)
                QMessageBox.information(self, "Succès", "Élève modifié avec succès")
                self.load_eleves()
            except ValueError as e:
                QMessageBox.critical(self, "Erreur", str(e))
    
    def delete_eleve(self):
        """Supprime l'élève sélectionné"""
        row = self.table.currentRow()
        if row < 0:
            return
        
        eleve = self.current_eleves[row]
        
        reply = QMessageBox.question(
            self, 
            "Confirmation",
            f"Voulez-vous vraiment supprimer l'élève {eleve.nom} {eleve.prenom} ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.eleve_service.delete_eleve(eleve.id)
                QMessageBox.information(self, "Succès", "Élève supprimé avec succès")
                self.load_eleves()
            except ValueError as e:
                QMessageBox.critical(self, "Erreur", str(e))
    
    def enregistrer_paiement(self):
        """Ouvre le dialogue d'enregistrement de paiement"""
        row = self.table.currentRow()
        if row < 0:
            return
        
        eleve = self.current_eleves[row]
        dialog = PaiementDialog(self, eleve)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Information", "Paiement enregistré avec succès")
            self.load_eleves()
    
    def voir_details(self):
        """Ouvre la fenêtre de détails de l'élève"""
        row = self.table.currentRow()
        if row < 0:
            return
        
        eleve = self.current_eleves[row]
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Détails - {eleve.nom} {eleve.prenom}")
        dialog.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(dialog)
        detail_widget = EleveDetailWidget(dialog, eleve.id)
        layout.addWidget(detail_widget)
        
        dialog.exec()
