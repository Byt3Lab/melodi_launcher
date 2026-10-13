"""
RedisInstaller: Automated installer for Redis In-Memory Data Store.
Supports both native apt package and Docker deployment.
"""

from app.installers.base import BaseInstaller
from app.remote.executor import Executor
from app.core.task_manager import TaskProgress
from app.system.package_manager import PackageManager
from app.system.systemd_manager import SystemdManager
from app.system.docker_manager import DockerManager

class RedisInstaller(BaseInstaller):
    def __init__(self):
        super().__init__(name="redis", display_name="Redis In-Memory Data Store")

    async def install(self, executor: Executor, task: TaskProgress, **kwargs):
        use_docker = kwargs.get("use_docker", False)

        if use_docker:
            await self._install_docker(executor, task)
        else:
            await self._install_native(executor, task)

    async def _install_native(self, executor: Executor, task: TaskProgress):
        task.update(10, "Vérification des prérequis système...")
        if await PackageManager.is_installed(executor, "redis-server"):
            task.complete("Redis Server est déjà installé sur le système.")
            return

        task.update(35, "Installation du paquet système 'redis-server'...")
        res = await PackageManager.install(executor, "redis-server")
        if not res["success"]:
            task.fail(f"Échec d'installation du paquet: {res.get('stderr', '')}")
            return

        task.update(75, "Démarrage et activation du service systemd 'redis-server'...")
        start_res = await SystemdManager.start(executor, "redis-server")
        if not start_res["success"]:
            task.fail(start_res["message"])
            return

        task.complete("Redis natif installé et démarré avec succès !")

    async def _install_docker(self, executor: Executor, task: TaskProgress):
        task.update(15, "Vérification de Docker...")
        if not await DockerManager.is_running(executor):
            task.fail("Docker n'est pas opérationnel sur la machine hôte.")
            return

        task.update(50, "Déploiement du conteneur Redis (redis:alpine)...")
        res = await DockerManager.run_container(
            executor=executor,
            name="melodi_redis",
            image="redis:alpine",
            ports={"6379": "6379"}
        )

        if not res["success"]:
            task.fail(f"Échec du déploiement Docker Redis: {res['message']}")
            return

        task.complete("Redis déployé avec succès via Docker sur le port 6379 !")
