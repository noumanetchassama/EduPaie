"""
Dialogue de création d'une nouvelle année scolaire.

Permet de créer « 2025-2026 » par exemple, en recopiant facultativement
les classes et leurs frais de l'année courante, et éventuellement en
définissant la nouvelle année comme année courante.
"""

import re

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from app.services.exceptions import EduPaieException
from app.services.school_year_service import SchoolYearService
from app.ui.widgets import COLOR_TEXT_SECONDARY, make_dialog_buttons

LABEL_PATTERN = re.compile(r"^(\d{4})-(\d{4})$")


class NewSchoolYearDialog(QDialog):
    """Création d'une année scolaire (format AAAA-AAAA)."""

    def __init__(self, school_year_service: SchoolYearService, parent=None):
        super().__init__(parent)
        self.school_year_service = school_year_service
        self.created_year = None  # année créée (si accepté)

        self.setWindowTitle("Nouvelle année scolaire")
        self.setMinimumWidth(440)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(10)

        self.label_edit = QLineEdit()
        self.label_edit.setPlaceholderText("Ex : 2025-2026")
        form.addRow("Libellé *", self.label_edit)

        self.copy_classes_check = QCheckBox(
            "Recopier les classes et leurs frais de l'année courante")
        self.copy_classes_check.setChecked(True)
        form.addRow("", self.copy_classes_check)

        self.set_current_check = QCheckBox(
            "Définir comme année courante (les nouveaux paiements y seront "
            "enregistrés)")
        self.set_current_check.setChecked(False)
        form.addRow("", self.set_current_check)

        layout.addLayout(form)

        note = QLabel(
            "Astuce : laissez la nouvelle année « non courante » pour "
            "préparer la rentrée tout en continuant à enregistrer les "
            "paiements dans l'année en cours.")
        note.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 9pt;")
        note.setWordWrap(True)
        layout.addWidget(note)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Créer")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Annuler")
        make_dialog_buttons(buttons)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.label_edit.setFocus()

    def _save(self):
        label = self.label_edit.text().strip()
        match = LABEL_PATTERN.match(label)
        if not match:
            QMessageBox.warning(
                self, "Libellé invalide",
                "Saisissez un libellé au format AAAA-AAAA (ex : 2025-2026).")
            return
        if int(match.group(2)) != int(match.group(1)) + 1:
            QMessageBox.warning(
                self, "Libellé invalide",
                "L'année scolaire doit couvrir deux années consécutives "
                "(ex : 2025-2026).")
            return
        try:
            self.created_year = self.school_year_service.create_school_year(
                label,
                copy_classes=self.copy_classes_check.isChecked(),
                set_current=self.set_current_check.isChecked())
        except EduPaieException as e:
            QMessageBox.critical(self, "Erreur", str(e))
            return
        self.accept()
