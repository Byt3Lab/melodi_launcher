"""
MelodiService: Service definition for MELODI ERP (supports Local, Remote SSH, and Docker).
"""

from typing import Dict, Any, List
from app.services.base import BaseService
from app.system.systemd_manager import SystemdManager
from app.system.docker_manager import DockerManager
from app.remote.executor import Executor
from app.remote.local_executor import LocalExecutor
from app.services.process_manager import ProcessManager
from app.config.settings import SettingsManager

class MelodiService(BaseService):
    def __init__(self, settings: SettingsManager, process_manager: ProcessManager):
        super().__init__(
            name="melodi",
            display_name="MELODI ERP",
            description="Le système ERP principal de l'entreprise MELODI.",
            port=5000
        )
        self.settings = settings
        self.process_manager = process_manager

    async def is_installed(self, executor: Executor) -> bool:
        c_status = await DockerManager.container_status(executor, "melodi_app")
        if c_status.get("exists", False):
            return True
        if isinstance(executor, LocalExecutor):
            return True
        return await SystemdManager.is_installed(executor, "melodi")

    async def status(self, executor: Executor) -> Dict[str, Any]:
        # 1. Vérifier si un conteneur Docker melodi_app existe
        c_status = await DockerManager.container_status(executor, "melodi_app")
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
                "pid": None,
                "uptime_seconds": 0,
                "uptime_formatted": "docker",
                "status_text": "● Running (Docker)" if is_running else "○ Stopped (Docker)"
            }

        # 2. Local Executor standard
        if isinstance(executor, LocalExecutor):
            proc_info = await self.process_manager.get_status_info()
            running = proc_info["is_running"]
            return {
                "name": self.name,
                "display_name": self.display_name,
                "description": self.description,
                "port": self.settings.get("melodi", "port", 5000),
                "is_installed": True,
                "is_running": running,
                "mode": "local",
                "pid": proc_info["pid"],
                "uptime_seconds": proc_info["uptime_seconds"],
                "uptime_formatted": proc_info["uptime_formatted"],
                "status_text": "● Running" if running else "○ Stopped"
            }

        # 3. Serveur distant systemd
        installed = await self.is_installed(executor)
        active = await SystemdManager.is_active(executor, "melodi") if installed else False
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "port": 5000,
            "is_installed": installed,
            "is_running": active,
            "mode": "systemd",
            "pid": None,
            "uptime_seconds": 0,
            "uptime_formatted": "systemd",
            "status_text": "● Running" if active else ("○ Stopped" if installed else "⚠ Not Installed")
        }

    async def start(self, executor: Executor) -> Dict[str, Any]:
        c_status = await DockerManager.container_status(executor, "melodi_app")
        if c_status.get("exists", False):
            return await DockerManager.start_container(executor, "melodi_app")

        if isinstance(executor, LocalExecutor):
            melodi_cfg = self.settings.get("melodi")
            cwd = self.settings.get_melodi_working_dir()
            command = melodi_cfg.get("command", ["python3", "main.py"])
            return await self.process_manager.start(command=command, cwd=cwd)
        else:
            return await SystemdManager.start(executor, "melodi")

    async def stop(self, executor: Executor) -> Dict[str, Any]:
        c_status = await DockerManager.container_status(executor, "melodi_app")
        if c_status.get("exists", False):
            return await DockerManager.stop_container(executor, "melodi_app")

        if isinstance(executor, LocalExecutor):
            return await self.process_manager.stop()
        else:
            return await SystemdManager.stop(executor, "melodi")

    async def restart(self, executor: Executor) -> Dict[str, Any]:
        c_status = await DockerManager.container_status(executor, "melodi_app")
        if c_status.get("exists", False):
            return await DockerManager.restart_container(executor, "melodi_app")

        if isinstance(executor, LocalExecutor):
            melodi_cfg = self.settings.get("melodi")
            cwd = self.settings.get_melodi_working_dir()
            command = melodi_cfg.get("command", ["python3", "main.py"])
            return await self.process_manager.restart(command=command, cwd=cwd)
        else:
            return await SystemdManager.restart(executor, "melodi")

    async def get_logs(self, executor: Executor, lines: int = 100) -> List[str]:
        c_status = await DockerManager.container_status(executor, "melodi_app")
        if c_status.get("exists", False):
            return await DockerManager.get_logs(executor, "melodi_app", lines)

        if isinstance(executor, LocalExecutor):
            log_mgr = self.process_manager.log_manager
            return log_mgr.get_recent_logs(lines=lines)
        else:
            return await SystemdManager.get_logs(executor, "melodi", lines)
