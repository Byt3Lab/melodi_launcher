"""
StatusPill: Pastille de statut colorée (Actif, Arrêté, En cours, Inconnu).
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel


PILL_STYLES = {
    "success": ("#22c55e", "rgba(34, 197, 94, 0.14)"),
    "danger": ("#ef4444", "rgba(239, 68, 68, 0.14)"),
    "warning": ("#f59e0b", "rgba(245, 158, 11, 0.14)"),
    "info": ("#38bdf8", "rgba(56, 189, 248, 0.14)"),
    "muted": ("#94a3b8", "rgba(148, 163, 184, 0.12)"),
}


class StatusPill(QLabel):
    def __init__(self, text: str = "Inconnu", kind: str = "muted", parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_status(text, kind)

    def set_status(self, text: str, kind: str = "muted") -> None:
        fg, bg = PILL_STYLES.get(kind, PILL_STYLES["muted"])
        self.setText(f"●  {text}")
        self.setStyleSheet(
            f"""
            QLabel {{
                color: {fg};
                background-color: {bg};
                border-radius: 11px;
                padding: 3px 10px;
                font-size: 12px;
                font-weight: 600;
            }}
            """
        )
