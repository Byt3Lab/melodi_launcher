"""
MelodiWebsocketInstaller: Automated step-by-step installer for MELODI WebSocket Server.
Installs into /opt/melodi with Python virtual environment and systemd service (melodi-websocket.service).
"""

import shlex
from app.installers.base import BaseInstaller
from app.remote.executor import Executor
from app.core.task_manager import TaskProgress
from app.system.package_manager import PackageManager

SYSTEMD_WS_UNIT_TEMPLATE = """[Unit]
Description=MELODI WebSocket Real-Time Server
After=network.target redis-server.service melodi.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/melodi
ExecStart=/opt/melodi/venv/bin/python3 websocket_server.py
Restart=always
RestartSec=5
StandardOutput=append:/var/log/melodi-websocket.log
StandardError=append:/var/log/melodi-websocket.log

[Install]
WantedBy=multi-user.target
"""

class MelodiWebsocketInstaller(BaseInstaller):
    def __init__(self):
        super().__init__(name="melodi_websocket", display_name="MELODI WebSocket")

    async def install(self, executor: Executor, task: TaskProgress, **kwargs):
        zip_path = kwargs.get("zip_path")
        await self._install_native(executor, task, zip_path)

    async def _install_native(self, executor: Executor, task: TaskProgress, zip_path: str = None):
        task.update(10, "Vérification des dépendances système (python3, python3-venv, unzip)...")
        deps_res = await PackageManager.install(executor, "python3 python3-venv unzip", on_output=task.append_log)
        if not deps_res["success"]:
            task.fail(f"Impossible d'installer les dépendances système: {deps_res.get('stderr', '')}")
            return

        task.update(25, "Préparation du répertoire /opt/melodi...")
        code, _, stderr = await executor.run_sudo("mkdir -p /opt/melodi && chmod 755 /opt/melodi", on_output=task.append_log)
        if code != 0:
            task.fail(f"Erreur création répertoire: {stderr}")
            return

        if zip_path:
            task.update(35, f"Extraction de l'archive ZIP WebSocket ({zip_path})...")
            code, _, stderr = await executor.run_sudo(f"unzip -o {shlex.quote(zip_path)} -d /opt/melodi", on_output=task.append_log)
            if code != 0:
                task.fail(f"Échec de l'extraction de l'archive ZIP: {stderr.strip()}")
                return

        task.update(50, "Vérification de l'environnement virtuel Python /opt/melodi/venv...")
        check_venv, _, _ = await executor.run("test -f /opt/melodi/venv/bin/python3")
        if check_venv != 0:
            code, _, stderr = await executor.run_sudo("python3 -m venv /opt/melodi/venv", on_output=task.append_log)
            if code != 0:
                task.fail(f"Erreur création venv Python: {stderr}")
                return

        task.update(65, "Installation des dépendances Python WebSocket...")
        check_req_code, _, _ = await executor.run("test -f /opt/melodi/requirements.txt")
        if check_req_code == 0:
            pip_cmd = "/opt/melodi/venv/bin/pip install --upgrade pip && /opt/melodi/venv/bin/pip install -r /opt/melodi/requirements.txt"
            code, _, stderr = await executor.run_sudo(pip_cmd, timeout=300.0, on_output=task.append_log)
            if code != 0:
                task.update(70, f"Avertissement installation pip: {stderr.strip()[:200]}")

        task.update(80, "Configuration de l'unité systemd /etc/systemd/system/melodi-websocket.service...")
        escaped_unit = SYSTEMD_WS_UNIT_TEMPLATE.replace('"', '\\"')
        cmd = f'echo "{escaped_unit}" | tee /etc/systemd/system/melodi-websocket.service > /dev/null'
        code, _, stderr = await executor.run_sudo(cmd, on_output=task.append_log)
        if code != 0:
            task.fail(f"Erreur écriture fichier systemd: {stderr}")
            return

        task.update(90, "Activation et démarrage du service systemd melodi-websocket...")
        await executor.run_sudo("systemctl daemon-reload && systemctl enable --now melodi-websocket", on_output=task.append_log)

        task.complete("MELODI WebSocket installé et configuré avec succès via systemd (Port 8001) !")
