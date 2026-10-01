"""
Thème Professionnel Éducatif pour EduPaie

Palette de couleurs professionnelle et adaptée au contexte scolaire :
- Bleu professionnel (#2c5282) : confiance, sérieux, éducation
- Bleu clair (#4299e1) : modernité, technologie
- Gris clair (#f7fafc) : fond apaisant
- Blanc (#ffffff) : clarté, lisibilité
- Vert doux (#48bb78) : succès, validation
- Orange doux (#ed8936) : avertissements
- Rouge doux (#f56565) : erreurs importantes
"""

from PySide6.QtGui import QColor, QPalette


# Couleurs principales
PRIMARY_BLUE = QColor(44, 82, 130)        # #2c5282 - Bleu professionnel
PRIMARY_BLUE_LIGHT = QColor(66, 153, 225)  # #4299e1 - Bleu clair
PRIMARY_BLUE_DARK = QColor(26, 54, 93)     # #1a365d - Bleu foncé

# Couleurs de fond
BACKGROUND = QColor(247, 250, 252)         # #f7fafc - Gris très clair
SURFACE = QColor(255, 255, 255)            # #ffffff - Blanc
ALTERNATE = QColor(237, 242, 247)          # #edf2f7 - Gris clair

# Couleurs sémantiques
SUCCESS_GREEN = QColor(72, 187, 120)       # #48bb78 - Vert doux
WARNING_ORANGE = QColor(237, 137, 54)      # #ed8936 - Orange doux
ERROR_RED = QColor(245, 101, 101)          # #f56565 - Rouge doux

# Couleurs de texte
TEXT_PRIMARY = QColor(26, 32, 44)          # #1a202c
TEXT_SECONDARY = QColor(74, 85, 104)       # #4a5568
TEXT_MUTED = QColor(160, 174, 192)         # #a0aec0


def get_professional_palette() -> QPalette:
    """
    Retourne une palette Qt avec le thème professionnel éducatif.

    Le bleu professionnel est utilisé comme couleur principale
    pour inspirer confiance et sérieux dans le contexte scolaire.
    """
    palette = QPalette()

    palette.setColor(QPalette.Window, BACKGROUND)
    palette.setColor(QPalette.WindowText, TEXT_PRIMARY)

    palette.setColor(QPalette.Base, SURFACE)
    palette.setColor(QPalette.AlternateBase, ALTERNATE)

    palette.setColor(QPalette.Text, TEXT_PRIMARY)
    palette.setColor(QPalette.BrightText, SURFACE)

    palette.setColor(QPalette.Button, PRIMARY_BLUE)
    palette.setColor(QPalette.ButtonText, SURFACE)

    palette.setColor(QPalette.Light, PRIMARY_BLUE_LIGHT)
    palette.setColor(QPalette.Dark, PRIMARY_BLUE_DARK)

    palette.setColor(QPalette.Highlight, PRIMARY_BLUE_LIGHT)
    palette.setColor(QPalette.HighlightedText, TEXT_PRIMARY)

    palette.setColor(QPalette.Link, PRIMARY_BLUE_LIGHT)
    palette.setColor(QPalette.LinkVisited, PRIMARY_BLUE)

    palette.setColor(QPalette.ToolTipBase, PRIMARY_BLUE_DARK)
    palette.setColor(QPalette.ToolTipText, SURFACE)

    return palette


def get_professional_stylesheet() -> str:
    """
    Retourne une stylesheet QSS pour un thème professionnel éducatif.

    Design moderne, épuré et adapté au contexte scolaire :
    - Typographie claire et lisible
    - Espacements généreux
    - Bordures subtiles

    Variantes de boutons : appliquer la propriété « class »
    (secondary / success / danger) avec widget.setProperty("class", "...").
    """
    return """
    /* ==================== Thème Professionnel Éducatif — EduPaie ==================== */

    QWidget {
        background-color: #f7fafc;
        color: #1a202c;
        font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
        font-size: 10pt;
    }

    /* ==================== BOUTONS ==================== */
    QPushButton {
        background-color: #2c5282;
        color: #ffffff;
        border: none;
        border-radius: 8px;
        padding: 9px 18px;
        font-weight: 600;
        font-size: 10.5pt;
        min-height: 32px;
    }
    QPushButton:hover { background-color: #3b5d87; }
    QPushButton:pressed { background-color: #1a365d; }
    QPushButton:focus { outline: none; }
    QPushButton:disabled {
        background-color: #cbd5e0;
        color: #718096;
    }

    QPushButton[class="secondary"] { background-color: #e2e8f0; color: #2d3748; }
    QPushButton[class="secondary"]:hover { background-color: #cbd5e0; }
    QPushButton[class="secondary"]:pressed { background-color: #a0aec0; }

    QPushButton[class="success"] { background-color: #48bb78; }
    QPushButton[class="success"]:hover { background-color: #38a169; }
    QPushButton[class="danger"] { background-color: #f56565; }
    QPushButton[class="danger"]:hover { background-color: #e53e3e; }

    QToolButton {
        background-color: transparent;
        border: 1px solid #cbd5e0;
        border-radius: 6px;
        padding: 6px;
    }
    QToolButton:hover { background-color: #e2e8f0; border-color: #2c5282; }

    /* ==================== CHAMPS DE SAISIE ==================== */
    QLineEdit, QTextEdit, QPlainTextEdit {
        background-color: #ffffff;
        border: 2px solid #e2e8f0;
        border-radius: 6px;
        padding: 7px 11px;
        selection-background-color: #4299e1;
        selection-color: #ffffff;
    }
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
        border: 2px solid #4299e1;
        background-color: #fdfefe;
    }
    QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {
        background-color: #edf2f7;
        color: #a0aec0;
    }

    /* ==================== COMBO / SPIN / DATE ==================== */
    QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {
        background-color: #ffffff;
        border: 2px solid #e2e8f0;
        border-radius: 6px;
        padding: 7px 11px;
        min-height: 26px;
    }
    QComboBox:hover { border: 2px solid #cbd5e0; }
    QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {
        border: 2px solid #4299e1;
    }
    QComboBox::drop-down { border: none; width: 24px; }
    QComboBox::down-arrow {
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid #2c5282;
        margin-right: 6px;
    }
    QComboBox QAbstractItemView {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        selection-background-color: #4299e1;
        selection-color: #ffffff;
    }

    QCalendarWidget QWidget { alternate-background-color: #edf2f7; }

    /* ==================== TABLEAUX ==================== */
    QTableWidget, QTableView {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        gridline-color: #edf2f7;
        selection-background-color: #4299e1;
        selection-color: #ffffff;
        font-size: 10pt;
    }
    QTableWidget::item, QTableView::item { padding: 6px; }
    QTableWidget::item:selected, QTableView::item:selected {
        background-color: #4299e1;
        color: #ffffff;
    }
    QHeaderView::section {
        background-color: #2c5282;
        color: #ffffff;
        padding: 9px 10px;
        border: none;
        border-right: 1px solid #1a365d;
        font-weight: 600;
        font-size: 10pt;
    }
    QHeaderView::section:hover { background-color: #3b5d87; }

    /* ==================== LISTES ==================== */
    QListWidget {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 4px;
    }
    QListWidget::item { padding: 8px; border-radius: 5px; }
    QListWidget::item:selected { background-color: #4299e1; color: #ffffff; }

    /* ==================== ONGLETS ==================== */
    QTabWidget::pane {
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        background-color: #ffffff;
        top: -1px;
    }
    QTabBar::tab {
        background-color: #edf2f7;
        color: #4a5568;
        border: 1px solid #e2e8f0;
        border-bottom: none;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        padding: 9px 18px;
        margin-right: 4px;
        font-weight: 500;
    }
    QTabBar::tab:selected { background-color: #ffffff; color: #2c5282; }
    QTabBar::tab:hover:!selected { background-color: #e2e8f0; }

    /* ==================== GROUP BOX ==================== */
    QGroupBox {
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        margin-top: 14px;
        padding: 14px;
        font-weight: 600;
        font-size: 11pt;
        color: #2c5282;
        background-color: #ffffff;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 14px;
        padding: 0 6px;
        background-color: #ffffff;
    }

    /* ==================== DIVERS ==================== */
    QProgressBar {
        background-color: #edf2f7;
        border: none;
        border-radius: 4px;
        text-align: center;
        height: 18px;
        font-weight: 600;
    }
    QProgressBar::chunk { background-color: #4299e1; border-radius: 4px; }

    QLabel { color: #2d3748; }

    QMessageBox { background-color: #ffffff; }
    QMessageBox QPushButton { min-width: 96px; padding: 7px 14px; }

    QStatusBar {
        background-color: #2c5282;
        color: #ffffff;
    }
    QStatusBar::item { border: none; }

    QCheckBox, QRadioButton { spacing: 8px; }
    QCheckBox::indicator, QRadioButton::indicator {
        width: 17px; height: 17px;
        border: 2px solid #cbd5e0;
        background-color: #ffffff;
    }
    QCheckBox::indicator { border-radius: 4px; }
    QRadioButton::indicator { border-radius: 9px; }
    QCheckBox::indicator:checked, QRadioButton::indicator:checked {
        background-color: #4299e1;
        border-color: #4299e1;
    }
    QCheckBox::indicator:hover, QRadioButton::indicator:hover { border-color: #2c5282; }

    /* ==================== SCROLL BARS ==================== */
    QScrollBar:vertical {
        background-color: #f7fafc; width: 10px; border-radius: 5px; margin: 0;
    }
    QScrollBar::handle:vertical {
        background-color: #cbd5e0; border-radius: 5px; min-height: 30px;
    }
    QScrollBar::handle:vertical:hover { background-color: #a0aec0; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { background: none; height: 0; }
    QScrollBar:horizontal {
        background-color: #f7fafc; height: 10px; border-radius: 5px; margin: 0;
    }
    QScrollBar::handle:horizontal {
        background-color: #cbd5e0; border-radius: 5px; min-width: 30px;
    }
    QScrollBar::handle:horizontal:hover { background-color: #a0aec0; }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { background: none; width: 0; }
    """
