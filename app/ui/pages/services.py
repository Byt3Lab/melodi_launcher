"""
ServicesPage: Gestion ergonomique des services (MELODI ERP, PostgreSQL, Redis).
"""

import webbrowser
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMenu, QScrollArea
)
from qasync import asyncSlot
from app.i18n import t
from app.system.systemd_manager import SystemdManager
from app.ui.app_context import AppContext
from app.ui.widgets.card import Card
from app.ui.widgets.status_pill import StatusPill
from app.ui.widgets.icon import load_svg_icon


SERVICES_META = [
    {"id": "melodi", "name": "MELODI ERP", "port": 5000, "desc_key": "services.melodi_desc"},
    {"id": "postgresql", "name": "PostgreSQL", "port": 5432, "desc_key": "services.pg_desc"},
]


class ServicesPage(QWidget):
    view_service_logs = Signal(str)

    def __init__(self, ctx: AppContext, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self._cards: dict[str, dict] = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content.setObjectName("ScrollContent")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)

        # Header
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

        self.refresh_btn = QPushButton()
        self.refresh_btn.setProperty("variant", "secondary")
        self.refresh_btn.setIcon(load_svg_icon("refresh", "#94a3b8", 15))
        self.refresh_btn.clicked.connect(self.refresh)
        header.addWidget(self.refresh_btn)

        self.open_btn = QPushButton()
        self.open_btn.setProperty("variant", "primary")
        self.open_btn.setIcon(load_svg_icon("external-link", "#082f49", 15))
        self.open_btn.clicked.connect(self._open_browser)
        header.addWidget(self.open_btn)
        layout.addLayout(header)

        # Service Cards
        for meta in SERVICES_META:
            svc_id = meta["id"]
            card = Card(padding=18)
            row = QHBoxLayout()
            row.setSpacing(14)

            info = QVBoxLayout()
            info.setSpacing(4)
            top_line = QHBoxLayout()
            top_line.setSpacing(8)
            name_lbl = QLabel(meta["name"])
            name_lbl.setObjectName("SectionTitle")
            port_lbl = QLabel()
            port_lbl.setStyleSheet(
                "background-color: rgba(148,163,184,0.12); color: #94a3b8; "
                "border-radius: 6px; padding: 2px 8px; font-size: 11px; font-weight: 600;"
            )
            top_line.addWidget(name_lbl)
            top_line.addWidget(port_lbl)
            top_line.addStretch()

            desc_lbl = QLabel()
            desc_lbl.setObjectName("MutedText")

            info.addLayout(top_line)
            info.addWidget(desc_lbl)
            row.addLayout(info, stretch=1)

            pill = StatusPill(t("status.unknown"), "muted")
            pill.setFixedWidth(126)
            row.addWidget(pill)

            primary_btn = QPushButton()
            primary_btn.setProperty("variant", "primary")
            primary_btn.setFixedWidth(114)
            primary_btn.clicked.connect(lambda _=False, sid=svc_id: self._on_primary_action(sid))
            row.addWidget(primary_btn)

            more_btn = QPushButton()
            more_btn.setProperty("variant", "secondary")
            more_btn.setIcon(load_svg_icon("more", "#94a3b8", 16))
            more_btn.setFixedWidth(38)
            menu = QMenu(more_btn)
            act_restart = menu.addAction("")
            act_restart.triggered.connect(lambda _=False, sid=svc_id: self._run_action(sid, "restart"))
            act_logs = menu.addAction("")
            act_logs.triggered.connect(lambda _=False, sid=svc_id: self._open_logs(sid))
            more_btn.setMenu(menu)
            row.addWidget(more_btn)

            card.body_layout.addLayout(row)
            layout.addWidget(card)

            self._cards[svc_id] = {
                "meta": meta,
                "port_lbl": port_lbl,
                "desc_lbl": desc_lbl,
                "pill": pill,
                "btn": primary_btn,
                "more": more_btn,
                "act_restart": act_restart,
                "act_logs": act_logs,
                "state": "unknown",
            }

        layout.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)

        self.ctx.server_changed.connect(lambda _: self.refresh())
        self.ctx.language_changed.connect(self.retranslate)
        self.retranslate()

    def retranslate(self, *_) -> None:
        self.title_lbl.setText(t("services.title"))
        self.subtitle_lbl.setText(t("services.subtitle"))
        self.refresh_btn.setText(t("common.refresh"))
        self.open_btn.setText(t("common.open_erp"))

        for refs in self._cards.values():
            meta = refs["meta"]
            refs["port_lbl"].setText(t("services.port", port=meta["port"]))
            refs["desc_lbl"].setText(t(meta["desc_key"]))
            refs["act_restart"].setText(t("common.restart"))
            refs["act_logs"].setText(t("services.view_logs"))
        self._render_states()

    def _render_states(self) -> None:
        for refs in self._cards.values():
            state = refs["state"]
            btn = refs["btn"]
            if state == "active":
                refs["pill"].set_status(t("status.active"), "success")
                btn.setText(t("common.stop"))
                btn.setProperty("variant", "danger")
            elif state == "stopped":
                refs["pill"].set_status(t("status.stopped"), "danger")
                btn.setText(t("common.start"))
                btn.setProperty("variant", "primary")
            elif state == "running":
                refs["pill"].set_status(t("status.running"), "warning")
            elif state == "unreachable":
                refs["pill"].set_status(t("status.unreachable"), "warning")
                btn.setText(t("common.start"))
            else:
                refs["pill"].set_status(t("status.unknown"), "muted")
                btn.setText(t("common.start"))
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh()

    def _open_browser(self):
        srv = self.ctx.current_server
        host = srv.get("host", "localhost") if srv.get("type") == "ssh" else "localhost"
        webbrowser.open(f"http://{host}:5000")

    def _open_logs(self, svc_id: str):
        self.view_service_logs.emit(svc_id)
        self.ctx.navigate_requested.emit("logs")

    @asyncSlot()
    async def refresh(self):
        executor = self.ctx.executor
        for svc_id, refs in self._cards.items():
            try:
                active = await SystemdManager.is_active(executor, svc_id)
                refs["state"] = "active" if active else "stopped"
            except Exception:
                refs["state"] = "unreachable"
        self._render_states()

    @asyncSlot()
    async def _on_primary_action(self, svc_id: str):
        action = "stop" if self._cards[svc_id]["state"] == "active" else "start"
        await self._run_action_coro(svc_id, action)

    @asyncSlot()
    async def _run_action(self, svc_id: str, action: str):
        await self._run_action_coro(svc_id, action)

    async def _run_action_coro(self, svc_id: str, action: str):
        refs = self._cards[svc_id]
        refs["btn"].setEnabled(False)
        refs["more"].setEnabled(False)
        refs["state"] = "running"
        self._render_states()
        executor = self.ctx.executor

        try:
            if action == "start":
                res = await SystemdManager.start(executor, svc_id, on_output=self.ctx.emit_log)
            elif action == "stop":
                res = await SystemdManager.stop(executor, svc_id, on_output=self.ctx.emit_log)
            else:
                res = await SystemdManager.restart(executor, svc_id, on_output=self.ctx.emit_log)
            self.ctx.show_toast(res["message"], "success" if res["success"] else "error")
        except Exception as exc:
            self.ctx.show_toast(str(exc), "error")
        finally:
            refs["btn"].setEnabled(True)
            refs["more"].setEnabled(True)
            await self.refresh()
