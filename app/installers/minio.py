"""
MinioInstaller: Automated installer for MinIO Object Storage (S3 compatible).
Supports both Docker deployment and native standalone binary deployment.
"""

from app.installers.base import BaseInstaller
from app.remote.executor import Executor
from app.core.task_manager import TaskProgress
from app.system.systemd_manager import SystemdManager
from app.system.docker_manager import DockerManager

SYSTEMD_MINIO_TEMPLATE = """[Unit]
Description=MinIO Object Storage S3
Documentation=https://docs.min.io
Wants=network-online.target
After=network-online.target

[Service]
WorkingDirectory=/usr/local/
User=root
Group=root
EnvironmentFile=-/etc/default/minio
ExecStart=/usr/local/bin/minio server /var/lib/minio/data --address ":9000" --console-address ":9001"
Restart=always
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
"""

class MinioInstaller(BaseInstaller):
    def __init__(self):
        super().__init__(name="minio", display_name="MinIO Object Storage (S3)")

    async def install(self, executor: Executor, task: TaskProgress, **kwargs):
        use_docker = kwargs.get("use_docker", True)
        root_user = kwargs.get("root_user", "minioadmin")
        root_password = kwargs.get("root_password", "minioadmin")

        if use_docker:
            await self._install_docker(executor, task, root_user, root_password)
        else:
            await self._install_native(executor, task, root_user, root_password)

    async def _install_docker(self, executor: Executor, task: TaskProgress, user: str, password: str):
        task.update(15, "Vérification de la disponibilité de Docker...")
        if not await DockerManager.is_running(executor):
            task.fail("Docker n'est pas opérationnel sur la machine hôte.")
            return

        task.update(35, "Création du dossier de stockage /var/lib/minio/data...")
        await executor.run_sudo("mkdir -p /var/lib/minio/data")

        task.update(55, "Déploiement du conteneur MinIO (minio/minio)...")
        res = await DockerManager.run_container(
            executor=executor,
            name="melodi_minio",
            image="quay.io/minio/minio:latest",
            ports={"9000": "9000", "9001": "9001"},
            volumes={"/var/lib/minio/data": "/data"},
            env={"MINIO_ROOT_USER": user, "MINIO_ROOT_PASSWORD": password},
            cmd_args='server /data --console-address ":9001"'
        )

        if not res["success"]:
            task.fail(f"Échec de l'installation MinIO Docker: {res['message']}")
            return

        task.complete("MinIO déployé avec succès via Docker (API S3: port 9000, Console: port 9001) !")

    async def _install_native(self, executor: Executor, task: TaskProgress, user: str, password: str):
        task.update(15, "Téléchargement du binaire MinIO officiel pour Linux x86_64...")
        cmd_dl = "curl -fsSL https://dl.min.io/server/minio/release/linux-amd64/minio -o /usr/local/bin/minio && chmod +x /usr/local/bin/minio"
        code, _, stderr = await executor.run_sudo(cmd_dl)
        if code != 0:
            task.fail(f"Échec du téléchargement du binaire MinIO: {stderr.strip()}")
            return

        task.update(45, "Création du dossier de stockage et configuration de l'environnement...")
        await executor.run_sudo("mkdir -p /var/lib/minio/data")
        env_content = f"MINIO_ROOT_USER={user}\\nMINIO_ROOT_PASSWORD={password}\\n"
        await executor.run_sudo(f"printf '{env_content}' > /etc/default/minio && chmod 600 /etc/default/minio")

        task.update(70, "Génération de l'unité systemd /etc/systemd/system/minio.service...")
        escaped_unit = SYSTEMD_MINIO_TEMPLATE.replace('"', '\\"')
        await executor.run_sudo(f'echo "{escaped_unit}" | tee /etc/systemd/system/minio.service > /dev/null')

        task.update(90, "Activation et démarrage du service systemd 'minio'...")
        await executor.run_sudo("systemctl daemon-reload && systemctl enable --now minio")

        task.complete("MinIO natif installé et démarré (API S3: port 9000, Console: port 9001) !")
