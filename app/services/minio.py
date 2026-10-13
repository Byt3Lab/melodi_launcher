"""
MinioService: Service definition for MinIO Object Storage (S3).
Supports both native systemd service and Docker container runtime.
"""

from typing import Dict, Any, List
from app.services.base import BaseService
from app.system.systemd_manager import SystemdManager
from app.system.docker_manager import DockerManager
from app.remote.executor import Executor

class MinioService(BaseService):
    def __init__(self):
        super().__init__(
            name="minio",
            display_name="MinIO S3 Storage",
            description="Serveur de stockage d'objets haute performance compatible Amazon S3.",
            port=9000
        )

    async def is_installed(self, executor: Executor) -> bool:
        c_status = await DockerManager.container_status(executor, "melodi_minio")
        if c_status.get("exists", False):
            return True
        code, stdout, _ = await executor.run("which minio")
        return code == 0 or await SystemdManager.is_installed(executor, "minio")

    async def status(self, executor: Executor) -> Dict[str, Any]:
        c_status = await DockerManager.container_status(executor, "melodi_minio")
        if c_status.get("exists", False):
            is_running = c_status.get("running", False)
            return {
                "name": self.name,
                "display_name": self.display_name,
                "description": self.description,
                "port": self.port,
                "console_port": 9001,
                "is_installed": True,
                "is_running": is_running,
                "mode": "docker",
                "status_text": "● Running (Docker)" if is_running else "○ Stopped (Docker)"
            }

        installed = await SystemdManager.is_installed(executor, "minio")
        active = await SystemdManager.is_active(executor, "minio") if installed else False
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "port": self.port,
            "console_port": 9001,
            "is_installed": installed,
            "is_running": active,
            "mode": "native",
            "status_text": "● Running" if active else ("○ Stopped" if installed else "⚠ Not Installed")
        }

    async def start(self, executor: Executor) -> Dict[str, Any]:
        c_status = await DockerManager.container_status(executor, "melodi_minio")
        if c_status.get("exists", False):
            return await DockerManager.start_container(executor, "melodi_minio")
        return await SystemdManager.start(executor, "minio")

    async def stop(self, executor: Executor) -> Dict[str, Any]:
        c_status = await DockerManager.container_status(executor, "melodi_minio")
        if c_status.get("exists", False):
            return await DockerManager.stop_container(executor, "melodi_minio")
        return await SystemdManager.stop(executor, "minio")

    async def restart(self, executor: Executor) -> Dict[str, Any]:
        c_status = await DockerManager.container_status(executor, "melodi_minio")
        if c_status.get("exists", False):
            return await DockerManager.restart_container(executor, "melodi_minio")
        return await SystemdManager.restart(executor, "minio")

    async def get_logs(self, executor: Executor, lines: int = 100) -> List[str]:
        c_status = await DockerManager.container_status(executor, "melodi_minio")
        if c_status.get("exists", False):
            return await DockerManager.get_logs(executor, "melodi_minio", lines)
        return await SystemdManager.get_logs(executor, "minio", lines)
