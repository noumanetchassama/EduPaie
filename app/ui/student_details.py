"""
Fiche élève : informations, solde, historique chronologique des paiements,
consultation / téléchargement / réimpression des reçus.
"""

from PySide6.QtCore import QRect, Qt, QTimer
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
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
from app.ui.widgets import (
    COLOR_TEXT_SECONDARY,
    FlowLayout,
    StatusBadge,
    ask_yes_no,
    make_button,
    make_card,
    make_status_badge_cell,
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
                 student_id: int, school_year_id: int = None,
                 on_changed=None, parent=None):
        super().__init__(parent)
        self.student_service = student_service
        self.payment_service = payment_service
        self.balance_service = balance_service
        self.receipt_service = receipt_service
        self.student_id = student_id
        self.school_year_id = school_year_id  # None = année courante
        self.on_changed = on_changed
        self.student = None
        self.year = None

        self.setWindowTitle("Fiche élève")
        self.setMinimumSize(950, 680)
        self._build_ui()
        self.reload()

    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

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
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        # « Solde après » tient dans la table, la colonne Statut est fixe
        # pour loger le badge sans rognage.
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 140)
        self.table.verticalHeader().setVisible(False)
        self.table.itemSelectionChanged.connect(self._on_selection)
        layout.addWidget(self.table, 1)

        # ---- Actions (flow responsive : les boutons passent à la ligne) ----
        actions_container = QWidget()
        actions = FlowLayout(actions_container, margin=0, spacing=12)
        self.receipt_btn = make_button(
            "Voir le reçu", role="secondary",
            icon=QStyle.StandardPixmap.SP_FileDialogInfoView,
            tooltip="Aperçu du reçu sélectionné")
        self.receipt_btn.clicked.connect(self.view_receipt)
        self.receipt_btn.setEnabled(False)
        actions.addWidget(self.receipt_btn)

        self.download_btn = make_button(
            "Télécharger reçu PDF", role="success",
            icon=QStyle.StandardPixmap.SP_DialogSaveButton,
            tooltip="Enregistrer le reçu en PDF")
        self.download_btn.clicked.connect(self.download_receipt)
        self.download_btn.setEnabled(False)
        actions.addWidget(self.download_btn)

        self.print_btn = make_button(
            "Imprimer le reçu", role="secondary",
            icon=QStyle.StandardPixmap.SP_DialogOpenButton,
            tooltip="Ouvrir le PDF pour impression")
        self.print_btn.clicked.connect(self.print_receipt)
        self.print_btn.setEnabled(False)
        actions.addWidget(self.print_btn)

        self.edit_payment_btn = make_button(
            "Modifier paiement…", role="secondary",
            icon=QStyle.StandardPixmap.SP_DialogSaveButton)
        self.edit_payment_btn.clicked.connect(self.edit_payment)
        self.edit_payment_btn.setEnabled(False)
        actions.addWidget(self.edit_payment_btn)

        self.cancel_btn = make_button(
            "Annuler paiement…", role="secondary")
        self.cancel_btn.clicked.connect(self.cancel_payment)
        self.cancel_btn.setEnabled(False)
        actions.addWidget(self.cancel_btn)

        self.delete_payment_btn = make_button(
            "Supprimer paiement", role="danger",
            icon=QStyle.StandardPixmap.SP_TrashIcon)
        self.delete_payment_btn.clicked.connect(self.delete_payment)
        self.delete_payment_btn.setEnabled(False)
        actions.addWidget(self.delete_payment_btn)

        self.new_payment_btn = make_button(
            "Enregistrer paiement",
            icon=QStyle.StandardPixmap.SP_DialogApplyButton)
        self.new_payment_btn.clicked.connect(self.add_payment)
        actions.addWidget(self.new_payment_btn)

        self.move_btn = make_button(
            "Déplacer classe…", role="secondary",
            icon=QStyle.StandardPixmap.SP_ArrowForward,
            tooltip="Transférer l'élève vers une autre classe de l'année courante")
        self.move_btn.clicked.connect(self.move_student_dialog)
        actions.addWidget(self.move_btn)
        layout.addWidget(actions_container)

    # ------------------------------------------------------------------

    def _resolve_year(self):
        """Année scolaire consultée (défaut : année courante)."""
        if self.school_year_id:
            year = self.student_service.school_year_repo.get_by_id(
                self.school_year_id)
            if year is not None:
                return year
        return self.student_service.get_current_school_year()

    def reload(self):
        """Recharge l'élève, son solde et l'historique des paiements."""
        self.student = self.student_service.get_student(self.student_id)
        if not self.student:
            QMessageBox.warning(self, "Erreur", "Élève introuvable.")
            self.reject()
            return

        year = self._resolve_year()
        self.year = year
        current_year = self.student_service.get_current_school_year()

        # Classe de l'élève pour l'année consultée (apparier par nom)
        class_for_year = self.student_service.get_class_for_year(
            self.student, year.id)
        if class_for_year:
            class_name = class_for_year.name
        else:
            class_obj = self.student_service.class_repo.get_by_id(
                self.student.class_id)
            class_name = class_obj.name if class_obj else "—"

        self.setWindowTitle(
            f"Fiche élève — {self.student.first_name} {self.student.last_name} "
            f"({year.label})")
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

        # Les paiements s'enregistrent uniquement dans l'année courante
        is_current = (current_year is not None and year.id == current_year.id)
        self.new_payment_btn.setEnabled(is_current)
        if is_current:
            self.new_payment_btn.setToolTip("")
        else:
            self.new_payment_btn.setToolTip(
                "Les paiements sont enregistrés dans l'année scolaire "
                f"courante ({current_year.label if current_year else '?'}).")

        try:
            info = self.balance_service.get_balance_info(
                self.student.id, year.id,
                class_id=class_for_year.id if class_for_year else None)
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
        """Affiche l'historique chronologique avec solde cumulé (année consultée)."""
        year = self.year or self.student_service.get_current_school_year()
        payments = self.payment_service.get_student_payments(
            self.student_id, school_year_id=year.id, valid_only=False)
        # Ordre chronologique pour le calcul du solde après paiement
        chronological = sorted(payments, key=lambda p: (p.paid_on or "", p.id or 0))

        class_for_year = self.student_service.get_class_for_year(
            self.student, year.id) if self.student else None
        try:
            total_due = self.balance_service.get_total_due(
                self.student_id, year.id,
                class_id=class_for_year.id if class_for_year else None)
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

        # 1) Dimensionner colonne et lignes AVANT l'insertion des widgets de
        #    statut : un cell widget installé dans une cellule non dimensionnée
        #    conserve sa géométrie d'insertion (127×27 dans 140×40) et la
        #    pastille est alors tronquée (11 px rognés en bas).
        self.table.resizeColumnsToContents()
        for row in range(self.table.rowCount()):
            self.table.setRowHeight(row, 40)
        # La colonne « Solde après » reste élastique (étirée ci-dessus),
        # la colonne Statut garde sa largeur fixe définie à la construction.
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 140)

        # 2) Installer les widgets de statut dans des cellules déjà dimensionnées…
        for row, p in enumerate(display):
            payment_status = "Valide" if p.is_valid else "Annulé"
            self.table.setCellWidget(
                row, 5, make_status_badge_cell(payment_status))

        # 3) …puis ré-appliquer la géométrie : Qt dimensionne le cell widget
        #    à son sizeHint du moment de l'insertion (avant polissage du style)
        #    et le re-centre ensuite sans jamais le recalculer.
        self._sync_status_widgets()

        # Sélectionner automatiquement le paiement le plus récent :
        # les boutons de reçus sont actifs dès l'ouverture de la fiche.
        if self.table.rowCount():
            self.table.selectRow(0)
        else:
            self._on_selection()

    def _sync_status_widgets(self):
        """Aligne chaque widget de statut sur sa cellule (colonne 5).

        Qt installe les cell widgets avec le sizeHint du moment de l'insertion
        (avant polissage du style) puis les re-centre sur cette taille obsolète
        à chaque show/redimensionnement : le wrapper resterait alors en
        127×27 dans une cellule de 140×40 et la pastille serait tronquée.
        """
        table = getattr(self, "table", None)
        if table is None:
            return
        for row in range(table.rowCount()):
            widget = table.cellWidget(row, 5)
            if widget is None:
                continue
            cell = table.visualRect(table.model().index(row, 5))
            if not cell.isValid():
                continue
            parent = widget.parentWidget()
            if parent is table.viewport():
                widget.setGeometry(cell)
            elif parent is not None:
                origin = table.viewport().mapToGlobal(cell.topLeft())
                widget.setGeometry(QRect(parent.mapFromGlobal(origin),
                                         cell.size()))

    def showEvent(self, event):
        """Réaligne les statuts après l'affichage (re-centrage Qt)."""
        super().showEvent(event)
        self._sync_status_widgets()
        QTimer.singleShot(0, self._sync_status_widgets)

    def resizeEvent(self, event):
        """Réaligne les statuts après un redimensionnement (re-centrage Qt)."""
        super().resizeEvent(event)
        self._sync_status_widgets()
        QTimer.singleShot(0, self._sync_status_widgets)

    def _selected_payment(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        receipt_no = self.table.item(row, 3).text()
        return self.payment_service.get_payment_by_receipt(receipt_no)

    def _on_selection(self):
        has = self._selected_payment() is not None
        for btn in (self.receipt_btn, self.download_btn, self.print_btn,
                    self.cancel_btn, self.edit_payment_btn,
                    self.delete_payment_btn):
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
        """Ouvre le dialogue d'enregistrement de paiement (année courante)."""
        from app.ui.payment_dialog import PaymentDialog
        dlg = PaymentDialog(
            self.payment_service, self.balance_service,
            self.student_service, self.student, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            if dlg.created_payment:
                QMessageBox.information(
                    self,
                    "Paiement enregistré",
                    "Le paiement a bien été enregistré.\n\n"
                    f"Numéro de reçu : {dlg.created_payment.receipt_no}\n"
                    f"Montant : {format_euros(dlg.created_payment.amount_int)}",
                )
            self.reload()
            if self.on_changed:
                self.on_changed()

    def move_student_dialog(self):
        """Déplace l'élève vers une autre classe (liste de l'année courante)."""
        if not self.student:
            return
        classes = self.student_service.get_all_classes()  # année courante
        others = [c for c in classes if c.id != self.student.class_id]
        if not others:
            QMessageBox.information(
                self, "Aucune autre classe",
                "Créez d'abord une autre classe dans la page « Classes ».")
            return

        name, ok = self._french_input_dialog(
            self, "Déplacer l'élève",
            f"Nouvelle classe pour {self.student.first_name} "
            f"{self.student.last_name} :",
            [c.name for c in others], editable=False)
        if not ok:
            return
        target = next((c for c in others if c.name == name), None)
        if not target:
            return
        try:
            self.student_service.move_student(self.student.id, target.id)
        except EduPaieException as e:
            QMessageBox.critical(self, "Déplacement impossible", str(e))
            return
        QMessageBox.information(
            self, "Élève déplacé",
            f"{self.student.first_name} {self.student.last_name} a été déplacé "
            f"en « {target.name} ».\nLe total dû a été recalculé "
            "et l'opération est tracée dans le journal d'audit.")
        self.reload()
        if self.on_changed:
            self.on_changed()

    def edit_payment(self):
        """Modifie le paiement sélectionné (montant, date, mode, référence)."""
        payment = self._selected_payment()
        if not payment:
            return
        from app.ui.payment_edit_dialog import PaymentEditDialog
        dlg = PaymentEditDialog(
            self.payment_service, self.student_service,
            self.student, payment, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(
                self, "Paiement modifié",
                "Le paiement a été mis à jour.\n"
                "Le reçu conserve son numéro mais reflète la correction.")
            self.reload()
            if self.on_changed:
                self.on_changed()

    def delete_payment(self):
        """Supprime définitivement le paiement sélectionné (double confirmation)."""
        payment = self._selected_payment()
        if not payment:
            return
        if not ask_yes_no(
                self, "Confirmer la suppression",
                f"Supprimer DÉFINITIVEMENT le paiement {payment.receipt_no} "
                f"({self._fmt(payment.paid_on)}) ?\n\n"
                "Le numéro de reçu ne sera pas réutilisé et le reçu ne sera "
                "plus consultable. Pour garder une trace, préférez « Annuler "
                "ce paiement… »."):
            return
        try:
            self.payment_service.delete_payment(payment.id)
        except EduPaieException as e:
            QMessageBox.critical(self, "Suppression impossible", str(e))
            return
        QMessageBox.information(self, "Paiement supprimé",
                                "Le paiement a été supprimé avec succès.")
        self.reload()
        if self.on_changed:
            self.on_changed()

    def cancel_payment(self):
        """Annule le paiement sélectionné avec motif obligatoire."""
        payment = self._selected_payment()
        if not payment:
            return
        reason, ok = self._french_input_dialog(
            self, "Annuler le paiement",
            "Motif d'annulation :", CANCEL_REASONS, editable=True)
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

    @staticmethod
    def _french_input_dialog(parent, title: str, label: str, items,
                             editable: bool = False):
        """
        QInputDialog de liste avec boutons français (OK / Annuler).

        La version statique QInputDialog.getItem affiche les libellés
        natifs en anglais (« Cancel ») : on force des libellés français
        via setOkButtonText / setCancelButtonText.

        Returns:
            (texte sélectionné, accepté)
        """
        from PySide6.QtWidgets import QInputDialog

        dlg = QInputDialog(parent)
        dlg.setWindowTitle(title)
        dlg.setLabelText(label)
        dlg.setComboBoxItems(list(items))
        dlg.setComboBoxEditable(editable)
        # Les libellés natifs sont en anglais (OK / Cancel)
        dlg.setOkButtonText("OK")
        dlg.setCancelButtonText("Annuler")

        accepted = dlg.exec() == QDialog.DialogCode.Accepted
        return dlg.textValue(), accepted
