"""
MelodiWebsocketService: Service definition for MELODI WebSocket Server (supports Local Subprocess & Remote Systemd).
"""

import os
from typing import Dict, Any, List
from app.services.base import BaseService
from app.system.systemd_manager import SystemdManager
from app.remote.executor import Executor
from app.remote.local_executor import LocalExecutor
from app.services.process_manager import ProcessManager
from app.config.settings import SettingsManager

class MelodiWebsocketService(BaseService):
    def __init__(self, settings: SettingsManager, process_manager: ProcessManager):
        super().__init__(
            name="melodi_websocket",
            display_name="MELODI WebSocket",
            description="Serveur WebSocket temps réel pour les notifications et événements de MELODI ERP.",
            port=8001
        )
        self.settings = settings
        self.process_manager = process_manager

    def _get_command_and_cwd(self) -> tuple[list[str], str]:
        ws_cfg = self.settings.get("melodi_websocket") or {}
        melodi_cfg = self.settings.get("melodi") or {}

        path = ws_cfg.get("path") or melodi_cfg.get("path")
        cwd = path if (path and os.path.exists(path)) else self.settings.get_melodi_working_dir()

        command = list(ws_cfg.get("command", ["python3", "websocket_server.py"]))
        python_bin = ws_cfg.get("python") or melodi_cfg.get("python")

        if python_bin and os.path.exists(python_bin) and len(command) > 0 and command[0] in ["python", "python3"]:
            command = [python_bin] + command[1:]

        return command, cwd

    async def is_installed(self, executor: Executor) -> bool:
        if isinstance(executor, LocalExecutor):
            return True
        return await SystemdManager.is_installed(executor, "melodi-websocket")

    async def status(self, executor: Executor) -> Dict[str, Any]:
        port = self.settings.get("melodi_websocket", "port", 8001)
        if isinstance(executor, LocalExecutor):
            proc_info = await self.process_manager.get_status_info()
            running = proc_info["is_running"]
            if not running and await SystemdManager.is_installed(executor, "melodi-websocket"):
                running = await SystemdManager.is_active(executor, "melodi-websocket")
            return {
                "name": self.name,
                "display_name": self.display_name,
                "description": self.description,
                "port": port,
                "is_installed": True,
                "is_running": running,
                "mode": "local",
                "pid": proc_info["pid"],
                "uptime_seconds": proc_info["uptime_seconds"],
                "uptime_formatted": proc_info["uptime_formatted"],
                "status_text": "● Running" if running else "○ Stopped"
            }

        installed = await self.is_installed(executor)
        active = await SystemdManager.is_active(executor, "melodi-websocket") if installed else False
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "port": port,
            "is_installed": installed,
            "is_running": active,
            "mode": "systemd",
            "pid": None,
            "uptime_seconds": 0,
            "uptime_formatted": "systemd",
            "status_text": "● Running" if active else ("○ Stopped" if installed else "⚠ Not Installed")
        }

    async def start(self, executor: Executor) -> Dict[str, Any]:
        if isinstance(executor, LocalExecutor):
            if await SystemdManager.is_installed(executor, "melodi-websocket"):
                return await SystemdManager.start(executor, "melodi-websocket")
            command, cwd = self._get_command_and_cwd()
            return await self.process_manager.start(command=command, cwd=cwd)
        else:
            return await SystemdManager.start(executor, "melodi-websocket")

    async def stop(self, executor: Executor) -> Dict[str, Any]:
        if isinstance(executor, LocalExecutor):
            if await self.process_manager.is_running():
                return await self.process_manager.stop()
            if await SystemdManager.is_installed(executor, "melodi-websocket"):
                return await SystemdManager.stop(executor, "melodi-websocket")
            return await self.process_manager.stop()
        else:
            return await SystemdManager.stop(executor, "melodi-websocket")

    async def restart(self, executor: Executor) -> Dict[str, Any]:
        if isinstance(executor, LocalExecutor):
            if await SystemdManager.is_installed(executor, "melodi-websocket") and not await self.process_manager.is_running():
                return await SystemdManager.restart(executor, "melodi-websocket")
            command, cwd = self._get_command_and_cwd()
            return await self.process_manager.restart(command=command, cwd=cwd)
        else:
            return await SystemdManager.restart(executor, "melodi-websocket")

    async def get_logs(self, executor: Executor, lines: int = 100) -> List[str]:
        if isinstance(executor, LocalExecutor):
            log_mgr = self.process_manager.log_manager
            return log_mgr.get_recent_logs(lines=lines)
        else:
            return await SystemdManager.get_logs(executor, "melodi-websocket", lines)
