"""
Sidebar: Barre latérale de navigation, sélecteur de serveur compact, langue et bascule de thème.
"""

import os
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox
)
from app import i18n
from app.i18n import t
from app.ui.app_context import AppContext
from app.ui.widgets.icon import load_svg_icon
from app.utils.helpers import resource_path


NAV_ITEMS = [
    ("dashboard", "nav.dashboard", "dashboard"),
    ("install", "nav.install", "download"),
    ("services", "nav.services", "services"),
    ("logs", "nav.logs", "logs"),
    ("servers", "nav.servers", "servers"),
]


class Sidebar(QFrame):
    page_selected = Signal(str)

    def __init__(self, ctx: AppContext, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self.setObjectName("Sidebar")
        self.setFixedWidth(228)
        self._nav_buttons: dict[str, tuple[QPushButton, str, str]] = {}
        self._active_key = "dashboard"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 18, 14, 16)
        layout.setSpacing(12)

        # Brand Header
        brand_row = QHBoxLayout()
        brand_row.setSpacing(10)
        logo_lbl = QLabel()
        icon_path = resource_path(os.path.join("assets", "icon.png"))
        if os.path.exists(icon_path):
            pix = QPixmap(icon_path).scaled(30, 30, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_lbl.setPixmap(pix)
        brand_row.addWidget(logo_lbl)

        brand_text = QVBoxLayout()
        brand_text.setSpacing(1)
        self.brand_title = QLabel()
        self.brand_title.setObjectName("BrandTitle")
        self.brand_subtitle = QLabel()
        self.brand_subtitle.setObjectName("BrandSubtitle")
        brand_text.addWidget(self.brand_title)
        brand_text.addWidget(self.brand_subtitle)
        brand_row.addLayout(brand_text)
        brand_row.addStretch()
        layout.addLayout(brand_row)

        # Compact Server Selector
        self.srv_section_lbl = QLabel()
        self.srv_section_lbl.setStyleSheet("font-size: 10px; font-weight: 700; letter-spacing: 0.8px; color: #64748b;")
        layout.addWidget(self.srv_section_lbl)

        self.server_combo = QComboBox()
        self.server_combo.currentIndexChanged.connect(self._on_server_combo_changed)
        layout.addWidget(self.server_combo)

        # Navigation
        self.nav_section_lbl = QLabel()
        self.nav_section_lbl.setStyleSheet("font-size: 10px; font-weight: 700; letter-spacing: 0.8px; color: #64748b; margin-top: 6px;")
        layout.addWidget(self.nav_section_lbl)

        nav_box = QVBoxLayout()
        nav_box.setSpacing(4)
        for key, tr_key, icon_name in NAV_ITEMS:
            btn = QPushButton()
            btn.setProperty("variant", "nav")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _=False, k=key: self.select_page(k))
            nav_box.addWidget(btn)
            self._nav_buttons[key] = (btn, tr_key, icon_name)
        layout.addLayout(nav_box)

        layout.addStretch()

        # Language selector
        self.lang_combo = QComboBox()
        for code, native_name in i18n.SUPPORTED.items():
            self.lang_combo.addItem(f"🌐  {native_name}", userData=code)
        self._sync_language_combo()
        self.lang_combo.currentIndexChanged.connect(self._on_lang_changed)
        layout.addWidget(self.lang_combo)

        # Theme toggle
        self.theme_btn = QPushButton()
        self.theme_btn.setProperty("variant", "ghost")
        self.theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_btn.clicked.connect(self.ctx.toggle_theme)
        layout.addWidget(self.theme_btn)

        self.ctx.servers_updated.connect(self.refresh_servers)
        self.ctx.server_changed.connect(self._sync_server_selection)
        self.ctx.theme_changed.connect(self.refresh_icons)
        self.ctx.language_changed.connect(self.retranslate)

        self.retranslate()
        self.refresh_servers()
        self.select_page("dashboard")

    def retranslate(self, *_) -> None:
        self.brand_title.setText(t("app.brand"))
        self.brand_subtitle.setText(t("app.subtitle"))
        self.srv_section_lbl.setText(t("nav.active_server"))
        self.nav_section_lbl.setText(t("nav.navigation"))
        for _, (btn, tr_key, _) in self._nav_buttons.items():
            btn.setText(f"  {t(tr_key)}")
        self._sync_language_combo()
        self.refresh_icons()

    def _sync_language_combo(self) -> None:
        self.lang_combo.blockSignals(True)
        cur = self.ctx.language
        for i in range(self.lang_combo.count()):
            if self.lang_combo.itemData(i) == cur:
                self.lang_combo.setCurrentIndex(i)
                break
        self.lang_combo.blockSignals(False)

    def _on_lang_changed(self, index: int) -> None:
        if index < 0:
            return
        code = self.lang_combo.itemData(index)
        if code and code != self.ctx.language:
            self.ctx.set_language(code)

    def refresh_servers(self) -> None:
        self.server_combo.blockSignals(True)
        current_id = self.ctx.current_server_id
        self.server_combo.clear()
        for idx, srv in enumerate(self.ctx.server_manager.get_all_servers()):
            prefix = "🏠 " if srv.get("type") == "local" else "🌐 "
            self.server_combo.addItem(f"{prefix}{srv.get('name', srv['id'])}", userData=srv["id"])
            if srv["id"] == current_id:
                self.server_combo.setCurrentIndex(idx)
        self.server_combo.blockSignals(False)

    def _sync_server_selection(self, server_id: str) -> None:
        self.server_combo.blockSignals(True)
        for i in range(self.server_combo.count()):
            if self.server_combo.itemData(i) == server_id:
                self.server_combo.setCurrentIndex(i)
                break
        self.server_combo.blockSignals(False)

    def _on_server_combo_changed(self, index: int) -> None:
        if index < 0:
            return
        sid = self.server_combo.itemData(index)
        if sid and sid != self.ctx.current_server_id:
            self.ctx.set_current_server(sid)

    def select_page(self, key: str) -> None:
        self._active_key = key
        for k, (btn, _, _) in self._nav_buttons.items():
            btn.setProperty("active", "true" if k == key else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self.refresh_icons()
        self.page_selected.emit(key)

    def refresh_icons(self) -> None:
        t_tok = self.ctx.tokens
        for k, (btn, _, icon_name) in self._nav_buttons.items():
            color = t_tok["accent"] if k == self._active_key else t_tok["text_secondary"]
            btn.setIcon(load_svg_icon(icon_name, color=color, size=17))

        if self.ctx.theme_name == "dark":
            self.theme_btn.setText(f"  {t('nav.theme_light')}")
            self.theme_btn.setIcon(load_svg_icon("sun", color=t_tok["text_secondary"], size=16))
        else:
            self.theme_btn.setText(f"  {t('nav.theme_dark')}")
            self.theme_btn.setIcon(load_svg_icon("moon", color=t_tok["text_secondary"], size=16))
