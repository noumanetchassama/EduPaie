"""
Page « Élèves » : liste recherchable/filtrable, CRUD, paiements et fiches.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
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

from app.config import format_euros
from app.services.balance_service import BalanceService
from app.services.exceptions import EduPaieException
from app.services.payment_service import PaymentService
from app.services.receipt_service import ReceiptService
from app.services.student_service import StudentService
from app.ui.payment_dialog import PaymentDialog
from app.ui.student_details import StudentDetailsDialog
from app.ui.student_form import StudentForm
from app.ui.widgets import (
    COLOR_TEXT_SECONDARY,
    FlowLayout,
    PageHeader,
    StatusBadge,
    make_card,
)

STATUS_FILTERS = {
    "Tous les statuts": None,
    "Soldés": "Soldé",
    "Partiellement payés": "Partiellement payé",
    "Non payés": "Non payé",
}


class StudentsPage(QWidget):
    """Liste des élèves avec recherche, filtres et actions."""

    def __init__(self, student_service: StudentService, payment_service: PaymentService,
                 balance_service: BalanceService, receipt_service: ReceiptService,
                 on_data_changed=None, parent=None):
        super().__init__(parent)
        self.student_service = student_service
        self.payment_service = payment_service
        self.balance_service = balance_service
        self.receipt_service = receipt_service
        self.on_data_changed = on_data_changed
        self._rows = []  # lignes calculées (élève + montants)

        self._build_ui()
        self.refresh()

    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        # ---- En-tête ----
        self.add_btn = QPushButton("＋ Nouvel élève")
        self.add_btn.clicked.connect(self.add_student)
        header = PageHeader(
            "Élèves",
            "Gestion des inscriptions et suivi des paiements par élève")
        header.add_action(self.add_btn)
        layout.addWidget(header)

        # ---- Barre de recherche / filtres (flow responsive) ----
        filters_container = QWidget()
        filters = FlowLayout(filters_container, margin=10, spacing=10)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(
            "🔍  Rechercher un élève (nom, prénom, matricule)…")
        self.search_edit.textChanged.connect(self._apply_filters)
        self.search_edit.setMinimumWidth(220)
        self.search_edit.setMaximumWidth(420)
        filters.addWidget(self.search_edit)

        self.class_combo = QComboBox()
        self.class_combo.setMinimumContentsLength(12)
        self.class_combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.class_combo.currentIndexChanged.connect(self._apply_filters)
        filters.addWidget(QLabel("Classe :"))
        filters.addWidget(self.class_combo)

        self.status_combo = QComboBox()
        for label in STATUS_FILTERS:
            self.status_combo.addItem(label)
        self.status_combo.currentIndexChanged.connect(self._apply_filters)
        filters.addWidget(QLabel("Statut :"))
        filters.addWidget(self.status_combo)

        layout.addWidget(make_card(filters_container.layout()))

        # ---- Tableau ----
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["Nom", "Prénom", "Matricule", "Classe", "Total dû",
             "Payé", "Solde", "Statut"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.doubleClicked.connect(lambda _: self.view_details())
        layout.addWidget(self.table, 1)

        # ---- Barre d'actions (flow responsive : se replie en colonnes) ----
        actions_container = QWidget()
        actions = FlowLayout(actions_container, margin=0, spacing=8)

        self.pay_btn = QPushButton("Enregistrer un paiement")
        self.pay_btn.clicked.connect(self.record_payment)
        self.pay_btn.setEnabled(False)
        actions.addWidget(self.pay_btn)

        self.details_btn = QPushButton("Voir la fiche")
        self.details_btn.clicked.connect(self.view_details)
        self.details_btn.setEnabled(False)
        actions.addWidget(self.details_btn)

        self.edit_btn = QPushButton("Modifier")
        self.edit_btn.clicked.connect(self.edit_student)
        self.edit_btn.setEnabled(False)
        actions.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("Supprimer")
        self.delete_btn.clicked.connect(self.delete_student)
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

    # ------------------------------------------------------------------
    # Données
    # ------------------------------------------------------------------

    def refresh(self):
        """Recalcule les lignes (élèves + soldes) et applique les filtres."""
        year = self.student_service.get_current_school_year()
        classes = {c.id: c.name for c in self.student_service.get_all_classes()}

        self._rows = []
        for s in self.student_service.get_all_students():
            try:
                info = self.balance_service.get_balance_info(s.id, year.id)
            except Exception:
                continue
            self._rows.append({
                "student": s,
                "class_name": classes.get(s.class_id, "—"),
                "school_year": year.label,
                "total_due": info["total_due_int"],
                "total_paid": info["total_paid_int"],
                "balance": info["balance_int"],
                "status": info["status"],
            })

        self._reload_class_filter()
        self._apply_filters()

    def _reload_class_filter(self):
        current = self.class_combo.currentText()
        self.class_combo.blockSignals(True)
        self.class_combo.clear()
        self.class_combo.addItem("Toutes les classes", None)
        for name in sorted({r["class_name"] for r in self._rows if r["class_name"] != "—"}):
            self.class_combo.addItem(name, name)
        index = self.class_combo.findText(current)
        self.class_combo.setCurrentIndex(index if index >= 0 else 0)
        self.class_combo.blockSignals(False)

    def _apply_filters(self):
        query = self.search_edit.text().strip().lower()
        class_name = self.class_combo.currentData()
        status = STATUS_FILTERS.get(self.status_combo.currentText())

        rows = self._rows
        if class_name:
            rows = [r for r in rows if r["class_name"] == class_name]
        if status:
            rows = [r for r in rows if r["status"] == status]
        if query:
            def matches(r):
                s = r["student"]
                return (query in (s.last_name or "").lower()
                        or query in (s.first_name or "").lower()
                        or query in (s.matricule or "").lower())
            rows = [r for r in rows if matches(r)]

        rows.sort(key=lambda r: ((r["student"].last_name or "").lower(),
                                 (r["student"].first_name or "").lower()))
        self._fill_table(rows)

    def _fill_table(self, rows):
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            s = r["student"]

            item = QTableWidgetItem(s.last_name or "")
            item.setData(Qt.ItemDataRole.UserRole, s.id)
            self.table.setItem(i, 0, item)
            self.table.setItem(i, 1, QTableWidgetItem(s.first_name or ""))
            self.table.setItem(i, 2, QTableWidgetItem(s.matricule or ""))
            self.table.setItem(i, 3, QTableWidgetItem(r["class_name"]))

            for col, key in ((4, "total_due"), (5, "total_paid"), (6, "balance")):
                cell = QTableWidgetItem(format_euros(r[key]))
                cell.setTextAlignment(Qt.AlignmentFlag.AlignRight
                                      | Qt.AlignmentFlag.AlignVCenter)
                if key == "balance":
                    cell.setForeground(Qt.GlobalColor.darkGreen
                                       if r[key] == 0 else Qt.GlobalColor.red)
                self.table.setItem(i, col, cell)

            badge = StatusBadge(r["status"])
            self.table.setCellWidget(i, 7, badge)

        total = len(self._rows)
        shown = len(rows)
        self.count_label.setText(f"{shown} élève(s) affiché(s) sur {total}")
        self._on_selection()

    def _selected_row(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        student_id = item.data(Qt.ItemDataRole.UserRole)
        for r in self._rows:
            if r["student"].id == student_id:
                return r
        return None

    def _on_selection(self):
        has = self._selected_row() is not None
        for btn in (self.pay_btn, self.details_btn, self.edit_btn, self.delete_btn):
            btn.setEnabled(has)

    def _notify_change(self):
        if self.on_data_changed:
            self.on_data_changed()

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def add_student(self):
        dlg = StudentForm(self.student_service, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Élève ajouté",
                                    "L'élève a bien été enregistré.")
            self.refresh()
            self._notify_change()

    def edit_student(self):
        sel = self._selected_row()
        if not sel:
            return
        dlg = StudentForm(self.student_service, student=sel["student"], parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Élève modifié",
                                    "Les modifications ont été enregistrées.")
            self.refresh()
            self._notify_change()

    def delete_student(self):
        sel = self._selected_row()
        if not sel:
            return
        s = sel["student"]
        reply = QMessageBox.question(
            self, "Confirmer la suppression",
            f"Supprimer définitivement l'élève {s.first_name} {s.last_name} ?\n\n"
            "La suppression est refusée si des paiements existent "
            "(l'historique des reçus doit être conservé).",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            self.student_service.delete_student(s.id)
        except EduPaieException as e:
            QMessageBox.critical(self, "Suppression impossible", str(e))
            return
        QMessageBox.information(self, "Élève supprimé",
                                "L'élève a été supprimé.")
        self.refresh()
        self._notify_change()

    def record_payment(self):
        sel = self._selected_row()
        if not sel:
            return
        dlg = PaymentDialog(self.payment_service, self.balance_service,
                            self.student_service, sel["student"], parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.refresh()
            self._notify_change()

    def view_details(self):
        sel = self._selected_row()
        if not sel:
            return
        dlg = StudentDetailsDialog(
            self.student_service, self.payment_service, self.balance_service,
            self.receipt_service, sel["student"].id,
            on_changed=self._notify_change, parent=self)
        dlg.exec()
        self.refresh()

    def open_student_details(self, student_id: int):
        """Ouvre directement la fiche d'un élève (utilisé par le tableau de bord)."""
        try:
            student = self.student_service.get_student(student_id)
        except Exception:
            student = None
        if not student:
            return
        dlg = StudentDetailsDialog(
            self.student_service, self.payment_service, self.balance_service,
            self.receipt_service, student_id,
            on_changed=self._notify_change, parent=self)
        dlg.exec()
        self.refresh()
