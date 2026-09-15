"""
RedisInstaller: Automated step-by-step installer for Redis Server.
"""

from app.installers.base import BaseInstaller
from app.remote.executor import Executor
from app.core.task_manager import TaskProgress
from app.system.package_manager import PackageManager
from app.system.systemd_manager import SystemdManager

class RedisInstaller(BaseInstaller):
    def __init__(self):
        super().__init__(name="redis", display_name="Redis Server")

    async def install(self, executor: Executor, task: TaskProgress):
        task.update(10, "Vérification des prérequis système...")
        if await PackageManager.is_installed(executor, "redis-server"):
            task.complete("Redis Server est déjà installé sur le système.")
            return

        task.update(35, "Installation du paquet apt 'redis-server'...")
        res = await PackageManager.install(executor, "redis-server")
        if not res["success"]:
            task.fail(f"Échec d'installation du paquet apt: {res['stderr']}")
            return

        task.update(80, "Démarrage du service systemd 'redis-server'...")
        start_res = await SystemdManager.start(executor, "redis-server")
        if not start_res["success"]:
            task.fail(start_res["message"])
            return

        task.complete("Redis Server installé et activé avec succès !")
