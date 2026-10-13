"""
DockerService: Service representation for Docker daemon.
"""

from typing import Dict, Any, List
from app.services.base import BaseService
from app.system.docker_manager import DockerManager
from app.system.systemd_manager import SystemdManager
from app.remote.executor import Executor

class DockerService(BaseService):
    def __init__(self):
        super().__init__(
            name="docker",
            display_name="Docker Engine",
            description="Plateforme de conteneurisation pour exécuter des services isolés.",
            port=0
        )

    async def is_installed(self, executor: Executor) -> bool:
        return await DockerManager.is_installed(executor)

    async def status(self, executor: Executor) -> Dict[str, Any]:
        installed = await self.is_installed(executor)
        active = await DockerManager.is_running(executor) if installed else False
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
        return await SystemdManager.start(executor, "docker")

    async def stop(self, executor: Executor) -> Dict[str, Any]:
        return await SystemdManager.stop(executor, "docker")

    async def restart(self, executor: Executor) -> Dict[str, Any]:
        return await SystemdManager.restart(executor, "docker")

    async def get_logs(self, executor: Executor, lines: int = 100) -> List[str]:
        return await SystemdManager.get_logs(executor, "docker", lines)
