"""
MelodiInstaller: Automated step-by-step installer & systemd setup for MELODI ERP.
"""

from app.installers.base import BaseInstaller
from app.remote.executor import Executor
from app.core.task_manager import TaskProgress
from app.system.package_manager import PackageManager
from app.system.systemd_manager import SystemdManager

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

    async def install(self, executor: Executor, task: TaskProgress):
        task.update(10, "Vérification des dépendances système (python3, python3-venv, git)...")
        deps_res = await PackageManager.install(executor, "python3 python3-venv git")
        if not deps_res["success"]:
            task.fail(f"Impossible d'installer les dépendances système: {deps_res['stderr']}")
            return

        task.update(30, "Préparation du répertoire de déploiement /opt/melodi...")
        code, _, stderr = await executor.run("sudo mkdir -p /opt/melodi && sudo chmod 755 /opt/melodi")
        if code != 0:
            task.fail(f"Erreur création répertoire: {stderr}")
            return

        task.update(50, "Création de l'environnement virtuel Python /opt/melodi/venv...")
        code, _, stderr = await executor.run("python3 -m venv /opt/melodi/venv")
        if code != 0:
            task.fail(f"Erreur création venv Python: {stderr}")
            return

        task.update(75, "Configuration du fichier de service systemd /etc/systemd/system/melodi.service...")
        escaped_unit = SYSTEMD_UNIT_TEMPLATE.replace('"', '\\"')
        cmd = f'echo "{escaped_unit}" | sudo tee /etc/systemd/system/melodi.service > /dev/null'
        code, _, stderr = await executor.run(cmd)
        if code != 0:
            task.fail(f"Erreur écriture fichier systemd: {stderr}")
            return

        task.update(90, "Rechargement du démon systemd (systemctl daemon-reload)...")
        code, _, stderr = await executor.run("sudo systemctl daemon-reload && sudo systemctl enable melodi")
        if code != 0:
            task.fail(f"Erreur activation du service systemd: {stderr}")
            return

        task.complete("Installation et configuration du service systemd MELODI ERP terminées !")
