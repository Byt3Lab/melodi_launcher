"""
LogView: Console de logs colorée, bornée à 5 000 lignes, avec recherche et export.
"""

import time
from PySide6.QtGui import QTextCharFormat, QColor, QTextCursor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit,
    QPushButton, QLineEdit, QFileDialog, QApplication
)
from app.i18n import t
from app.ui.widgets.icon import load_svg_icon


class LogView(QWidget):
    def __init__(self, parent=None, show_toolbar: bool = True, max_lines: int = 5000):
        super().__init__(parent)
        self._entries: list[tuple[str, str]] = []
        self._max_lines = max_lines

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        if show_toolbar:
            bar = QHBoxLayout()
            bar.setSpacing(8)

            self.filter_input = QLineEdit()
            self.filter_input.textChanged.connect(self._apply_filter)
            bar.addWidget(self.filter_input, stretch=1)

            self.copy_btn = QPushButton()
            self.copy_btn.setProperty("variant", "secondary")
            self.copy_btn.setIcon(load_svg_icon("copy", "#94a3b8", 15))
            self.copy_btn.clicked.connect(self.copy_all)
            bar.addWidget(self.copy_btn)

            self.save_btn = QPushButton()
            self.save_btn.setProperty("variant", "secondary")
            self.save_btn.setIcon(load_svg_icon("download", "#94a3b8", 15))
            self.save_btn.clicked.connect(self.save_to_file)
            bar.addWidget(self.save_btn)

            self.clear_btn = QPushButton()
            self.clear_btn.setProperty("variant", "ghost")
            self.clear_btn.setIcon(load_svg_icon("trash", "#94a3b8", 15))
            self.clear_btn.clicked.connect(self.clear)
            bar.addWidget(self.clear_btn)

            layout.addLayout(bar)
            self.retranslate()
        else:
            self.filter_input = None
            self.copy_btn = None
            self.save_btn = None
            self.clear_btn = None

        self.editor = QPlainTextEdit()
        self.editor.setObjectName("LogConsole")
        self.editor.setReadOnly(True)
        self.editor.setMaximumBlockCount(max_lines)
        layout.addWidget(self.editor, stretch=1)

    def retranslate(self) -> None:
        if self.filter_input is not None:
            self.filter_input.setPlaceholderText(t("logs.filter_placeholder"))
            self.copy_btn.setText(t("common.copy"))
            self.save_btn.setText(t("common.export"))
            self.clear_btn.setText(t("common.clear"))

    @staticmethod
    def _detect_color(line: str) -> str:
        lower = line.lower()
        if "✓" in line or "succès" in lower or "success" in lower:
            return "#4ade80"
        if "❌" in line or "erreur" in lower or "error" in lower or "failed" in lower or "échec" in lower:
            return "#f87171"
        if "⚠️" in line or "avertissement" in lower or "warning" in lower:
            return "#fbbf24"
        if "==>" in line or "étape" in lower or "step" in lower or line.startswith("["):
            return "#38bdf8"
        return "#cbd5e1"

    def append_line(self, text: str) -> None:
        if not text:
            return
        ts = time.strftime("%H:%M:%S")
        lines = text.splitlines() if "\n" in text else [text]
        flt = self.filter_input.text().strip().lower() if self.filter_input else ""

        for raw in lines:
            cleaned = raw.rstrip("\r\n")
            if not cleaned:
                continue
            full = f"[{ts}] {cleaned}"
            color = self._detect_color(cleaned)
            self._entries.append((full, color))
            if len(self._entries) > self._max_lines:
                self._entries = self._entries[-self._max_lines:]

            if not flt or flt in full.lower():
                self._insert_colored(full, color)

    def _insert_colored(self, line: str, color: str) -> None:
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        cursor.insertText(line + "\n", fmt)
        self.editor.setTextCursor(cursor)
        self.editor.ensureCursorVisible()

    def _apply_filter(self) -> None:
        flt = self.filter_input.text().strip().lower() if self.filter_input else ""
        self.editor.clear()
        for line, color in self._entries:
            if not flt or flt in line.lower():
                self._insert_colored(line, color)

    def clear(self) -> None:
        self._entries.clear()
        self.editor.clear()

    def copy_all(self) -> None:
        text = self.editor.toPlainText().strip()
        if text:
            QApplication.clipboard().setText(text)

    def save_to_file(self) -> None:
        text = self.editor.toPlainText().strip()
        if not text:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, t("logs.export_title"), "melodi_logs.log", t("logs.export_filter")
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
