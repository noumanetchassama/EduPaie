"""
Dialogue d'enregistrement d'un paiement avec validation du solde en temps réel.
"""

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
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
from app.ui.widgets import (
    COLOR_DANGER,
    COLOR_SUCCESS,
    COLOR_TEXT_SECONDARY,
    make_card,
)


class PaymentDialog(QDialog):
    """Dialogue pour enregistrer un paiement pour un élève."""

    def __init__(self, payment_service: PaymentService, balance_service: BalanceService,
                 student_service: StudentService, student, parent=None):
        super().__init__(parent)
        self.payment_service = payment_service
        self.balance_service = balance_service
        self.student_service = student_service
        self.student = student
        self.created_payment = None
        self._overpayment_accepted = False

        self.setWindowTitle(f"Enregistrer un paiement — {student.first_name} {student.last_name}")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # ---- Carte élève + solde ----
        info_layout = QVBoxLayout()
        info_layout.setSpacing(6)
        self.student_label = QLabel()
        self.student_label.setStyleSheet("font-size: 12pt; font-weight: 700;")
        info_layout.addWidget(self.student_label)
        self.detail_label = QLabel()
        self.detail_label.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY};")
        info_layout.addWidget(self.detail_label)
        self.solde_label = QLabel()
        self.solde_label.setStyleSheet("font-size: 13pt; font-weight: 700;")
        info_layout.addWidget(self.solde_label)
        layout.addWidget(make_card(info_layout))

        # ---- Formulaire ----
        form = QFormLayout()
        form.setSpacing(10)

        self.amount_edit = QLineEdit()
        self.amount_edit.setPlaceholderText("Ex : 250,00")
        form.addRow("Montant payé *", self.amount_edit)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setMaximumDate(QDate.currentDate())
        form.addRow("Date du paiement *", self.date_edit)

        self.method_combo = QComboBox()
        for mode in PaymentService.MODES_PAIEMENT:
            self.method_combo.addItem(PaymentService.MODES_PAIEMENT_LABELS[mode], mode)
        form.addRow("Mode de paiement *", self.method_combo)

        self.reference_edit = QLineEdit()
        self.reference_edit.setPlaceholderText("N° de chèque, transaction… (optionnel)")
        form.addRow("Référence", self.reference_edit)

        layout.addLayout(form)

        # ---- Avertissement dynamique ----
        self.warning_label = QLabel("")
        self.warning_label.setWordWrap(True)
        self.warning_label.setStyleSheet(f"color: {COLOR_DANGER}; font-weight: 600;")
        self.warning_label.hide()
        layout.addWidget(self.warning_label)

        # ---- Boutons ----
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.save_btn = self.buttons.button(QDialogButtonBox.StandardButton.Save)
        self.save_btn.setText("Enregistrer le paiement")
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Annuler")
        self.buttons.accepted.connect(self._save)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

        self._refresh_student_info()
        self.amount_edit.textChanged.connect(self._on_amount_changed)
        self.amount_edit.setFocus()

    # ------------------------------------------------------------------

    def _refresh_student_info(self):
        year = self.student_service.get_current_school_year()
        self.student_label.setText(
            f"{self.student.first_name} {self.student.last_name}")
        self.detail_label.setText(
            f"Matricule : {self.student.matricule} — Année : {year.label}")
        try:
            self._balance = self.balance_service.get_balance(self.student.id, year.id)
            self.solde_label.setText(f"Solde restant dû : {format_euros(self._balance)}")
            self.solde_label.setStyleSheet(
                f"color: {COLOR_SUCCESS if self._balance == 0 else COLOR_DANGER};"
                "font-size: 13pt; font-weight: 700;")
        except Exception:
            self._balance = None
            self.solde_label.setText("Solde indisponible")

    def _on_amount_changed(self, text: str):
        """Met à jour l'aperçu du solde après paiement et l'avertissement."""
        text = text.replace(",", ".").replace(" ", "")
        try:
            amount = float(text) if text else 0.0
        except ValueError:
            amount = None

        if amount is None or self._balance is None:
            self.warning_label.hide()
            self.save_btn.setEnabled(True)
            return

        cents = int(round(amount * 100))
        if cents <= 0:
            self.warning_label.hide()
            self.save_btn.setEnabled(True)
            return

        remaining = self._balance - cents
        if remaining < 0:
            self.warning_label.setText(
                "⚠ Le montant saisi dépasse le solde restant : le solde ne peut "
                "pas devenir négatif. Enregistrement refusé."
            )
            self.warning_label.show()
        elif remaining == 0:
            self.warning_label.setText(
                "✓ Ce paiement solde intégralement les frais de scolarité.")
            self.warning_label.setStyleSheet(
                f"color: {COLOR_SUCCESS}; font-weight: 600;")
            self.warning_label.show()
        else:
            self.warning_label.setText(
                f"Solde restant après ce paiement : {format_euros(remaining)}")
            self.warning_label.setStyleSheet(
                f"color: {COLOR_TEXT_SECONDARY}; font-weight: 600;")
            self.warning_label.show()

    def _save(self):
        from PySide6.QtWidgets import QApplication  # import local, léger

        text = self.amount_edit.text().replace(",", ".").replace(" ", "")
        try:
            amount = float(text)
        except ValueError:
            QMessageBox.warning(self, "Montant invalide",
                                "Saisissez un montant numérique (ex : 250,00).")
            self.amount_edit.setFocus()
            return

        try:
            self.created_payment = self.payment_service.create_payment(
                student_id=self.student.id,
                amount_euros=amount,
                paid_on=self.date_edit.date().toString("yyyy-MM-dd"),
                method=self.method_combo.currentData(),
                reference=self.reference_edit.text().strip() or None,
                allow_overpayment=False,
            )
        except EduPaieException as e:
            QMessageBox.critical(self, "Paiement refusé", str(e))
            return

        QMessageBox.information(
            self,
            "Paiement enregistré",
            "Le paiement a bien été enregistré.\n\n"
            f"Numéro de reçu : {self.created_payment.receipt_no}\n"
            f"Montant : {format_euros(self.created_payment.amount_int)}",
        )
        self.accept()
