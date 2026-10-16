"""
RedisInstaller: Automated installer for Redis In-Memory Data Store.
Installs Redis Server natively via system package manager and systemd.
"""

from app.installers.base import BaseInstaller
from app.remote.executor import Executor
from app.core.task_manager import TaskProgress
from app.system.package_manager import PackageManager
from app.system.systemd_manager import SystemdManager

class RedisInstaller(BaseInstaller):
    def __init__(self):
        super().__init__(name="redis", display_name="Redis In-Memory Data Store")

    async def install(self, executor: Executor, task: TaskProgress, **kwargs):
        await self._install_native(executor, task)

    async def _install_native(self, executor: Executor, task: TaskProgress):
        task.update(10, "Vérification des prérequis système...")
        if await PackageManager.is_installed(executor, "redis-server"):
            task.complete("Redis Server est déjà installé sur le système.")
            return

        task.update(35, "Installation du paquet système 'redis-server'...")
        res = await PackageManager.install(executor, "redis-server", on_output=task.append_log)
        if not res["success"]:
            task.fail(f"Échec d'installation du paquet: {res.get('stderr', '')}")
            return

        task.update(75, "Démarrage et activation du service systemd 'redis-server'...")
        start_res = await SystemdManager.start(executor, "redis-server", on_output=task.append_log)
        if not start_res["success"]:
            task.fail(start_res["message"])
            return

        task.complete("Redis natif installé et démarré avec succès !")
