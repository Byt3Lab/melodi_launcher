"""
LogsPage: Page dédiée aux journaux d'exécution en direct et aux logs journalctl des services.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton
)
from qasync import asyncSlot
from app.i18n import t
from app.system.systemd_manager import SystemdManager
from app.ui.app_context import AppContext
from app.ui.widgets.log_view import LogView
from app.ui.widgets.icon import load_svg_icon


class LogsPage(QWidget):
    def __init__(self, ctx: AppContext, parent=None):
        super().__init__(parent)
        self.ctx = ctx

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        self.title_lbl = QLabel()
        self.title_lbl.setObjectName("PageTitle")
        self.subtitle_lbl = QLabel()
        self.subtitle_lbl.setObjectName("PageSubtitle")
        title_box.addWidget(self.title_lbl)
        title_box.addWidget(self.subtitle_lbl)
        header.addLayout(title_box)
        header.addStretch()

        self.source_combo = QComboBox()
        self.source_combo.addItem("", userData="live")
        self.source_combo.addItem("", userData="melodi")
        self.source_combo.addItem("", userData="postgresql")
        self.source_combo.setMinimumWidth(230)
        self.source_combo.currentIndexChanged.connect(self._on_source_changed)
        header.addWidget(self.source_combo)

        self.fetch_btn = QPushButton()
        self.fetch_btn.setProperty("variant", "secondary")
        self.fetch_btn.setIcon(load_svg_icon("refresh", "#94a3b8", 15))
        self.fetch_btn.clicked.connect(self.fetch_service_logs)
        self.fetch_btn.setVisible(False)
        header.addWidget(self.fetch_btn)

        layout.addLayout(header)

        self.live_view = LogView(show_toolbar=True)
        self.journal_view = LogView(show_toolbar=True)
        self.journal_view.setVisible(False)

        layout.addWidget(self.live_view, stretch=1)
        layout.addWidget(self.journal_view, stretch=1)

        self.ctx.log_emitted.connect(self.live_view.append_line)
        self.ctx.language_changed.connect(self.retranslate)
        self.retranslate()

    def retranslate(self, *_) -> None:
        self.title_lbl.setText(t("logs.title"))
        self.subtitle_lbl.setText(t("logs.subtitle"))
        self.fetch_btn.setText(t("logs.load_journalctl"))
        self.source_combo.setItemText(0, t("logs.source_live"))
        self.source_combo.setItemText(1, t("logs.source_service", name="melodi"))
        self.source_combo.setItemText(2, t("logs.source_service", name="postgresql"))
        self.live_view.retranslate()
        self.journal_view.retranslate()

    def select_service(self, svc_id: str) -> None:
        for i in range(self.source_combo.count()):
            if self.source_combo.itemData(i) == svc_id:
                self.source_combo.setCurrentIndex(i)
                break
        self.fetch_service_logs()

    def _on_source_changed(self) -> None:
        src = self.source_combo.currentData()
        is_live = src == "live"
        self.live_view.setVisible(is_live)
        self.journal_view.setVisible(not is_live)
        self.fetch_btn.setVisible(not is_live)
        if not is_live:
            self.fetch_service_logs()

    @asyncSlot()
    async def fetch_service_logs(self) -> None:
        svc = self.source_combo.currentData()
        if not svc or svc == "live":
            return
        self.fetch_btn.setEnabled(False)
        self.journal_view.clear()
        self.journal_view.append_line(t("logs.loading", service=svc))
        try:
            lines = await SystemdManager.get_logs(self.ctx.executor, svc, lines=100)
            for line in lines:
                self.journal_view.append_line(line)
        except Exception as exc:
            self.journal_view.append_line(t("logs.load_error", error=exc))
        finally:
            self.fetch_btn.setEnabled(True)
