"""
Dialogue de modification d'un paiement existant.

Mêmes contrôles que la création (montant, date, mode) avec une particularité :
le solde est calculé en excluant le paiement en cours de modification.
"""

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from app.config import format_euros
from app.services.balance_service import BalanceService
from app.services.exceptions import EduPaieException
from app.services.payment_service import PaymentService
from app.services.student_service import StudentService
from app.ui.widgets import COLOR_TEXT_SECONDARY, make_dialog_buttons


class PaymentEditDialog(QDialog):
    """Modification d'un paiement : montant, date, mode, référence."""

    def __init__(self, payment_service: PaymentService,
                 student_service: StudentService, student, payment,
                 parent=None):
        super().__init__(parent)
        self.payment_service = payment_service
        self.student_service = student_service
        self.student = student
        self.payment = payment

        self.setWindowTitle(f"Modifier le paiement {payment.receipt_no}")
        self.setMinimumWidth(460)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        head = QLabel(
            f"{student.first_name} {student.last_name} — reçu "
            f"{payment.receipt_no}\nLe numéro de reçu reste inchangé.")
        head.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY};")
        layout.addWidget(head)

        form = QFormLayout()
        form.setSpacing(10)

        self.amount_edit = QLineEdit()
        self.amount_edit.setText(str(payment.amount_int))
        self.amount_edit.setPlaceholderText("Ex : 25 000")
        form.addRow("Montant (FCFA) *", self.amount_edit)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        try:
            y, m, d = (int(x) for x in payment.paid_on.split("-"))
            self.date_edit.setDate(QDate(y, m, d))
        except (ValueError, AttributeError):
            self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setMaximumDate(QDate.currentDate())
        form.addRow("Date du paiement *", self.date_edit)

        self.method_combo = QComboBox()
        for mode in PaymentService.MODES_PAIEMENT:
            self.method_combo.addItem(
                PaymentService.MODES_PAIEMENT_LABELS[mode], mode)
        idx = self.method_combo.findData(payment.method)
        if idx >= 0:
            self.method_combo.setCurrentIndex(idx)
        form.addRow("Mode de paiement *", self.method_combo)

        self.reference_edit = QLineEdit(payment.reference or "")
        self.reference_edit.setPlaceholderText("N° de chèque, transaction… (optionnel)")
        form.addRow("Référence", self.reference_edit)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Enregistrer")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Annuler")
        make_dialog_buttons(buttons)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.amount_edit.setFocus()

    def _save(self):
        text = self.amount_edit.text().replace(" ", "").replace("\u202f", "").replace(",", ".")
        try:
            amount = float(text)
        except ValueError:
            QMessageBox.warning(self, "Montant invalide",
                                "Saisissez un montant en FCFA (ex : 25 000).")
            self.amount_edit.setFocus()
            return

        try:
            self.payment_service.update_payment(
                payment_id=self.payment.id,
                amount_euros=amount,
                paid_on=self.date_edit.date().toString("yyyy-MM-dd"),
                method=self.method_combo.currentData(),
                reference=self.reference_edit.text().strip() or None,
            )
        except EduPaieException as e:
            QMessageBox.critical(self, "Modification refusée", str(e))
            return
        self.accept()
