"""
PostfixService: Service definition for Postfix Mail Transfer Agent.
Supports both systemd native and Docker container runtime.
"""

from typing import Dict, Any, List
from app.services.base import BaseService
from app.system.systemd_manager import SystemdManager
from app.system.package_manager import PackageManager
from app.system.docker_manager import DockerManager
from app.remote.executor import Executor

class PostfixService(BaseService):
    def __init__(self):
        super().__init__(
            name="postfix",
            display_name="Postfix Mail Server",
            description="Agent de transfert de courrier (MTA) pour l'envoi d'emails transactionnels.",
            port=25
        )

    async def _is_docker_running(self, executor: Executor) -> bool:
        c_status = await DockerManager.container_status(executor, "melodi_postfix")
        return c_status.get("running", False)

    async def is_installed(self, executor: Executor) -> bool:
        native = await PackageManager.is_installed(executor, "postfix") or await SystemdManager.is_installed(executor, "postfix")
        if native:
            return True
        c_status = await DockerManager.container_status(executor, "melodi_postfix")
        return c_status.get("exists", False)

    async def status(self, executor: Executor) -> Dict[str, Any]:
        c_status = await DockerManager.container_status(executor, "melodi_postfix")
        if c_status.get("exists", False):
            is_running = c_status.get("running", False)
            return {
                "name": self.name,
                "display_name": self.display_name,
                "description": self.description,
                "port": self.port,
                "is_installed": True,
                "is_running": is_running,
                "mode": "docker",
                "status_text": "● Running (Docker)" if is_running else "○ Stopped (Docker)"
            }

        installed = await PackageManager.is_installed(executor, "postfix") or await SystemdManager.is_installed(executor, "postfix")
        active = await SystemdManager.is_active(executor, "postfix") if installed else False
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
        c_status = await DockerManager.container_status(executor, "melodi_postfix")
        if c_status.get("exists", False):
            return await DockerManager.start_container(executor, "melodi_postfix")
        return await SystemdManager.start(executor, "postfix")

    async def stop(self, executor: Executor) -> Dict[str, Any]:
        c_status = await DockerManager.container_status(executor, "melodi_postfix")
        if c_status.get("exists", False):
            return await DockerManager.stop_container(executor, "melodi_postfix")
        return await SystemdManager.stop(executor, "postfix")

    async def restart(self, executor: Executor) -> Dict[str, Any]:
        c_status = await DockerManager.container_status(executor, "melodi_postfix")
        if c_status.get("exists", False):
            return await DockerManager.restart_container(executor, "melodi_postfix")
        return await SystemdManager.restart(executor, "postfix")

    async def get_logs(self, executor: Executor, lines: int = 100) -> List[str]:
        c_status = await DockerManager.container_status(executor, "melodi_postfix")
        if c_status.get("exists", False):
            return await DockerManager.get_logs(executor, "melodi_postfix", lines)
        return await SystemdManager.get_logs(executor, "postfix", lines)
