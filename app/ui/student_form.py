"""
Formulaire d'ajout / modification d'un élève.
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

from app.services.exceptions import EduPaieException
from app.services.student_service import StudentService
from app.ui.widgets import COLOR_DANGER, make_dialog_buttons


class StudentForm(QDialog):
    """Dialogue pour créer ou modifier un élève."""

    def __init__(self, student_service: StudentService, student=None, parent=None):
        super().__init__(parent)
        self.student_service = student_service
        self.student = student
        self.created_student = None

        self.setWindowTitle("Modifier l'élève" if student else "Nouvel élève")
        self.setMinimumWidth(460)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        # Matricule (auto si vide)
        self.matricule_edit = QLineEdit()
        if student:
            self.matricule_edit.setText(student.matricule or "")
        else:
            self.matricule_edit.setPlaceholderText("Généré automatiquement si vide")
        form.addRow("Matricule", self.matricule_edit)

        self.last_name_edit = QLineEdit()
        if student:
            self.last_name_edit.setText(student.last_name or "")
        self.last_name_edit.setPlaceholderText("Nom de famille")
        form.addRow("Nom *", self.last_name_edit)

        self.first_name_edit = QLineEdit()
        if student:
            self.first_name_edit.setText(student.first_name or "")
        self.first_name_edit.setPlaceholderText("Prénom")
        form.addRow("Prénom *", self.first_name_edit)

        self.class_combo = QComboBox()
        for cls in self.student_service.get_all_classes():
            self.class_combo.addItem(cls.name, cls.id)
        if student:
            index = self.class_combo.findData(student.class_id)
            if index >= 0:
                self.class_combo.setCurrentIndex(index)
        form.addRow("Classe *", self.class_combo)

        self.birth_date_edit = QDateEdit()
        self.birth_date_edit.setCalendarPopup(True)
        self.birth_date_edit.setDisplayFormat("dd/MM/yyyy")
        if student and student.birth_date:
            try:
                y, m, d = (int(x) for x in student.birth_date.split("-"))
                self.birth_date_edit.setDate(QDate(y, m, d))
            except (ValueError, TypeError):
                self.birth_date_edit.setDate(QDate(2010, 1, 1))
        else:
            self.birth_date_edit.setDate(QDate(2010, 1, 1))
        form.addRow("Date de naissance", self.birth_date_edit)

        self.parent_name_edit = QLineEdit()
        if student:
            self.parent_name_edit.setText(student.parent_name or "")
        form.addRow("Parent / tuteur", self.parent_name_edit)

        self.parent_phone_edit = QLineEdit()
        if student:
            self.parent_phone_edit.setText(student.parent_phone or "")
        self.parent_phone_edit.setPlaceholderText("Ex : 06 12 34 56 78")
        form.addRow("Téléphone parent", self.parent_phone_edit)

        self.parent_email_edit = QLineEdit()
        if student:
            self.parent_email_edit.setText(student.parent_email or "")
        self.parent_email_edit.setPlaceholderText("parent@exemple.fr")
        form.addRow("Email parent", self.parent_email_edit)

        layout.addLayout(form)

        note = QLabel(
            "Le total des frais de scolarité dus est défini par classe "
            "(plans de frais) et s'applique automatiquement à chaque élève."
        )
        note.setWordWrap(True)
        note.setStyleSheet(f"color: {COLOR_DANGER}; font-size: 9pt;")
        layout.addWidget(note)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Enregistrer")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Annuler")
        make_dialog_buttons(buttons)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.last_name_edit.setFocus()

    # ------------------------------------------------------------------

    def _save(self):
        last_name = self.last_name_edit.text().strip()
        first_name = self.first_name_edit.text().strip()
        if not last_name:
            QMessageBox.warning(self, "Champ requis", "Le nom est obligatoire.")
            self.last_name_edit.setFocus()
            return
        if not first_name:
            QMessageBox.warning(self, "Champ requis", "Le prénom est obligatoire.")
            self.first_name_edit.setFocus()
            return
        if self.class_combo.currentData() is None:
            QMessageBox.warning(self, "Champ requis", "La classe est obligatoire.")
            return

        birth = None
        if self.birth_date_edit.date().isValid():
            birth = self.birth_date_edit.date().toString("yyyy-MM-dd")

        try:
            if self.student:
                self.student.matricule = self.matricule_edit.text().strip() or self.student.matricule
                self.student.last_name = last_name
                self.student.first_name = first_name
                self.student.class_id = self.class_combo.currentData()
                self.student.birth_date = birth
                self.student.parent_name = self.parent_name_edit.text().strip() or None
                self.student.parent_phone = self.parent_phone_edit.text().strip() or None
                self.student.parent_email = self.parent_email_edit.text().strip() or None
                self.student_service.update_student(self.student)
            else:
                self.created_student = self.student_service.create_student(
                    last_name=last_name,
                    first_name=first_name,
                    class_id=self.class_combo.currentData(),
                    matricule=self.matricule_edit.text().strip() or None,
                    birth_date=birth,
                    parent_name=self.parent_name_edit.text().strip() or None,
                    parent_phone=self.parent_phone_edit.text().strip() or None,
                    parent_email=self.parent_email_edit.text().strip() or None,
                )
        except EduPaieException as e:
            QMessageBox.critical(self, "Erreur", str(e))
            return

        self.accept()
