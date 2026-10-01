"""
Page « Classes » : gestion des classes et de leurs frais de scolarité.

Créer / modifier / supprimer une classe ; le montant des frais est
appliqué à tous les élèves de la classe (calcul du solde automatique).
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.services.class_service import ClassService
from app.services.exceptions import EduPaieException
from app.ui.widgets import (
    COLOR_DANGER,
    COLOR_PRIMARY,
    COLOR_TEXT_SECONDARY,
    FlowLayout,
    PageHeader,
    make_card,
)

LEVELS = ["6ème", "5ème", "4ème", "3ème", "2nde", "1ère", "Tle",
          "CP1", "CP2", "CE1", "CE2", "CM1", "CM2"]


class ClassForm(QDialog):
    """Dialogue de création / modification d'une classe."""

    def __init__(self, class_service: ClassService, class_row=None, parent=None):
        super().__init__(parent)
        self.class_service = class_service
        self.class_row = class_row  # dict retourné par get_all_classes()

        self.setWindowTitle("Modifier la classe" if class_row else "Nouvelle classe")
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        self.name_edit = QLineEdit()
        if class_row:
            self.name_edit.setText(class_row["class"].name)
        self.name_edit.setPlaceholderText("Ex : 6ème A")
        form.addRow("Nom de la classe *", self.name_edit)

        self.level_combo = QComboBox()
        self.level_combo.setEditable(True)
        self.level_combo.addItems(LEVELS)
        if class_row:
            idx = self.level_combo.findText(class_row["class"].level)
            self.level_combo.setCurrentIndex(idx if idx >= 0 else 0)
            self.level_combo.setCurrentText(class_row["class"].level)
        form.addRow("Niveau *", self.level_combo)

        self.fee_edit = QLineEdit()
        if class_row:
            self.fee_edit.setText(str(class_row["fee_int"]))
        else:
            self.fee_edit.setPlaceholderText("Ex : 50 000")
        form.addRow("Frais de scolarité annuels (FCFA) *", self.fee_edit)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Enregistrer")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Annuler")
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.name_edit.setFocus()

    def _save(self):
        name = self.name_edit.text().strip()
        level = self.level_combo.currentText().strip()
        fee_text = self.fee_edit.text().strip()

        if not name:
            QMessageBox.warning(self, "Champ requis", "Le nom est obligatoire.")
            return
        if not fee_text:
            QMessageBox.warning(self, "Champ requis",
                                "Le montant des frais est obligatoire.")
            return
        try:
            fee = float(fee_text.replace(" ", "").replace(",", "."))
        except ValueError:
            QMessageBox.warning(self, "Montant invalide",
                                "Saisissez un montant en FCFA (ex : 50 000).")
            return

        try:
            if self.class_row:
                self.class_service.update_class(
                    self.class_row["class"].id, name, level, fee)
            else:
                self.class_service.create_class(name, level, fee)
        except EduPaieException as e:
            QMessageBox.critical(self, "Erreur", str(e))
            return
        self.accept()


class ClassesPage(QWidget):
    """Gestion des classes : liste, création, modification, suppression."""

    def __init__(self, class_service: ClassService, on_data_changed=None, parent=None):
        super().__init__(parent)
        self.class_service = class_service
        self.on_data_changed = on_data_changed
        self._rows = []

        self._build_ui()
        self.refresh()

    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        # ---- En-tête ----
        self.add_btn = QPushButton("＋ Nouvelle classe")
        self.add_btn.clicked.connect(self.add_class)
        header = PageHeader(
            "Classes",
            "Niveaux, séries et frais de scolarité appliqués aux élèves")
        header.add_action(self.add_btn)
        layout.addWidget(header)

        # ---- Tableau ----
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Classe", "Niveau", "Frais annuels", "Échéance", "Élèves inscrits"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)

        # ---- Barre d'actions (flow responsive) ----
        actions_container = QWidget()
        actions = FlowLayout(actions_container, margin=0, spacing=8)

        self.edit_btn = QPushButton("Modifier")
        self.edit_btn.clicked.connect(self.edit_class)
        self.edit_btn.setEnabled(False)
        actions.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("Supprimer")
        self.delete_btn.clicked.connect(self.delete_class)
        self.delete_btn.setEnabled(False)
        actions.addWidget(self.delete_btn)

        self.count_label = QLabel("")
        self.count_label.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY};")
        actions.addWidget(self.count_label)

        self.refresh_btn = QPushButton("⟳ Actualiser")
        self.refresh_btn.clicked.connect(self.refresh)
        actions.addWidget(self.refresh_btn)

        layout.addWidget(actions_container)

        self.table.itemSelectionChanged.connect(self._on_selection)
        self.table.doubleClicked.connect(lambda _: self.edit_class())

    # ------------------------------------------------------------------

    def refresh(self):
        """Recharge la liste des classes."""
        try:
            self._rows = self.class_service.get_all_classes()
        except EduPaieException:
            self._rows = []

        self.table.setRowCount(len(self._rows))
        for i, r in enumerate(self._rows):
            c = r["class"]
            self.table.setItem(i, 0, QTableWidgetItem(c.name))
            self.table.setItem(i, 1, QTableWidgetItem(c.level))

            fee_item = QTableWidgetItem(r["fee_formatted"])
            fee_item.setTextAlignment(Qt.AlignmentFlag.AlignRight
                                      | Qt.AlignmentFlag.AlignVCenter)
            fee_item.setForeground(Qt.GlobalColor.darkGreen)
            self.table.setItem(i, 2, fee_item)

            due = r.get("due_date") or "—"
            self.table.setItem(i, 3, QTableWidgetItem(due))

            nb = r["nb_students"]
            nb_item = QTableWidgetItem(str(nb))
            nb_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if nb == 0:
                nb_item.setForeground(Qt.GlobalColor.gray)
            self.table.setItem(i, 4, nb_item)

        self.count_label.setText(f"{len(self._rows)} classe(s)")
        self._on_selection()

    def _selected_row(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self._rows):
            return None
        return self._rows[row]

    def _on_selection(self):
        has = self._selected_row() is not None
        self.edit_btn.setEnabled(has)
        self.delete_btn.setEnabled(has)

    def _notify(self):
        if self.on_data_changed:
            self.on_data_changed()

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def add_class(self):
        dlg = ClassForm(self.class_service, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Classe créée",
                                    "La classe a bien été créée.")
            self.refresh()
            self._notify()

    def edit_class(self):
        sel = self._selected_row()
        if not sel:
            return
        dlg = ClassForm(self.class_service, class_row=sel, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Classe modifiée",
                                    "Les modifications ont été enregistrées.\n"
                                    "Les soldes des élèves de la classe ont "
                                    "été recalculés.")
            self.refresh()
            self._notify()

    def delete_class(self):
        sel = self._selected_row()
        if not sel:
            return
        c = sel["class"]
        reply = QMessageBox.question(
            self, "Confirmer la suppression",
            f"Supprimer la classe « {c.name} » et son plan de frais ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            self.class_service.delete_class(c.id)
        except EduPaieException as e:
            QMessageBox.critical(self, "Suppression impossible", str(e))
            return
        QMessageBox.information(self, "Classe supprimée",
                                "La classe a été supprimée.")
        self.refresh()
        self._notify()
