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

from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt


# Couleurs principales
PRIMARY_BLUE = QColor(44, 82, 130)       # #2c5282 - Bleu professionnel
PRIMARY_BLUE_LIGHT = QColor(66, 153, 225) # #4299e1 - Bleu clair
PRIMARY_BLUE_DARK = QColor(26, 54, 93)    # #1a365d - Bleu foncé

# Couleurs de fond
BACKGROUND = QColor(247, 250, 252)       # #f7fafc - Gris très clair
SURFACE = QColor(255, 255, 255)          # #ffffff - Blanc pure
ALTERNATE = QColor(237, 242, 247)        # #edf2f7 - Gris clair

# Couleurs sémantiques
SUCCESS_GREEN = QColor(72, 187, 120)    # #48bb78 - Vert doux
WARNING_ORANGE = QColor(237, 137, 54)    # #ed8936 - Orange doux
ERROR_RED = QColor(245, 101, 101)       # #f56565 - Rouge doux
INFO_BLUE = QColor(66, 153, 225)        # #4299e1 - Bleu info

# Couleurs de texte
TEXT_PRIMARY = QColor(26, 32, 44)        # #1a202c - Noir doux
TEXT_SECONDARY = QColor(74, 85, 104)     # #4a5568 - Gris moyen
TEXT_MUTED = QColor(160, 174, 192)      # #a0aec0 - Gris clair


def get_professional_theme():
    """
    Retourne une palette Qt avec le thème professionnel éducatif.

    Le bleu professionnel est utilisé comme couleur principale
    pour inspirer confiance et sérieux dans le contexte scolaire.
    """
    palette = QPalette()

    # Couleur de fenêtre (fond gris très clair)
    palette.setColor(QPalette.Window, BACKGROUND)
    palette.setColor(QPalette.WindowText, TEXT_PRIMARY)

    # Couleur de base (fond des widgets - blanc)
    palette.setColor(QPalette.Base, SURFACE)
    palette.setColor(QPalette.AlternateBase, ALTERNATE)

    # Couleur de texte
    palette.setColor(QPalette.Text, TEXT_PRIMARY)
    palette.setColor(QPalette.BrightText, SURFACE)

    # Couleur de bouton (bleu professionnel)
    palette.setColor(QPalette.Button, PRIMARY_BLUE)
    palette.setColor(QPalette.ButtonText, SURFACE)

    # Couleur de bouton survolé (bleu clair)
    palette.setColor(QPalette.Light, PRIMARY_BLUE_LIGHT)

    # Couleur de bouton pressé (bleu foncé)
    palette.setColor(QPalette.Dark, PRIMARY_BLUE_DARK)

    # Couleur de sélection (bleu clair)
    palette.setColor(QPalette.Highlight, PRIMARY_BLUE_LIGHT)
    palette.setColor(QPalette.HighlightedText, TEXT_PRIMARY)

    # Couleur de lien (bleu)
    palette.setColor(QPalette.Link, PRIMARY_BLUE_LIGHT)
    palette.setColor(QPalette.LinkVisited, PRIMARY_BLUE)

    return palette


def get_professional_stylesheet():
    """
    Retourne une stylesheet QSS pour un thème professionnel éducatif.

    Design moderne, épuré et adapté au contexte scolaire avec :
    - Typographie claire et lisible
    - Espacements généreux
    - Bordures subtiles
    - Couleurs apaisantes
    """
    return """
    /* Thème Professionnel Éducatif - EduPaie */

    /* ==================== FOND GÉNÉRAL ==================== */
    QWidget {
        background-color: #f7fafc;
        color: #1a202c;
        font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
        font-size: 10pt;
    }

    /* ==================== BOUTONS ==================== */
    QPushButton {
        background-color: #2c5282;  /* Bleu professionnel */
        color: #ffffff;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
        font-size: 11pt;
        min-height: 36px;
    }

    QPushButton:hover {
        background-color: #3b5d87;
    }

    QPushButton:pressed {
        background-color: #1a365d;
    }

    QPushButton:disabled {
        background-color: #cbd5e0;
        color: #718096;
    }

    /* Bouton secondaire (gris) */
    QPushButton[class="secondary"] {
        background-color: #e2e8f0;
        color: #2d3748;
    }

    QPushButton[class="secondary"]:hover {
        background-color: #cbd5e0;
    }

    /* Bouton succès (vert) */
    QPushButton[class="success"] {
        background-color: #48bb78;
        color: #ffffff;
    }

    QPushButton[class="success"]:hover {
        background-color: #38a169;
    }

    /* Bouton danger (rouge) */
    QPushButton[class="danger"] {
        background-color: #f56565;
        color: #ffffff;
    }

    QPushButton[class="danger"]:hover {
        background-color: #e53e3e;
    }

    /* ==================== BOUTONS D'OUTILS ==================== */
    QToolButton {
        background-color: transparent;
        border: 1px solid #cbd5e0;
        border-radius: 6px;
        padding: 6px;
    }

    QToolButton:hover {
        background-color: #e2e8f0;
        border-color: #2c5282;
    }

    /* ==================== CHAMPS DE SAISIE ==================== */
    QLineEdit, QTextEdit, QPlainTextEdit {
        background-color: #ffffff;
        border: 2px solid #e2e8f0;
        border-radius: 6px;
        padding: 8px 12px;
        selection-background-color: #4299e1;
        selection-color: #ffffff;
    }

    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
        border: 2px solid #4299e1;
        background-color: #f7fafc;
    }

    QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {
        background-color: #edf2f7;
        color: #a0aec0;
    }

    /* ==================== COMBO BOX ==================== */
    QComboBox {
        background-color: #ffffff;
        border: 2px solid #e2e8f0;
        border-radius: 6px;
        padding: 8px 12px;
        min-height: 28px;
    }

    QComboBox:hover {
        border: 2px solid #cbd5e0;
    }

    QComboBox:focus {
        border: 2px solid #4299e1;
    }

    QComboBox::drop-down {
        border: none;
        width: 24px;
    }

    QComboBox::down-arrow {
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid #2c5282;
    }

    QComboBox QAbstractItemView {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        selection-background-color: #4299e1;
        selection-color: #ffffff;
    }

    /* ==================== SPIN BOX ==================== */
    QSpinBox, QDoubleSpinBox {
        background-color: #ffffff;
        border: 2px solid #e2e8f0;
        border-radius: 6px;
        padding: 8px 12px;
    }

    QSpinBox:focus, QDoubleSpinBox:focus {
        border: 2px solid #4299e1;
    }

    QSpinBox::up-button, QDoubleSpinBox::up-button {
        background-color: #f7fafc;
        border: none;
        border-left: 1px solid #e2e8f0;
    }

    QSpinBox::down-button, QDoubleSpinBox::down-button {
        background-color: #f7fafc;
        border: none;
        border-left: 1px solid #e2e8f0;
    }

    /* ==================== DATE EDIT ==================== */
    QDateEdit {
        background-color: #ffffff;
        border: 2px solid #e2e8f0;
        border-radius: 6px;
        padding: 8px 12px;
    }

    QDateEdit:focus {
        border: 2px solid #4299e1;
    }

    QCalendarWidget {
        background-color: #ffffff;
    }

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

    QTableWidget::item, QTableView::item {
        padding: 8px;
        border-bottom: 1px solid #edf2f7;
    }

    QTableWidget::item:selected, QTableView::item:selected {
        background-color: #4299e1;
        color: #ffffff;
    }

    QTableWidget::item:hover, QTableView::item:hover {
        background-color: #f7fafc;
    }

    QHeaderView::section {
        background-color: #2c5282;
        color: #ffffff;
        padding: 10px 12px;
        border: none;
        border-right: 1px solid #1a365d;
        border-bottom: 1px solid #1a365d;
        font-weight: 600;
        font-size: 10pt;
    }

    QHeaderView::section:hover {
        background-color: #3b5d87;
    }

    /* ==================== TABS ==================== */
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
        padding: 10px 20px;
        margin-right: 4px;
        font-weight: 500;
    }

    QTabBar::tab:selected {
        background-color: #ffffff;
        color: #2c5282;
        border-bottom: 2px solid #ffffff;
    }

    QTabBar::tab:hover:!selected {
        background-color: #e2e8f0;
    }

    /* ==================== BARRES DE PROGRESSION ==================== */
    QProgressBar {
        background-color: #edf2f7;
        border: none;
        border-radius: 4px;
        text-align: center;
        height: 20px;
        font-weight: 600;
    }

    QProgressBar::chunk {
        background-color: #4299e1;
        border-radius: 4px;
    }

    /* ==================== SCROLL BARS ==================== */
    QScrollBar:vertical {
        background-color: #f7fafc;
        width: 10px;
        border-radius: 5px;
        margin: 0;
    }

    QScrollBar::handle:vertical {
        background-color: #cbd5e0;
        border-radius: 5px;
        min-height: 30px;
    }

    QScrollBar::handle:vertical:hover {
        background-color: #a0aec0;
    }

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        background: none;
        height: 0;
    }

    QScrollBar:horizontal {
        background-color: #f7fafc;
        height: 10px;
        border-radius: 5px;
        margin: 0;
    }

    QScrollBar::handle:horizontal {
        background-color: #cbd5e0;
        border-radius: 5px;
        min-width: 30px;
    }

    QScrollBar::handle:horizontal:hover {
        background-color: #a0aec0;
    }

    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        background: none;
        width: 0;
    }

    /* ==================== GROUP BOX ==================== */
    QGroupBox {
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        margin-top: 16px;
        padding-top: 20px;
        padding: 16px;
        font-weight: 600;
        font-size: 11pt;
        color: #2c5282;
        background-color: #ffffff;
    }

    QGroupBox::title {
        subcontrol-origin: margin;
        left: 16px;
        padding: 0 8px;
        background-color: #ffffff;
    }

    /* ==================== LABELS ==================== */
    QLabel {
        color: #2d3748;
    }

    QLabel[class="title"] {
        font-size: 20pt;
        font-weight: 700;
        color: #2c5282;
        padding: 8px 0;
    }

    QLabel[class="subtitle"] {
        font-size: 14pt;
        font-weight: 600;
        color: #4a5568;
        padding: 4px 0;
    }

    QLabel[class="highlight"] {
        color: #4299e1;
        font-weight: 600;
    }

    QLabel[class="error"] {
        color: #f56565;
        font-weight: 600;
    }

    QLabel[class="success"] {
        color: #48bb78;
        font-weight: 600;
    }

    QLabel[class="warning"] {
        color: #ed8936;
        font-weight: 600;
    }

    QLabel[class="muted"] {
        color: #a0aec0;
    }

    /* ==================== MESSAGE BOX ==================== */
    QMessageBox {
        background-color: #ffffff;
    }

    QMessageBox QPushButton {
        min-width: 100px;
        padding: 8px 16px;
    }

    /* ==================== STATUS BAR ==================== */
    QStatusBar {
        background-color: #2c5282;
        color: #ffffff;
        padding: 4px;
    }

    QStatusBar::item {
        border: none;
    }

    /* ==================== CHECK BOX ==================== */
    QCheckBox {
        spacing: 8px;
    }

    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border: 2px solid #cbd5e0;
        border-radius: 4px;
        background-color: #ffffff;
    }

    QCheckBox::indicator:checked {
        background-color: #4299e1;
        border-color: #4299e1;
    }

    QCheckBox::indicator:hover {
        border-color: #2c5282;
    }

    /* ==================== RADIO BUTTON ==================== */
    QRadioButton {
        spacing: 8px;
    }

    QRadioButton::indicator {
        width: 18px;
        height: 18px;
        border: 2px solid #cbd5e0;
        border-radius: 9px;
        background-color: #ffffff;
    }

    QRadioButton::indicator:checked {
        background-color: #4299e1;
        border-color: #4299e1;
    }

    QRadioButton::indicator:hover {
        border-color: #2c5282;
    }
    """
