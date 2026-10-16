"""
PostgreSQLService: Service definition for PostgreSQL Relational Database.
"""

from typing import Dict, Any, List
from app.services.base import BaseService
from app.system.systemd_manager import SystemdManager
from app.system.package_manager import PackageManager
from app.remote.executor import Executor

class PostgreSQLService(BaseService):
    def __init__(self):
        super().__init__(
            name="postgresql",
            display_name="PostgreSQL Database",
            description="Système de gestion de base de données relationnelle objet pour MELODI ERP.",
            port=5432
        )

    async def is_installed(self, executor: Executor) -> bool:
        return await PackageManager.is_installed(executor, "postgresql") or await SystemdManager.is_installed(executor, "postgresql")

    async def status(self, executor: Executor) -> Dict[str, Any]:
        installed = await self.is_installed(executor)
        active = await SystemdManager.is_active(executor, "postgresql") if installed else False
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "port": self.port,
            "is_installed": installed,
            "is_running": active,
            "mode": "native",
            "status_text": "● Running" if active else ("○ Stopped" if installed else "⚠ Not Installed")
        }

    async def start(self, executor: Executor) -> Dict[str, Any]:
        return await SystemdManager.start(executor, "postgresql")

    async def stop(self, executor: Executor) -> Dict[str, Any]:
        return await SystemdManager.stop(executor, "postgresql")

    async def restart(self, executor: Executor) -> Dict[str, Any]:
        return await SystemdManager.restart(executor, "postgresql")

    async def get_logs(self, executor: Executor, lines: int = 100) -> List[str]:
        return await SystemdManager.get_logs(executor, "postgresql", lines)
