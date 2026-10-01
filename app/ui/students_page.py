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
    QStyle,
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
    make_button,
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
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # ---- En-tête ----
        self.add_btn = make_button(
            "Nouvel élève", role="success",
            icon=QStyle.StandardPixmap.SP_FileDialogNewFolder,
            tooltip="Ajouter un nouvel élève")
        self.add_btn.clicked.connect(self.add_student)
        header = PageHeader(
            "Élèves",
            "Gestion des inscriptions et suivi des paiements par élève")
        header.add_action(self.add_btn)
        layout.addWidget(header)

        # ---- Barre de recherche / filtres (flow responsive) ----
        filters_container = QWidget()
        filters = FlowLayout(filters_container, margin=10, spacing=12)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(
            "Rechercher un élève (nom, prénom, matricule)…")
        self.search_edit.textChanged.connect(self._apply_filters)
        self.search_edit.setMinimumWidth(220)
        self.search_edit.setMaximumWidth(420)
        filters.addWidget(self.search_edit)

        self.class_combo = QComboBox()
        self.class_combo.setMinimumContentsLength(12)
        self.class_combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.class_combo.currentIndexChanged.connect(self._apply_filters)
        class_label = QLabel("Classe :")
        class_label.setStyleSheet("font-weight: 600; font-size: 10pt;")
        filters.addWidget(class_label)
        filters.addWidget(self.class_combo)

        self.status_combo = QComboBox()
        for label in STATUS_FILTERS:
            self.status_combo.addItem(label)
        self.status_combo.currentIndexChanged.connect(self._apply_filters)
        status_label = QLabel("Statut :")
        status_label.setStyleSheet("font-weight: 600; font-size: 10pt;")
        filters.addWidget(status_label)
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
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.doubleClicked.connect(lambda _: self.view_details())
        layout.addWidget(self.table, 1)

        # ---- Barre d'actions (flow responsive : se replie en colonnes) ----
        actions_container = QWidget()
        actions = FlowLayout(actions_container, margin=0, spacing=10)

        self.pay_btn = make_button(
            "Enregistrer un paiement",
            icon=QStyle.StandardPixmap.SP_DialogApplyButton,
            tooltip="Enregistrer un paiement pour l'élève sélectionné")
        self.pay_btn.clicked.connect(self.record_payment)
        self.pay_btn.setEnabled(False)
        actions.addWidget(self.pay_btn)

        self.details_btn = make_button(
            "Voir la fiche", role="secondary",
            icon=QStyle.StandardPixmap.SP_FileDialogInfoView,
            tooltip="Consulter la fiche et l'historique des paiements")
        self.details_btn.clicked.connect(self.view_details)
        self.details_btn.setEnabled(False)
        actions.addWidget(self.details_btn)

        self.edit_btn = make_button(
            "Modifier", role="secondary",
            icon=QStyle.StandardPixmap.SP_DialogSaveButton)
        self.edit_btn.clicked.connect(self.edit_student)
        self.edit_btn.setEnabled(False)
        actions.addWidget(self.edit_btn)

        self.delete_btn = make_button(
            "Supprimer", role="danger",
            icon=QStyle.StandardPixmap.SP_TrashIcon)
        self.delete_btn.clicked.connect(self.delete_student)
        self.delete_btn.setEnabled(False)
        actions.addWidget(self.delete_btn)

        self.count_label = QLabel("")
        self.count_label.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 10pt;")
        actions.addWidget(self.count_label)

        self.refresh_btn = make_button(
            "Actualiser", role="secondary",
            icon=QStyle.StandardPixmap.SP_BrowserReload)
        self.refresh_btn.clicked.connect(self.refresh)
        actions.addWidget(self.refresh_btn)

        layout.addWidget(actions_container)

        self.table.itemSelectionChanged.connect(self._on_selection)

    # ------------------------------------------------------------------
    # Données
    # ------------------------------------------------------------------

    def refresh(self, school_year_id=None):
        """Recalcule les lignes (élèves + soldes) pour l'année consultée."""
        try:
            overview = self.payment_service.get_overview(school_year_id)
        except Exception:
            overview = None

        if overview:
            year = overview["school_year"]
            self._rows = [{
                "student": r["student"],
                "class_name": r["class_name"],
                "school_year": r["school_year"],
                "total_due": r["total_due_int"],
                "total_paid": r["total_paid_int"],
                "balance": r["balance_int"],
                "status": r["status"],
            } for r in overview["students"]]
            self._year_id = year.id
            self._year_label = year.label
        else:
            self._rows = []
            self._year_id = school_year_id
            self._year_label = ""

        try:
            current_year = self.student_service.get_current_school_year()
        except Exception:
            current_year = None
        self._is_current_year = (
            current_year is None or self._year_id in (None, current_year.id))

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
        # Conserver la sélection courante si elle existe encore
        selected_id = None
        row = self.table.currentRow()
        if row >= 0:
            item = self.table.item(row, 0)
            if item:
                selected_id = item.data(Qt.ItemDataRole.UserRole)

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

        # Sélectionner automatiquement la 1re ligne (ou l'ancienne) : les
        # boutons d'action sont donc cliquables immédiatement.
        if rows:
            target = 0
            for i in range(self.table.rowCount()):
                if self.table.item(i, 0).data(Qt.ItemDataRole.UserRole) == selected_id:
                    target = i
                    break
            self.table.selectRow(target)
        else:
            self._on_selection()

        total = len(self._rows)
        shown = len(rows)
        self.count_label.setText(f"{shown} élève(s) affiché(s) sur {total}")

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
        for btn in (self.details_btn, self.edit_btn, self.delete_btn):
            btn.setEnabled(has)
        # Les paiements s'enregistrent uniquement dans l'année courante
        can_pay = has and getattr(self, "_is_current_year", True)
        self.pay_btn.setEnabled(can_pay)
        self.pay_btn.setToolTip(
            "" if can_pay else
            "Les paiements sont enregistrés dans l'année scolaire courante : "
            "sélectionnez-la dans la barre latérale.")

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
        if not getattr(self, "_is_current_year", True):
            QMessageBox.information(
                self, "Année consultée",
                "Vous consultez une année antérieure. Sélectionnez l'année "
                "courante dans la barre latérale pour enregistrer un "
                "paiement.")
            return
        dlg = PaymentDialog(self.payment_service, self.balance_service,
                            self.student_service, sel["student"], parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            if dlg.created_payment:
                QMessageBox.information(
                    self,
                    "Paiement enregistré",
                    "Le paiement a bien été enregistré.\n\n"
                    f"Numéro de reçu : {dlg.created_payment.receipt_no}\n"
                    f"Montant : {format_euros(dlg.created_payment.amount_int)}",
                )
            self.refresh()
            self._notify_change()

    def view_details(self):
        sel = self._selected_row()
        if not sel:
            return
        dlg = StudentDetailsDialog(
            self.student_service, self.payment_service, self.balance_service,
            self.receipt_service, sel["student"].id,
            school_year_id=getattr(self, "_year_id", None),
            on_changed=self._notify_change, parent=self)
        dlg.exec()
        self.refresh(getattr(self, "_year_id", None))

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
            school_year_id=getattr(self, "_year_id", None),
            on_changed=self._notify_change, parent=self)
        dlg.exec()
        self.refresh(getattr(self, "_year_id", None))
