"""
ToastManager: Notifications non-intrusives en bas à droite de la fenêtre.
"""

from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QGraphicsOpacityEffect, QWidget
from app.ui.widgets.icon import load_svg_pixmap


TOAST_COLORS = {
    "success": ("#22c55e", "#052e16", "check"),
    "error": ("#ef4444", "#450a0a", "x"),
    "warning": ("#f59e0b", "#451a03", "alert"),
    "info": ("#38bdf8", "#082f49", "info"),
}


class ToastNotification(QFrame):
    def __init__(self, parent: QWidget, message: str, kind: str = "info"):
        super().__init__(parent)
        accent, bg, icon_name = TOAST_COLORS.get(kind, TOAST_COLORS["info"])
        if icon_name == "info":
            icon_name = "alert"

        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: {bg};
                border: 1px solid {accent};
                border-radius: 10px;
            }}
            QLabel {{
                color: #f8fafc;
                font-size: 13px;
                font-weight: 500;
                border: none;
                background: transparent;
            }}
            """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(10)

        icon_lbl = QLabel(self)
        icon_lbl.setPixmap(load_svg_pixmap(icon_name, color=accent, size=18))
        layout.addWidget(icon_lbl)

        text_lbl = QLabel(message, self)
        text_lbl.setWordWrap(True)
        text_lbl.setMaximumWidth(340)
        layout.addWidget(text_lbl)

        self.effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.effect)
        self.effect.setOpacity(1.0)

        self.adjustSize()


class ToastManager:
    def __init__(self, host_window: QWidget):
        self.host = host_window
        self._active: list[ToastNotification] = []

    def show(self, message: str, kind: str = "info", duration_ms: int = 3800) -> None:
        toast = ToastNotification(self.host, message, kind)
        self._active.append(toast)
        self._reposition()
        toast.show()
        toast.raise_()

        QTimer.singleShot(duration_ms, lambda: self._dismiss(toast))

    def _dismiss(self, toast: ToastNotification) -> None:
        if toast not in self._active:
            return
        anim = QPropertyAnimation(toast.effect, b"opacity", toast)
        anim.setDuration(220)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.Type.OutQuad)

        def _cleanup():
            if toast in self._active:
                self._active.remove(toast)
            toast.deleteLater()
            self._reposition()

        anim.finished.connect(_cleanup)
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

    def _reposition(self) -> None:
        margin_r = 20
        margin_b = 20
        y = self.host.height() - margin_b
        for toast in reversed(self._active):
            toast.adjustSize()
            x = max(12, self.host.width() - toast.width() - margin_r)
            y -= toast.height()
            toast.move(x, max(12, y))
            y -= 8
