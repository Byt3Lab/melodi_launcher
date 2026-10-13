"""
PostgreSQLService: Service definition for PostgreSQL Relational Database.
Supports both native systemd service and Docker container runtime.
"""

from typing import Dict, Any, List
from app.services.base import BaseService
from app.system.systemd_manager import SystemdManager
from app.system.package_manager import PackageManager
from app.system.docker_manager import DockerManager
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
        c_status = await DockerManager.container_status(executor, "melodi_postgres")
        if c_status.get("exists", False):
            return True
        return await PackageManager.is_installed(executor, "postgresql") or await SystemdManager.is_installed(executor, "postgresql")

    async def status(self, executor: Executor) -> Dict[str, Any]:
        c_status = await DockerManager.container_status(executor, "melodi_postgres")
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

        installed = await PackageManager.is_installed(executor, "postgresql") or await SystemdManager.is_installed(executor, "postgresql")
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
        c_status = await DockerManager.container_status(executor, "melodi_postgres")
        if c_status.get("exists", False):
            return await DockerManager.start_container(executor, "melodi_postgres")
        return await SystemdManager.start(executor, "postgresql")

    async def stop(self, executor: Executor) -> Dict[str, Any]:
        c_status = await DockerManager.container_status(executor, "melodi_postgres")
        if c_status.get("exists", False):
            return await DockerManager.stop_container(executor, "melodi_postgres")
        return await SystemdManager.stop(executor, "postgresql")

    async def restart(self, executor: Executor) -> Dict[str, Any]:
        c_status = await DockerManager.container_status(executor, "melodi_postgres")
        if c_status.get("exists", False):
            return await DockerManager.restart_container(executor, "melodi_postgres")
        return await SystemdManager.restart(executor, "postgresql")

    async def get_logs(self, executor: Executor, lines: int = 100) -> List[str]:
        c_status = await DockerManager.container_status(executor, "melodi_postgres")
        if c_status.get("exists", False):
            return await DockerManager.get_logs(executor, "melodi_postgres", lines)
        return await SystemdManager.get_logs(executor, "postgresql", lines)
