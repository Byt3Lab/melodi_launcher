"""
MetricGauge: Carte métrique avec jauge circulaire dessinée via QPainter.
"""

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QPen, QColor, QFont
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from app.ui.widgets.card import Card


class RingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._percent = 0.0
        self._center_text = "0%"
        self._ring_color = QColor("#38bdf8")
        self._track_color = QColor("#26334a")
        self._text_color = QColor("#f1f5f9")
        self.setFixedSize(84, 84)

    def set_data(self, percent: float, center_text: str, ring_color: str, track_color: str, text_color: str) -> None:
        self._percent = max(0.0, min(100.0, float(percent)))
        self._center_text = center_text
        self._ring_color = QColor(ring_color)
        self._track_color = QColor(track_color)
        self._text_color = QColor(text_color)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(8, 8, self.width() - 16, self.height() - 16)
        pen_width = 7

        # Track
        track_pen = QPen(self._track_color, pen_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(track_pen)
        painter.drawEllipse(rect)

        # Value arc
        if self._percent > 0:
            arc_pen = QPen(self._ring_color, pen_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(arc_pen)
            span_angle = int(-self._percent / 100.0 * 360 * 16)
            painter.drawArc(rect, 90 * 16, span_angle)

        # Center text
        painter.setPen(self._text_color)
        pt_size = 9 if len(self._center_text) > 5 else 11
        font = QFont("Inter", pt_size, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self._center_text)
        painter.end()


class MetricGauge(Card):
    def __init__(self, title: str, parent=None):
        super().__init__(parent, padding=14)
        self.ring = RingWidget(self)
        self.title_lbl = QLabel(title)
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_lbl.setStyleSheet("font-weight: 600; font-size: 13px;")

        self.sub_lbl = QLabel("—")
        self.sub_lbl.setObjectName("MutedText")
        self.sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.body_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.body_layout.addWidget(self.ring, alignment=Qt.AlignmentFlag.AlignCenter)
        self.body_layout.addWidget(self.title_lbl)
        self.body_layout.addWidget(self.sub_lbl)

    def set_value(self, percent: float, center_text: str, subtitle: str, tokens: dict, color_override: str | None = None) -> None:
        if color_override:
            ring_color = color_override
        elif percent >= 85:
            ring_color = tokens["danger"]
        elif percent >= 65:
            ring_color = tokens["warning"]
        else:
            ring_color = tokens["accent"]

        self.ring.set_data(
            percent=percent,
            center_text=center_text,
            ring_color=ring_color,
            track_color=tokens["border"],
            text_color=tokens["text_primary"],
        )
        self.sub_lbl.setText(subtitle)
