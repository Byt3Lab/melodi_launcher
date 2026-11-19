"""
StepperHeader & TaskChecklist: Indicateurs visuels multilingues pour l'assistant d'installation.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame
from app.i18n import t
from app.ui.widgets.icon import load_svg_pixmap


class StepperHeader(QWidget):
    def __init__(self, step_keys: list[str], parent=None):
        super().__init__(parent)
        self._step_keys = step_keys
        self._current = 0
        self._items: list[tuple[QLabel, QLabel]] = []
        self._lines: list[QFrame] = []

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 8)
        layout.setSpacing(8)

        for idx, key in enumerate(step_keys):
            badge = QLabel(str(idx + 1))
            badge.setFixedSize(26, 26)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)

            lbl = QLabel(t(key))
            lbl.setStyleSheet("font-size: 12px; font-weight: 600;")

            layout.addWidget(badge)
            layout.addWidget(lbl)
            self._items.append((badge, lbl))

            if idx < len(step_keys) - 1:
                line = QFrame()
                line.setFrameShape(QFrame.Shape.HLine)
                line.setFixedHeight(2)
                layout.addWidget(line, stretch=1)
                self._lines.append(line)

    def retranslate(self) -> None:
        for idx, key in enumerate(self._step_keys):
            _, lbl = self._items[idx]
            lbl.setText(t(key))

    def set_step(self, index: int, tokens: dict) -> None:
        self._current = index
        for idx, (badge, lbl) in enumerate(self._items):
            if idx < index:
                badge.setText("✓")
                badge.setStyleSheet(
                    f"background-color: {tokens['success']}; color: #ffffff; border-radius: 13px; font-weight: 700;"
                )
                lbl.setStyleSheet(f"color: {tokens['text_primary']}; font-size: 12px; font-weight: 600;")
            elif idx == index:
                badge.setText(str(idx + 1))
                badge.setStyleSheet(
                    f"background-color: {tokens['accent']}; color: {tokens['accent_text']}; border-radius: 13px; font-weight: 700;"
                )
                lbl.setStyleSheet(f"color: {tokens['accent']}; font-size: 12px; font-weight: 700;")
            else:
                badge.setText(str(idx + 1))
                badge.setStyleSheet(
                    f"background-color: {tokens['bg_surface_alt']}; color: {tokens['text_muted']}; "
                    f"border: 1px solid {tokens['border']}; border-radius: 13px; font-weight: 600;"
                )
                lbl.setStyleSheet(f"color: {tokens['text_muted']}; font-size: 12px; font-weight: 500;")

        for idx, line in enumerate(self._lines):
            col = tokens["success"] if idx < index else tokens["border"]
            line.setStyleSheet(f"background-color: {col}; border: none;")


class TaskChecklist(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows: dict[str, tuple[QLabel, QLabel, QLabel]] = {}
        self._states: dict[str, tuple[str, str, str]] = {}  # key -> (label_key, state, detail)
        self.vbox = QVBoxLayout(self)
        self.vbox.setContentsMargins(0, 4, 0, 4)
        self.vbox.setSpacing(8)

    def set_tasks(self, tasks: list[tuple[str, str]]) -> None:
        while self.vbox.count():
            item = self.vbox.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._rows.clear()
        self._states.clear()

        for key, label_key in tasks:
            row = QWidget(self)
            hl = QHBoxLayout(row)
            hl.setContentsMargins(6, 4, 6, 4)
            hl.setSpacing(10)

            icon_lbl = QLabel("○")
            icon_lbl.setFixedWidth(20)
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_lbl.setStyleSheet("color: #64748b; font-size: 15px; font-weight: 700;")

            name_lbl = QLabel(t(label_key))
            name_lbl.setStyleSheet("font-size: 13px; font-weight: 500;")

            state_lbl = QLabel(t("status.pending"))
            state_lbl.setObjectName("MutedText")
            state_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            hl.addWidget(icon_lbl)
            hl.addWidget(name_lbl, stretch=1)
            hl.addWidget(state_lbl)

            self.vbox.addWidget(row)
            self._rows[key] = (icon_lbl, name_lbl, state_lbl)
            self._states[key] = (label_key, "pending", "")

    def retranslate(self) -> None:
        for key, (label_key, state, detail) in list(self._states.items()):
            _, name_lbl, _ = self._rows[key]
            name_lbl.setText(t(label_key))
            self.set_state(key, state, detail)

    def set_state(self, key: str, state: str, detail: str = "") -> None:
        """state: pending | running | success | error"""
        if key not in self._rows:
            return
        label_key = self._states[key][0]
        self._states[key] = (label_key, state, detail)
        icon_lbl, _, state_lbl = self._rows[key]
        if state == "running":
            icon_lbl.setText("◌")
            icon_lbl.setStyleSheet("color: #38bdf8; font-size: 16px; font-weight: 700;")
            state_lbl.setText(detail or t("status.running"))
            state_lbl.setStyleSheet("color: #38bdf8; font-size: 12px; font-weight: 600;")
        elif state == "success":
            icon_lbl.setPixmap(load_svg_pixmap("check", "#22c55e", 16))
            state_lbl.setText(detail or t("status.done"))
            state_lbl.setStyleSheet("color: #22c55e; font-size: 12px; font-weight: 600;")
        elif state == "error":
            icon_lbl.setPixmap(load_svg_pixmap("x", "#ef4444", 16))
            state_lbl.setText(detail or t("status.failed"))
            state_lbl.setStyleSheet("color: #ef4444; font-size: 12px; font-weight: 600;")
        else:
            icon_lbl.setText("○")
            icon_lbl.setStyleSheet("color: #64748b; font-size: 15px; font-weight: 700;")
            state_lbl.setText(detail or t("status.pending"))
            state_lbl.setStyleSheet("color: #94a3b8; font-size: 12px;")
