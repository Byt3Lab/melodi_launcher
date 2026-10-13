"""
PgAdminInstaller: Automated installer for pgAdmin 4 (PostgreSQL Web Administration UI).
Supports both Docker deployment (dpage/pgadmin4) and native apt package.
"""

from app.installers.base import BaseInstaller
from app.remote.executor import Executor
from app.core.task_manager import TaskProgress
from app.system.package_manager import PackageManager
from app.system.systemd_manager import SystemdManager
from app.system.docker_manager import DockerManager

class PgAdminInstaller(BaseInstaller):
    def __init__(self):
        super().__init__(name="pgadmin", display_name="pgAdmin 4 (Web DB Manager)")

    async def install(self, executor: Executor, task: TaskProgress, **kwargs):
        use_docker = kwargs.get("use_docker", True)
        email = kwargs.get("email", "admin@melodi.local")
        password = kwargs.get("password", "admin")

        if use_docker:
            await self._install_docker(executor, task, email, password)
        else:
            await self._install_native(executor, task)

    async def _install_docker(self, executor: Executor, task: TaskProgress, email: str, password: str):
        task.update(15, "Vérification de la disponibilité de Docker...")
        if not await DockerManager.is_running(executor):
            task.fail("Docker n'est pas opérationnel sur la machine hôte.")
            return

        task.update(40, "Préparation du volume de données pgAdmin...")
        await executor.run_sudo("mkdir -p /var/lib/pgadmin && chmod 777 /var/lib/pgadmin")

        task.update(65, "Déploiement du conteneur pgAdmin 4 (dpage/pgadmin4)...")
        res = await DockerManager.run_container(
            executor=executor,
            name="melodi_pgadmin",
            image="dpage/pgadmin4:latest",
            ports={"5050": "80"},
            volumes={"/var/lib/pgadmin": "/var/lib/pgadmin"},
            env={
                "PGADMIN_DEFAULT_EMAIL": email,
                "PGADMIN_DEFAULT_PASSWORD": password
            }
        )

        if not res["success"]:
            task.fail(f"Échec du déploiement Docker pgAdmin: {res['message']}")
            return

        task.complete("pgAdmin 4 déployé avec succès sur le port 5050 !")

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
