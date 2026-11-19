"""
AppContext: État partagé de l'application (serveur actif, bus de logs, notifications, thème, langue).
"""

from PySide6.QtCore import QObject, Signal, QSettings
from app import i18n
from app.core.server_manager import ServerManager
from app.remote.executor import Executor
from app.ui.theme import get_tokens


class AppContext(QObject):
    server_changed = Signal(str)
    servers_updated = Signal()
    log_emitted = Signal(str)
    theme_changed = Signal(str)
    language_changed = Signal(str)
    toast_requested = Signal(str, str)  # message, kind (info|success|warning|error)
    navigate_requested = Signal(str)    # page key

    def __init__(self, server_manager: ServerManager | None = None, settings: QSettings | None = None):
        super().__init__()
        self.server_manager = server_manager or ServerManager()
        self.settings = settings or QSettings("Byt3lab", "MelodiLauncher")
        self._current_server_id = "local"

        saved_theme = self.settings.value("theme", "dark")
        self._theme_name = saved_theme if saved_theme in ("dark", "light") else "dark"

        saved_lang = self.settings.value("language")
        lang = str(saved_lang) if saved_lang in i18n.SUPPORTED else i18n.detect_system_language()
        i18n.set_language(lang)

    @property
    def current_server_id(self) -> str:
        return self._current_server_id

    def set_current_server(self, server_id: str) -> None:
        if server_id not in [s["id"] for s in self.server_manager.get_all_servers()]:
            server_id = "local"
        self._current_server_id = server_id
        self.server_changed.emit(server_id)

    @property
    def executor(self) -> Executor:
        return self.server_manager.get_executor(self._current_server_id)

    @property
    def current_server(self) -> dict:
        return self.server_manager.get_server(self._current_server_id) or {}

    @property
    def theme_name(self) -> str:
        return self._theme_name

    @property
    def tokens(self) -> dict:
        return get_tokens(self._theme_name)

    def toggle_theme(self) -> None:
        self._theme_name = "light" if self._theme_name == "dark" else "dark"
        self.settings.setValue("theme", self._theme_name)
        self.theme_changed.emit(self._theme_name)

    @property
    def language(self) -> str:
        return i18n.get_language()

    def set_language(self, lang: str) -> None:
        if lang not in i18n.SUPPORTED:
            lang = i18n.FALLBACK
        i18n.set_language(lang)
        self.settings.setValue("language", lang)
        self.language_changed.emit(lang)

    def emit_log(self, text: str) -> None:
        if text:
            self.log_emitted.emit(text)

    def show_toast(self, message: str, kind: str = "info") -> None:
        self.toast_requested.emit(message, kind)
