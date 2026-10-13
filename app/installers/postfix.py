"""
PostfixInstaller: Automated installer and basic configuration for Postfix MTA.
Can install natively (system package) or via Docker.
"""

from app.installers.base import BaseInstaller
from app.remote.executor import Executor
from app.core.task_manager import TaskProgress
from app.system.package_manager import PackageManager
from app.system.systemd_manager import SystemdManager
from app.system.docker_manager import DockerManager

class PostfixInstaller(BaseInstaller):
    def __init__(self):
        super().__init__(name="postfix", display_name="Postfix Mail Server")

    async def install(self, executor: Executor, task: TaskProgress, **kwargs):
        use_docker = kwargs.get("use_docker", False)
        domain = kwargs.get("domain", "localhost")
        relayhost = kwargs.get("relayhost", "")

        if use_docker:
            await self._install_docker(executor, task, domain, relayhost)
        else:
            await self._install_native(executor, task, domain, relayhost)

    async def _install_native(self, executor: Executor, task: TaskProgress, domain: str, relayhost: str):
        task.update(15, "Vérification de l'installation de Postfix...")
        if await PackageManager.is_installed(executor, "postfix"):
            task.update(30, "Postfix est déjà installé. Mise à jour de la configuration...")
        else:
            task.update(25, "Pré-configuration debconf pour installation silencieuse non-interactive...")
            debconf_cmds = (
                f"echo 'postfix postfix/mailname string {domain}' | debconf-set-selections && "
                "echo 'postfix postfix/main_mailer_type string \"Internet Site\"' | debconf-set-selections"
            )
            await executor.run_sudo(debconf_cmds)

            task.update(45, "Installation du paquet système postfix et mailutils...")
            code, _, stderr = await executor.run_sudo("DEBIAN_FRONTEND=noninteractive apt-get install -y postfix mailutils")
            if code != 0:
                task.fail(f"Échec de l'installation de Postfix: {stderr.strip()}")
                return

        task.update(70, "Configuration de postfix (postconf)...")
        cmds = [
            f"postconf -e 'myhostname = {domain}'",
            "postconf -e 'inet_interfaces = loopback-only'",
            "postconf -e 'mydestination = $myhostname, localhost.$mydomain, localhost'",
        ]
        if relayhost:
            cmds.append(f"postconf -e 'relayhost = {relayhost}'")

        code, _, stderr = await executor.run_sudo(" && ".join(cmds))
        if code != 0:
            task.fail(f"Erreur de configuration postconf: {stderr.strip()}")
            return

        task.update(85, "Démarrage et activation du service systemd 'postfix'...")
        start_res = await SystemdManager.start(executor, "postfix")
        if not start_res["success"]:
            # On tente restart
            await SystemdManager.restart(executor, "postfix")

        task.complete("Serveur Postfix installé et configuré avec succès (envoi local / relais) !")

    async def _install_docker(self, executor: Executor, task: TaskProgress, domain: str, relayhost: str):
        task.update(15, "Vérification de la disponibilité de Docker...")
        if not await DockerManager.is_running(executor):
            task.fail("Docker n'est pas installé ou n'est pas actif sur le serveur cible.")
            return

        task.update(40, "Déploiement du conteneur Postfix (boky/postfix)...")
        env_vars = {
            "ALLOWED_NETWORKS": "127.0.0.1/32,172.16.0.0/12,192.168.0.0/16,10.0.0.0/8"
        }
        if relayhost:
            env_vars["RELAYHOST"] = relayhost

        res = await DockerManager.run_container(
            executor=executor,
            name="melodi_postfix",
            image="boky/postfix:latest",
            ports={"25": "587"},
            env=env_vars
        )

        if not res["success"]:
            task.fail(f"Échec du déploiement conteneur Postfix: {res['message']}")
            return

        task.complete("Conteneur Postfix déployé et opérationnel sur le port 25 !")
