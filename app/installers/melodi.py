"""
MelodiInstaller: Automated step-by-step installer for MELODI ERP.
Installs natively into /opt/melodi with Python virtual environment and systemd service.
"""

import os
import shlex
from app.installers.base import BaseInstaller
from app.remote.executor import Executor
from app.core.task_manager import TaskProgress
from app.system.package_manager import PackageManager

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

class MelodiInstaller(BaseInstaller):
    def __init__(self):
        super().__init__(name="melodi", display_name="MELODI ERP")

    async def install(self, executor: Executor, task: TaskProgress, **kwargs):
        zip_path = kwargs.get("zip_path") # Chemin absolu vers le zip sur le serveur hôte
        await self._install_native(executor, task, zip_path)

    async def _install_native(self, executor: Executor, task: TaskProgress, zip_path: str = None):
        task.update(10, "Vérification des dépendances système (python3, python3-venv, unzip, git)...")
        deps_res = await PackageManager.install(executor, "python3 python3-venv unzip git", on_output=task.append_log)
        if not deps_res["success"]:
            task.fail(f"Impossible d'installer les dépendances système: {deps_res.get('stderr', '')}")
            return

        task.update(25, "Préparation du répertoire de déploiement /opt/melodi...")
        code, _, stderr = await executor.run_sudo("mkdir -p /opt/melodi && chmod 755 /opt/melodi", on_output=task.append_log)
        if code != 0:
            task.fail(f"Erreur création répertoire: {stderr}")
            return

        # Extraction du ZIP source si fourni
        if zip_path:
            task.update(35, f"Extraction de l'archive source ZIP ({zip_path})...")
            code, _, stderr = await executor.run_sudo(f"unzip -o {shlex.quote(zip_path)} -d /opt/melodi", on_output=task.append_log)
            if code != 0:
                task.fail(f"Échec de l'extraction de l'archive ZIP: {stderr.strip()}")
                return
        else:
            task.update(35, "Initialisation du dossier d'application...")

        task.update(50, "Création de l'environnement virtuel Python /opt/melodi/venv...")
        code, _, stderr = await executor.run_sudo("python3 -m venv /opt/melodi/venv", on_output=task.append_log)
        if code != 0:
            task.fail(f"Erreur création venv Python: {stderr}")
            return

        task.update(65, "Installation des dépendances Python requises...")
        check_req_code, _, _ = await executor.run("test -f /opt/melodi/requirements.txt")
        if check_req_code == 0:
            pip_cmd = "/opt/melodi/venv/bin/pip install --upgrade pip && /opt/melodi/venv/bin/pip install -r /opt/melodi/requirements.txt"
            code, _, stderr = await executor.run_sudo(pip_cmd, timeout=300.0, on_output=task.append_log)
            if code != 0:
                task.update(70, f"Avertissement installation pip: {stderr.strip()[:200]}")

        task.update(80, "Configuration de l'unité systemd /etc/systemd/system/melodi.service...")
        escaped_unit = SYSTEMD_UNIT_TEMPLATE.replace('"', '\\"')
        cmd = f'echo "{escaped_unit}" | tee /etc/systemd/system/melodi.service > /dev/null'
        code, _, stderr = await executor.run_sudo(cmd, on_output=task.append_log)
        if code != 0:
            task.fail(f"Erreur écriture fichier systemd: {stderr}")
            return

        task.update(90, "Activation et démarrage du service systemd melodi...")
        await executor.run_sudo("systemctl daemon-reload && systemctl enable --now melodi", on_output=task.append_log)

        task.complete("MELODI ERP installé et configuré avec succès via systemd (Port 5000) !")
