"""
Fenêtre principale d'EduPaie — navigation latérale professionnelle et responsive.

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
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.services.balance_service import BalanceService
from app.services.class_service import ClassService
from app.services.payment_service import PaymentService
from app.services.receipt_service import ReceiptService
from app.services.student_service import StudentService
from app.ui.classes_page import ClassesPage
from app.ui.dashboard_page import DashboardPage
from app.ui.students_page import StudentsPage
from app.ui.widgets import COLOR_BG, COLOR_PRIMARY, COLOR_PRIMARY_DARK

NAV_ITEMS = [
    ("dashboard", "Tableau de bord", "◧"),
    ("students", "Élèves", "☰"),
    ("classes", "Classes", "▤"),
]


class MainWindow(QMainWindow):
    """Fenêtre principale d'EduPaie"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("EduPaie — Gestion des paiements scolaires")
        self.setMinimumSize(720, 560)
        self.resize(1280, 820)

        # Services partagés (une seule instance de Database via singleton)
        self.student_service = StudentService()
        self.payment_service = PaymentService()
        self.balance_service = BalanceService()
        self.class_service = ClassService(
            student_service=self.student_service)
        self.receipt_service = ReceiptService(payment_service=self.payment_service)

        self._sidebar_expanded = True
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
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self._sidebar_width = 230
        self._sidebar_collapsed_width = 58
        self.sidebar.setFixedWidth(self._sidebar_width)
        self.sidebar.setStyleSheet(
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
            QScrollArea#navScroll {{
                background: transparent;
                border: none;
            }}
            QWidget#navScrollContent {{ background: transparent; }}
            """
        )

        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(10, 14, 10, 12)
        sidebar_layout.setSpacing(6)

        # Ligne de marque : titre + bouton menu (replie/déplie la barre)
        brand_row = QHBoxLayout()
        brand_row.setSpacing(4)
        brand = QLabel("EduPaie")
        brand.setObjectName("brandTitle")
        brand_row.addWidget(brand)
        brand_row.addStretch()
        self.toggle_btn = QPushButton("☰")
        self.toggle_btn.setObjectName("navButton")
        self.toggle_btn.setCheckable(False)
        self.toggle_btn.setFixedWidth(36)
        self.toggle_btn.setToolTip("Replier / déplier le menu")
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.clicked.connect(self.toggle_sidebar)
        brand_row.addWidget(self.toggle_btn)
        sidebar_layout.addLayout(brand_row)

        self.brand_sub = QLabel("Gestion des paiements scolaires")
        self.brand_sub.setObjectName("brandSubtitle")
        self.brand_sub.setWordWrap(True)
        sidebar_layout.addWidget(self.brand_sub)
        sidebar_layout.addSpacing(12)

        # Zone défilante pour la navigation (utile sur petites fenêtres)
        nav_scroll = QScrollArea()
        nav_scroll.setObjectName("navScroll")
        nav_scroll.setWidgetResizable(True)
        nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        nav_content = QWidget()
        nav_content.setObjectName("navScrollContent")
        nav_layout = QVBoxLayout(nav_content)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(6)

        self._nav_buttons = {}
        for key, label, icon in NAV_ITEMS:
            btn = QPushButton(f"{icon}   {label}")
            btn.setObjectName("navButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _=False, k=key: self._navigate(k))
            nav_layout.addWidget(btn)
            self._nav_buttons[key] = btn
        nav_layout.addStretch()
        nav_scroll.setWidget(nav_content)
        sidebar_layout.addWidget(nav_scroll, 1)

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
        self.classes_page = ClassesPage(
            class_service=self.class_service,
            on_data_changed=self._refresh_all,
        )

        self.stack.addWidget(self.dashboard_page)
        self.stack.addWidget(self.students_page)
        self.stack.addWidget(self.classes_page)

        root.addWidget(self.sidebar)
        root.addWidget(self.stack, 1)
        self.setCentralWidget(central)

    # ------------------------------------------------------------------
    # Responsivité
    # ------------------------------------------------------------------

    def toggle_sidebar(self):
        """Replie/déplie la barre latérale (mode compact avec icônes)."""
        self._sidebar_expanded = not self._sidebar_expanded
        width = self._sidebar_width if self._sidebar_expanded \
            else self._sidebar_collapsed_width
        self.sidebar.setFixedWidth(width)

        for (key, label, icon), btn in zip(
                NAV_ITEMS, self._nav_buttons.values()):
            btn.setText(f"{icon}   {label}" if self._sidebar_expanded else icon)
            btn.setToolTip(label if not self._sidebar_expanded else "")

        self.brand_sub.setVisible(self._sidebar_expanded)
        self.school_year_label.setVisible(self._sidebar_expanded)
        self.toggle_btn.setText("☰" if self._sidebar_expanded else "›")

    def resizeEvent(self, event):
        """Replie automatiquement la barre latérale sous 950 px de large."""
        super().resizeEvent(event)
        if self.width() < 950 and self._sidebar_expanded:
            self.toggle_sidebar()
        elif self.width() >= 950 and not self._sidebar_expanded:
            self.toggle_sidebar()

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
        elif key == "classes":
            self.classes_page.refresh()
            self.stack.setCurrentWidget(self.classes_page)

    def _open_student_from_dashboard(self, student_id: int):
        """Ouvre la fiche d'un élève depuis le tableau de bord."""
        self._navigate("students")
        self.students_page.open_student_details(student_id)

    def _refresh_all(self):
        """Rafraîchit toutes les pages après une modification de données."""
        self.dashboard_page.refresh()
        self.students_page.refresh()
        self.classes_page.refresh()
        self._refresh_school_year_label()

    def _refresh_school_year_label(self):
        try:
            year = self.student_service.get_current_school_year()
            self.school_year_label.setText(f"Année scolaire : {year.label}")
        except Exception:
            self.school_year_label.setText("Année scolaire : non définie")
