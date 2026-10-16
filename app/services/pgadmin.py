"""
PgAdminService: Service definition for pgAdmin 4.
"""

from typing import Dict, Any, List
from app.services.base import BaseService
from app.system.systemd_manager import SystemdManager
from app.system.package_manager import PackageManager
from app.remote.executor import Executor

class PgAdminService(BaseService):
    def __init__(self):
        super().__init__(
            name="pgadmin",
            display_name="pgAdmin 4 (Web DB)",
            description="Interface d'administration et de gestion web pour bases PostgreSQL.",
            port=5050
        )

    async def is_installed(self, executor: Executor) -> bool:
        return await PackageManager.is_installed(executor, "pgadmin4-web")

    async def status(self, executor: Executor) -> Dict[str, Any]:
        installed = await self.is_installed(executor)
        active = await SystemdManager.is_active(executor, "apache2") if installed else False
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
        return await SystemdManager.start(executor, "apache2")

    async def stop(self, executor: Executor) -> Dict[str, Any]:
        return await SystemdManager.stop(executor, "apache2")

    async def restart(self, executor: Executor) -> Dict[str, Any]:
        return await SystemdManager.restart(executor, "apache2")

    async def get_logs(self, executor: Executor, lines: int = 100) -> List[str]:
        return ["Logs natifs pgAdmin consultables dans /var/log/apache2/ ou /var/log/pgadmin/"]
