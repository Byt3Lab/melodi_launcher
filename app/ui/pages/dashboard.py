"""
DashboardPage: Vue d'ensemble du serveur actif (jauges + instances MELODI ERP dynamiques + PostgreSQL).
"""

import webbrowser
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGridLayout, QScrollArea
)
from qasync import asyncSlot
from app.i18n import t
from app.system.system_info import SystemInfo
from app.system.systemd_manager import SystemdManager
from app.ui.app_context import AppContext
from app.ui.widgets.card import Card
from app.ui.widgets.metric_gauge import MetricGauge
from app.ui.widgets.status_pill import StatusPill
from app.ui.widgets.icon import load_svg_icon


class DashboardPage(QWidget):
    def __init__(self, ctx: AppContext, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self._busy = False
        self._last_metrics: dict | None = None
        self._service_states: dict[str, str] = {}
        self._service_rows: dict[str, tuple[StatusPill, QPushButton]] = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content.setObjectName("ScrollContent")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(20)

        # Header
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        self.title_lbl = QLabel()
        self.title_lbl.setObjectName("PageTitle")
        self.subtitle = QLabel()
        self.subtitle.setObjectName("PageSubtitle")
        title_box.addWidget(self.title_lbl)
        title_box.addWidget(self.subtitle)
        header.addLayout(title_box)
        header.addStretch()

        self.refresh_btn = QPushButton()
        self.refresh_btn.setProperty("variant", "secondary")
        self.refresh_btn.setIcon(load_svg_icon("refresh", "#94a3b8", 15))
        self.refresh_btn.clicked.connect(self.refresh_all)
        header.addWidget(self.refresh_btn)

        self.open_btn = QPushButton()
        self.open_btn.setProperty("variant", "primary")
        self.open_btn.setIcon(load_svg_icon("external-link", "#082f49", 15))
        self.open_btn.clicked.connect(self._open_first_instance)
        header.addWidget(self.open_btn)
        layout.addLayout(header)

        # 4 Metric Gauges
        metrics_grid = QGridLayout()
        metrics_grid.setSpacing(14)
        self.cpu_gauge = MetricGauge("")
        self.ram_gauge = MetricGauge("")
        self.disk_gauge = MetricGauge("")
        self.uptime_gauge = MetricGauge("")

        metrics_grid.addWidget(self.cpu_gauge, 0, 0)
        metrics_grid.addWidget(self.ram_gauge, 0, 1)
        metrics_grid.addWidget(self.disk_gauge, 0, 2)
        metrics_grid.addWidget(self.uptime_gauge, 0, 3)
        layout.addLayout(metrics_grid)

        # Services Summary Card (dynamic)
        srv_card = Card(padding=18)
        srv_header = QHBoxLayout()
        self.srv_title = QLabel()
        self.srv_title.setObjectName("SectionTitle")
        srv_header.addWidget(self.srv_title)
        srv_header.addStretch()
        self.manage_btn = QPushButton()
        self.manage_btn.setProperty("variant", "ghost")
        self.manage_btn.clicked.connect(lambda: self.ctx.navigate_requested.emit("services"))
        srv_header.addWidget(self.manage_btn)
        srv_card.body_layout.addLayout(srv_header)

        self.services_rows_box = QVBoxLayout()
        self.services_rows_box.setSpacing(10)
        srv_card.body_layout.addLayout(self.services_rows_box)
        layout.addWidget(srv_card)

        # Quick Deploy Banner
        deploy_card = Card(padding=18)
        dep_row = QHBoxLayout()
        dep_text = QVBoxLayout()
        self.dep_title = QLabel()
        self.dep_title.setObjectName("SectionTitle")
        self.dep_sub = QLabel()
        self.dep_sub.setObjectName("MutedText")
        dep_text.addWidget(self.dep_title)
        dep_text.addWidget(self.dep_sub)
        dep_row.addLayout(dep_text)
        dep_row.addStretch()
        self.go_install_btn = QPushButton()
        self.go_install_btn.setProperty("variant", "primary")
        self.go_install_btn.clicked.connect(lambda: self.ctx.navigate_requested.emit("install"))
        dep_row.addWidget(self.go_install_btn)
        deploy_card.body_layout.addLayout(dep_row)
        layout.addWidget(deploy_card)

        layout.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)

        self.timer = QTimer(self)
        self.timer.setInterval(8000)
        self.timer.timeout.connect(self._on_timer)

        self.ctx.server_changed.connect(self._on_server_or_instances_changed)
        self.ctx.instances_updated.connect(self._on_server_or_instances_changed)
        self.ctx.theme_changed.connect(lambda _: self._repaint_gauges())
        self.ctx.language_changed.connect(self.retranslate)

        self._rebuild_service_rows()
        self.retranslate()

    def _service_entries(self) -> list[tuple[str, str, int, bool]]:
        """Retourne [(service_name, display_name, port, is_melodi), ...]."""
        entries = []
        for inst in self.ctx.instance_manager.get_instances(self.ctx.current_server_id, kind="melodi"):
            entries.append((inst["service_name"], inst["name"], int(inst.get("port", 5000)), True))
        pg_list = self.ctx.instance_manager.get_pg_instances(self.ctx.current_server_id)
        if pg_list:
            for pg in pg_list:
                entries.append((pg["service_name"], pg["name"], int(pg.get("port", 5432)), False))
        else:
            entries.append(("postgresql", "PostgreSQL", 5432, False))
        return entries

    def _rebuild_service_rows(self) -> None:
        while self.services_rows_box.count():
            item = self.services_rows_box.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._service_rows.clear()
        self._service_states.clear()

        melodi_count = len(self.ctx.instance_manager.get_instances(self.ctx.current_server_id, kind="melodi"))
        self.open_btn.setEnabled(melodi_count > 0)
        if melodi_count == 0:
            empty_lbl = QLabel(t("dashboard.no_melodi_installed"))
            empty_lbl.setObjectName("MutedText")
            self.services_rows_box.addWidget(empty_lbl)

        for svc_id, label, port, is_melodi in self._service_entries():
            row_w = QWidget()
            row = QHBoxLayout(row_w)
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(10)

            name_lbl = QLabel(label)
            name_lbl.setStyleSheet("font-weight: 600; font-size: 13px;")
            port_lbl = QLabel(f":{port}")
            port_lbl.setObjectName("MutedText")

            pill = StatusPill(t("status.checking"), "muted")
            pill.setFixedWidth(126)

            action_btn = QPushButton()
            action_btn.setProperty("variant", "secondary")
            action_btn.setFixedWidth(104)
            action_btn.clicked.connect(lambda _=False, s=svc_id: self._toggle_service(s))

            row.addWidget(name_lbl)
            row.addWidget(port_lbl)
            row.addStretch()
            if is_melodi:
                open_i = QPushButton()
                open_i.setProperty("variant", "ghost")
                open_i.setIcon(load_svg_icon("external-link", "#38bdf8", 15))
                open_i.clicked.connect(lambda _=False, p=port: self._open_port(p))
                row.addWidget(open_i)
            row.addWidget(pill)
            row.addWidget(action_btn)

            self.services_rows_box.addWidget(row_w)
            self._service_rows[svc_id] = (pill, action_btn)
            self._service_states[svc_id] = "checking"

        self._render_services()

    def _on_server_or_instances_changed(self, *_) -> None:
        self._rebuild_service_rows()
        if self.isVisible():
            self.refresh_all()

    def retranslate(self, *_) -> None:
        self.title_lbl.setText(t("dashboard.title"))
        srv = self.ctx.current_server
        self.subtitle.setText(t("dashboard.target_active", name=srv.get("name", t("common.localhost"))))
        self.refresh_btn.setText(t("common.refresh"))
        self.open_btn.setText(t("common.open_erp"))
        self.cpu_gauge.title_lbl.setText(t("dashboard.cpu_title"))
        self.ram_gauge.title_lbl.setText(t("dashboard.ram_title"))
        self.disk_gauge.title_lbl.setText(t("dashboard.disk_title"))
        self.uptime_gauge.title_lbl.setText(t("dashboard.uptime_title"))
        self.srv_title.setText(t("dashboard.services_title"))
        self.manage_btn.setText(t("dashboard.manage_services"))
        self.dep_title.setText(t("dashboard.deploy_title"))
        self.dep_sub.setText(t("dashboard.deploy_desc"))
        self.go_install_btn.setText(t("dashboard.launch_wizard"))
        self._repaint_gauges()
        self._rebuild_service_rows()

    def _render_services(self) -> None:
        for svc_id, state in self._service_states.items():
            if svc_id not in self._service_rows:
                continue
            pill, btn = self._service_rows[svc_id]
            if state == "active":
                pill.set_status(t("status.active"), "success")
                btn.setText(t("common.stop"))
                btn.setProperty("action", "stop")
            elif state == "stopped":
                pill.set_status(t("status.stopped"), "danger")
                btn.setText(t("common.start"))
                btn.setProperty("action", "start")
                btn.setEnabled(True)
            elif state == "not_installed":
                pill.set_status(t("status.service_not_created"), "muted")
                btn.setText(t("services.create_btn"))
                btn.setProperty("action", "create")
                btn.setEnabled(False)
            elif state == "running":
                pill.set_status(t("status.running"), "warning")
            elif state == "unreachable":
                pill.set_status(t("status.unreachable"), "warning")
                btn.setText(t("common.start"))
                btn.setProperty("action", "start")
                btn.setEnabled(True)
            else:
                pill.set_status(t("status.checking"), "muted")
                btn.setText(t("common.start"))

    def showEvent(self, event):
        super().showEvent(event)
        self.timer.start()
        self.refresh_all()

    def hideEvent(self, event):
        super().hideEvent(event)
        self.timer.stop()

    def _on_timer(self):
        if self.isVisible() and not self._busy:
            self.refresh_all()

    def _open_port(self, port: int):
        srv = self.ctx.current_server
        host = srv.get("host", "localhost") if srv.get("type") == "ssh" else "localhost"
        webbrowser.open(f"http://{host}:{port}")

    def _open_first_instance(self):
        insts = self.ctx.instance_manager.get_instances(self.ctx.current_server_id)
        port = int(insts[0].get("port", 5000)) if insts else 5000
        self._open_port(port)

    def _repaint_gauges(self):
        metrics = self._last_metrics
        tokens = self.ctx.tokens
        if not metrics:
            return
        if metrics.get("status") != "offline":
            cpu = float(metrics.get("cpu_percent", 0))
            self.cpu_gauge.set_value(cpu, f"{cpu:.0f}%", t("dashboard.cpu_sub"), tokens)

            ram_pct = float(metrics.get("ram_percent", 0))
            ram_u = metrics.get("ram_used_gb", 0)
            ram_t = metrics.get("ram_total_gb", 0)
            self.ram_gauge.set_value(ram_pct, f"{ram_pct:.0f}%", f"{ram_u} / {ram_t} Go", tokens)

            d_pct = float(metrics.get("disk_percent", 0))
            d_u = metrics.get("disk_used_gb", 0)
            d_t = metrics.get("disk_total_gb", 0)
            self.disk_gauge.set_value(d_pct, f"{d_pct:.0f}%", f"{d_u} / {d_t} Go", tokens)

            up = metrics.get("uptime_formatted", "—")
            self.uptime_gauge.set_value(
                100, t("status.online"), t("dashboard.uptime_sub", uptime=up),
                tokens, color_override=tokens["success"]
            )
        else:
            self.uptime_gauge.set_value(
                0, t("status.offline"), t("dashboard.conn_failed"),
                tokens, color_override=tokens["danger"]
            )

    @asyncSlot()
    async def refresh_all(self):
        if self._busy:
            return
        self._busy = True
        srv = self.ctx.current_server
        self.subtitle.setText(t("dashboard.target_active", name=srv.get("name", t("common.localhost"))))
        executor = self.ctx.executor

        try:
            metrics = await SystemInfo.get_metrics(executor)
            if metrics:
                self._last_metrics = metrics
                self._repaint_gauges()

            for svc_id in list(self._service_rows.keys()):
                self._service_states[svc_id] = await SystemdManager.get_status(executor, svc_id)
            self._render_services()
        except Exception as exc:
            self.ctx.emit_log(t("dashboard.refresh_error", error=exc))
        finally:
            self._busy = False

    @asyncSlot()
    async def _toggle_service(self, svc_id: str):
        if svc_id not in self._service_rows:
            return
        _, btn = self._service_rows[svc_id]
        action = btn.property("action") or "start"
        btn.setEnabled(False)
        self._service_states[svc_id] = "running"
        self._render_services()
        executor = self.ctx.executor

        try:
            if action == "stop":
                res = await SystemdManager.stop(executor, svc_id, on_output=self.ctx.emit_log)
            else:
                res = await SystemdManager.start(executor, svc_id, on_output=self.ctx.emit_log)
            self.ctx.show_toast(res["message"], "success" if res["success"] else "error")
        except Exception as exc:
            self.ctx.show_toast(str(exc), "error")
        finally:
            btn.setEnabled(True)
            await self.refresh_all()
