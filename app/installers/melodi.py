"""
MelodiInstaller: Automated step-by-step installer for MELODI ERP.
Supports:
1. Native installation from user-provided ZIP archive or Git repository into /opt/melodi with systemd service.
2. Docker containerized deployment from user-provided ZIP archive (build/run container) or pre-configured Docker image.
"""

import os
import shlex
from app.installers.base import BaseInstaller
from app.remote.executor import Executor
from app.core.task_manager import TaskProgress
from app.system.package_manager import PackageManager
from app.system.docker_manager import DockerManager

SYSTEMD_UNIT_TEMPLATE = """[Unit]
Description=MELODI ERP Application Service
After=network.target postgresql.service redis-server.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/melodi
ExecStart=/opt/melodi/venv/bin/python3 main.py
Restart=always
RestartSec=5
StandardOutput=append:/var/log/melodi.log
StandardError=append:/var/log/melodi.log

[Install]
WantedBy=multi-user.target
"""

DOCKERFILE_TEMPLATE = """FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*
COPY . /app
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi
EXPOSE 5000
CMD ["python3", "main.py"]
"""

class MelodiInstaller(BaseInstaller):
    def __init__(self):
        super().__init__(name="melodi", display_name="MELODI ERP")

    async def install(self, executor: Executor, task: TaskProgress, **kwargs):
        use_docker = kwargs.get("use_docker", False)
        zip_path = kwargs.get("zip_path") # Chemin absolu vers le zip sur le serveur hôte

        if use_docker:
            await self._install_docker(executor, task, zip_path)
        else:
            await self._install_native(executor, task, zip_path)

    async def _install_native(self, executor: Executor, task: TaskProgress, zip_path: str = None):
        task.update(10, "Vérification des dépendances système (python3, python3-venv, unzip, git)...")
        deps_res = await PackageManager.install(executor, "python3 python3-venv unzip git")
        if not deps_res["success"]:
            task.fail(f"Impossible d'installer les dépendances système: {deps_res.get('stderr', '')}")
            return

        task.update(25, "Préparation du répertoire de déploiement /opt/melodi...")
        code, _, stderr = await executor.run_sudo("mkdir -p /opt/melodi && chmod 755 /opt/melodi")
        if code != 0:
            task.fail(f"Erreur création répertoire: {stderr}")
            return

        # Extraction du ZIP source si fourni
        if zip_path:
            task.update(35, f"Extraction de l'archive source ZIP ({zip_path})...")
            code, _, stderr = await executor.run_sudo(f"unzip -o {shlex.quote(zip_path)} -d /opt/melodi")
            if code != 0:
                task.fail(f"Échec de l'extraction de l'archive ZIP: {stderr.strip()}")
                return
        else:
            task.update(35, "Aucun ZIP fourni, initialisation du dossier d'application...")

        task.update(50, "Création de l'environnement virtuel Python /opt/melodi/venv...")
        code, _, stderr = await executor.run_sudo("python3 -m venv /opt/melodi/venv")
        if code != 0:
            task.fail(f"Erreur création venv Python: {stderr}")
            return

        task.update(65, "Installation des dépendances Python requises...")
        check_req_code, _, _ = await executor.run("test -f /opt/melodi/requirements.txt")
        if check_req_code == 0:
            pip_cmd = "/opt/melodi/venv/bin/pip install --upgrade pip && /opt/melodi/venv/bin/pip install -r /opt/melodi/requirements.txt"
            code, _, stderr = await executor.run_sudo(pip_cmd)
            if code != 0:
                task.update(70, f"Avertissement installation pip: {stderr.strip()[:200]}")

        task.update(80, "Configuration de l'unité systemd /etc/systemd/system/melodi.service...")
        escaped_unit = SYSTEMD_UNIT_TEMPLATE.replace('"', '\\"')
        cmd = f'echo "{escaped_unit}" | tee /etc/systemd/system/melodi.service > /dev/null'
        code, _, stderr = await executor.run_sudo(cmd)
        if code != 0:
            task.fail(f"Erreur écriture fichier systemd: {stderr}")
            return

        task.update(90, "Activation et démarrage du service systemd melodi...")
        await executor.run_sudo("systemctl daemon-reload && systemctl enable --now melodi")

        task.complete("MELODI ERP installé et configuré avec succès via systemd (Port 5000) !")

    async def _install_docker(self, executor: Executor, task: TaskProgress, zip_path: str = None):
        task.update(10, "Vérification de Docker...")
        if not await DockerManager.is_running(executor):
            task.fail("Docker n'est pas opérationnel sur la machine hôte.")
            return

        task.update(25, "Préparation du répertoire /opt/melodi_docker...")
        await executor.run_sudo("mkdir -p /opt/melodi_docker")

        if zip_path:
            task.update(40, f"Extraction de l'archive ZIP ({zip_path})...")
            await PackageManager.install(executor, "unzip")
            code, _, stderr = await executor.run_sudo(f"unzip -o {shlex.quote(zip_path)} -d /opt/melodi_docker")
            if code != 0:
                task.fail(f"Échec de l'extraction de l'archive ZIP: {stderr.strip()}")
                return

        task.update(60, "Génération du Dockerfile pour MELODI ERP si nécessaire...")
        check_df, _, _ = await executor.run("test -f /opt/melodi_docker/Dockerfile")
        if check_df != 0:
            df_content = DOCKERFILE_TEMPLATE.replace('"', '\\"')
            await executor.run_sudo(f'echo "{df_content}" | tee /opt/melodi_docker/Dockerfile > /dev/null')

        task.update(75, "Construction de l'image Docker melodi:latest...")
        build_code, stdout, stderr = await executor.run_sudo("docker build -t melodi:latest /opt/melodi_docker", timeout=300.0)
        if build_code != 0:
            task.fail(f"Échec du build de l'image Docker: {stderr.strip()[:300]}")
            return

        task.update(90, "Lancement du conteneur MELODI ERP (port 5000)...")
        res = await DockerManager.run_container(
            executor=executor,
            name="melodi_app",
            image="melodi:latest",
            ports={"5000": "5000"},
            volumes={"/opt/melodi_docker/data": "/app/data"}
        )

        if not res["success"]:
            task.fail(f"Échec du lancement du conteneur: {res['message']}")
            return

        task.complete("MELODI ERP déployé avec succès via Docker (Port 5000) !")
