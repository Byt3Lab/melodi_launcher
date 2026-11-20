"""
MainWindow: Fenêtre principale PySide6 pour MELODI Control Center.
"""

import os
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QStackedWidget, QApplication
)
from app.i18n import t
from app.ui.app_context import AppContext
from app.ui.sidebar import Sidebar
from app.ui.theme import build_stylesheet
from app.ui.widgets.toast import ToastManager
from app.ui.pages.dashboard import DashboardPage
from app.ui.pages.install_wizard import InstallWizardPage
from app.ui.pages.services import ServicesPage
from app.ui.pages.logs import LogsPage
from app.ui.pages.servers import ServersPage
from app.utils.helpers import resource_path


class MainWindow(QMainWindow):
    def __init__(self, ctx: AppContext | None = None):
        super().__init__()
        self.ctx = ctx or AppContext()
        self.setWindowTitle(t("app.title"))
        self.ctx.language_changed.connect(lambda _: self.setWindowTitle(t("app.title")))
        self.resize(1160, 760)
        self.setMinimumSize(960, 640)

        icon_path = resource_path(os.path.join("assets", "icon.png"))
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        central = QWidget(self)
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)

        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.sidebar = Sidebar(self.ctx, self)
        root_layout.addWidget(self.sidebar)

        self.stack = QStackedWidget(self)
        self.pages = {}
        self._build_pages()
        root_layout.addWidget(self.stack, stretch=1)

        self.toast_manager = ToastManager(self)

        # Connexions
        self.sidebar.page_selected.connect(self._switch_page)
        self.ctx.navigate_requested.connect(self.sidebar.select_page)
        self.ctx.server_changed.connect(self._reload_for_server)
        self.ctx.toast_requested.connect(self.toast_manager.show)
        self.ctx.theme_changed.connect(self._apply_theme)

        self._apply_theme(self.ctx.theme_name)
        self._switch_page("dashboard")

    def _build_pages(self) -> None:
        """Instancie ou réinstancie toutes les pages pour le serveur actif."""
        self.pages = {
            "dashboard": DashboardPage(self.ctx, self),
            "install": InstallWizardPage(self.ctx, self),
            "services": ServicesPage(self.ctx, self),
            "logs": LogsPage(self.ctx, self),
            "servers": ServersPage(self.ctx, self),
        }
        for page in self.pages.values():
            self.stack.addWidget(page)
        self.pages["services"].view_service_logs.connect(self.pages["logs"].select_service)

    def _reload_for_server(self, _server_id: str) -> None:
        """Recharge complètement les pages et la barre latérale lors d'un changement de serveur."""
        current_widget = self.stack.currentWidget()
        current_key = next(
            (k for k, w in self.pages.items() if w is current_widget),
            "dashboard",
        )

        for page in self.pages.values():
            if hasattr(page, "timer"):
                page.timer.stop()
            self.stack.removeWidget(page)
            page.deleteLater()
        self.pages.clear()

        self._build_pages()
        self.sidebar.refresh_icons()
        self._switch_page(current_key)

    def _switch_page(self, key: str) -> None:
        if key in self.pages:
            self.stack.setCurrentWidget(self.pages[key])

    def _apply_theme(self, theme_name: str) -> None:
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(build_stylesheet(theme_name))
        self.sidebar.refresh_icons()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "toast_manager"):
            self.toast_manager._reposition()
