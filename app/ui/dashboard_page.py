"""
Tableau de bord : vue d'ensemble (élèves, encaissé, restant dû, non soldés)
et liste des élèves filtrable par statut de paiement.
"""

import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
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
from app.services.payment_service import PaymentService
from app.services.student_service import StudentService
from app.ui.widgets import (
    COLOR_DANGER,
    COLOR_PRIMARY,
    COLOR_SUCCESS,
    COLOR_TEXT_SECONDARY,
    COLOR_WARNING,
    FlowLayout,
    PageHeader,
    StatCard,
    make_button,
    make_card,
    make_status_badge_cell,
)

STATUS_FILTERS = {
    "Tous les statuts": None,
    "Soldés": "Soldé",
    "Partiellement payés": "Partiellement payé",
    "Non payés": "Non payé",
}


class DashboardPage(QWidget):
    """Vue d'ensemble financière de l'établissement."""

    def __init__(self, payment_service: PaymentService, student_service: StudentService,
                 on_open_student=None, parent=None):
        super().__init__(parent)
        self.payment_service = payment_service
        self.student_service = student_service
        self.on_open_student = on_open_student
        self._overview = None
        self._year_id = None  # année scolaire affichée (conservée par Actualiser)

        self._build_ui()

    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(18)

        self.refresh_btn = make_button(
            "Actualiser", role="secondary",
            icon=QStyle.StandardPixmap.SP_BrowserReload)
        self.refresh_btn.clicked.connect(self.refresh)
        self.header = PageHeader(
            "Tableau de bord",
            "Situation globale des paiements de scolarité")
        self.header.add_action(self.refresh_btn)
        layout.addWidget(self.header)

        # ---- Cartes statistiques HERO : 4 cartes alignées sur une même
        # ligne (mêmes largeurs et même hauteur), 4 → 2 → 1 selon la
        # largeur — la hauteur libérée revient à la liste des élèves ----
        cards_container = QWidget()
        cards = FlowLayout(cards_container, margin=0, spacing=14,
                           equalize=True)
        self.card_students = StatCard("Élèves inscrits", COLOR_PRIMARY)
        self.card_collected = StatCard("Total encaissé", COLOR_SUCCESS)
        self.card_remaining = StatCard("Total restant dû", COLOR_WARNING)
        self.card_unsettled = StatCard("Élèves non soldés", COLOR_DANGER)
        for card in (self.card_students, self.card_collected,
                     self.card_remaining, self.card_unsettled):
            cards.addWidget(card)
        layout.addWidget(cards_container)

        # ---- Répartition par statut ----
        breakdown = QHBoxLayout()
        breakdown.setSpacing(18)
        self.soldes_label = QLabel()
        self.partiels_label = QLabel()
        self.impayes_label = QLabel()
        for lbl in (self.soldes_label, self.partiels_label, self.impayes_label):
            lbl.setStyleSheet("font-size: 11.5pt; font-weight: 600;")
            breakdown.addWidget(lbl)
        breakdown.addStretch()
        filter_label = QLabel("Filtrer par statut :")
        filter_label.setStyleSheet("font-weight: 700; font-size: 10.5pt;")
        breakdown.addWidget(filter_label)
        self.status_combo = QComboBox()
        for label in STATUS_FILTERS:
            self.status_combo.addItem(label)
        self.status_combo.currentIndexChanged.connect(self._apply_filter)
        breakdown.addWidget(self.status_combo)
        layout.addWidget(make_card(breakdown))

        # ---- Table des élèves ----
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["Nom", "Prénom", "Classe", "Total dû", "Payé", "Solde", "Statut"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        # Colonnes de texte élastiques, colonnes de données dimensionnées
        # au contenu, badge de statut à largeur fixe → aucun espace mort.
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for col in (2, 3, 4, 5):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(6, 150)
        header.setStretchLastSection(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(
            """
            QTableWidget {
                font-size: 11pt;
                font-weight: 500;
            }
            QTableWidget::item {
                padding: 12px;
                border-bottom: 1px solid #e2e8f0;
            }
            QTableWidget::item:selected {
                background-color: #2c5282;
                color: #ffffff;
            }
            QHeaderView::section {
                font-size: 11pt;
                font-weight: 700;
                padding: 14px;
                background-color: #2c5282;
                color: #ffffff;
                border: none;
                border-right: 1px solid #1a365d;
            }
            """
        )
        self.table.doubleClicked.connect(self._open_selected)
        layout.addWidget(self.table, 1)

        hint = QLabel("Astuce : double-cliquez sur un élève pour ouvrir sa fiche "
                      "et consulter l'historique de ses paiements.")
        hint.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 10pt; font-style: italic; font-weight: 500;")
        layout.addWidget(hint)

    # ------------------------------------------------------------------

    def refresh(self, school_year_id=None):
        """Recalcule toutes les statistiques pour l'année scolaire consultée.

        Un appel sans argument (bouton « Actualiser », qui transmet un
        booléen depuis Qt) conserve l'année affichée au lieu de repasser
        à l'année courante.
        """
        if not school_year_id:
            school_year_id = getattr(self, "_year_id", None)
        try:
            self._overview = self.payment_service.get_overview(school_year_id)
        except Exception:
            logging.exception("Échec de l'actualisation du tableau de bord")
            self._overview = None
            QMessageBox.warning(
                self,
                "Actualisation impossible",
                "Les données du tableau de bord n'ont pas pu être actualisées. "
                "Les chiffres affichés peuvent être anciens.",
            )
            return

        o = self._overview
        year = o["school_year"]
        self._year_id = year.id
        self.header.subtitle_label.setText(
            f"Situation des paiements — Année scolaire {year.label}")

        self.card_students.set_value(str(o["nb_students"]))
        self.card_collected.set_value(format_euros(o["total_paid_int"]))
        self.card_remaining.set_value(format_euros(o["total_balance_int"]))
        self.card_unsettled.set_value(
            str(o["nb_not_settled"]),
            hint=f"{o['nb_paid']} soldé(s) sur {o['nb_students']}")

        total = max(o["nb_students"], 1)
        self.soldes_label.setText(
            f"● <b style='color:{COLOR_SUCCESS};'>Soldés :</b> "
            f"{o['nb_paid']} ({o['nb_paid'] * 100 // total} %)")
        self.partiels_label.setText(
            f"● <b style='color:{COLOR_WARNING};'>Partiels :</b> "
            f"{o['nb_partial']} ({o['nb_partial'] * 100 // total} %)")
        self.impayes_label.setText(
            f"● <b style='color:{COLOR_DANGER};'>Non payés :</b> "
            f"{o['nb_unpaid']} ({o['nb_unpaid'] * 100 // total} %)")

        self._apply_filter()

    def _apply_filter(self):
        if not self._overview:
            self.table.setRowCount(0)
            return
        status = STATUS_FILTERS.get(self.status_combo.currentText())
        rows = self._overview["students"]
        if status:
            rows = [r for r in rows if r["status"] == status]
        rows = sorted(rows, key=lambda r: ((r["student"].last_name or "").lower(),
                                           (r["student"].first_name or "").lower()))

        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            s = r["student"]
            item = QTableWidgetItem(s.last_name or "")
            item.setData(Qt.ItemDataRole.UserRole, s.id)
            self.table.setItem(i, 0, item)
            self.table.setItem(i, 1, QTableWidgetItem(s.first_name or ""))
            self.table.setItem(i, 2, QTableWidgetItem(r["class_name"]))

            for col, key in ((3, "total_due_int"), (4, "total_paid_int"),
                             (5, "balance_int")):
                cell = QTableWidgetItem(format_euros(r[key]))
                cell.setTextAlignment(Qt.AlignmentFlag.AlignRight
                                      | Qt.AlignmentFlag.AlignVCenter)
                if key == "balance_int":
                    cell.setForeground(Qt.GlobalColor.darkGreen
                                       if r[key] == 0 else Qt.GlobalColor.red)
                self.table.setItem(i, col, cell)

            self.table.setCellWidget(
                i, 6, make_status_badge_cell(r["status"]))

        # Ajuster la hauteur des lignes pour les badges de statut
        for row in range(self.table.rowCount()):
            self.table.setRowHeight(row, 40)

    def _open_selected(self):
        row = self.table.currentRow()
        if row < 0 or not self.on_open_student:
            return
        student_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if student_id:
            self.on_open_student(student_id)
