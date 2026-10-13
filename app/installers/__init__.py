from .base import BaseInstaller
from .melodi import MelodiInstaller
from .postgresql import PostgreSQLInstaller
from .redis import RedisInstaller
from .nginx import NginxInstaller
from .docker import DockerInstaller
from .minio import MinioInstaller
from .pgadmin import PgAdminInstaller
from .postfix import PostfixInstaller

__all__ = [
    "BaseInstaller",
    "MelodiInstaller",
    "PostgreSQLInstaller",
    "RedisInstaller",
    "NginxInstaller",
    "DockerInstaller",
    "MinioInstaller",
    "PgAdminInstaller",
    "PostfixInstaller"
]
