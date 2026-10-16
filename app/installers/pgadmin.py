"""
PgAdminInstaller: Automated installer for pgAdmin 4 (PostgreSQL Web Administration UI).
Installs pgAdmin 4 natively via official apt package.
"""

from app.installers.base import BaseInstaller
from app.remote.executor import Executor
from app.core.task_manager import TaskProgress
from app.system.package_manager import PackageManager

class PgAdminInstaller(BaseInstaller):
    def __init__(self):
        super().__init__(name="pgadmin", display_name="pgAdmin 4 (Web DB Manager)")

    async def install(self, executor: Executor, task: TaskProgress, **kwargs):
        await self._install_native(executor, task)

    async def _install_native(self, executor: Executor, task: TaskProgress):
        task.update(15, "Ajout du dépôt officiel pgAdmin 4 pour Debian/Ubuntu...")
        repo_cmd = (
            "curl -fsS https://www.pgadmin.org/static/packages_pgadmin_org.pub | gpg --dearmor -o /usr/share/keyrings/packages-pgadmin-org.gpg --yes && "
            "echo \"deb [signed-by=/usr/share/keyrings/packages-pgadmin-org.gpg] https://ftp.postgresql.org/pub/pgadmin/pgadmin4/apt/$(. /etc/os-release && echo \"$VERSION_CODENAME\") pgadmin4 main\" | "
            "tee /etc/apt/sources.list.d/pgadmin4.list > /dev/null"
        )
        code, _, stderr = await executor.run_sudo(repo_cmd)
        if code != 0:
            task.fail(f"Échec de configuration du dépôt pgAdmin: {stderr.strip()}")
            return

        task.update(45, "Mise à jour des dépôts apt et installation de pgadmin4-web...")
        await PackageManager.update_index(executor)
        res = await PackageManager.install(executor, "pgadmin4-web")
        if not res["success"]:
            task.fail(f"Échec de l'installation de pgadmin4-web: {res.get('stderr', '')}")
            return

        task.complete("pgAdmin 4 (Web) installé avec succès !")
