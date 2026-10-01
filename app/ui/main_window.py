"""
Fenêtre principale d'EduPaie — navigation latérale professionnelle.

L'application s'appuie exclusivement sur la nouvelle architecture
(app/) : modèles, repositories, services et interface.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.config import CURRENCY_SYMBOL
from app.services.balance_service import BalanceService
from app.services.payment_service import PaymentService
from app.services.receipt_service import ReceiptService
from app.services.student_service import StudentService
from app.ui.dashboard_page import DashboardPage
from app.ui.students_page import StudentsPage
from app.ui.widgets import COLOR_BG, COLOR_PRIMARY, COLOR_PRIMARY_DARK, COLOR_TEXT_SECONDARY

NAV_ITEMS = [
    ("dashboard", "Tableau de bord", "◧"),
    ("students", "Élèves", "☰"),
]


class MainWindow(QMainWindow):
    """Fenêtre principale d'EduPaie"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("EduPaie — Gestion des paiements scolaires")
        self.setMinimumSize(1180, 760)
        self.resize(1280, 820)

        # Services partagés (une seule instance de Database via singleton)
        self.student_service = StudentService()
        self.payment_service = PaymentService()
        self.balance_service = BalanceService()
        self.receipt_service = ReceiptService(payment_service=self.payment_service)

        self._build_ui()
        self._navigate("dashboard")

    # ------------------------------------------------------------------
    # Construction de l'interface
    # ------------------------------------------------------------------

    def _build_ui(self):
        central = QWidget()
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---- Barre latérale ----
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(230)
        sidebar.setStyleSheet(
            f"""
            QFrame#sidebar {{
                background-color: {COLOR_PRIMARY_DARK};
            }}
            QLabel#brandTitle {{
                color: #ffffff; font-size: 15pt; font-weight: 700;
                background: transparent;
            }}
            QLabel#brandSubtitle {{
                color: rgba(255,255,255,0.65); font-size: 8.5pt;
                background: transparent;
            }}
            QPushButton#navButton {{
                color: rgba(255,255,255,0.85);
                background-color: transparent;
                border: none;
                border-radius: 8px;
                padding: 11px 14px;
                font-size: 11pt;
                font-weight: 500;
                text-align: left;
            }}
            QPushButton#navButton:hover {{
                background-color: rgba(255,255,255,0.12);
            }}
            QPushButton#navButton:checked {{
                background-color: {COLOR_PRIMARY};
                color: #ffffff;
                font-weight: 600;
            }}
            """
        )

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(14, 20, 14, 14)
        sidebar_layout.setSpacing(6)

        brand = QLabel("EduPaie")
        brand.setObjectName("brandTitle")
        sidebar_layout.addWidget(brand)
        brand_sub = QLabel("Gestion des paiements scolaires")
        brand_sub.setObjectName("brandSubtitle")
        sidebar_layout.addWidget(brand_sub)
        sidebar_layout.addSpacing(18)

        self._nav_buttons = {}
        for key, label, icon in NAV_ITEMS:
            btn = QPushButton(f"{icon}   {label}")
            btn.setObjectName("navButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _=False, k=key: self._navigate(k))
            sidebar_layout.addWidget(btn)
            self._nav_buttons[key] = btn

        sidebar_layout.addStretch()

        # Pied de barre latérale : année scolaire courante
        self.school_year_label = QLabel("")
        self.school_year_label.setObjectName("brandSubtitle")
        self.school_year_label.setWordWrap(True)
        sidebar_layout.addWidget(self.school_year_label)
        self._refresh_school_year_label()

        # ---- Zone de contenu ----
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background-color: {COLOR_BG};")

        self.dashboard_page = DashboardPage(
            payment_service=self.payment_service,
            student_service=self.student_service,
            on_open_student=self._open_student_from_dashboard,
        )
        self.students_page = StudentsPage(
            student_service=self.student_service,
            payment_service=self.payment_service,
            balance_service=self.balance_service,
            receipt_service=self.receipt_service,
            on_data_changed=self._refresh_all,
        )

        self.stack.addWidget(self.dashboard_page)
        self.stack.addWidget(self.students_page)

        root.addWidget(sidebar)
        root.addWidget(self.stack, 1)
        self.setCentralWidget(central)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _navigate(self, key: str):
        for k, btn in self._nav_buttons.items():
            btn.setChecked(k == key)
        if key == "dashboard":
            self.dashboard_page.refresh()
            self.stack.setCurrentWidget(self.dashboard_page)
        elif key == "students":
            self.students_page.refresh()
            self.stack.setCurrentWidget(self.students_page)

    def _open_student_from_dashboard(self, student_id: int):
        """Ouvre la fiche d'un élève depuis le tableau de bord."""
        self._navigate("students")
        self.students_page.open_student_details(student_id)

    def _refresh_all(self):
        """Rafraîchit toutes les pages après une modification de données."""
        self.dashboard_page.refresh()
        self.students_page.refresh()
        self._refresh_school_year_label()

    def _refresh_school_year_label(self):
        try:
            year = self.student_service.get_current_school_year()
            self.school_year_label.setText(f"Année scolaire : {year.label}")
        except Exception:
            self.school_year_label.setText("Année scolaire : non définie")
