"""
ServicesPage: Sépare clairement l'installation source du service système (systemctl).
Permet d'enregistrer une source existante et de créer, démarrer, arrêter, redémarrer ou supprimer
le service systemctl associé à chaque installation de façon isolée.
"""

import os
import re
import webbrowser
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMenu, QScrollArea,
    QMessageBox, QDialog, QFormLayout, QLineEdit, QSpinBox, QFileDialog
)
from qasync import asyncSlot
from app.core.instance_manager import slugify_service_name, slugify_pg_service_name
from app.core.task_manager import TaskProgress
from app.i18n import t
from app.installers.melodi import MelodiInstaller
from app.installers.postgresql import PostgreSQLInstaller
from app.system.systemd_manager import SystemdManager
from app.ui.app_context import AppContext
from app.ui.widgets.card import Card
from app.ui.widgets.status_pill import StatusPill
from app.ui.widgets.icon import load_svg_icon


class RegisterSourceDialog(QDialog):
    """Enregistre un dossier source MELODI ERP déjà installé sur le serveur pour pouvoir gérer son service."""

    def __init__(self, ctx: AppContext, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self.setWindowTitle(t("services.register_title"))
        self.setMinimumWidth(460)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setSpacing(10)

        next_port = ctx.instance_manager.suggest_next_port(ctx.current_server_id, 5000, kind="melodi")
        default_name = "MELODI ERP" if next_port == 5000 else f"MELODI {next_port}"
        self.name_edit = QLineEdit(default_name)
        form.addRow(t("wizard.source.instance_name_label"), self.name_edit)

        self.port_spin = QSpinBox()
        self.port_spin.setRange(1024, 65535)
        self.port_spin.setValue(next_port)
        form.addRow(t("wizard.source.port_label"), self.port_spin)

        dir_row = QHBoxLayout()
        default_dir = "C:\\melodi" if (ctx.current_server_id == "local" and os.name == "nt") else "/opt/melodi"
        self.dir_edit = QLineEdit(default_dir)
        browse_btn = QPushButton(t("common.browse"))
        browse_btn.setProperty("variant", "secondary")
        browse_btn.clicked.connect(self._browse_dir)
        dir_row.addWidget(self.dir_edit, stretch=1)
        dir_row.addWidget(browse_btn)
        dir_w = QWidget()
        dir_w.setLayout(dir_row)
        dir_row.setContentsMargins(0, 0, 0, 0)
        form.addRow(t("services.register_dir"), dir_w)

        self.pg_port_spin = QSpinBox()
        self.pg_port_spin.setRange(1024, 65535)
        self.pg_port_spin.setValue(5432)
        form.addRow(t("wizard.comp.pg_port_label"), self.pg_port_spin)

        layout.addLayout(form)

        btns = QHBoxLayout()
        btns.addStretch()
        cancel_btn = QPushButton(t("common.cancel"))
        cancel_btn.setProperty("variant", "secondary")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton(t("common.save"))
        save_btn.setProperty("variant", "primary")
        save_btn.clicked.connect(self._on_save)
        btns.addWidget(cancel_btn)
        btns.addWidget(save_btn)
        layout.addLayout(btns)

    def _browse_dir(self):
        path = QFileDialog.getExistingDirectory(self, t("services.register_title"))
        if path:
            self.dir_edit.setText(path)

    def _on_save(self):
        name = self.name_edit.text().strip() or "MELODI ERP"
        install_dir = self.dir_edit.text().strip()
        if not install_dir:
            self.dir_edit.setFocus()
            return
        port = self.port_spin.value()
        pg_port = self.pg_port_spin.value()
        res = self.ctx.instance_manager.add_or_update_instance(
            server_id=self.ctx.current_server_id,
            name=name,
            port=port,
            install_dir=install_dir,
            service_name=slugify_service_name(name),
            kind="melodi",
            pg_port=pg_port,
            pg_service_name=slugify_pg_service_name(pg_port),
        )
        if not res.get("success"):
            self.ctx.show_toast(t("wizard.source.hint_port_used", port=port), "error")
            return
        self.ctx.instances_updated.emit()
        self.accept()


class CreateServiceDialog(QDialog):
    """Affiche et valide le nom du service et le port générés avant de créer le service système."""

    def __init__(self, ctx: AppContext, meta: dict, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self.meta = meta
        self.chosen_service_name = meta["id"]
        self.chosen_port = int(meta["port"])

        self.setWindowTitle(t("services.create_dialog_title"))
        self.setMinimumWidth(470)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        desc = QLabel(t("services.create_dialog_desc"))
        desc.setObjectName("MutedText")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        form = QFormLayout()
        form.setSpacing(10)

        self.svc_edit = QLineEdit(self.chosen_service_name)
        self.svc_edit.setPlaceholderText(t("services.service_name_placeholder"))
        self.svc_edit.textChanged.connect(self._reset_status)
        form.addRow(t("services.service_name_label"), self.svc_edit)

        self.port_spin = QSpinBox()
        self.port_spin.setRange(1024, 65535)
        self.port_spin.setValue(self.chosen_port)
        self.port_spin.valueChanged.connect(self._reset_status)
        form.addRow(t("wizard.source.port_label"), self.port_spin)

        dir_lbl = QLabel(meta.get("install_dir", ""))
        dir_lbl.setObjectName("MutedText")
        form.addRow(t("services.register_dir"), dir_lbl)

        layout.addLayout(form)

        status_row = QHBoxLayout()
        self.check_btn = QPushButton(t("services.check_availability"))
        self.check_btn.setProperty("variant", "secondary")
        self.check_btn.clicked.connect(self._on_check_clicked)
        self.status_pill = StatusPill(t("status.not_tested"), "muted")
        status_row.addWidget(self.check_btn)
        status_row.addWidget(self.status_pill)
        status_row.addStretch()
        layout.addLayout(status_row)

        self.hint_lbl = QLabel("")
        self.hint_lbl.setWordWrap(True)
        self.hint_lbl.setStyleSheet("color: #ef4444; font-size: 12px;")
        layout.addWidget(self.hint_lbl)

        btns = QHBoxLayout()
        btns.addStretch()
        cancel_btn = QPushButton(t("common.cancel"))
        cancel_btn.setProperty("variant", "secondary")
        cancel_btn.clicked.connect(self.reject)
        self.create_btn = QPushButton(t("services.create_btn"))
        self.create_btn.setProperty("variant", "primary")
        self.create_btn.clicked.connect(self._on_confirm_clicked)
        btns.addWidget(cancel_btn)
        btns.addWidget(self.create_btn)
        layout.addLayout(btns)

    def _reset_status(self):
        self.status_pill.set_status(t("status.not_tested"), "muted")
        self.hint_lbl.setText("")

    async def _run_availability_check(self) -> bool:
        svc = self.svc_edit.text().strip()
        port = self.port_spin.value()

        if not re.match(r"^[a-z0-9][a-z0-9_-]*$", svc):
            self.status_pill.set_status(t("status.error"), "danger")
            self.hint_lbl.setText(t("services.err_invalid_name"))
            return False

        self.check_btn.setEnabled(False)
        self.create_btn.setEnabled(False)
        self.status_pill.set_status(t("services.checking_availability"), "warning")
        self.hint_lbl.setText("")

        try:
            kind = "melodi" if self.meta["is_melodi"] else "postgresql"
            if self.ctx.instance_manager.is_port_used(
                self.ctx.current_server_id, port, exclude_service_name=self.meta["id"], kind=kind
            ):
                self.status_pill.set_status(t("status.failed"), "danger")
                self.hint_lbl.setText(t("wizard.source.hint_port_used", port=port))
                return False

            avail = await SystemdManager.check_availability(self.ctx.executor, svc, port)
            if not avail["service_available"]:
                self.status_pill.set_status(t("status.failed"), "danger")
                self.hint_lbl.setText(t("services.err_service_exists", name=svc))
                return False
            if not avail["port_available"]:
                self.status_pill.set_status(t("status.failed"), "danger")
                self.hint_lbl.setText(t("services.err_port_busy", port=port))
                return False

            self.status_pill.set_status(t("services.available_ok"), "success")
            self.chosen_service_name = svc
            self.chosen_port = port
            return True
        finally:
            self.check_btn.setEnabled(True)
            self.create_btn.setEnabled(True)

    @asyncSlot()
    async def _on_check_clicked(self):
        await self._run_availability_check()

    @asyncSlot()
    async def _on_confirm_clicked(self):
        if await self._run_availability_check():
            self.accept()


class ServicesPage(QWidget):
    view_service_logs = Signal(str)

    def __init__(self, ctx: AppContext, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self._cards: dict[str, dict] = {}

        self._refreshing = False
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

        self.register_btn = QPushButton()
        self.register_btn.setProperty("variant", "secondary")
        self.register_btn.setIcon(load_svg_icon("plus", "#94a3b8", 15))
        self.register_btn.clicked.connect(self._register_existing_source)
        header.addWidget(self.register_btn)

        self.refresh_btn = QPushButton()
        self.refresh_btn.setProperty("variant", "secondary")
        self.refresh_btn.setIcon(load_svg_icon("refresh", "#94a3b8", 15))
        self.refresh_btn.clicked.connect(self.refresh)
        header.addWidget(self.refresh_btn)

        self.open_btn = QPushButton()
        self.open_btn.setProperty("variant", "primary")
        self.open_btn.setIcon(load_svg_icon("external-link", "#082f49", 15))
        self.open_btn.clicked.connect(self._open_first_instance)
        header.addWidget(self.open_btn)
        layout.addLayout(header)

        self.cards_container = QVBoxLayout()
        self.cards_container.setSpacing(14)
        layout.addLayout(self.cards_container)

        layout.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)

        self.ctx.server_changed.connect(self._on_list_changed)
        self.ctx.instances_updated.connect(self._on_list_changed)
        self.ctx.language_changed.connect(self.retranslate)

        self._rebuild_cards()
        self.retranslate()

    def _melodi_entries(self) -> list[dict]:
        entries = []
        for inst in self.ctx.instance_manager.get_instances(self.ctx.current_server_id, kind="melodi"):
            desc = inst.get("install_dir") or t("services.melodi_desc")
            if inst.get("pg_port"):
                desc = f"{desc}  •  {t('services.linked_pg', port=inst['pg_port'])}"
            entries.append({
                "id": inst["service_name"],
                "instance_id": inst["id"],
                "name": inst["name"],
                "port": int(inst.get("port", 5000)),
                "install_dir": inst.get("install_dir", "/opt/melodi"),
                "pg_service_name": inst.get("pg_service_name", "postgresql"),
                "pg_port": int(inst.get("pg_port", 5432)),
                "desc": desc,
                "is_melodi": True,
                "is_default": False,
            })
        return entries

    def _pg_entries(self) -> list[dict]:
        pg_list = self.ctx.instance_manager.get_pg_instances(self.ctx.current_server_id)
        if not pg_list:
            return [{
                "id": "postgresql",
                "instance_id": None,
                "name": "PostgreSQL",
                "port": 5432,
                "install_dir": "/var/lib/postgresql",
                "desc_key": "services.pg_desc",
                "is_melodi": False,
                "is_default": True,
            }]
        entries = []
        for inst in pg_list:
            entries.append({
                "id": inst["service_name"],
                "instance_id": inst["id"],
                "name": inst["name"],
                "port": int(inst.get("port", 5432)),
                "install_dir": inst.get("install_dir", "/var/lib/postgresql"),
                "desc": inst.get("install_dir") or t("services.pg_desc"),
                "is_melodi": False,
                "is_default": False,
            })
        return entries

    def _add_section_label(self, text: str) -> None:
        lbl = QLabel(text)
        lbl.setObjectName("SectionTitle")
        self.cards_container.addWidget(lbl)

    def _add_service_card(self, meta: dict) -> None:
        svc_id = meta["id"]
        port = meta["port"]
        card = Card(padding=18)
        row = QHBoxLayout()
        row.setSpacing(14)

        info = QVBoxLayout()
        info.setSpacing(4)
        top_line = QHBoxLayout()
        top_line.setSpacing(8)
        name_lbl = QLabel(meta["name"])
        name_lbl.setObjectName("SectionTitle")
        port_lbl = QLabel(t("services.port", port=port))
        port_lbl.setStyleSheet(
            "background-color: rgba(148,163,184,0.12); color: #94a3b8; "
            "border-radius: 6px; padding: 2px 8px; font-size: 11px; font-weight: 600;"
        )
        top_line.addWidget(name_lbl)
        top_line.addWidget(port_lbl)
        top_line.addStretch()

        desc_lbl = QLabel(t(meta["desc_key"]) if "desc_key" in meta else meta["desc"])
        desc_lbl.setObjectName("MutedText")

        info.addLayout(top_line)
        info.addWidget(desc_lbl)
        row.addLayout(info, stretch=1)

        pill = StatusPill(t("status.unknown"), "muted")
        pill.setFixedWidth(134)
        row.addWidget(pill)

        primary_btn = QPushButton()
        primary_btn.setProperty("variant", "primary")
        primary_btn.setFixedWidth(124)
        primary_btn.clicked.connect(lambda _=False, sid=svc_id: self._on_primary_action(sid))
        row.addWidget(primary_btn)

        more_btn = QPushButton()
        more_btn.setProperty("variant", "secondary")
        more_btn.setIcon(load_svg_icon("more", "#94a3b8", 16))
        more_btn.setFixedWidth(38)
        menu = QMenu(more_btn)
        act_open = None
        if meta["is_melodi"]:
            act_open = menu.addAction(t("services.open_in_browser"))
            act_open.triggered.connect(lambda _=False, p=port: self._open_port(p))
        act_restart = menu.addAction(t("common.restart"))
        act_restart.triggered.connect(lambda _=False, sid=svc_id: self._run_action(sid, "restart"))
        act_create = menu.addAction(t("services.create_service"))
        act_create.triggered.connect(lambda _=False, sid=svc_id: self._prompt_create_service(sid))
        act_logs = menu.addAction(t("services.view_logs"))
        act_logs.triggered.connect(lambda _=False, sid=svc_id: self._open_logs(sid))
        menu.addSeparator()
        act_delete = menu.addAction(t("services.delete_service"))
        act_delete.triggered.connect(lambda _=False, sid=svc_id: self._prompt_delete_service(sid))
        act_remove = None
        if not meta["is_default"]:
            act_remove = menu.addAction(t("services.remove_instance"))
            act_remove.triggered.connect(lambda _=False, iid=meta["instance_id"]: self._remove_instance(iid))
        more_btn.setMenu(menu)
        row.addWidget(more_btn)

        card.body_layout.addLayout(row)
        self.cards_container.addWidget(card)

        self._cards[svc_id] = {
            "meta": meta,
            "port_lbl": port_lbl,
            "desc_lbl": desc_lbl,
            "pill": pill,
            "btn": primary_btn,
            "more": more_btn,
            "act_open": act_open,
            "act_restart": act_restart,
            "act_create": act_create,
            "act_logs": act_logs,
            "act_delete": act_delete,
            "act_remove": act_remove,
            "state": "unknown",
        }

    def _rebuild_cards(self) -> None:
        while self.cards_container.count():
            item = self.cards_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cards.clear()

        # Section 1 : Applications MELODI ERP installées
        self._add_section_label(t("services.melodi_apps_section"))
        melodi_list = self._melodi_entries()
        self.open_btn.setEnabled(bool(melodi_list))
        if not melodi_list:
            empty_card = Card(padding=18)
            erow = QHBoxLayout()
            elbl = QLabel(t("services.empty_melodi"))
            elbl.setObjectName("MutedText")
            ebtn = QPushButton(t("dashboard.launch_wizard"))
            ebtn.setProperty("variant", "primary")
            ebtn.clicked.connect(lambda: self.ctx.navigate_requested.emit("install"))
            erow.addWidget(elbl)
            erow.addStretch()
            erow.addWidget(ebtn)
            empty_card.body_layout.addLayout(erow)
            self.cards_container.addWidget(empty_card)
        else:
            for meta in melodi_list:
                self._add_service_card(meta)

        # Section 2 : Instances PostgreSQL
        self._add_section_label(t("services.pg_section"))
        for meta in self._pg_entries():
            self._add_service_card(meta)

        self._render_states()

    def _on_list_changed(self, *_) -> None:
        self._rebuild_cards()
        if self.isVisible():
            self.refresh()

    def retranslate(self, *_) -> None:
        self.title_lbl.setText(t("services.title"))
        self.subtitle_lbl.setText(t("services.subtitle"))
        self.register_btn.setText(t("services.register_existing"))
        self.refresh_btn.setText(t("common.refresh"))
        self.open_btn.setText(t("common.open_erp"))
        self._rebuild_cards()

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
            elif state == "not_installed":
                refs["pill"].set_status(t("status.service_not_created"), "muted")
                btn.setText(t("services.create_btn"))
                btn.setProperty("variant", "secondary")
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

    def _register_existing_source(self):
        dlg = RegisterSourceDialog(self.ctx, self)
        dlg.exec()

    def _open_port(self, port: int):
        srv = self.ctx.current_server
        host = srv.get("host", "localhost") if srv.get("type") == "ssh" else "localhost"
        webbrowser.open(f"http://{host}:{port}")

    def _open_first_instance(self):
        insts = self.ctx.instance_manager.get_instances(self.ctx.current_server_id, kind="melodi")
        port = int(insts[0].get("port", 5000)) if insts else 5000
        self._open_port(port)

    def _open_logs(self, svc_id: str):
        self.view_service_logs.emit(svc_id)
        self.ctx.navigate_requested.emit("logs")

    def _remove_instance(self, instance_id: str):
        res = self.ctx.instance_manager.delete_instance(instance_id)
        if res.get("success"):
            self.ctx.instances_updated.emit()
            self.ctx.show_toast(t("services.instance_removed"), "info")

    def _prompt_create_service(self, svc_id: str):
        """Ouvre le dialogue synchrone hors tâche asyncio pour éviter le blocage qasync."""
        if svc_id not in self._cards:
            return
        meta = self._cards[svc_id]["meta"]
        dlg = CreateServiceDialog(self.ctx, meta, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._execute_create_service(svc_id, dlg.chosen_service_name, dlg.chosen_port)

    @asyncSlot()
    async def _execute_create_service(self, svc_id: str, target_svc: str, target_port: int):
        if svc_id not in self._cards:
            return
        meta = self._cards[svc_id]["meta"]

        if not meta["is_default"] and (target_svc != svc_id or target_port != meta["port"]):
            if meta.get("instance_id"):
                self.ctx.instance_manager.delete_instance(meta["instance_id"])
            self.ctx.instance_manager.add_or_update_instance(
                server_id=self.ctx.current_server_id,
                name=meta["name"],
                port=target_port,
                install_dir=meta["install_dir"],
                service_name=target_svc,
                kind="melodi" if meta["is_melodi"] else "postgresql",
                pg_port=meta.get("pg_port") if meta["is_melodi"] else None,
                pg_service_name=meta.get("pg_service_name") if meta["is_melodi"] else None,
            )
            self.ctx.instances_updated.emit()
            svc_id = target_svc
            meta = self._cards[svc_id]["meta"]

        refs = self._cards[svc_id]
        refs["btn"].setEnabled(False)
        refs["more"].setEnabled(False)
        refs["state"] = "running"
        self._render_states()

        try:
            if meta["is_melodi"]:
                ok, err = await MelodiInstaller.create_service(
                    self.ctx.executor,
                    service_name=target_svc,
                    app_dir=meta["install_dir"],
                    port=target_port,
                    pg_service_name=meta.get("pg_service_name", "postgresql"),
                    pg_port=meta.get("pg_port", 5432),
                    on_output=self.ctx.emit_log,
                )
                self.ctx.show_toast(
                    t("services.service_created", name=target_svc) if ok else t("systemd.start_failed", name=target_svc, error=err),
                    "success" if ok else "error",
                )
            else:
                task = TaskProgress("pg_svc", "PostgreSQL Service", self.ctx.executor.name)
                await PostgreSQLInstaller().install(
                    self.ctx.executor,
                    task,
                    port=target_port,
                    service_name=target_svc,
                    data_dir=meta["install_dir"],
                )
                self.ctx.show_toast(
                    t("services.service_created", name=target_svc) if not task.is_failed() else (task.error or "Error"),
                    "success" if not task.is_failed() else "error",
                )
        except Exception as exc:
            self.ctx.show_toast(str(exc), "error")
        finally:
            if svc_id in self._cards:
                self._cards[svc_id]["btn"].setEnabled(True)
                self._cards[svc_id]["more"].setEnabled(True)
        await self.refresh()

    def _prompt_delete_service(self, svc_id: str):
        if svc_id not in self._cards:
            return
        reply = QMessageBox.question(
            self,
            t("services.delete_confirm_title"),
            t("services.delete_confirm_body", name=svc_id),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._execute_delete_service(svc_id)

    @asyncSlot()
    async def _execute_delete_service(self, svc_id: str):
        """Supprime uniquement le service systemctl, tout en conservant l'installation source."""
        if svc_id not in self._cards:
            return
        refs = self._cards[svc_id]
        refs["btn"].setEnabled(False)
        refs["more"].setEnabled(False)
        refs["state"] = "running"
        self._render_states()

        try:
            res = await SystemdManager.delete(self.ctx.executor, svc_id, on_output=self.ctx.emit_log)
            msg = t("services.service_deleted_keep_source", name=svc_id) if res["success"] else res["message"]
            self.ctx.show_toast(msg, "success" if res["success"] else "error")
        except Exception as exc:
            self.ctx.show_toast(str(exc), "error")
        finally:
            if svc_id in self._cards:
                self._cards[svc_id]["btn"].setEnabled(True)
                self._cards[svc_id]["more"].setEnabled(True)
        await self.refresh()

    @asyncSlot()
    async def refresh(self):
        if self._refreshing:
            return
        self._refreshing = True
        self.refresh_btn.setEnabled(False)
        executor = self.ctx.executor
        try:
            for svc_id in list(self._cards.keys()):
                try:
                    state = await SystemdManager.get_status(executor, svc_id)
                except Exception:
                    state = "unreachable"
                if svc_id in self._cards:
                    self._cards[svc_id]["state"] = state
                    self._render_states()
        finally:
            self._refreshing = False
            self.refresh_btn.setEnabled(True)

    def _on_primary_action(self, svc_id: str):
        if svc_id not in self._cards:
            return
        state = self._cards[svc_id]["state"]
        if state == "not_installed":
            self._prompt_create_service(svc_id)
            return
        action = "stop" if state == "active" else "start"
        self._run_action(svc_id, action)

    @asyncSlot()
    async def _run_action(self, svc_id: str, action: str):
        await self._run_action_coro(svc_id, action)

    async def _run_action_coro(self, svc_id: str, action: str):
        if svc_id not in self._cards:
            return
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
