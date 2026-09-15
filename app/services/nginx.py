"""
NginxService: Service definition for Nginx Reverse Proxy & HTTP Web Server.
"""

from typing import Dict, Any, List
from app.services.base import BaseService
from app.system.systemd_manager import SystemdManager
from app.system.package_manager import PackageManager
from app.remote.executor import Executor

class NginxService(BaseService):
    def __init__(self):
        super().__init__(
            name="nginx",
            display_name="Nginx Web Server / Reverse Proxy",
            description="Serveur web et proxy inverse HTTP performant.",
            port=80
        )

    async def is_installed(self, executor: Executor) -> bool:
        return await PackageManager.is_installed(executor, "nginx") or await SystemdManager.is_installed(executor, "nginx")

    async def status(self, executor: Executor) -> Dict[str, Any]:
        installed = await self.is_installed(executor)
        active = await SystemdManager.is_active(executor, "nginx") if installed else False
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "port": self.port,
            "is_installed": installed,
            "is_running": active,
            "status_text": "● Running" if active else ("○ Stopped" if installed else "⚠ Not Installed")
        }

    async def test_config(self, executor: Executor) -> Dict[str, Any]:
        """Exécute 'nginx -t' pour valider les fichiers de configuration avant reload."""
        code, stdout, stderr = await executor.run_sudo("nginx -t")
        return {
            "success": code == 0,
            "output": stdout + stderr,
            "message": "Configuration Nginx valide." if code == 0 else "Erreur de syntaxe dans la configuration Nginx."
        }

    async def start(self, executor: Executor) -> Dict[str, Any]:
        return await SystemdManager.start(executor, "nginx")

    async def stop(self, executor: Executor) -> Dict[str, Any]:
        return await SystemdManager.stop(executor, "nginx")

    async def restart(self, executor: Executor) -> Dict[str, Any]:
        test_res = await self.test_config(executor)
        if not test_res["success"]:
            return {"success": False, "message": f"Impossible de redémarrer Nginx: {test_res['message']}"}
        return await SystemdManager.restart(executor, "nginx")

    async def get_logs(self, executor: Executor, lines: int = 100) -> List[str]:
        return await SystemdManager.get_logs(executor, "nginx", lines)
