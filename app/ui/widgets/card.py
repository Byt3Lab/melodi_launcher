"""
Card: Conteneur réutilisable avec bordure subtile et coins arrondis.
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout


class Card(QFrame):
    def __init__(self, parent=None, padding: int = 16, elevated: bool = False):
        super().__init__(parent)
        self.setObjectName("CardElevated" if elevated else "Card")
        self.body_layout = QVBoxLayout(self)
        self.body_layout.setContentsMargins(padding, padding, padding, padding)
        self.body_layout.setSpacing(10)
