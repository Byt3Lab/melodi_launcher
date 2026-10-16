"""
RedisService: Service definition for Redis In-Memory Data Store.
"""

from typing import Dict, Any, List
from app.services.base import BaseService
from app.system.systemd_manager import SystemdManager
from app.system.package_manager import PackageManager
from app.remote.executor import Executor

class RedisService(BaseService):
    def __init__(self):
        super().__init__(
            name="redis",
            display_name="Redis In-Memory Data Store",
            description="Serveur de cache et courtier de messages rapide en mémoire.",
            port=6379
        )

    async def is_installed(self, executor: Executor) -> bool:
        return await PackageManager.is_installed(executor, "redis-server") or await SystemdManager.is_installed(executor, "redis-server")

    async def status(self, executor: Executor) -> Dict[str, Any]:
        installed = await self.is_installed(executor)
        active = await SystemdManager.is_active(executor, "redis-server") if installed else False
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
        return await SystemdManager.start(executor, "redis-server")

    async def stop(self, executor: Executor) -> Dict[str, Any]:
        return await SystemdManager.stop(executor, "redis-server")

    async def restart(self, executor: Executor) -> Dict[str, Any]:
        return await SystemdManager.restart(executor, "redis-server")

    async def get_logs(self, executor: Executor, lines: int = 100) -> List[str]:
        return await SystemdManager.get_logs(executor, "redis-server", lines)
