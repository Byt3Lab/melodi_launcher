"""
DockerInstaller: Automated step-by-step installer for Docker Engine.
Supports Debian / Ubuntu via official docker apt repository.
"""

from app.installers.base import BaseInstaller
from app.remote.executor import Executor
from app.core.task_manager import TaskProgress
from app.system.package_manager import PackageManager
from app.system.docker_manager import DockerManager

class DockerInstaller(BaseInstaller):
    def __init__(self):
        super().__init__(name="docker", display_name="Docker Engine")

    async def install(self, executor: Executor, task: TaskProgress, **kwargs):
        task.update(10, "Vérification de la présence de Docker...")
        if await DockerManager.is_installed(executor):
            task.complete("Docker Engine est déjà installé sur le système.")
            return

        task.update(25, "Installation des dépendances de base (ca-certificates, curl, gnupg)...")
        res = await PackageManager.install(executor, "ca-certificates curl gnupg lsb-release")
        if not res["success"]:
            task.fail(f"Échec d'installation des dépendances: {res.get('stderr', '')}")
            return

        task.update(45, "Configuration du keyring et du dépôt officiel Docker...")
        setup_repo_cmd = (
            "install -m 0755 -d /etc/apt/keyrings && "
            "curl -fsSL https://download.docker.com/linux/$(. /etc/os-release && echo \"$ID\")/gpg -o /etc/apt/keyrings/docker.asc && "
            "chmod a+r /etc/apt/keyrings/docker.asc && "
            "echo \"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/$(. /etc/os-release && echo \"$ID\") $(. /etc/os-release && echo \"$VERSION_CODENAME\") stable\" | "
            "tee /etc/apt/sources.list.d/docker.list > /dev/null"
        )
        code, _, stderr = await executor.run_sudo(setup_repo_cmd)
        if code != 0:
            task.update(50, "Repli sur l'installation du paquet distribution 'docker.io'...")
            res_io = await PackageManager.install(executor, "docker.io docker-compose-v2")
            if not res_io["success"]:
                task.fail(f"Échec de l'installation de docker.io: {res_io.get('stderr', '')}")
                return
        else:
            task.update(65, "Mise à jour des dépôts et installation de docker-ce...")
            await PackageManager.update_index(executor)
            res_ce = await PackageManager.install(executor, "docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin")
            if not res_ce["success"]:
                task.fail(f"Échec de l'installation de docker-ce: {res_ce.get('stderr', '')}")
                return

        task.update(85, "Démarrage et activation du service Docker...")
        await executor.run_sudo("systemctl enable --now docker")

        task.complete("Docker Engine installé et opérationnel avec succès !")
