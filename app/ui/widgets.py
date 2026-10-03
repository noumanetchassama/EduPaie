"""
Éléments d'interface réutilisables : en-tête de page, cartes statistiques,
badges de statut et FlowLayout (barres d'actions qui se replient en
plusieurs lignes sur les fenêtres étroites → interface responsive).
"""

from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLayout,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)


def make_button(text: str, role: str = None, icon=None,
                tooltip: str = None, parent=None) -> QPushButton:
    """
    Crée un bouton homogène, lisible et immédiatement cliquable.

    - Icônes Qt natives (`QStyle.StandardPixmap`) : toujours rendues, quel
      que soit le système (pas d'emoji ni de caractères exotiques).
    - Curseur « main » pour montrer que le bouton est cliquable.
    - `role` : None (primaire) / "secondary" / "success" / "danger" —
      stylés par la feuille de style du thème.
    """
    btn = QPushButton(text, parent)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    if role:
        btn.setProperty("class", role)
    if icon is not None:
        btn.setIcon(btn.style().standardIcon(icon))
        btn.setIconSize(QSize(16, 16))
    if tooltip:
        btn.setToolTip(tooltip)
    return btn


def make_dialog_buttons(button_box):
    """Applique les rôles visuels aux boutons d'un QDialogButtonBox."""
    from PySide6.QtWidgets import QDialogButtonBox
    save = button_box.button(QDialogButtonBox.StandardButton.Save)
    if save:
        save.setProperty("class", "success")
        save.setCursor(Qt.CursorShape.PointingHandCursor)
    cancel = button_box.button(QDialogButtonBox.StandardButton.Cancel)
    if cancel:
        cancel.setProperty("class", "secondary")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)


def ask_yes_no(parent, title: str, text: str, default_yes: bool = False) -> bool:
    """
    Boîte de confirmation « Oui / Non » en français.

    Les libellés natifs de QMessageBox sont en anglais (Yes/No) : on les
    remplace par « Oui » / « Non » et on ferme par « Non » par défaut
    (Échap ou crois = Non).

    Returns:
        True si l'utilisateur a cliqué sur « Oui »
    """
    from PySide6.QtWidgets import QMessageBox

    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Question)
    box.setWindowTitle(title)
    box.setText(text)
    yes_btn = box.addButton("Oui", QMessageBox.ButtonRole.YesRole)
    no_btn = box.addButton("Non", QMessageBox.ButtonRole.NoRole)
    box.setDefaultButton(no_btn)  # Échap / Entrée = Non par défaut
    box.exec()
    # clickedButton() : robuste à la fermeture par Échap/crois (→ False)
    return box.clickedButton() is yes_btn

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
COLOR_SURFACE_WHITE = "#ffffff"


def status_colors(status: str):
    """Retourne (couleur texte, couleur fond) associées à un statut de paiement."""
    if status == "Soldé":
        return COLOR_SUCCESS, "#d4edda"
    if status == "Partiellement payé":
        return COLOR_WARNING, "#fff3cd"
    if status == "Non payé":
        return COLOR_DANGER, "#f8d7da"
    if status == "En retard":
        return COLOR_DANGER, "#f8d7da"
    return COLOR_TEXT_SECONDARY, "#e2e8f0"


# Libellés compacts utilisés dans les tableaux denses : le badge étant
# dimensionné à la colonne, « Partiellement payé » (272 px) y serait rogné.
# La fiche élève, plus large, affiche le libellé complet.
STATUS_SHORT = {
    "Partiellement payé": "Partiel",
}


def short_status(status: str) -> str:
    """Libellé compact d'un statut pour les colonnes de tableau."""
    return STATUS_SHORT.get(status, status)


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
                border-radius: 12px;
                padding: 6px 18px;
                font-weight: 600;
                font-size: 10pt;
                border: 1px solid {fg};
            }}
            """
        )
        self.setMinimumWidth(100)
        self.setMinimumHeight(30)


class StatCard(QFrame):
    """
    Carte de statistique pour le tableau de bord (bloc HERO).

    Compacte (une seule ligne de valeur) pour laisser la place à la liste
    des élèves ; `FlowLayout(equalize=True)` aligne ensuite largeurs et
    hauteurs des cartes d'une même ligne.
    """

    MIN_WIDTH = 200  # largeur minimale (FlowLayout responsive 4 → 2 → 1)

    def __init__(self, title: str, color: str, parent=None):
        super().__init__(parent)
        self.setObjectName("statCard")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumWidth(self.MIN_WIDTH)
        self.setStyleSheet(
            f"""
            QFrame#statCard {{
                background-color: {color};
                border-radius: 14px;
                border: 2px solid {color};
            }}
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(
            "color: rgba(255,255,255,0.95); font-size: 10.5pt; font-weight: 700;"
            "background: transparent; border: none;")
        layout.addWidget(self.title_label)

        self.value_label = QLabel("—")
        self.value_label.setStyleSheet(
            "color: #ffffff; font-size: 18pt; font-weight: 800;"
            "background: transparent; border: none;")
        layout.addWidget(self.value_label)

        self.hint_label = QLabel("")
        self.hint_label.setStyleSheet(
            "color: rgba(255,255,255,0.90); font-size: 9.5pt; font-weight: 500;"
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
                border-radius: 14px;
            }}
            QLabel#headerTitle {{
                color: {COLOR_PRIMARY};
                font-size: 17pt; font-weight: 800; background: transparent;
            }}
            QLabel#headerSubtitle {{
                color: {COLOR_TEXT_SECONDARY}; font-size: 10.5pt; background: transparent;
            }}
            """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 14, 20, 14)

        text_box = QVBoxLayout()
        text_box.setSpacing(4)
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
        self._actions_box.setSpacing(12)
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
            border-radius: 14px;
        }}
        """
    )
    child_layout.setContentsMargins(18, 18, 18, 18)
    card.setLayout(child_layout)
    return card


class FlowLayout(QLayout):
    """
    Layout « fluide » : les widgets sont disposés de gauche à droite et
    passent à la ligne suivante quand la largeur manque (responsive).
    Implémentation canonique Qt adaptée à PySide6.
    """

    def __init__(self, parent=None, margin=0, spacing=14, equalize=False):
        super().__init__(parent)
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        self._spacing = spacing
        self._items = []
        # equalize=True : les widgets d'une même ligne ont tous la même
        # largeur ET la même hauteur (cartes du tableau de bord alignées).
        self._equalize = equalize

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def clear(self):
        while self._items:
            item = self._items.pop()
            w = item.widget()
            if w is not None:
                w.setParent(None)

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(),
                      margins.top() + margins.bottom())
        return size

    def _do_layout(self, rect, test_only):
        margins = self.contentsMargins()
        effective = rect.adjusted(margins.left(), margins.top(),
                                  -margins.right(), -margins.bottom())
        space = self._spacing

        if self._equalize:
            rows, col_width = self._compute_rows(effective.width(), space)
            if not rows:
                return margins.top() + margins.bottom()
            # Hauteur unique pour TOUTES les cartes : la grille entière
            # est alignée (bord haut et bord bas identiques).
            row_height = max(item.sizeHint().height() for item in self._items)
            y = effective.y()
            for index, row in enumerate(rows):
                if index:
                    y += space
                x = effective.x()
                for item in row:
                    if not test_only:
                        # Positionnement direct du widget : QWidgetItem
                        # recontraint la hauteur (sizeHint) et centre la
                        # carte, ce qui désaligne la ligne HERO.
                        cell = QRect(x, y, col_width, row_height)
                        widget = item.widget()
                        if widget is not None:
                            widget.setGeometry(cell)
                        else:
                            item.setGeometry(cell)
                    x += col_width + space
                y += row_height
            total = row_height * len(rows) + space * (len(rows) - 1)
            return margins.top() + total + margins.bottom()

        x, y = effective.x(), effective.y()
        line_height = 0
        for item in self._items:
            hint = item.sizeHint()
            next_x = x + hint.width() + space
            if next_x - space > effective.right() + 1 and line_height > 0:
                x = effective.x()
                y = y + line_height + space
                next_x = x + hint.width() + space
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), hint))

            x = next_x
            line_height = max(line_height, hint.height())

        return y + line_height - rect.y() + margins.bottom()

    def _compute_rows(self, width: int, space: int):
        """
        Répartit les items en grille régulière (mode equalize).

        1. Nombre maximal de colonnes pour lesquelles la largeur partagée
           reste supérieure ou égale à la largeur minimale des items ;
        2. Une dernière ligne orpheline (un seul item) est évitée quand
           on peut descendre d'une colonne (3+1 → 2+2) ;
        3. Toutes les colonnes ont exactement la même largeur.

        Returns:
            (rows, col_width)
        """
        if not self._items:
            return [], 0
        min_width = max(item.minimumSize().width() for item in self._items)
        cols = 1
        for k in range(2, len(self._items) + 1):
            share = (width - space * (k - 1)) // k
            if share < min_width:
                break
            cols = k
        # Éviter une dernière ligne à item unique (ex. 4 cartes → 3+1)
        if len(self._items) % cols == 1 and cols > 2:
            cols -= 1
        rows = [self._items[i:i + cols]
                for i in range(0, len(self._items), cols)]
        col_width = max(min_width,
                        (width - space * (cols - 1)) // cols)
        return rows, col_width
