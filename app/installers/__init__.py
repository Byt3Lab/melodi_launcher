from .base import BaseInstaller
from .melodi import MelodiInstaller
from .melodi_websocket import MelodiWebsocketInstaller
from .melodi_process_manager import MelodiProcessManagerInstaller
from .postgresql import PostgreSQLInstaller
from .redis import RedisInstaller
from .pgadmin import PgAdminInstaller

__all__ = [
    "BaseInstaller",
    "MelodiInstaller",
    "MelodiWebsocketInstaller",
    "MelodiProcessManagerInstaller",
    "PostgreSQLInstaller",
    "RedisInstaller",
    "PgAdminInstaller"
]

