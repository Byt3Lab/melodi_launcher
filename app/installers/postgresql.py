"""
PostgreSQLInstaller: Automated installer for PostgreSQL.
Supports both native apt package and Docker deployment.
"""

from app.installers.base import BaseInstaller
from app.remote.executor import Executor
from app.core.task_manager import TaskProgress
from app.system.package_manager import PackageManager
from app.system.systemd_manager import SystemdManager
from app.system.docker_manager import DockerManager

class PostgreSQLInstaller(BaseInstaller):
    def __init__(self):
        super().__init__(name="postgresql", display_name="PostgreSQL Database")

    async def install(self, executor: Executor, task: TaskProgress, **kwargs):
        use_docker = kwargs.get("use_docker", False)
        password = kwargs.get("password", "melodi_db_pass")

        if use_docker:
            await self._install_docker(executor, task, password)
        else:
            await self._install_native(executor, task)

    async def _install_native(self, executor: Executor, task: TaskProgress):
        task.update(10, "Vérification des prérequis système...")
        if await PackageManager.is_installed(executor, "postgresql"):
            task.complete("PostgreSQL est déjà installé sur le système.")
            return

        task.update(30, "Mise à jour des dépôts apt et installation du paquet 'postgresql'...")
        res = await PackageManager.install(executor, "postgresql postgresql-contrib")
        if not res["success"]:
            task.fail(f"Échec d'installation du paquet apt: {res.get('stderr', '')}")
            return

        task.update(75, "Démarrage et activation du service systemd 'postgresql'...")
        start_res = await SystemdManager.start(executor, "postgresql")
        if not start_res["success"]:
            task.fail(start_res["message"])
            return

        task.complete("PostgreSQL natif installé et démarré avec succès !")

    async def _install_docker(self, executor: Executor, task: TaskProgress, password: str):
        task.update(15, "Vérification de Docker...")
        if not await DockerManager.is_running(executor):
            task.fail("Docker n'est pas opérationnel sur la machine hôte.")
            return

        task.update(40, "Préparation du stockage persistant /var/lib/postgresql/docker_data...")
        await executor.run_sudo("mkdir -p /var/lib/postgresql/docker_data")

        task.update(65, "Déploiement du conteneur PostgreSQL...")
        res = await DockerManager.run_container(
            executor=executor,
            name="melodi_postgres",
            image="postgres:16-alpine",
            ports={"5432": "5432"},
            volumes={"/var/lib/postgresql/docker_data": "/var/lib/postgresql/data"},
            env={"POSTGRES_PASSWORD": password, "POSTGRES_USER": "melodi", "POSTGRES_DB": "melodi"}
        )

        if not res["success"]:
            task.fail(f"Échec du déploiement Docker: {res['message']}")
            return

        task.complete("PostgreSQL déployé avec succès via Docker sur le port 5432 !")
