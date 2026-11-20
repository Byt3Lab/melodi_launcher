"""
SystemdManager: Cross-platform service management (systemd on Linux, Services/ScheduledTasks on Windows).
Supports multiple MELODI ERP instances (melodi, melodi-<slug>) and PostgreSQL.
"""

import shlex
from typing import Dict, Any, List, Optional, Callable
from app.core.instance_manager import win_task_name_for_service
from app.i18n import t
from app.remote.executor import Executor


class SystemdManager:
    @staticmethod
    def _is_melodi_service(service_name: str) -> bool:
        return service_name == "melodi" or service_name.startswith("melodi-")

    @staticmethod
    async def _win_service_pattern(service_name: str) -> str:
        return "postgresql*" if "postgres" in service_name.lower() else service_name

    @staticmethod
    async def _is_active_raw(executor: Executor, service_name: str) -> tuple[int, bool]:
        """Retourne (exit_code, is_active) avec timeout pour détecter les hôtes injoignables."""
        if await executor.is_windows():
            if SystemdManager._is_melodi_service(service_name):
                task_name = win_task_name_for_service(service_name)
                cmd = (
                    'powershell -NoProfile -Command "'
                    f"$s = Get-Service -Name '{service_name}' -ErrorAction SilentlyContinue; "
                    "if ($s -and $s.Status -eq 'Running') { 'active'; exit 0 }; "
                    f"$t = Get-ScheduledTask -TaskName '{task_name}' -ErrorAction SilentlyContinue; "
                    "if ($t -and $t.State -eq 'Running') { 'active' } else { 'inactive' }\""
                )
            else:
                pat = await SystemdManager._win_service_pattern(service_name)
                cmd = (
                    f'powershell -NoProfile -Command "'
                    f"$s = Get-Service -Name '{pat}' -ErrorAction SilentlyContinue | Where-Object {{$_.Status -eq 'Running'}}; "
                    f"if ($s) {{ 'active' }} else {{ 'inactive' }}\""
                )
            code, stdout, _ = await executor.run(cmd, timeout=8.0)
            return code, (code == 0 and stdout.strip().lower() == "active")

        code, stdout, _ = await executor.run(f"systemctl is-active {shlex.quote(service_name)}", timeout=8.0)
        return code, (code == 0 and stdout.strip() == "active")

    @staticmethod
    async def is_active(executor: Executor, service_name: str) -> bool:
        """Vérifie si un service est actif (systemctl sous Linux, Get-Service / ScheduledTask sous Windows)."""
        _, active = await SystemdManager._is_active_raw(executor, service_name)
        return active

    @staticmethod
    async def _is_installed_raw(executor: Executor, service_name: str) -> tuple[int, bool]:
        """Retourne (exit_code, is_installed) avec timeout pour détecter les hôtes injoignables."""
        if await executor.is_windows():
            if SystemdManager._is_melodi_service(service_name):
                task_name = win_task_name_for_service(service_name)
                cmd = (
                    'powershell -NoProfile -Command "'
                    f"$s = Get-Service -Name '{service_name}' -ErrorAction SilentlyContinue; "
                    f"$t = Get-ScheduledTask -TaskName '{task_name}' -ErrorAction SilentlyContinue; "
                    "if ($s -or $t) { 'yes' } else { 'no' }\""
                )
            else:
                pat = await SystemdManager._win_service_pattern(service_name)
                cmd = (
                    f'powershell -NoProfile -Command "'
                    f"$s = Get-Service -Name '{pat}' -ErrorAction SilentlyContinue; "
                    f"if ($s) {{ 'yes' }} else {{ 'no' }}\""
                )
            code, stdout, _ = await executor.run(cmd, timeout=8.0)
            return code, (code == 0 and stdout.strip().lower() == "yes")

        code, stdout, _ = await executor.run(
            f"systemctl list-unit-files {shlex.quote(service_name)}.service",
            timeout=8.0,
        )
        return code, (code == 0 and service_name in stdout)

    @staticmethod
    async def is_installed(executor: Executor, service_name: str) -> bool:
        """Vérifie si un service existe sur le système."""
        _, installed = await SystemdManager._is_installed_raw(executor, service_name)
        return installed

    @staticmethod
    async def get_status(executor: Executor, service_name: str) -> str:
        """Retourne 'active', 'stopped', 'not_installed' ou 'unreachable'."""
        code, active = await SystemdManager._is_active_raw(executor, service_name)
        if code == -1:
            return "unreachable"
        if active:
            return "active"
        code_inst, installed = await SystemdManager._is_installed_raw(executor, service_name)
        if code_inst == -1:
            return "unreachable"
        return "stopped" if installed else "not_installed"

    @staticmethod
    async def start(executor: Executor, service_name: str, on_output: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
        """Démarre un service (systemd sous Linux, Start-Service / Start-ScheduledTask sous Windows)."""
        if await executor.is_windows():
            if SystemdManager._is_melodi_service(service_name):
                task_name = win_task_name_for_service(service_name)
                cmd = (
                    'powershell -NoProfile -Command "'
                    f"$s = Get-Service -Name '{service_name}' -ErrorAction SilentlyContinue; "
                    f"if ($s) {{ Start-Service -Name '{service_name}' }} else {{ Start-ScheduledTask -TaskName '{task_name}' }}\""
                )
            else:
                pat = await SystemdManager._win_service_pattern(service_name)
                cmd = f'powershell -NoProfile -Command "Get-Service -Name \'{pat}\' | Start-Service"'
            code, _, stderr = await executor.run(cmd, on_output=on_output)
            return {
                "success": code == 0,
                "message": t("systemd.started", name=service_name) if code == 0 else t("systemd.start_failed", name=service_name, error=stderr.strip())
            }

        code, _, stderr = await executor.run_sudo(f"systemctl start {service_name}", on_output=on_output)
        return {
            "success": code == 0,
            "message": t("systemd.started", name=service_name) if code == 0 else t("systemd.start_failed", name=service_name, error=stderr.strip())
        }

    @staticmethod
    async def stop(executor: Executor, service_name: str, on_output: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
        """Arrête un service (systemd sous Linux, Stop-Service / Stop-ScheduledTask sous Windows)."""
        if await executor.is_windows():
            if SystemdManager._is_melodi_service(service_name):
                task_name = win_task_name_for_service(service_name)
                cmd = (
                    'powershell -NoProfile -Command "'
                    f"$s = Get-Service -Name '{service_name}' -ErrorAction SilentlyContinue; "
                    f"if ($s) {{ Stop-Service -Name '{service_name}' -Force }} else {{ Stop-ScheduledTask -TaskName '{task_name}' }}\""
                )
            else:
                pat = await SystemdManager._win_service_pattern(service_name)
                cmd = f'powershell -NoProfile -Command "Get-Service -Name \'{pat}\' | Stop-Service -Force"'
            code, _, stderr = await executor.run(cmd, on_output=on_output)
            return {
                "success": code == 0,
                "message": t("systemd.stopped", name=service_name) if code == 0 else t("systemd.stop_failed", name=service_name, error=stderr.strip())
            }

        code, _, stderr = await executor.run_sudo(f"systemctl stop {service_name}", on_output=on_output)
        return {
            "success": code == 0,
            "message": t("systemd.stopped", name=service_name) if code == 0 else t("systemd.stop_failed", name=service_name, error=stderr.strip())
        }

    @staticmethod
    async def restart(executor: Executor, service_name: str, on_output: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
        """Redémarre un service."""
        if await executor.is_windows():
            if SystemdManager._is_melodi_service(service_name):
                await SystemdManager.stop(executor, service_name, on_output=on_output)
                res = await SystemdManager.start(executor, service_name, on_output=on_output)
                return {
                    "success": res["success"],
                    "message": t("systemd.restarted", name=service_name) if res["success"] else t("systemd.restart_failed", name=service_name, error=res["message"])
                }
            pat = await SystemdManager._win_service_pattern(service_name)
            cmd = f'powershell -NoProfile -Command "Get-Service -Name \'{pat}\' | Restart-Service -Force"'
            code, _, stderr = await executor.run(cmd, on_output=on_output)
            return {
                "success": code == 0,
                "message": t("systemd.restarted", name=service_name) if code == 0 else t("systemd.restart_failed", name=service_name, error=stderr.strip())
            }

        code, _, stderr = await executor.run_sudo(f"systemctl restart {service_name}", on_output=on_output)
        return {
            "success": code == 0,
            "message": t("systemd.restarted", name=service_name) if code == 0 else t("systemd.restart_failed", name=service_name, error=stderr.strip())
        }

    @staticmethod
    async def delete(executor: Executor, service_name: str, on_output: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
        """Arrête, désactive et supprime un service (systemd sous Linux, Service/ScheduledTask sous Windows)."""
        if await executor.is_windows():
            if SystemdManager._is_melodi_service(service_name):
                task_name = win_task_name_for_service(service_name)
                await SystemdManager.stop(executor, service_name, on_output=on_output)
                cmd = (
                    f'powershell -NoProfile -Command "'
                    f"schtasks /Delete /TN '{task_name}' /F 2>$null; "
                    f"if (Get-Service -Name '{service_name}' -ErrorAction SilentlyContinue) {{ sc.exe delete '{service_name}' }}\""
                )
            else:
                await SystemdManager.stop(executor, service_name, on_output=on_output)
                cmd = f'sc.exe delete "{service_name}"'
            code, _, stderr = await executor.run(cmd, on_output=on_output)
            return {
                "success": code == 0,
                "message": t("systemd.deleted", name=service_name) if code == 0 else t("systemd.delete_failed", name=service_name, error=stderr.strip())
            }

        svc = shlex.quote(service_name)
        unit_path = shlex.quote(f"/etc/systemd/system/{service_name}.service")
        cmd = (
            f"systemctl stop {svc} 2>/dev/null || true; "
            f"systemctl disable {svc} 2>/dev/null || true; "
            f"rm -f {unit_path} && "
            f"systemctl daemon-reload && "
            f"(systemctl reset-failed {svc} 2>/dev/null || true)"
        )
        code, _, stderr = await executor.run_sudo(cmd, on_output=on_output)
        return {
            "success": code == 0,
            "message": t("systemd.deleted", name=service_name) if code == 0 else t("systemd.delete_failed", name=service_name, error=stderr.strip())
        }

    @staticmethod
    async def get_logs(executor: Executor, service_name: str, lines: int = 100, log_path: Optional[str] = None) -> List[str]:
        """Extrait les logs récents (journalctl sous Linux, fichier log / EventLog sous Windows)."""
        if await executor.is_windows():
            if SystemdManager._is_melodi_service(service_name):
                target_log = log_path or f"C:\\{service_name}\\melodi.log"
                cmd = (
                    f'powershell -NoProfile -Command "'
                    f"if (Test-Path '{target_log}') {{ Get-Content -Path '{target_log}' -Tail {lines} }} "
                    f"else {{ 'No log file found at {target_log}' }}\""
                )
            else:
                cmd = (
                    f'powershell -NoProfile -Command "'
                    f"Get-EventLog -LogName Application -Source 'PostgreSQL*' -Newest {lines} -ErrorAction SilentlyContinue "
                    f"| Format-Table TimeGenerated,EntryType,Message -AutoSize | Out-String\""
                )
            code, stdout, _ = await executor.run(cmd)
            if code == 0 and stdout.strip():
                return stdout.splitlines()
            return [t("systemd.logs_error", name=service_name)]

        code, stdout, _ = await executor.run(f"journalctl -u {service_name} -n {lines} --no-pager")
        if code == 0:
            return stdout.splitlines()
        return [t("systemd.logs_error", name=service_name)]

    @staticmethod
    async def check_availability(executor: Executor, service_name: str, port: int) -> Dict[str, bool]:
        """Vérifie si le nom de service et le port TCP sont disponibles sur la machine cible."""
        service_exists = await SystemdManager.is_installed(executor, service_name)

        if await executor.is_windows():
            cmd = (
                f'powershell -NoProfile -Command "'
                f"if (Get-NetTCPConnection -LocalPort {int(port)} -State Listen -ErrorAction SilentlyContinue) "
                f"{{ 'used' }} else {{ 'free' }}\""
            )
            code, stdout, _ = await executor.run(cmd, timeout=5.0)
            port_in_use = code == 0 and stdout.strip().lower() == "used"
        else:
            cmd = f'sh -c "ss -tlnH sport = :{int(port)} 2>/dev/null | grep -q . && echo used || echo free"'
            code, stdout, _ = await executor.run(cmd, timeout=5.0)
            port_in_use = code == 0 and "used" in stdout.lower()

        return {
            "service_available": not service_exists,
            "port_available": not port_in_use,
            "available": (not service_exists) and (not port_in_use),
        }
