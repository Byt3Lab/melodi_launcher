"""
SystemdManager: Abstraction for managing Linux systemd services (start, stop, status, logs).
"""

from typing import Dict, Any, List
from app.remote.executor import Executor

class SystemdManager:
    @staticmethod
    async def is_active(executor: Executor, service_name: str) -> bool:
        """Vérifie si une unité systemd est active (systemctl is-active)."""
        code, stdout, _ = await executor.run(f"systemctl is-active {service_name}")
        return code == 0 and stdout.strip() == "active"

    @staticmethod
    async def is_installed(executor: Executor, service_name: str) -> bool:
        """Vérifie si une unité systemd existe sur le système."""
        code, stdout, _ = await executor.run(f"systemctl list-unit-files {service_name}.service")
        return code == 0 and service_name in stdout

    @staticmethod
    async def start(executor: Executor, service_name: str) -> Dict[str, Any]:
        """Démarrer un service systemd via run_sudo."""
        code, stdout, stderr = await executor.run_sudo(f"systemctl start {service_name}")
        return {
            "success": code == 0,
            "message": f"Service '{service_name}' démarré." if code == 0 else f"Échec au démarrage de '{service_name}': {stderr.strip()}"
        }

    @staticmethod
    async def stop(executor: Executor, service_name: str) -> Dict[str, Any]:
        """Arrêter un service systemd via run_sudo."""
        code, stdout, stderr = await executor.run_sudo(f"systemctl stop {service_name}")
        return {
            "success": code == 0,
            "message": f"Service '{service_name}' arrêté." if code == 0 else f"Échec de l'arrêt de '{service_name}': {stderr.strip()}"
        }

    @staticmethod
    async def restart(executor: Executor, service_name: str) -> Dict[str, Any]:
        """Redémarrer un service systemd via run_sudo."""
        code, stdout, stderr = await executor.run_sudo(f"systemctl restart {service_name}")
        return {
            "success": code == 0,
            "message": f"Service '{service_name}' redémarré." if code == 0 else f"Échec du redémarrage de '{service_name}': {stderr.strip()}"
        }

    @staticmethod
    async def get_logs(executor: Executor, service_name: str, lines: int = 100) -> List[str]:
        """Extrait les logs récents d'un service via journalctl."""
        code, stdout, _ = await executor.run(f"journalctl -u {service_name} -n {lines} --no-pager")
        if code == 0:
            return stdout.splitlines()
        return [f"Impossible d'extraire les logs journalctl pour {service_name}"]
