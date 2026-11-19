"""
ServersPage & ServerDialog: Gestion des profils serveurs (Localhost et SSH) avec stockage sécurisé keyring.
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QDialog,
    QFormLayout, QLineEdit, QSpinBox, QRadioButton, QFileDialog, QScrollArea
)
from qasync import asyncSlot
from app.i18n import t
from app.ui.app_context import AppContext
from app.ui.widgets.card import Card
from app.ui.widgets.status_pill import StatusPill
from app.ui.widgets.icon import load_svg_icon


class ServerDialog(QDialog):
    def __init__(self, ctx: AppContext, server: dict | None = None, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self.server = server
        self.is_local = bool(server and server.get("id") == "local")

        self.setWindowTitle(t("dialog.edit_title") if server else t("dialog.add_title"))
        self.setMinimumWidth(460)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        title = QLabel(t("dialog.edit_heading") if server else t("dialog.add_heading"))
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        self.name_edit = QLineEdit(server.get("name", "") if server else "")
        self.name_edit.setPlaceholderText(t("dialog.name_placeholder"))
        form.addRow(t("dialog.name"), self.name_edit)

        self.host_edit = QLineEdit(server.get("host", "") if server else "")
        self.host_edit.setPlaceholderText(t("dialog.host_placeholder"))
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(int(server.get("port", 22)) if server else 22)
        self.user_edit = QLineEdit(server.get("username", "ubuntu") if server else "ubuntu")

        if not self.is_local:
            form.addRow(t("dialog.host"), self.host_edit)
            form.addRow(t("dialog.port"), self.port_spin)
            form.addRow(t("dialog.user"), self.user_edit)

            auth_row = QHBoxLayout()
            self.rb_key = QRadioButton(t("dialog.auth_key"))
            self.rb_pwd = QRadioButton(t("dialog.auth_pwd"))
            auth_mode = (server.get("auth_method") if server else None) or "key"
            if auth_mode == "password":
                self.rb_pwd.setChecked(True)
            else:
                self.rb_key.setChecked(True)
            self.rb_key.toggled.connect(self._toggle_auth_fields)
            auth_row.addWidget(self.rb_key)
            auth_row.addWidget(self.rb_pwd)
            auth_row.addStretch()
            form.addRow(t("dialog.auth"), auth_row)

            key_row = QHBoxLayout()
            default_key = ctx.server_manager.credentials.get_default_key_path()
            self.key_edit = QLineEdit((server.get("key_path") if server else "") or default_key)
            browse_btn = QPushButton(t("common.browse"))
            browse_btn.setProperty("variant", "secondary")
            browse_btn.clicked.connect(self._browse_key)
            key_row.addWidget(self.key_edit, stretch=1)
            key_row.addWidget(browse_btn)
            self.key_row_widget = QWidget()
            self.key_row_widget.setLayout(key_row)
            key_row.setContentsMargins(0, 0, 0, 0)
            form.addRow(t("dialog.key_path"), self.key_row_widget)

            self.pwd_edit = QLineEdit()
            self.pwd_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.pwd_edit.setPlaceholderText(t("dialog.pwd_keep") if server else t("dialog.pwd_placeholder"))
            form.addRow(t("dialog.ssh_pwd"), self.pwd_edit)
        else:
            self.rb_key = None
            self.rb_pwd = None
            self.key_edit = None
            self.pwd_edit = None

        self.sudo_edit = QLineEdit()
        self.sudo_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.sudo_edit.setPlaceholderText(t("dialog.sudo_placeholder"))
        form.addRow(t("dialog.sudo_pwd"), self.sudo_edit)

        layout.addLayout(form)

        if not self.is_local:
            self._toggle_auth_fields()

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton(t("common.cancel"))
        cancel_btn.setProperty("variant", "secondary")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton(t("common.save"))
        save_btn.setProperty("variant", "primary")
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _toggle_auth_fields(self):
        use_key = self.rb_key.isChecked()
        self.key_row_widget.setEnabled(use_key)
        self.pwd_edit.setEnabled(not use_key)

    def _browse_key(self):
        path, _ = QFileDialog.getOpenFileName(
            self, t("dialog.select_key_title"), os.path.expanduser("~/.ssh")
        )
        if path:
            self.key_edit.setText(path)

    def _on_save(self):
        if not self.is_local and not self.host_edit.text().strip():
            self.host_edit.setFocus()
            return

        if self.is_local:
            sudo_val = self.sudo_edit.text()
            if sudo_val:
                self.ctx.server_manager.set_server_sudo_password("local", sudo_val)
            self.ctx.server_manager.update_server("local", {"name": self.name_edit.text().strip() or t("common.localhost")})
        else:
            auth_method = "key" if self.rb_key.isChecked() else "password"
            payload = {
                "name": self.name_edit.text().strip() or self.host_edit.text().strip(),
                "type": "ssh",
                "host": self.host_edit.text().strip(),
                "port": self.port_spin.value(),
                "username": self.user_edit.text().strip() or "root",
                "auth_method": auth_method,
                "key_path": self.key_edit.text().strip() if auth_method == "key" else "",
            }
            if self.pwd_edit.text():
                payload["password"] = self.pwd_edit.text()
            if self.sudo_edit.text():
                payload["sudo_password"] = self.sudo_edit.text()

            if self.server:
                self.ctx.server_manager.update_server(self.server["id"], payload)
            else:
                res = self.ctx.server_manager.add_server(payload)
                self.ctx.set_current_server(res["server"]["id"])

        self.ctx.servers_updated.emit()
        self.accept()


class ServersPage(QWidget):
    def __init__(self, ctx: AppContext, parent=None):
        super().__init__(parent)
        self.ctx = ctx

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content.setObjectName("ScrollContent")
        self.main_layout = QVBoxLayout(content)
        self.main_layout.setContentsMargins(28, 24, 28, 24)
        self.main_layout.setSpacing(16)

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

        self.add_btn = QPushButton()
        self.add_btn.setProperty("variant", "primary")
        self.add_btn.setIcon(load_svg_icon("plus", "#082f49", 16))
        self.add_btn.clicked.connect(self._add_server)
        header.addWidget(self.add_btn)
        self.main_layout.addLayout(header)

        self.list_container = QVBoxLayout()
        self.list_container.setSpacing(12)
        self.main_layout.addLayout(self.list_container)
        self.main_layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)

        self.ctx.servers_updated.connect(self.rebuild_list)
        self.ctx.server_changed.connect(lambda _: self.rebuild_list())
        self.ctx.language_changed.connect(self.retranslate)
        self.retranslate()

    def retranslate(self, *_) -> None:
        self.title_lbl.setText(t("servers.title"))
        self.subtitle_lbl.setText(t("servers.subtitle"))
        self.add_btn.setText(t("servers.add_btn"))
        self.rebuild_list()

    def rebuild_list(self) -> None:
        while self.list_container.count():
            item = self.list_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        active_id = self.ctx.current_server_id
        for srv in self.ctx.server_manager.get_all_servers():
            sid = srv["id"]
            is_local = srv.get("type") == "local"
            card = Card(padding=16)
            row = QHBoxLayout()
            row.setSpacing(12)

            info = QVBoxLayout()
            info.setSpacing(3)
            top = QHBoxLayout()
            top.setSpacing(8)
            name_lbl = QLabel(srv.get("name", sid))
            name_lbl.setObjectName("SectionTitle")
            type_lbl = QLabel(t("servers.type_local") if is_local else t("servers.type_ssh"))
            type_lbl.setStyleSheet(
                "background-color: rgba(56,189,248,0.14); color: #38bdf8; "
                "border-radius: 6px; padding: 2px 8px; font-size: 11px; font-weight: 600;"
            )
            top.addWidget(name_lbl)
            top.addWidget(type_lbl)
            if sid == active_id:
                act_pill = StatusPill(t("status.active"), "success")
                top.addWidget(act_pill)
            top.addStretch()

            detail_txt = t("servers.local_machine") if is_local else f"{srv.get('username', 'root')}@{srv.get('host', '')}:{srv.get('port', 22)}"
            detail_lbl = QLabel(detail_txt)
            detail_lbl.setObjectName("MutedText")

            info.addLayout(top)
            info.addWidget(detail_lbl)
            row.addLayout(info, stretch=1)

            status_pill = StatusPill(t("status.not_tested"), "muted")
            status_pill.setFixedWidth(120)
            row.addWidget(status_pill)

            if sid != active_id:
                use_btn = QPushButton(t("common.select"))
                use_btn.setProperty("variant", "secondary")
                use_btn.clicked.connect(lambda _=False, s=sid: self.ctx.set_current_server(s))
                row.addWidget(use_btn)

            test_btn = QPushButton(t("common.test"))
            test_btn.setProperty("variant", "secondary")
            test_btn.clicked.connect(lambda _=False, s=sid, p=status_pill, b=test_btn: self._test_server(s, p, b))
            row.addWidget(test_btn)

            edit_btn = QPushButton()
            edit_btn.setProperty("variant", "ghost")
            edit_btn.setIcon(load_svg_icon("edit", "#94a3b8", 16))
            edit_btn.clicked.connect(lambda _=False, data=srv: self._edit_server(data))
            row.addWidget(edit_btn)

            if not is_local:
                del_btn = QPushButton()
                del_btn.setProperty("variant", "ghost")
                del_btn.setIcon(load_svg_icon("trash", "#ef4444", 16))
                del_btn.clicked.connect(lambda _=False, s=sid: self._delete_server(s))
                row.addWidget(del_btn)

            card.body_layout.addLayout(row)
            self.list_container.addWidget(card)

    def _add_server(self):
        dlg = ServerDialog(self.ctx, None, self)
        dlg.exec()

    def _edit_server(self, srv: dict):
        dlg = ServerDialog(self.ctx, srv, self)
        dlg.exec()

    def _delete_server(self, sid: str):
        res = self.ctx.server_manager.delete_server(sid)
        if res["success"]:
            if self.ctx.current_server_id == sid:
                self.ctx.set_current_server("local")
            self.ctx.servers_updated.emit()
            self.ctx.show_toast(t("servers.deleted"), "info")

    @asyncSlot()
    async def _test_server(self, sid: str, pill: StatusPill, btn: QPushButton):
        btn.setEnabled(False)
        pill.set_status(t("status.testing"), "warning")
        try:
            res = await self.ctx.server_manager.test_server_connection(sid)
            if res.get("success"):
                pill.set_status(t("status.online"), "success")
                self.ctx.show_toast(t("servers.conn_success"), "success")
            else:
                pill.set_status(t("status.failed"), "danger")
                self.ctx.show_toast(res.get("message", t("servers.conn_failed")), "error")
        except Exception as exc:
            pill.set_status(t("status.error"), "danger")
            self.ctx.show_toast(str(exc), "error")
        finally:
            btn.setEnabled(True)
