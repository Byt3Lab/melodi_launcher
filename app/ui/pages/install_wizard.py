"""
InstallWizardPage: Assistant simplifié de déploiement MELODI ERP (100 % centré sur MELODI ERP, sans Redis).
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QStackedWidget,
    QComboBox, QRadioButton, QLineEdit, QCheckBox, QProgressBar, QFileDialog,
    QFormLayout
)
from qasync import asyncSlot
from app.i18n import t
from app.core.task_manager import TaskProgress
from app.installers.melodi import MelodiInstaller
from app.installers.postgresql import PostgreSQLInstaller
from app.ui.app_context import AppContext
from app.ui.pages.servers import ServerDialog
from app.ui.widgets.card import Card
from app.ui.widgets.stepper import StepperHeader, TaskChecklist
from app.ui.widgets.status_pill import StatusPill
from app.ui.widgets.log_view import LogView
from app.ui.widgets.icon import load_svg_icon


WIZARD_STEP_KEYS = [
    "wizard.step.target",
    "wizard.step.source",
    "wizard.step.components",
    "wizard.step.summary",
    "wizard.step.install",
]


class InstallWizardPage(QWidget):
    def __init__(self, ctx: AppContext, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self._step = 0
        self._is_running = False
        self._current_task: TaskProgress | None = None
        self._target_state = "not_tested"

        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 24, 28, 20)
        outer.setSpacing(16)

        self.title_lbl = QLabel()
        self.title_lbl.setObjectName("PageTitle")
        self.subtitle_lbl = QLabel()
        self.subtitle_lbl.setObjectName("PageSubtitle")
        outer.addWidget(self.title_lbl)
        outer.addWidget(self.subtitle_lbl)

        self.stepper = StepperHeader(WIZARD_STEP_KEYS)
        outer.addWidget(self.stepper)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_step_target())
        self.stack.addWidget(self._build_step_source())
        self.stack.addWidget(self._build_step_options())
        self.stack.addWidget(self._build_step_summary())
        self.stack.addWidget(self._build_step_progress())
        outer.addWidget(self.stack, stretch=1)

        footer = QHBoxLayout()
        self.back_btn = QPushButton()
        self.back_btn.setProperty("variant", "secondary")
        self.back_btn.clicked.connect(self._go_prev)

        self.next_btn = QPushButton()
        self.next_btn.setProperty("variant", "primary")
        self.next_btn.clicked.connect(self._go_next)

        footer.addWidget(self.back_btn)
        footer.addStretch()
        footer.addWidget(self.next_btn)
        outer.addLayout(footer)

        self.ctx.servers_updated.connect(self._refresh_target_combo)
        self.ctx.server_changed.connect(self._sync_target_combo)
        self.ctx.theme_changed.connect(lambda _: self.stepper.set_step(self._step, self.ctx.tokens))
        self.ctx.language_changed.connect(self.retranslate)

        self._refresh_target_combo()
        self.retranslate()
        self._update_step_ui()

    def _build_step_target(self) -> QWidget:
        page = QWidget()
        vbox = QVBoxLayout(page)
        vbox.setContentsMargins(0, 6, 0, 0)

        card = Card(padding=22)
        self.target_heading = QLabel()
        self.target_heading.setObjectName("SectionTitle")
        self.target_desc = QLabel()
        self.target_desc.setObjectName("MutedText")
        card.body_layout.addWidget(self.target_heading)
        card.body_layout.addWidget(self.target_desc)

        row = QHBoxLayout()
        row.setSpacing(10)
        self.target_combo = QComboBox()
        self.target_combo.currentIndexChanged.connect(self._on_target_combo_changed)
        row.addWidget(self.target_combo, stretch=1)

        self.add_srv_btn = QPushButton()
        self.add_srv_btn.setProperty("variant", "secondary")
        self.add_srv_btn.setIcon(load_svg_icon("plus", "#94a3b8", 15))
        self.add_srv_btn.clicked.connect(self._open_add_server)
        row.addWidget(self.add_srv_btn)
        card.body_layout.addLayout(row)

        test_row = QHBoxLayout()
        self.test_conn_btn = QPushButton()
        self.test_conn_btn.setProperty("variant", "secondary")
        self.test_conn_btn.clicked.connect(self._test_target)
        self.target_pill = StatusPill(t("status.not_tested"), "muted")
        test_row.addWidget(self.test_conn_btn)
        test_row.addWidget(self.target_pill)
        test_row.addStretch()
        card.body_layout.addLayout(test_row)

        vbox.addWidget(card)
        vbox.addStretch()
        return page

    def _build_step_source(self) -> QWidget:
        page = QWidget()
        vbox = QVBoxLayout(page)
        vbox.setContentsMargins(0, 6, 0, 0)

        card = Card(padding=22)
        self.source_heading = QLabel()
        self.source_heading.setObjectName("SectionTitle")
        card.body_layout.addWidget(self.source_heading)

        mode_row = QHBoxLayout()
        self.rb_folder = QRadioButton()
        self.rb_zip = self.rb_folder  # alias
        self.rb_url = QRadioButton()
        self.rb_folder.setChecked(True)
        self.rb_folder.toggled.connect(self._on_source_changed)
        mode_row.addWidget(self.rb_folder)
        mode_row.addWidget(self.rb_url)
        mode_row.addStretch()
        card.body_layout.addLayout(mode_row)

        local_row = QHBoxLayout()
        local_row.setSpacing(8)
        self.source_edit = QLineEdit()
        self.zip_edit = self.source_edit  # alias
        self.source_edit.textChanged.connect(self._validate_current_step)

        self.folder_browse = QPushButton()
        self.folder_browse.setProperty("variant", "secondary")
        self.folder_browse.setIcon(load_svg_icon("folder", "#94a3b8", 15))
        self.folder_browse.clicked.connect(self._browse_folder)

        self.zip_browse = QPushButton()
        self.zip_browse.setProperty("variant", "secondary")
        self.zip_browse.setIcon(load_svg_icon("download", "#94a3b8", 15))
        self.zip_browse.clicked.connect(self._browse_zip)

        local_row.addWidget(self.source_edit, stretch=1)
        local_row.addWidget(self.folder_browse)
        local_row.addWidget(self.zip_browse)
        self.local_container = QWidget()
        self.local_container.setLayout(local_row)
        local_row.setContentsMargins(0, 0, 0, 0)
        card.body_layout.addWidget(self.local_container)

        self.url_edit = QLineEdit()
        self.url_edit.textChanged.connect(self._validate_current_step)
        self.url_edit.setVisible(False)
        card.body_layout.addWidget(self.url_edit)

        form = QFormLayout()
        self.dest_label = QLabel()
        default_dir = "C:\\melodi" if os.name == "nt" else "/opt/melodi"
        self.dest_edit = QLineEdit(default_dir)
        self.dest_edit.textChanged.connect(self._validate_current_step)
        form.addRow(self.dest_label, self.dest_edit)
        card.body_layout.addLayout(form)

        self.source_hint = QLabel("")
        self.source_hint.setStyleSheet("color: #f59e0b; font-size: 12px;")
        card.body_layout.addWidget(self.source_hint)

        vbox.addWidget(card)
        vbox.addStretch()
        return page

    def _build_step_options(self) -> QWidget:
        page = QWidget()
        vbox = QVBoxLayout(page)
        vbox.setContentsMargins(0, 6, 0, 0)

        card = Card(padding=22)
        self.comp_heading = QLabel()
        self.comp_heading.setObjectName("SectionTitle")
        card.body_layout.addWidget(self.comp_heading)

        self.chk_pg = QCheckBox()
        self.chk_pg.setChecked(True)

        self.chk_venv = QCheckBox()
        self.chk_venv.setChecked(True)

        self.chk_service = QCheckBox()
        self.chk_service.setChecked(True)

        card.body_layout.addWidget(self.chk_pg)
        card.body_layout.addWidget(self.chk_venv)
        card.body_layout.addWidget(self.chk_service)

        vbox.addWidget(card)
        vbox.addStretch()
        return page

    def _build_step_summary(self) -> QWidget:
        page = QWidget()
        vbox = QVBoxLayout(page)
        vbox.setContentsMargins(0, 6, 0, 0)

        card = Card(padding=22)
        self.summary_heading = QLabel()
        self.summary_heading.setObjectName("SectionTitle")
        card.body_layout.addWidget(self.summary_heading)

        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet("font-size: 13px; line-height: 1.6;")
        card.body_layout.addWidget(self.summary_label)

        vbox.addWidget(card)
        vbox.addStretch()
        return page

    def _build_step_progress(self) -> QWidget:
        page = QWidget()
        vbox = QVBoxLayout(page)
        vbox.setContentsMargins(0, 6, 0, 0)
        vbox.setSpacing(12)

        card = Card(padding=20)
        top = QHBoxLayout()
        self.progress_title = QLabel()
        self.progress_title.setObjectName("SectionTitle")
        self.progress_pct = QLabel("0%")
        self.progress_pct.setStyleSheet("font-weight: 700; color: #38bdf8;")
        top.addWidget(self.progress_title)
        top.addStretch()
        top.addWidget(self.progress_pct)
        card.body_layout.addLayout(top)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        card.body_layout.addWidget(self.progress_bar)

        self.checklist = TaskChecklist()
        card.body_layout.addWidget(self.checklist)

        ctrl_row = QHBoxLayout()
        self.details_btn = QPushButton()
        self.details_btn.setProperty("variant", "secondary")
        self.details_btn.setIcon(load_svg_icon("chevron-right", "#94a3b8", 15))
        self.details_btn.clicked.connect(self._toggle_details)

        self.cancel_btn = QPushButton()
        self.cancel_btn.setProperty("variant", "danger")
        self.cancel_btn.clicked.connect(self._cancel_install)

        self.goto_services_btn = QPushButton()
        self.goto_services_btn.setProperty("variant", "primary")
        self.goto_services_btn.setVisible(False)
        self.goto_services_btn.clicked.connect(lambda: self.ctx.navigate_requested.emit("services"))

        ctrl_row.addWidget(self.details_btn)
        ctrl_row.addStretch()
        ctrl_row.addWidget(self.cancel_btn)
        ctrl_row.addWidget(self.goto_services_btn)
        card.body_layout.addLayout(ctrl_row)

        vbox.addWidget(card)

        self.detail_logs = LogView(show_toolbar=False)
        self.detail_logs.setVisible(False)
        self.detail_logs.setMinimumHeight(180)
        vbox.addWidget(self.detail_logs, stretch=1)

        return page

    def retranslate(self, *_) -> None:
        self.title_lbl.setText(t("wizard.title"))
        self.subtitle_lbl.setText(t("wizard.subtitle"))
        self.stepper.retranslate()
        self.back_btn.setText(t("common.prev"))

        self.target_heading.setText(t("wizard.target.heading"))
        self.target_desc.setText(t("wizard.target.desc"))
        self.add_srv_btn.setText(t("wizard.target.new_ssh"))
        self.test_conn_btn.setText(t("wizard.target.test_btn"))
        self._render_target_pill()

        self.source_heading.setText(t("wizard.source.heading"))
        self.rb_folder.setText(t("wizard.source.folder_mode"))
        self.rb_url.setText(t("wizard.source.url_mode"))
        self.source_edit.setPlaceholderText(t("wizard.source.folder_placeholder"))
        self.folder_browse.setText(t("wizard.source.browse_folder"))
        self.zip_browse.setText(t("wizard.source.browse_zip"))
        self.url_edit.setPlaceholderText(t("wizard.source.url_placeholder"))
        self.dest_label.setText(t("wizard.source.dest_label"))

        self.comp_heading.setText(t("wizard.comp.heading"))
        self.chk_pg.setText(t("wizard.comp.pg"))
        self.chk_venv.setText(t("wizard.comp.venv"))
        self.chk_service.setText(t("wizard.comp.service"))

        self.summary_heading.setText(t("wizard.summary.heading"))
        self.cancel_btn.setText(t("common.cancel"))
        self.goto_services_btn.setText(t("wizard.progress.goto_services"))
        self.details_btn.setText(
            t("wizard.progress.hide_details") if self.detail_logs.isVisible() else t("wizard.progress.show_details")
        )
        self.checklist.retranslate()
        self._update_step_ui()

    def _render_target_pill(self) -> None:
        kind_map = {
            "not_tested": ("status.not_tested", "muted"),
            "testing": ("status.testing", "warning"),
            "connected": ("status.connected", "success"),
            "failed": ("status.failed", "danger"),
            "error": ("status.error", "danger"),
        }
        tr_key, kind = kind_map.get(self._target_state, ("status.not_tested", "muted"))
        self.target_pill.set_status(t(tr_key), kind)

    def _refresh_target_combo(self):
        self.target_combo.blockSignals(True)
        cid = self.ctx.current_server_id
        self.target_combo.clear()
        for idx, srv in enumerate(self.ctx.server_manager.get_all_servers()):
            prefix = "🏠 " if srv.get("type") == "local" else "🌐 "
            self.target_combo.addItem(f"{prefix}{srv.get('name', srv['id'])}", userData=srv["id"])
            if srv["id"] == cid:
                self.target_combo.setCurrentIndex(idx)
        self.target_combo.blockSignals(False)

    def _sync_target_combo(self, sid: str):
        self.target_combo.blockSignals(True)
        for i in range(self.target_combo.count()):
            if self.target_combo.itemData(i) == sid:
                self.target_combo.setCurrentIndex(i)
                break
        self.target_combo.blockSignals(False)
        self._target_state = "not_tested"
        self._render_target_pill()

    def _on_target_combo_changed(self, idx: int):
        if idx >= 0:
            sid = self.target_combo.itemData(idx)
            if sid and sid != self.ctx.current_server_id:
                self.ctx.set_current_server(sid)

    def _open_add_server(self):
        dlg = ServerDialog(self.ctx, None, self)
        dlg.exec()

    @asyncSlot()
    async def _test_target(self):
        self.test_conn_btn.setEnabled(False)
        self._target_state = "testing"
        self._render_target_pill()
        try:
            res = await self.ctx.server_manager.test_server_connection(self.ctx.current_server_id)
            if res.get("success"):
                self._target_state = "connected"
                is_win = await self.ctx.executor.is_windows()
                cur_dest = self.dest_edit.text().strip()
                if is_win and cur_dest == "/opt/melodi":
                    self.dest_edit.setText("C:\\melodi")
                elif not is_win and cur_dest == "C:\\melodi":
                    self.dest_edit.setText("/opt/melodi")
                self.ctx.show_toast(t("servers.conn_success"), "success")
            else:
                self._target_state = "failed"
                self.ctx.show_toast(res.get("message", t("servers.conn_failed")), "error")
        except Exception as exc:
            self._target_state = "error"
            self.ctx.show_toast(str(exc), "error")
        finally:
            self._render_target_pill()
            self.test_conn_btn.setEnabled(True)

    def _on_source_changed(self):
        is_local = self.rb_folder.isChecked()
        self.local_container.setVisible(is_local)
        self.url_edit.setVisible(not is_local)
        self._validate_current_step()

    def _browse_folder(self):
        path = QFileDialog.getExistingDirectory(self, t("wizard.source.select_folder"))
        if path:
            self.source_edit.setText(path)

    def _browse_zip(self):
        path, _ = QFileDialog.getOpenFileName(
            self, t("wizard.source.select_zip"), "", t("wizard.source.zip_filter")
        )
        if path:
            self.source_edit.setText(path)

    def _toggle_details(self):
        vis = not self.detail_logs.isVisible()
        self.detail_logs.setVisible(vis)
        self.details_btn.setText(t("wizard.progress.hide_details") if vis else t("wizard.progress.show_details"))
        icon = "chevron-down" if vis else "chevron-right"
        self.details_btn.setIcon(load_svg_icon(icon, "#94a3b8", 15))

    def _validate_current_step(self) -> bool:
        valid = True
        self.source_hint.setText("")

        if self._step == 1:
            dest = self.dest_edit.text().strip()
            if not dest:
                self.source_hint.setText(t("wizard.source.hint_dest"))
                valid = False
            elif self.rb_folder.isChecked():
                sp = self.source_edit.text().strip()
                if not sp or not os.path.exists(sp):
                    if sp:
                        self.source_hint.setText(t("wizard.source.hint_zip_missing"))
                    valid = False
            else:
                url = self.url_edit.text().strip()
                if not (url.startswith("http://") or url.startswith("https://")):
                    self.source_hint.setText(t("wizard.source.hint_url_invalid"))
                    valid = False

        self.next_btn.setEnabled(valid and not self._is_running)
        return valid

    def _update_step_ui(self):
        self.stepper.set_step(self._step, self.ctx.tokens)
        self.stack.setCurrentIndex(self._step)

        self.back_btn.setVisible(0 < self._step < 4)
        self.next_btn.setVisible(self._step < 4)

        if self._step == 3:
            self._populate_summary()
            self.next_btn.setText(t("wizard.start_install"))
        else:
            self.next_btn.setText(t("common.next"))

        self._validate_current_step()

    def _populate_summary(self):
        srv = self.ctx.current_server
        target_txt = srv.get("name", t("common.localhost"))
        if srv.get("type") == "ssh":
            target_txt += f" ({srv.get('username')}@{srv.get('host')})"

        if self.rb_folder.isChecked():
            sp = self.source_edit.text().strip()
            src_txt = sp if sp else t("wizard.summary.no_zip")
        else:
            src_txt = self.url_edit.text().strip()

        opts = ["MELODI ERP"]
        if self.chk_pg.isChecked():
            opts.append("PostgreSQL")
        if self.chk_venv.isChecked():
            opts.append(t("wizard.summary.opt_venv"))
        if self.chk_service.isChecked():
            opts.append(t("wizard.summary.opt_service"))
        if len(opts) == 1:
            opts.append(t("wizard.summary.opt_files_only"))

        self.summary_label.setText(
            t(
                "wizard.summary.body",
                target=target_txt,
                source=src_txt,
                dest=self.dest_edit.text().strip() or "/opt/melodi",
                components=", ".join(opts),
            )
        )

    def _go_prev(self):
        if self._step > 0 and not self._is_running:
            self._step -= 1
            self._update_step_ui()

    def _go_next(self):
        if not self._validate_current_step():
            return
        if self._step < 3:
            self._step += 1
            self._update_step_ui()
        elif self._step == 3:
            self._step = 4
            self._update_step_ui()
            self._start_installation()

    def _cancel_install(self):
        if self._current_task:
            self._current_task.cancel()
            self.detail_logs.append_line(t("wizard.progress.cancel_requested"))
            self.cancel_btn.setEnabled(False)

    @asyncSlot()
    async def _start_installation(self):
        self._is_running = True
        self.goto_services_btn.setVisible(False)
        self.cancel_btn.setEnabled(True)
        self.cancel_btn.setVisible(True)
        self.detail_logs.clear()
        self.progress_bar.setValue(0)
        self.progress_pct.setText("0%")
        self.progress_title.setText(t("wizard.progress.running"))

        tasks_def = [("connect", "wizard.task.connect")]
        if self.chk_pg.isChecked():
            tasks_def.append(("pg", "wizard.task.pg"))
        tasks_def.append(("melodi", "wizard.task.melodi"))
        if self.chk_venv.isChecked():
            tasks_def.append(("venv", "wizard.task.venv"))
        if self.chk_service.isChecked():
            tasks_def.append(("service", "wizard.task.service"))
        self.checklist.set_tasks(tasks_def)

        executor = self.ctx.executor
        task = TaskProgress("install", "MELODI Install", executor.name)
        self._current_task = task

        orig_update = task.update
        orig_log = task.append_log

        def _on_update(pct: int, desc: str):
            orig_update(pct, desc)
            self.progress_bar.setValue(pct)
            self.progress_pct.setText(f"{pct}%")
            self.progress_title.setText(desc)
            self.detail_logs.append_line(f"[{pct}%] {desc}")
            self.ctx.emit_log(f"[{pct}%] {desc}")

        def _on_log(text: str):
            orig_log(text)
            self.detail_logs.append_line(text)
            self.ctx.emit_log(text)

        task.update = _on_update
        task.append_log = _on_log

        try:
            self.checklist.set_state("connect", "running")
            if hasattr(executor, "connect"):
                ok = await executor.connect()
                if not ok:
                    self.checklist.set_state("connect", "error", t("wizard.err.conn_refused"))
                    raise RuntimeError(t("wizard.err.conn_failed", name=executor.name))
            self.checklist.set_state("connect", "success")

            if self.chk_pg.isChecked():
                self.checklist.set_state("pg", "running")
                await PostgreSQLInstaller().install(executor, task)
                if task.is_failed():
                    self.checklist.set_state("pg", "error")
                    raise RuntimeError(task.error or t("wizard.err.pg_failed"))
                self.checklist.set_state("pg", "success")

            self.checklist.set_state("melodi", "running")
            is_win = await executor.is_windows()
            default_dest = "C:\\melodi" if is_win else "/opt/melodi"
            dest_dir = self.dest_edit.text().strip() or default_dest
            setup_venv = self.chk_venv.isChecked()
            setup_service = self.chk_service.isChecked()

            kwargs = {
                "destination_dir": dest_dir,
                "setup_venv": setup_venv,
                "setup_service": setup_service,
                "deploy_only": not setup_venv and not setup_service,
                "on_step_done": self.checklist.set_state,
            }

            if self.rb_folder.isChecked():
                sp = self.source_edit.text().strip()
                if os.path.isdir(sp):
                    kwargs["source_dir"] = sp
                elif os.path.isfile(sp):
                    if executor.name != "Localhost":
                        task.update(20, t("wizard.uploading_zip"))
                        remote_zip = (
                            f"C:\\Windows\\Temp\\{os.path.basename(sp)}"
                            if is_win
                            else f"/tmp/{os.path.basename(sp)}"
                        )
                        ok_up, err_up = await executor.upload_file(sp, remote_zip)
                        if not ok_up:
                            raise RuntimeError(t("wizard.err.upload", error=err_up))
                        kwargs["zip_path"] = remote_zip
                    else:
                        kwargs["zip_path"] = sp
            else:
                kwargs["url"] = self.url_edit.text().strip()
                kwargs["source_type"] = "url"

            await MelodiInstaller().install(executor, task, **kwargs)
            if task.is_failed():
                self.checklist.set_state("melodi", "error")
                raise RuntimeError(task.error or t("wizard.err.melodi_failed"))
            self.checklist.set_state("melodi", "success")

            self.progress_bar.setValue(100)
            self.progress_pct.setText("100%")
            self.progress_title.setText(t("wizard.done_title"))
            self.cancel_btn.setVisible(False)
            self.goto_services_btn.setVisible(True)
            self.back_btn.setVisible(True)
            self.ctx.show_toast(t("wizard.done_toast"), "success")

        except Exception as exc:
            self.progress_title.setText(t("wizard.failed_title", error=exc))
            self.detail_logs.append_line(f"❌ {exc}")
            self.cancel_btn.setVisible(False)
            self.back_btn.setVisible(True)
            if not self.detail_logs.isVisible():
                self._toggle_details()
            self.ctx.show_toast(t("wizard.failed_toast", error=exc), "error")
        finally:
            self._is_running = False
