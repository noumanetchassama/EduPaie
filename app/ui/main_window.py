"""
Fenêtre principale d'EduPaie — navigation latérale professionnelle et responsive.

L'application s'appuie exclusivement sur la nouvelle architecture
(app/) : modèles, repositories, services et interface.
"""

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from app.services.audit_service import AuditService
from app.services.balance_service import BalanceService
from app.services.class_service import ClassService
from app.services.payment_service import PaymentService
from app.services.receipt_service import ReceiptService
from app.services.school_year_service import SchoolYearService
from app.services.student_service import StudentService
from app.ui.audit_page import AuditLogPage
from app.ui.classes_page import ClassesPage
from app.ui.dashboard_page import DashboardPage
from app.ui.school_year_dialog import NewSchoolYearDialog
from app.ui.students_page import StudentsPage
from app.ui.widgets import COLOR_BG, COLOR_BORDER, COLOR_PRIMARY, COLOR_PRIMARY_DARK

# (clé, libellé, icône native Qt — toujours rendue, même sans emoji)
NAV_ITEMS = [
    ("dashboard", "Tableau de bord", QStyle.StandardPixmap.SP_ComputerIcon),
    ("students", "Élèves", QStyle.StandardPixmap.SP_DirHomeIcon),
    ("classes", "Classes", QStyle.StandardPixmap.SP_DirIcon),
    ("audit", "Journal d'audit", QStyle.StandardPixmap.SP_FileDialogDetailedView),
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
        self.audit_service = AuditService()
        self.school_year_service = SchoolYearService(
            student_service=self.student_service)

        self._sidebar_expanded = True
        self._selected_year_id = None  # année scolaire consultée (défaut : courante)
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
                color: rgba(255,255,255,0.92);
                background-color: transparent;
                border: none;
                border-radius: 8px;
                padding: 11px 14px;
                font-size: 11pt;
                font-weight: 500;
                text-align: left;
                min-width: 0px;
            }}
            QPushButton#navButton:hover {{
                background-color: rgba(255,255,255,0.12);
            }}
            QPushButton#navButton:checked {{
                background-color: {COLOR_PRIMARY};
                color: #ffffff;
                font-weight: 600;
            }}
            QPushButton#sidebarToggle {{
                color: #ffffff;
                background-color: transparent;
                border: none;
                border-radius: 8px;
                padding: 2px;
                min-width: 0px;
            }}
            QPushButton#sidebarToggle:hover {{
                background-color: rgba(255,255,255,0.15);
            }}
            QScrollArea#navScroll {{
                background: transparent;
                border: none;
            }}
            QWidget#navScrollContent {{ background: transparent; }}
            QLabel#yearCaption {{
                color: rgba(255,255,255,0.65); font-size: 8pt;
                background: transparent;
            }}
            QComboBox#yearCombo {{
                color: #ffffff;
                background-color: rgba(255,255,255,0.10);
                border: 1px solid rgba(255,255,255,0.28);
                border-radius: 6px;
                padding: 3px 8px;
                min-height: 24px;
                font-size: 9.5pt;
            }}
            QComboBox#yearCombo:hover {{
                background-color: rgba(255,255,255,0.18);
            }}
            QComboBox#yearCombo::drop-down {{ border: none; width: 20px; }}
            QComboBox#yearCombo::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid rgba(255,255,255,0.8);
                margin-right: 5px;
            }}
            QComboBox#yearCombo QAbstractItemView {{
                background-color: #ffffff;
                color: #1a202c;
                border: 1px solid {COLOR_BORDER};
                selection-background-color: {COLOR_PRIMARY};
                selection-color: #ffffff;
            }}
            QPushButton#yearAdd {{
                color: #ffffff;
                background-color: rgba(255,255,255,0.12);
                border: none;
                border-radius: 6px;
                font-weight: 700;
                font-size: 12pt;
                min-width: 0px;
                padding: 0px;
            }}
            QPushButton#yearAdd:hover {{
                background-color: rgba(255,255,255,0.28);
            }}
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
        self.toggle_btn = QPushButton()
        self.toggle_btn.setObjectName("sidebarToggle")
        self.toggle_btn.setCheckable(False)
        self.toggle_btn.setFixedSize(34, 34)
        self.toggle_btn.setIconSize(QSize(18, 18))
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
            btn = QPushButton(label)
            btn.setObjectName("navButton")
            btn.setIcon(self.style().standardIcon(icon))
            btn.setIconSize(QSize(18, 18))
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip(label)
            btn.clicked.connect(lambda _=False, k=key: self._navigate(k))
            nav_layout.addWidget(btn)
            self._nav_buttons[key] = btn
        nav_layout.addStretch()
        nav_scroll.setWidget(nav_content)
        sidebar_layout.addWidget(nav_scroll, 1)

        # Pied de barre latérale : année scolaire consultée
        self.year_caption = QLabel("Année scolaire consultée")
        self.year_caption.setObjectName("yearCaption")
        sidebar_layout.addWidget(self.year_caption)

        year_row = QWidget()
        year_row.setStyleSheet("background: transparent;")
        year_layout = QHBoxLayout(year_row)
        year_layout.setContentsMargins(0, 0, 0, 0)
        year_layout.setSpacing(6)

        self.year_combo = QComboBox()
        self.year_combo.setObjectName("yearCombo")
        self.year_combo.setToolTip(
            "Consulter les données d'une année scolaire "
            "(tableau de bord, élèves, classes)")
        self.year_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.year_combo.currentIndexChanged.connect(self._on_year_changed)
        year_layout.addWidget(self.year_combo, 1)

        self.year_add_btn = QPushButton("+")
        self.year_add_btn.setObjectName("yearAdd")
        self.year_add_btn.setFixedSize(28, 30)
        self.year_add_btn.setToolTip("Créer une nouvelle année scolaire")
        self.year_add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.year_add_btn.clicked.connect(self._create_school_year)
        year_layout.addWidget(self.year_add_btn)

        sidebar_layout.addWidget(year_row)
        self._reload_year_combo()

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
        self.audit_page = AuditLogPage(audit_service=self.audit_service)

        self.stack.addWidget(self.dashboard_page)
        self.stack.addWidget(self.students_page)
        self.stack.addWidget(self.classes_page)
        self.stack.addWidget(self.audit_page)

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
            btn.setText(label if self._sidebar_expanded else "")
            btn.setProperty("collapsed", not self._sidebar_expanded)
            btn.setToolTip(label)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        self.brand_sub.setVisible(self._sidebar_expanded)
        self.year_caption.setVisible(self._sidebar_expanded)
        self.year_combo.setVisible(self._sidebar_expanded)
        self.year_add_btn.setVisible(self._sidebar_expanded)
        arrow = (QStyle.StandardPixmap.SP_ArrowLeft if self._sidebar_expanded
                 else QStyle.StandardPixmap.SP_ArrowRight)
        self.toggle_btn.setIcon(self.style().standardIcon(arrow))

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
            self.dashboard_page.refresh(self._selected_year_id)
            self.stack.setCurrentWidget(self.dashboard_page)
        elif key == "students":
            self.students_page.refresh(self._selected_year_id)
            self.stack.setCurrentWidget(self.students_page)
        elif key == "classes":
            self.classes_page.refresh(self._selected_year_id)
            self.stack.setCurrentWidget(self.classes_page)
        elif key == "audit":
            self.audit_page.refresh()
            self.stack.setCurrentWidget(self.audit_page)

    def _open_student_from_dashboard(self, student_id: int):
        """Ouvre la fiche d'un élève depuis le tableau de bord."""
        self._navigate("students")
        self.students_page.open_student_details(student_id)

    def _refresh_all(self):
        """Rafraîchit toutes les pages après une modification de données."""
        self.dashboard_page.refresh(self._selected_year_id)
        self.students_page.refresh(self._selected_year_id)
        self.classes_page.refresh(self._selected_year_id)
        self.audit_page.refresh()
        self._reload_year_combo()

    # ------------------------------------------------------------------
    # Sélection de l'année scolaire consultée
    # ------------------------------------------------------------------

    def _on_year_changed(self, index: int):
        """Change l'année scolaire affichée par le tableau de bord et les pages."""
        year_id = self.year_combo.itemData(index)
        self._selected_year_id = year_id
        self._refresh_all()

    def _reload_year_combo(self):
        """Recharge la liste des années scolaires en conservant la sélection."""
        try:
            years = self.school_year_service.get_all()
            current = self.school_year_service.get_current()
        except Exception:
            years, current = [], None

        if self._selected_year_id is None and current is not None:
            self._selected_year_id = current.id

        self.year_combo.blockSignals(True)
        self.year_combo.clear()
        selected_index = 0
        for i, y in enumerate(years):
            text = f"{y.label} — courante" if (current and y.id == current.id) else y.label
            self.year_combo.addItem(text, y.id)
            if y.id == self._selected_year_id:
                selected_index = i
        self.year_combo.setCurrentIndex(selected_index)
        self.year_combo.setEnabled(bool(years))
        self.year_combo.blockSignals(False)

        # L'année consultée suit la sélection effective du combo
        if self.year_combo.currentData() is not None:
            self._selected_year_id = self.year_combo.currentData()

    def _create_school_year(self):
        """Ouvre le dialogue de création d'une nouvelle année scolaire."""
        dlg = NewSchoolYearDialog(self.school_year_service, parent=self)
        if dlg.exec() == NewSchoolYearDialog.DialogCode.Accepted:
            created = getattr(dlg, "created_year", None)
            if created is not None:
                self._selected_year_id = created.id
            self._refresh_all()
