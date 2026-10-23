"""
MelodiInstaller: Automated step-by-step installer for MELODI ERP.
Installs natively into /opt/melodi with Python virtual environment and systemd service.
"""

import os
import shlex
from typing import Optional
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

    async def deploy_archive(self, executor: Executor, task: TaskProgress, **kwargs) -> Optional[str]:
        """
        Téléverse/télécharge l'archive ZIP, la décompresse dans le dossier cible (défaut /opt)
        et supprime le fichier ZIP temporaire.
        Retourne le dossier d'application final ou None en cas d'échec.
        """
        source_type = kwargs.get("source_type")
        url = kwargs.get("url") or kwargs.get("download_url")
        zip_path = kwargs.get("zip_path")
        destination_dir = kwargs.get("destination_dir") or kwargs.get("target_dir") or "/opt"
        delete_zip = kwargs.get("delete_zip", kwargs.get("cleanup_zip", True))

        # 1. Vérification rapide des outils nécessaires (unzip, curl, wget)
        check_tools_code, _, _ = await executor.run("which unzip curl")
        if check_tools_code != 0:
            task.update(10, "Installation des outils système manquants (unzip, curl, wget)...")
            tools_res = await PackageManager.install(executor, "unzip curl wget", on_output=task.append_log)
            if not tools_res["success"]:
                task.update(12, f"Avertissement installation outils: {tools_res.get('stderr', '')[:150]}")

        # 2. Résolution du fichier ZIP (Téléchargement direct si URL)
        effective_zip_path = zip_path
        if url or source_type == "url":
            if not url:
                task.fail("URL de téléchargement manquante.")
                return None
            task.update(20, f"Téléchargement direct de l'archive MELODI ERP depuis l'URL ({url})...")
            download_dest = "/tmp/melodi_download.zip"
            success_dl, err_dl = await executor.download_file(url, download_dest, on_output=task.append_log)
            if not success_dl:
                task.fail(f"Échec du téléchargement de l'archive: {err_dl}")
                return None
            effective_zip_path = download_dest

        if not effective_zip_path:
            task.update(30, "Aucune archive ZIP fournie, vérification du dossier existant...")
            return destination_dir

        # 3. Préparation du répertoire de destination (défaut: /opt)
        task.update(30, f"Préparation du répertoire de destination {destination_dir}...")
        code, _, stderr = await executor.run_sudo(
            f"mkdir -p {shlex.quote(destination_dir)} && chmod 755 {shlex.quote(destination_dir)}",
            on_output=task.append_log
        )
        if code != 0:
            task.fail(f"Impossible de créer le dossier cible {destination_dir}: {stderr.strip()}")
            return None

        # 4. Décompression de l'archive ZIP
        task.update(40, f"Décompression de l'archive ({effective_zip_path}) dans {destination_dir}...")
        code, _, stderr = await executor.run_sudo(
            f"unzip -o {shlex.quote(effective_zip_path)} -d {shlex.quote(destination_dir)}",
            on_output=task.append_log
        )
        if code != 0:
            task.fail(f"Échec de la décompression ZIP: {stderr.strip()}")
            return None
        task.append_log("✓ Archive décompressée avec succès.")

        # 5. Suppression automatique de l'archive ZIP
        if delete_zip:
            task.update(48, f"Nettoyage : suppression de l'archive ZIP ({effective_zip_path})...")
            del_code, _, del_err = await executor.run_sudo(
                f"rm -f {shlex.quote(effective_zip_path)}",
                on_output=task.append_log
            )
            if del_code == 0:
                task.append_log("✓ Fichier ZIP supprimé avec succès.")
            else:
                task.append_log(f"Avertissement: Impossible de supprimer le ZIP: {del_err.strip()}")

        # 6. Détection de l'emplacement réel de l'application
        # Si le dossier contient un sous-dossier melodi contenant main.py ou requirements.txt
        melodi_sub = os.path.join(destination_dir, "melodi")
        code_sub, _, _ = await executor.run(f"test -d {shlex.quote(melodi_sub)}")
        final_dir = melodi_sub if code_sub == 0 else destination_dir

        if kwargs.get("deploy_only") and not task.is_failed():
            task.complete(f"Archive MELODI ERP déployée avec succès dans {final_dir} et archive ZIP supprimée !")

        return final_dir

    async def install(self, executor: Executor, task: TaskProgress, **kwargs):
        if kwargs.get("deploy_only"):
            res_dir = await self.deploy_archive(executor, task, **kwargs)
            return

        await self._install_native(executor, task, **kwargs)

    async def _install_native(self, executor: Executor, task: TaskProgress, **kwargs):
        task.update(10, "Vérification des dépendances système (python3, python3-venv, unzip, curl, wget, git)...")
        deps_res = await PackageManager.install(executor, "python3 python3-venv unzip curl wget git", on_output=task.append_log)
        if not deps_res["success"]:
            task.fail(f"Impossible d'installer les dépendances système: {deps_res.get('stderr', '')}")
            return

        # Déploiement de l'archive si URL ou zip_path fourni
        app_dir = kwargs.get("destination_dir") or kwargs.get("target_dir") or "/opt/melodi"
        if kwargs.get("zip_path") or kwargs.get("url") or kwargs.get("download_url"):
            deployed_dir = await self.deploy_archive(executor, task, **kwargs)
            if not deployed_dir or task.is_failed():
                return
            app_dir = deployed_dir
        else:
            task.update(25, f"Préparation du répertoire de déploiement {app_dir}...")
            code, _, stderr = await executor.run_sudo(f"mkdir -p {shlex.quote(app_dir)} && chmod 755 {shlex.quote(app_dir)}", on_output=task.append_log)
            if code != 0:
                task.fail(f"Erreur création répertoire: {stderr}")
                return

        task.update(50, f"Création de l'environnement virtuel Python {app_dir}/venv...")
        code, _, stderr = await executor.run_sudo(f"python3 -m venv {shlex.quote(app_dir)}/venv", on_output=task.append_log)
        if code != 0:
            task.fail(f"Erreur création venv Python: {stderr}")
            return

        task.update(65, "Installation des dépendances Python requises...")
        check_req_code, _, _ = await executor.run(f"test -f {shlex.quote(app_dir)}/requirements.txt")
        if check_req_code == 0:
            pip_cmd = f"{shlex.quote(app_dir)}/venv/bin/pip install --upgrade pip && {shlex.quote(app_dir)}/venv/bin/pip install -r {shlex.quote(app_dir)}/requirements.txt"
            code, _, stderr = await executor.run_sudo(pip_cmd, timeout=300.0, on_output=task.append_log)
            if code != 0:
                task.update(70, f"Avertissement installation pip: {stderr.strip()[:200]}")

        task.update(80, "Configuration de l'unité systemd /etc/systemd/system/melodi.service...")
        unit_content = (
            SYSTEMD_UNIT_TEMPLATE
            .replace("/opt/melodi/venv/bin/python3 main.py", f"{app_dir}/venv/bin/python3 main.py")
            .replace("WorkingDirectory=/opt/melodi", f"WorkingDirectory={app_dir}")
        )
        escaped_unit = unit_content.replace('"', '\\"')
        cmd = f'echo "{escaped_unit}" | tee /etc/systemd/system/melodi.service > /dev/null'
        code, _, stderr = await executor.run_sudo(cmd, on_output=task.append_log)
        if code != 0:
            task.fail(f"Erreur écriture fichier systemd: {stderr}")
            return

        task.update(90, "Activation et démarrage du service systemd melodi...")
        await executor.run_sudo("systemctl daemon-reload && systemctl enable --now melodi", on_output=task.append_log)

        task.complete(f"MELODI ERP installé et configuré avec succès dans {app_dir} via systemd (Port 5000) !")
