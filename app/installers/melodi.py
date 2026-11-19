"""
MelodiInstaller: Automated step-by-step installer for MELODI ERP.
Supports deploying from a local source folder, a local .zip archive, or a download URL,
configuring a Python virtual environment (venv) and creating an auto-start systemd service.
"""

import asyncio
import os
import shlex
import shutil
import tempfile
import zipfile
from typing import Optional
from app.i18n import t
from app.installers.base import BaseInstaller
from app.remote.executor import Executor
from app.core.task_manager import TaskProgress
from app.system.package_manager import PackageManager

SYSTEMD_UNIT_TEMPLATE = """[Unit]
Description=MELODI ERP Application Service
After=network.target postgresql.service

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

    async def deploy_source_folder(
        self,
        executor: Executor,
        task: TaskProgress,
        source_dir: str,
        destination_dir: str = "/opt/melodi"
    ) -> Optional[str]:
        """
        Déploie un dossier source local vers la machine locale ou un serveur distant (SSH).
        En local : copie directe (ou utilisation sur place si même dossier).
        À distance : compression temporaire automatique + envoi SFTP + extraction.
        """
        if not os.path.isdir(source_dir):
            task.fail(t("executor.local.file_not_found", path=source_dir))
            return None

        is_win = await executor.is_windows()

        if executor.name == "Localhost":
            if os.path.abspath(source_dir) == os.path.abspath(destination_dir):
                task.append_log(t("installer.melodi.copy_ok"))
                return destination_dir

            if is_win:
                task.update(35, t("installer.melodi.copying_folder", src=source_dir, dest=destination_dir))
                try:
                    os.makedirs(destination_dir, exist_ok=True)
                    await asyncio.to_thread(shutil.copytree, source_dir, destination_dir, dirs_exist_ok=True)
                    task.append_log(t("installer.melodi.copy_ok"))
                    return destination_dir
                except Exception as exc:
                    task.fail(t("installer.melodi.copy_failed", error=str(exc)))
                    return None

            task.update(25, t("installer.melodi.prep_dir", path=destination_dir))
            code, _, stderr = await executor.run_sudo(
                f"mkdir -p {shlex.quote(destination_dir)} && chmod 755 {shlex.quote(destination_dir)}",
                on_output=task.append_log
            )
            if code != 0:
                task.fail(t("installer.melodi.mkdir_failed", path=destination_dir, error=stderr.strip()))
                return None

            task.update(35, t("installer.melodi.copying_folder", src=source_dir, dest=destination_dir))
            src_dot = os.path.join(source_dir, ".")
            code, _, stderr = await executor.run_sudo(
                f"cp -a {shlex.quote(src_dot)} {shlex.quote(destination_dir)}/",
                on_output=task.append_log
            )
            if code != 0:
                task.fail(t("installer.melodi.copy_failed", error=stderr.strip()))
                return None
            task.append_log(t("installer.melodi.copy_ok"))
            return destination_dir

        # Serveur distant SSH : compression temporaire + SFTP + extraction
        task.update(18, t("wizard.packing_folder"))
        tmp_dir = tempfile.mkdtemp(prefix="melodi_pack_")
        try:
            archive_base = os.path.join(tmp_dir, "melodi_source")
            local_zip = shutil.make_archive(archive_base, "zip", root_dir=source_dir)
            task.update(25, t("wizard.uploading_zip"))
            remote_zip = "C:\\Windows\\Temp\\melodi_source_upload.zip" if is_win else "/tmp/melodi_source_upload.zip"
            ok_up, err_up = await executor.upload_file(local_zip, remote_zip)
            if not ok_up:
                task.fail(t("wizard.err.upload", error=err_up))
                return None
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

        return await self.deploy_archive(
            executor,
            task,
            zip_path=remote_zip,
            destination_dir=destination_dir,
            delete_zip=True
        )

    async def deploy_archive(self, executor: Executor, task: TaskProgress, **kwargs) -> Optional[str]:
        """
        Téléverse/télécharge l'archive ZIP, la décompresse dans le dossier cible
        et supprime le fichier ZIP temporaire (compatible Linux et Windows).
        """
        is_win = await executor.is_windows()
        source_type = kwargs.get("source_type")
        url = kwargs.get("url") or kwargs.get("download_url")
        zip_path = kwargs.get("zip_path")
        default_dest = "C:\\melodi" if is_win else "/opt/melodi"
        destination_dir = kwargs.get("destination_dir") or kwargs.get("target_dir") or default_dest
        delete_zip = kwargs.get("delete_zip", kwargs.get("cleanup_zip", True))

        if is_win:
            return await self._deploy_archive_windows(executor, task, url, source_type, zip_path, destination_dir, delete_zip, kwargs.get("deploy_only", False))

        # 1. Vérification rapide des outils nécessaires (unzip, curl, wget)
        check_tools_code, _, _ = await executor.run("which unzip curl")
        if check_tools_code != 0:
            task.update(10, t("installer.melodi.installing_tools"))
            tools_res = await PackageManager.install(executor, "unzip curl wget", on_output=task.append_log)
            if not tools_res["success"]:
                task.update(12, t("installer.melodi.tools_warn", error=tools_res.get("stderr", "")[:150]))

        # 2. Résolution du fichier ZIP (Téléchargement direct si URL)
        effective_zip_path = zip_path
        if url or source_type == "url":
            if not url:
                task.fail(t("installer.melodi.missing_url"))
                return None
            task.update(20, t("installer.melodi.downloading", url=url))
            download_dest = "/tmp/melodi_download.zip"
            success_dl, err_dl = await executor.download_file(url, download_dest, on_output=task.append_log)
            if not success_dl:
                task.fail(t("installer.melodi.download_failed", error=err_dl))
                return None
            effective_zip_path = download_dest

        if not effective_zip_path:
            task.update(30, t("installer.melodi.no_zip"))
            return destination_dir

        # 3. Préparation du répertoire de destination
        task.update(30, t("installer.melodi.prep_dir", path=destination_dir))
        code, _, stderr = await executor.run_sudo(
            f"mkdir -p {shlex.quote(destination_dir)} && chmod 755 {shlex.quote(destination_dir)}",
            on_output=task.append_log
        )
        if code != 0:
            task.fail(t("installer.melodi.mkdir_failed", path=destination_dir, error=stderr.strip()))
            return None

        # 4. Décompression de l'archive ZIP
        task.update(40, t("installer.melodi.unzipping", zip_path=effective_zip_path, dest=destination_dir))
        code, _, stderr = await executor.run_sudo(
            f"unzip -o {shlex.quote(effective_zip_path)} -d {shlex.quote(destination_dir)}",
            on_output=task.append_log
        )
        if code != 0:
            task.fail(t("installer.melodi.unzip_failed", error=stderr.strip()))
            return None
        task.append_log(t("installer.melodi.unzip_ok"))

        # 5. Suppression automatique de l'archive ZIP
        if delete_zip:
            task.update(48, t("installer.melodi.cleanup", zip_path=effective_zip_path))
            del_code, _, del_err = await executor.run_sudo(
                f"rm -f {shlex.quote(effective_zip_path)}",
                on_output=task.append_log
            )
            if del_code == 0:
                task.append_log(t("installer.melodi.cleanup_ok"))
            else:
                task.append_log(t("installer.melodi.cleanup_warn", error=del_err.strip()))

        # 6. Détection de l'emplacement réel de l'application
        melodi_sub = os.path.join(destination_dir, "melodi")
        code_sub, _, _ = await executor.run(f"test -d {shlex.quote(melodi_sub)}")
        final_dir = melodi_sub if code_sub == 0 else destination_dir

        if kwargs.get("deploy_only") and not task.is_failed():
            task.complete(t("installer.melodi.deploy_done", path=final_dir))

        return final_dir

    async def _deploy_archive_windows(
        self,
        executor: Executor,
        task: TaskProgress,
        url: Optional[str],
        source_type: Optional[str],
        zip_path: Optional[str],
        destination_dir: str,
        delete_zip: bool,
        deploy_only: bool
    ) -> Optional[str]:
        effective_zip = zip_path
        if url or source_type == "url":
            if not url:
                task.fail(t("installer.melodi.missing_url"))
                return None
            task.update(20, t("installer.melodi.downloading", url=url))
            dl_dest = os.path.join(tempfile.gettempdir(), "melodi_download.zip") if executor.name == "Localhost" else "C:\\Windows\\Temp\\melodi_download.zip"
            ok_dl, err_dl = await executor.download_file(url, dl_dest, on_output=task.append_log)
            if not ok_dl:
                task.fail(t("installer.melodi.download_failed", error=err_dl))
                return None
            effective_zip = dl_dest

        if not effective_zip:
            task.update(30, t("installer.melodi.no_zip"))
            return destination_dir

        task.update(40, t("installer.melodi.unzipping", zip_path=effective_zip, dest=destination_dir))
        if executor.name == "Localhost":
            try:
                os.makedirs(destination_dir, exist_ok=True)
                def _extract():
                    with zipfile.ZipFile(effective_zip, "r") as zf:
                        zf.extractall(destination_dir)
                await asyncio.to_thread(_extract)
            except Exception as exc:
                task.fail(t("installer.melodi.unzip_failed", error=str(exc)))
                return None
            if delete_zip and os.path.exists(effective_zip):
                try:
                    os.remove(effective_zip)
                except OSError:
                    pass
            melodi_sub = os.path.join(destination_dir, "melodi")
            final_dir = melodi_sub if os.path.isdir(melodi_sub) else destination_dir
        else:
            ps_extract = (
                f'powershell -NoProfile -Command "'
                f"New-Item -ItemType Directory -Force -Path '{destination_dir}' | Out-Null; "
                f"Expand-Archive -Path '{effective_zip}' -DestinationPath '{destination_dir}' -Force\""
            )
            code, _, stderr = await executor.run(ps_extract, on_output=task.append_log)
            if code != 0:
                task.fail(t("installer.melodi.unzip_failed", error=stderr.strip()))
                return None
            if delete_zip:
                await executor.run(f'powershell -NoProfile -Command "Remove-Item -Force -ErrorAction SilentlyContinue \'{effective_zip}\'"')
            sub_check, sub_out, _ = await executor.run(f'powershell -NoProfile -Command "Test-Path \'{destination_dir}\\melodi\'"')
            final_dir = f"{destination_dir}\\melodi" if (sub_check == 0 and sub_out.strip().lower() == "true") else destination_dir

        task.append_log(t("installer.melodi.unzip_ok"))
        if deploy_only and not task.is_failed():
            task.complete(t("installer.melodi.deploy_done", path=final_dir))
        return final_dir

    async def install(self, executor: Executor, task: TaskProgress, **kwargs):
        is_win = await executor.is_windows()
        default_dest = "C:\\melodi" if is_win else "/opt/melodi"

        if kwargs.get("deploy_only"):
            if kwargs.get("source_dir"):
                res_dir = await self.deploy_source_folder(
                    executor,
                    task,
                    kwargs["source_dir"],
                    kwargs.get("destination_dir") or default_dest
                )
                if res_dir and not task.is_failed():
                    task.complete(t("installer.melodi.deploy_done", path=res_dir))
            else:
                await self.deploy_archive(executor, task, **kwargs)
            return

        if is_win:
            await self._install_windows(executor, task, **kwargs)
        else:
            await self._install_native(executor, task, **kwargs)

    async def _install_windows(self, executor: Executor, task: TaskProgress, **kwargs):
        setup_venv = kwargs.get("setup_venv", True)
        setup_service = kwargs.get("setup_service", True)
        on_step_done = kwargs.get("on_step_done")
        app_dir = kwargs.get("destination_dir") or kwargs.get("target_dir") or "C:\\melodi"

        task.update(10, t("installer.melodi.checking_deps"))
        py_code, _, _ = await executor.run("python --version")
        if py_code != 0:
            await PackageManager.install(executor, "python3", on_output=task.append_log)

        if kwargs.get("source_dir"):
            deployed_dir = await self.deploy_source_folder(executor, task, kwargs["source_dir"], app_dir)
            if not deployed_dir or task.is_failed():
                return
            app_dir = deployed_dir
        elif kwargs.get("zip_path") or kwargs.get("url") or kwargs.get("download_url"):
            deployed_dir = await self.deploy_archive(executor, task, **kwargs)
            if not deployed_dir or task.is_failed():
                return
            app_dir = deployed_dir
        else:
            await executor.run(f'powershell -NoProfile -Command "New-Item -ItemType Directory -Force -Path \'{app_dir}\' | Out-Null"')

        if callable(on_step_done):
            on_step_done("melodi", "success")

        if setup_venv:
            if callable(on_step_done):
                on_step_done("venv", "running")
            task.update(55, t("installer.melodi.creating_venv", path=app_dir))
            code, _, stderr = await executor.run(f'python -m venv "{app_dir}\\venv"', on_output=task.append_log)
            if code != 0:
                if callable(on_step_done):
                    on_step_done("venv", "error")
                task.fail(t("installer.melodi.venv_failed", error=stderr))
                return

            task.update(70, t("installer.melodi.installing_pip"))
            req_check, req_out, _ = await executor.run(f'powershell -NoProfile -Command "Test-Path \'{app_dir}\\requirements.txt\'"')
            if req_check == 0 and req_out.strip().lower() == "true":
                pip_cmd = f'"{app_dir}\\venv\\Scripts\\pip.exe" install --upgrade pip && "{app_dir}\\venv\\Scripts\\pip.exe" install -r "{app_dir}\\requirements.txt"'
                code, _, stderr = await executor.run(pip_cmd, timeout=300.0, on_output=task.append_log)
                if code != 0:
                    task.update(75, t("installer.melodi.pip_warn", error=stderr.strip()[:200]))
            if callable(on_step_done):
                on_step_done("venv", "success")

        if setup_service:
            if callable(on_step_done):
                on_step_done("service", "running")
            task.update(85, t("installer.melodi.configuring_systemd"))
            python_exe = f"{app_dir}\\venv\\Scripts\\python.exe" if setup_venv else "python"
            bat_path = f"{app_dir}\\start_melodi.bat"
            bat_ps = (
                f'powershell -NoProfile -Command "'
                f"$content = @'\n@echo off\ncd /d \"{app_dir}\"\n\"{python_exe}\" main.py >> \"{app_dir}\\melodi.log\" 2>&1\n'@; "
                f"Set-Content -Path '{bat_path}' -Value $content -Encoding ASCII\""
            )
            await executor.run(bat_ps, on_output=task.append_log)

            task.update(92, t("installer.melodi.starting_service"))
            reg_cmd = (
                f'schtasks /Create /TN "MELODI_ERP" /TR "\\"{bat_path}\\"" '
                f'/SC ONSTART /RL HIGHEST /F'
            )
            code, _, stderr = await executor.run(reg_cmd, on_output=task.append_log)
            if code != 0:
                if callable(on_step_done):
                    on_step_done("service", "error")
                task.fail(t("installer.melodi.systemd_failed", error=stderr))
                return
            await executor.run('powershell -NoProfile -Command "Start-ScheduledTask -TaskName \'MELODI_ERP\'"', on_output=task.append_log)
            if callable(on_step_done):
                on_step_done("service", "success")

        task.complete(t("installer.melodi.done", path=app_dir))

    async def _install_native(self, executor: Executor, task: TaskProgress, **kwargs):
        setup_venv = kwargs.get("setup_venv", True)
        setup_service = kwargs.get("setup_service", True)
        on_step_done = kwargs.get("on_step_done")

        task.update(10, t("installer.melodi.checking_deps"))
        deps_res = await PackageManager.install(executor, "python3 python3-venv unzip curl wget git", on_output=task.append_log)
        if not deps_res["success"]:
            task.fail(t("installer.melodi.deps_failed", error=deps_res.get("stderr", "")))
            return

        app_dir = kwargs.get("destination_dir") or kwargs.get("target_dir") or "/opt/melodi"
        if kwargs.get("source_dir"):
            deployed_dir = await self.deploy_source_folder(executor, task, kwargs["source_dir"], app_dir)
            if not deployed_dir or task.is_failed():
                return
            app_dir = deployed_dir
        elif kwargs.get("zip_path") or kwargs.get("url") or kwargs.get("download_url"):
            deployed_dir = await self.deploy_archive(executor, task, **kwargs)
            if not deployed_dir or task.is_failed():
                return
            app_dir = deployed_dir
        else:
            task.update(25, t("installer.melodi.prep_dir", path=app_dir))
            code, _, stderr = await executor.run_sudo(f"mkdir -p {shlex.quote(app_dir)} && chmod 755 {shlex.quote(app_dir)}", on_output=task.append_log)
            if code != 0:
                task.fail(t("installer.melodi.mkdir_failed", path=app_dir, error=stderr))
                return

        if callable(on_step_done):
            on_step_done("melodi", "success")

        if setup_venv:
            if callable(on_step_done):
                on_step_done("venv", "running")
            task.update(55, t("installer.melodi.creating_venv", path=app_dir))
            code, _, stderr = await executor.run_sudo(f"python3 -m venv {shlex.quote(app_dir)}/venv", on_output=task.append_log)
            if code != 0:
                if callable(on_step_done):
                    on_step_done("venv", "error")
                task.fail(t("installer.melodi.venv_failed", error=stderr))
                return

            task.update(70, t("installer.melodi.installing_pip"))
            check_req_code, _, _ = await executor.run(f"test -f {shlex.quote(app_dir)}/requirements.txt")
            if check_req_code == 0:
                pip_cmd = f"{shlex.quote(app_dir)}/venv/bin/pip install --upgrade pip && {shlex.quote(app_dir)}/venv/bin/pip install -r {shlex.quote(app_dir)}/requirements.txt"
                code, _, stderr = await executor.run_sudo(pip_cmd, timeout=300.0, on_output=task.append_log)
                if code != 0:
                    task.update(75, t("installer.melodi.pip_warn", error=stderr.strip()[:200]))
            if callable(on_step_done):
                on_step_done("venv", "success")

        if setup_service:
            if callable(on_step_done):
                on_step_done("service", "running")
            task.update(85, t("installer.melodi.configuring_systemd"))
            python_bin = f"{app_dir}/venv/bin/python3" if setup_venv else "/usr/bin/python3"
            unit_content = (
                SYSTEMD_UNIT_TEMPLATE
                .replace("/opt/melodi/venv/bin/python3 main.py", f"{python_bin} main.py")
                .replace("WorkingDirectory=/opt/melodi", f"WorkingDirectory={app_dir}")
            )
            escaped_unit = unit_content.replace('"', '\\"')
            cmd = f'echo "{escaped_unit}" | tee /etc/systemd/system/melodi.service > /dev/null'
            code, _, stderr = await executor.run_sudo(cmd, on_output=task.append_log)
            if code != 0:
                if callable(on_step_done):
                    on_step_done("service", "error")
                task.fail(t("installer.melodi.systemd_failed", error=stderr))
                return

            task.update(92, t("installer.melodi.starting_service"))
            await executor.run_sudo("systemctl daemon-reload && systemctl enable --now melodi", on_output=task.append_log)
            if callable(on_step_done):
                on_step_done("service", "success")

        task.complete(t("installer.melodi.done", path=app_dir))
