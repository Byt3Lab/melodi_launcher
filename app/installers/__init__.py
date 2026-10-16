from .base import BaseInstaller
from .melodi import MelodiInstaller
from .postgresql import PostgreSQLInstaller
from .redis import RedisInstaller
from .pgadmin import PgAdminInstaller

__all__ = [
    "BaseInstaller",
    "MelodiInstaller",
    "PostgreSQLInstaller",
    "RedisInstaller",
    "PgAdminInstaller"
]
