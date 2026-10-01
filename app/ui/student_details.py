"""
Fiche élève : informations, solde, historique chronologique des paiements,
consultation / téléchargement / réimpression des reçus.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
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
from app.ui.widgets import (
    COLOR_TEXT_SECONDARY,
    FlowLayout,
    StatusBadge,
    make_card,
)

CANCEL_REASONS = [
    "Erreur de saisie du montant",
    "Paiement en double",
    "Chèque sans provision",
    "Annulation demandée par la famille",
    "Autre motif",
]


class StudentDetailsDialog(QDialog):
    """Dialogue affichant la fiche complète d'un élève."""

    def __init__(self, student_service: StudentService, payment_service: PaymentService,
                 balance_service: BalanceService, receipt_service: ReceiptService,
                 student_id: int, on_changed=None, parent=None):
        super().__init__(parent)
        self.student_service = student_service
        self.payment_service = payment_service
        self.balance_service = balance_service
        self.receipt_service = receipt_service
        self.student_id = student_id
        self.on_changed = on_changed
        self.student = None

        self.setWindowTitle("Fiche élève")
        self.setMinimumSize(880, 620)
        self._build_ui()
        self.reload()

    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # ---- En-tête : identité + solde ----
        header_layout = QHBoxLayout()
        identity_layout = QVBoxLayout()
        self.name_label = QLabel("")
        self.name_label.setStyleSheet("font-size: 15pt; font-weight: 700;")
        identity_layout.addWidget(self.name_label)
        self.info_label = QLabel("")
        self.info_label.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY};")
        self.info_label.setWordWrap(True)
        identity_layout.addWidget(self.info_label)
        header_layout.addLayout(identity_layout, 1)

        side_layout = QVBoxLayout()
        side_layout.addWidget(QLabel("Statut de paiement :"))
        self.status_badge = StatusBadge()
        side_layout.addWidget(self.status_badge)
        self.balance_label = QLabel("")
        self.balance_label.setStyleSheet("font-size: 12pt; font-weight: 700;")
        self.balance_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        side_layout.addWidget(self.balance_label)
        header_layout.addLayout(side_layout)
        layout.addWidget(make_card(header_layout))

        # ---- Historique des paiements ----
        title = QLabel("Historique des paiements")
        title.setStyleSheet("font-size: 12pt; font-weight: 700;")
        layout.addWidget(title)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Date", "Montant", "Mode", "N° de reçu", "Solde après", "Statut"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.itemSelectionChanged.connect(self._on_selection)
        layout.addWidget(self.table, 1)

        # ---- Actions (flow responsive : les boutons passent à la ligne) ----
        actions_container = QWidget()
        actions = FlowLayout(actions_container, margin=0, spacing=8)
        self.receipt_btn = QPushButton("👁 Voir le reçu")
        self.receipt_btn.clicked.connect(self.view_receipt)
        self.receipt_btn.setEnabled(False)
        actions.addWidget(self.receipt_btn)

        self.download_btn = QPushButton("⬇ Télécharger le reçu (PDF)")
        self.download_btn.clicked.connect(self.download_receipt)
        self.download_btn.setEnabled(False)
        actions.addWidget(self.download_btn)

        self.print_btn = QPushButton("🖨 Imprimer le reçu")
        self.print_btn.clicked.connect(self.print_receipt)
        self.print_btn.setEnabled(False)
        actions.addWidget(self.print_btn)

        self.cancel_btn = QPushButton("Annuler ce paiement…")
        self.cancel_btn.clicked.connect(self.cancel_payment)
        self.cancel_btn.setEnabled(False)
        actions.addWidget(self.cancel_btn)

        self.new_payment_btn = QPushButton("＋ Enregistrer un paiement")
        self.new_payment_btn.clicked.connect(self.add_payment)
        actions.addWidget(self.new_payment_btn)
        layout.addWidget(actions_container)

    # ------------------------------------------------------------------

    def reload(self):
        """Recharge l'élève, son solde et l'historique des paiements."""
        self.student = self.student_service.get_student(self.student_id)
        if not self.student:
            QMessageBox.warning(self, "Erreur", "Élève introuvable.")
            self.reject()
            return

        year = self.student_service.get_current_school_year()
        class_obj = self.student_service.class_repo.get_by_id(self.student.class_id)
        class_name = class_obj.name if class_obj else "—"

        self.setWindowTitle(
            f"Fiche élève — {self.student.first_name} {self.student.last_name}")
        self.name_label.setText(
            f"{self.student.first_name} {self.student.last_name}")
        parent_bits = [b for b in (
            self.student.parent_name,
            self.student.parent_phone,
            self.student.parent_email) if b]
        self.info_label.setText(
            f"Matricule : {self.student.matricule}   •   Classe : {class_name}   •   "
            f"Année : {year.label}"
            + (f"   •   Parent : {' — '.join(parent_bits)}" if parent_bits else ""))

        try:
            info = self.balance_service.get_balance_info(self.student.id, year.id)
            self.status_badge.set_status(info["status"])
            self.balance_label.setText(
                f"Solde : {info['balance_formatted']}\n"
                f"Payé : {info['total_paid_formatted']} / "
                f"Total dû : {info['total_due_formatted']}")
        except Exception:
            self.status_badge.set_status("Non payé")
            self.balance_label.setText("Solde indisponible")

        self._load_payments()

    def _load_payments(self):
        """Affiche l'historique chronologique avec solde cumulé."""
        payments = self.payment_service.get_student_payments(
            self.student_id, valid_only=False)
        # Ordre chronologique pour le calcul du solde après paiement
        chronological = sorted(payments, key=lambda p: (p.paid_on or "", p.id or 0))

        year = self.student_service.get_current_school_year()
        try:
            total_due = self.balance_service.get_total_due(self.student_id, year.id)
        except Exception:
            total_due = 0

        running = total_due
        balance_after_by_id = {}
        for p in chronological:
            if p.is_valid:
                running -= p.amount_int
            balance_after_by_id[p.id] = running

        # Affichage du plus récent au plus ancien
        display = sorted(chronological, key=lambda p: (p.paid_on or "", p.id or 0),
                         reverse=True)

        self.table.setRowCount(len(display))
        for row, p in enumerate(display):
            date_txt = p.paid_on or ""
            try:
                y, m, d = date_txt.split("-")
                date_txt = f"{d}/{m}/{y}"
            except ValueError:
                pass

            self.table.setItem(row, 0, QTableWidgetItem(date_txt))

            amount_item = QTableWidgetItem(format_euros(p.amount_int))
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight
                                         | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 1, amount_item)

            self.table.setItem(row, 2, QTableWidgetItem(
                PaymentService.MODES_PAIEMENT_LABELS.get(p.method, p.method)))
            self.table.setItem(row, 3, QTableWidgetItem(p.receipt_no))

            after = balance_after_by_id.get(p.id)
            after_item = QTableWidgetItem(
                format_euros(after) if after is not None else "—")
            after_item.setTextAlignment(Qt.AlignmentFlag.AlignRight
                                        | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 4, after_item)

            status_widget = QWidget()
            lay = QHBoxLayout(status_widget)
            lay.setContentsMargins(4, 2, 4, 2)
            badge = StatusBadge("Valide" if p.is_valid else "Annulé")
            lay.addWidget(badge)
            self.table.setCellWidget(row, 5, status_widget)

        self.table.resizeColumnsToContents()
        self._on_selection()

    def _selected_payment(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        receipt_no = self.table.item(row, 3).text()
        return self.payment_service.get_payment_by_receipt(receipt_no)

    def _on_selection(self):
        has = self._selected_payment() is not None
        for btn in (self.receipt_btn, self.download_btn, self.print_btn,
                    self.cancel_btn):
            btn.setEnabled(has)

    # ------------------------------------------------------------------
    # Reçus
    # ------------------------------------------------------------------

    def view_receipt(self):
        """Affiche un aperçu du reçu dans une boîte de dialogue."""
        payment = self._selected_payment()
        if not payment:
            return
        snapshot = self.payment_service.get_payment_snapshot(payment.id)
        if not snapshot:
            QMessageBox.warning(self, "Reçu indisponible",
                                "Aucun snapshot enregistré pour ce paiement.")
            return
        s = snapshot
        QMessageBox.information(
            self,
            f"Reçu {s.get('receipt_no', '')}",
            f"<h3>Reçu de paiement</h3>"
            f"<p><b>N° :</b> {s.get('receipt_no', '')} — "
            f"émis le {s.get('receipt_date', '')}</p>"
            f"<p><b>Élève :</b> {s['student']['first_name']} "
            f"{s['student']['last_name']} ({s['student']['class']})</p>"
            f"<p><b>Montant payé :</b> {s['payment']['amount_formatted']}</p>"
            f"<p><b>Date :</b> {self._fmt(s['payment']['paid_on'])} — "
            f"<b>Mode :</b> {s['payment']['method']}</p>"
            f"<p><b>Solde restant après paiement :</b> "
            f"{s['balance']['after_formatted']}</p>",
        )
        # Le reçu vient d'être consulté : proposer directement le PDF
        self.download_receipt()

    def download_receipt(self):
        """Exporte le reçu PDF à l'emplacement choisi par l'utilisateur."""
        payment = self._selected_payment()
        if not payment:
            return
        default_name = f"recu_{payment.receipt_no}.pdf"
        path, _ = QFileDialog.getSaveFileName(
            self, "Télécharger le reçu (PDF)", default_name,
            "Documents PDF (*.pdf)")
        if not path:
            return
        if not path.lower().endswith(".pdf"):
            path += ".pdf"
        try:
            self.receipt_service.generate_receipt_pdf(payment, output_path=path)
        except EduPaieException as e:
            QMessageBox.critical(self, "Erreur", str(e))
            return
        QMessageBox.information(self, "Reçu téléchargé",
                                f"Le reçu a été enregistré :\n{path}")

    def print_receipt(self):
        """Génère le reçu et l'ouvre dans la visionneuse PDF (impression directe)."""
        payment = self._selected_payment()
        if not payment:
            return
        try:
            self.receipt_service.print_receipt(payment)
        except EduPaieException as e:
            QMessageBox.critical(self, "Erreur", str(e))

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def add_payment(self):
        """Ouvre le dialogue d'enregistrement de paiement."""
        from app.ui.payment_dialog import PaymentDialog
        dlg = PaymentDialog(
            self.payment_service, self.balance_service,
            self.student_service, self.student, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted and self.on_changed:
            self.reload()
            self.on_changed()

    def cancel_payment(self):
        """Annule le paiement sélectionné avec motif obligatoire."""
        payment = self._selected_payment()
        if not payment:
            return
        from PySide6.QtWidgets import QInputDialog
        reason, ok = QInputDialog.getItem(
            self, "Annuler le paiement",
            "Motif d'annulation :", CANCEL_REASONS, 0, True)
        if not ok:
            return
        try:
            self.payment_service.cancel_payment(payment.id, reason)
        except EduPaieException as e:
            QMessageBox.critical(self, "Annulation refusée", str(e))
            return
        QMessageBox.information(
            self, "Paiement annulé",
            "Le paiement a été annulé (le reçu reste consultable dans "
            "l'historique).")
        self.reload()
        if self.on_changed:
            self.on_changed()

    @staticmethod
    def _fmt(date_str: str) -> str:
        try:
            y, m, d = str(date_str).split("-")
            return f"{d}/{m}/{y}"
        except ValueError:
            return str(date_str)
