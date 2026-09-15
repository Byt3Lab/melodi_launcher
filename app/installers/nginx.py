"""
NginxInstaller: Automated step-by-step installer for Nginx Web Server.
"""

from app.installers.base import BaseInstaller
from app.remote.executor import Executor
from app.core.task_manager import TaskProgress
from app.system.package_manager import PackageManager
from app.system.systemd_manager import SystemdManager

class NginxInstaller(BaseInstaller):
    def __init__(self):
        super().__init__(name="nginx", display_name="Nginx Web Server")

    async def install(self, executor: Executor, task: TaskProgress):
        task.update(10, "Vérification des prérequis système...")
        if await PackageManager.is_installed(executor, "nginx"):
            task.complete("Nginx est déjà installé sur le système.")
            return

        task.update(35, "Installation du paquet apt 'nginx'...")
        res = await PackageManager.install(executor, "nginx")
        if not res["success"]:
            task.fail(f"Échec d'installation du paquet apt: {res['stderr']}")
            return

        task.update(70, "Test de la configuration Nginx (nginx -t)...")
        code, stdout, stderr = await executor.run_sudo("nginx -t")
        if code != 0:
            task.fail(f"Configuration Nginx invalide: {stderr}")
            return

        task.update(85, "Démarrage du service systemd 'nginx'...")
        start_res = await SystemdManager.start(executor, "nginx")
        if not start_res["success"]:
            task.fail(start_res["message"])
            return

        task.complete("Nginx Web Server installé et démarré avec succès !")
