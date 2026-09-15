"""
CeleryService: Service definition for Celery Background Task Worker.
"""

from typing import Dict, Any, List
from app.services.base import BaseService
from app.system.systemd_manager import SystemdManager
from app.remote.executor import Executor

class CeleryService(BaseService):
    def __init__(self):
        super().__init__(
            name="celery",
            display_name="Celery Worker",
            description="Gestionnaire de file d'attente et d'exécution de tâches asynchrones en arrière-plan.",
            port=0
        )

    async def is_installed(self, executor: Executor) -> bool:
        return await SystemdManager.is_installed(executor, "celery")

    async def status(self, executor: Executor) -> Dict[str, Any]:
        installed = await self.is_installed(executor)
        active = await SystemdManager.is_active(executor, "celery") if installed else False
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "port": self.port,
            "is_installed": installed,
            "is_running": active,
            "status_text": "● Running" if active else ("○ Stopped" if installed else "⚠ Not Installed")
        }

    async def start(self, executor: Executor) -> Dict[str, Any]:
        return await SystemdManager.start(executor, "celery")

    async def stop(self, executor: Executor) -> Dict[str, Any]:
        return await SystemdManager.stop(executor, "celery")

    async def restart(self, executor: Executor) -> Dict[str, Any]:
        return await SystemdManager.restart(executor, "celery")

    async def get_logs(self, executor: Executor, lines: int = 100) -> List[str]:
        return await SystemdManager.get_logs(executor, "celery", lines)
