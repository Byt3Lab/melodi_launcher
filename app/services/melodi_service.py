"""
MelodiService: Service implementation specifically for MELODI ERP.
"""

import os
from typing import Dict, Any
from app.services.base_service import BaseService
from app.services.process_manager import ProcessManager
from app.config.settings import SettingsManager

class MelodiService(BaseService):
    def __init__(self, settings: SettingsManager, process_manager: ProcessManager):
        super().__init__(
            name="melodi",
            display_name="MELODI ERP",
            description="Le système ERP principal de l'entreprise MELODI."
        )
        self.settings = settings
        self.process_manager = process_manager

    def _get_execution_command_and_cwd(self) -> tuple[list[str], str]:
        """Détermine la commande complète et le répertoire de travail selon les réglages."""
        melodi_cfg = self.settings.get("melodi")
        cwd = self.settings.get_melodi_working_dir()

        command = melodi_cfg.get("command", ["python3", "main.py"])
        python_bin = melodi_cfg.get("python")

        # Remplacement de l'interpréteur python si un venv spécifique est configuré
        if python_bin and os.path.exists(python_bin) and len(command) > 0 and command[0] in ["python", "python3"]:
            command = [python_bin] + command[1:]

        return command, cwd

    async def start(self) -> Dict[str, Any]:
        """Démarre le service MELODI ERP."""
        command, cwd = self._get_execution_command_and_cwd()
        return await self.process_manager.start(command=command, cwd=cwd)

    async def stop(self) -> Dict[str, Any]:
        """Arrête le service MELODI ERP."""
        return await self.process_manager.stop()

    async def restart(self) -> Dict[str, Any]:
        """Redémarre le service MELODI ERP."""
        command, cwd = self._get_execution_command_and_cwd()
        return await self.process_manager.restart(command=command, cwd=cwd)

    async def status(self) -> Dict[str, Any]:
        """Retourne le statut complet du service MELODI ERP."""
        proc_info = await self.process_manager.get_status_info()
        melodi_cfg = self.settings.get("melodi")
        
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "is_running": proc_info["is_running"],
            "pid": proc_info["pid"],
            "uptime_seconds": proc_info["uptime_seconds"],
            "uptime_formatted": proc_info["uptime_formatted"],
            "port": melodi_cfg.get("port", 5000),
            "command": " ".join(self._get_execution_command_and_cwd()[0]),
            "working_dir": self._get_execution_command_and_cwd()[1]
        }
