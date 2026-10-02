"""
Page « Journal d'audit » : traçabilité des opérations.

Liste qui a créé, modifié, supprimé ou annulé des élèves, paiements,
classes et années scolaires, avec filtres par élément et par action.
"""

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QHeaderView,
    QLabel,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.services.audit_service import ACTION_FILTERS, ENTITY_FILTERS, AuditService
from app.ui.widgets import (
    COLOR_DANGER,
    COLOR_INFO,
    COLOR_SUCCESS,
    COLOR_TEXT_SECONDARY,
    COLOR_WARNING,
    FlowLayout,
    PageHeader,
    make_button,
    make_card,
)

# Couleur d'affichage par action
ACTION_COLORS = {
    "Création": COLOR_SUCCESS,
    "Modification": COLOR_INFO,
    "Suppression": COLOR_DANGER,
    "Archivage": COLOR_WARNING,
    "Annulation": COLOR_WARNING,
}


class AuditLogPage(QWidget):
    """Journal d'audit : toutes les opérations tracées sur les données."""

    def __init__(self, audit_service: AuditService, parent=None):
        super().__init__(parent)
        self.audit_service = audit_service
        self._build_ui()
        self.refresh()

    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        self.refresh_btn = make_button(
            "Actualiser", role="secondary",
            icon=QStyle.StandardPixmap.SP_BrowserReload,
            tooltip="Recharger le journal")
        self.refresh_btn.clicked.connect(self.refresh)
        header = PageHeader(
            "Journal d'audit",
            "Qui a créé, modifié, supprimé ou annulé des données")
        header.add_action(self.refresh_btn)
        layout.addWidget(header)

        # ---- Filtres (flow responsive) ----
        filters_container = QWidget()
        filters = FlowLayout(filters_container, margin=10, spacing=10)

        filters.addWidget(QLabel("Élément :"))
        self.entity_combo = QComboBox()
        for label in ENTITY_FILTERS:
            self.entity_combo.addItem(label)
        self.entity_combo.currentIndexChanged.connect(self.refresh)
        filters.addWidget(self.entity_combo)

        filters.addWidget(QLabel("Action :"))
        self.action_combo = QComboBox()
        for label in ACTION_FILTERS:
            self.action_combo.addItem(label)
        self.action_combo.currentIndexChanged.connect(self.refresh)
        filters.addWidget(self.action_combo)

        self.count_label = QLabel("")
        self.count_label.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY};")
        filters.addWidget(self.count_label)

        layout.addWidget(make_card(filters_container.layout()))

        # ---- Tableau ----
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Date et heure", "Action", "Élément", "Libellé", "Détails",
             "Utilisateur"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)

        hint = QLabel(
            "Chaque création, modification, suppression ou annulation "
            "d'élève, de paiement, de classe ou d'année scolaire est "
            "enregistrée automatiquement avec l'utilisateur système.")
        hint.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 9pt;")
        layout.addWidget(hint)

    # ------------------------------------------------------------------

    def refresh(self):
        """Recharge le journal avec les filtres courants."""
        entity = ENTITY_FILTERS.get(self.entity_combo.currentText())
        action = ACTION_FILTERS.get(self.action_combo.currentText())
        try:
            entries = self.audit_service.get_entries(entity=entity, action=action)
        except Exception:
            entries = []

        self.table.setRowCount(len(entries))
        for row, e in enumerate(entries):
            self.table.setItem(row, 0, QTableWidgetItem(self._fmt_datetime(e["created_at"])))

            action_item = QTableWidgetItem(e["action"] or "")
            color = ACTION_COLORS.get(e["action"])
            if color:
                action_item.setForeground(QColor(color))
            font = action_item.font()
            font.setBold(True)
            action_item.setFont(font)
            self.table.setItem(row, 1, action_item)

            self.table.setItem(row, 2, QTableWidgetItem(e["entity"] or ""))
            self.table.setItem(row, 3, QTableWidgetItem(e["entity_label"] or ""))
            self.table.setItem(row, 4, QTableWidgetItem(e["details"] or ""))
            self.table.setItem(row, 5, QTableWidgetItem(e["user"] or ""))

        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)
        if self.table.columnWidth(4) > 420:
            self.table.setColumnWidth(4, 420)
        self.count_label.setText(f"{len(entries)} opération(s) enregistrée(s)")

    @staticmethod
    def _fmt_datetime(value) -> str:
        """AAAA-MM-JJ HH:MM:SS → JJ/MM/AAAA HH:MM."""
        try:
            date_part, time_part = str(value).split(" ")
            y, m, d = date_part.split("-")
            return f"{d}/{m}/{y} {time_part[:5]}"
        except (ValueError, AttributeError):
            return str(value or "")
