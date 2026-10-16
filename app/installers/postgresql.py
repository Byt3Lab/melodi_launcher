"""
PostgreSQLInstaller: Automated installer for PostgreSQL.
Installs PostgreSQL natively via system package manager and systemd.
"""

from app.installers.base import BaseInstaller
from app.remote.executor import Executor
from app.core.task_manager import TaskProgress
from app.system.package_manager import PackageManager
from app.system.systemd_manager import SystemdManager

class PostgreSQLInstaller(BaseInstaller):
    def __init__(self):
        super().__init__(name="postgresql", display_name="PostgreSQL Database")

    async def install(self, executor: Executor, task: TaskProgress, **kwargs):
        await self._install_native(executor, task)

    async def _install_native(self, executor: Executor, task: TaskProgress):
        task.update(10, "Vérification des prérequis système...")
        if await PackageManager.is_installed(executor, "postgresql"):
            task.complete("PostgreSQL est déjà installé sur le système.")
            return

        task.update(30, "Mise à jour des dépôts apt et installation du paquet 'postgresql'...")
        res = await PackageManager.install(executor, "postgresql postgresql-contrib", on_output=task.append_log)
        if not res["success"]:
            task.fail(f"Échec d'installation du paquet apt: {res.get('stderr', '')}")
            return

        task.update(75, "Démarrage et activation du service systemd 'postgresql'...")
        start_res = await SystemdManager.start(executor, "postgresql", on_output=task.append_log)
        if not start_res["success"]:
            task.fail(start_res["message"])
            return

        task.complete("PostgreSQL natif installé et démarré avec succès !")
