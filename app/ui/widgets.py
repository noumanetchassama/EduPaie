"""
Éléments d'interface réutilisables : en-tête de page, cartes statistiques
et badges de statut de paiement.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout

# Couleurs du thème professionnel éducatif (cohérent avec app/ui/theme.py)
COLOR_PRIMARY = "#2c5282"
COLOR_PRIMARY_LIGHT = "#4299e1"
COLOR_PRIMARY_DARK = "#1a365d"
COLOR_BG = "#f7fafc"
COLOR_SURFACE = "#ffffff"
COLOR_SUCCESS = "#38a169"
COLOR_WARNING = "#dd6b20"
COLOR_DANGER = "#e53e3e"
COLOR_INFO = "#3182ce"
COLOR_TEXT = "#1a202c"
COLOR_TEXT_SECONDARY = "#4a5568"
COLOR_BORDER = "#e2e8f0"


def status_colors(status: str):
    """Retourne (couleur texte, couleur fond) associées à un statut de paiement."""
    if status == "Soldé":
        return COLOR_SUCCESS, "#e6f4ea"
    if status == "Partiellement payé":
        return COLOR_WARNING, "#fdf1e3"
    if status == "En retard":
        return COLOR_DANGER, "#fdeaea"
    return COLOR_DANGER, "#fdeaea"


class StatusBadge(QLabel):
    """Badge coloré affichant le statut de paiement d'un élève."""

    def __init__(self, status: str = "", parent=None):
        super().__init__(status, parent)
        self.set_status(status)

    def set_status(self, status: str):
        fg, bg = status_colors(status)
        self.setText(status or "—")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(
            f"""
            QLabel {{
                color: {fg};
                background-color: {bg};
                border-radius: 10px;
                padding: 4px 12px;
                font-weight: 600;
                font-size: 10pt;
            }}
            """
        )


class StatCard(QFrame):
    """Carte de statistique pour le tableau de bord."""

    def __init__(self, title: str, color: str, icon: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("statCard")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet(
            f"""
            QFrame#statCard {{
                background-color: {color};
                border-radius: 12px;
            }}
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(2)

        self.title_label = QLabel(f"{icon}  {title}" if icon else title)
        self.title_label.setStyleSheet(
            "color: rgba(255,255,255,0.85); font-size: 10pt; font-weight: 600;"
            "background: transparent; border: none;")
        layout.addWidget(self.title_label)

        self.value_label = QLabel("—")
        self.value_label.setStyleSheet(
            "color: #ffffff; font-size: 21pt; font-weight: 700;"
            "background: transparent; border: none;")
        layout.addWidget(self.value_label)

        self.hint_label = QLabel("")
        self.hint_label.setStyleSheet(
            "color: rgba(255,255,255,0.75); font-size: 8.5pt;"
            "background: transparent; border: none;")
        self.hint_label.hide()
        layout.addWidget(self.hint_label)

    def set_value(self, value: str, hint: str = ""):
        self.value_label.setText(value)
        if hint:
            self.hint_label.setText(hint)
            self.hint_label.show()
        else:
            self.hint_label.hide()


class PageHeader(QFrame):
    """En-tête de page : titre, sous-titre et zone d'actions à droite."""

    def __init__(self, title: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("pageHeader")
        self.setStyleSheet(
            f"""
            QFrame#pageHeader {{
                background-color: {COLOR_SURFACE};
                border: 1px solid {COLOR_BORDER};
                border-radius: 10px;
            }}
            QLabel#headerTitle {{
                color: {COLOR_PRIMARY};
                font-size: 16pt; font-weight: 700; background: transparent;
            }}
            QLabel#headerSubtitle {{
                color: {COLOR_TEXT_SECONDARY}; font-size: 10pt; background: transparent;
            }}
            """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)

        text_box = QVBoxLayout()
        text_box.setSpacing(0)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("headerTitle")
        text_box.addWidget(self.title_label)
        if subtitle:
            self.subtitle_label = QLabel(subtitle)
            self.subtitle_label.setObjectName("headerSubtitle")
            text_box.addWidget(self.subtitle_label)
        layout.addLayout(text_box)
        layout.addStretch()
        self._actions_box = QHBoxLayout()
        self._actions_box.setSpacing(8)
        layout.addLayout(self._actions_box)

    def add_action(self, widget):
        """Ajoute un widget (bouton…) à droite de l'en-tête."""
        self._actions_box.addWidget(widget)


def make_card(child_layout) -> QFrame:
    """Encapsule un layout dans une carte blanche arrondie."""
    card = QFrame()
    card.setObjectName("card")
    card.setStyleSheet(
        f"""
        QFrame#card {{
            background-color: {COLOR_SURFACE};
            border: 1px solid {COLOR_BORDER};
            border-radius: 10px;
        }}
        """
    )
    child_layout.setContentsMargins(14, 14, 14, 14)
    card.setLayout(child_layout)
    return card
