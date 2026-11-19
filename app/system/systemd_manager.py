"""
SystemdManager: Cross-platform service management (systemd on Linux, Services/ScheduledTasks on Windows).
"""

from typing import Dict, Any, List, Optional, Callable
from app.i18n import t
from app.remote.executor import Executor


class SystemdManager:
    @staticmethod
    async def _win_service_pattern(service_name: str) -> str:
        return "postgresql*" if "postgres" in service_name.lower() else service_name

    @staticmethod
    async def is_active(executor: Executor, service_name: str) -> bool:
        """Vérifie si un service est actif (systemctl sous Linux, Get-Service / ScheduledTask sous Windows)."""
        if await executor.is_windows():
            if service_name == "melodi":
                cmd = (
                    'powershell -NoProfile -Command "'
                    "$s = Get-Service -Name 'melodi' -ErrorAction SilentlyContinue; "
                    "if ($s -and $s.Status -eq 'Running') { 'active'; exit 0 }; "
                    "$t = Get-ScheduledTask -TaskName 'MELODI_ERP' -ErrorAction SilentlyContinue; "
                    "if ($t -and $t.State -eq 'Running') { 'active' } else { 'inactive' }\""
                )
            else:
                pat = await SystemdManager._win_service_pattern(service_name)
                cmd = (
                    f'powershell -NoProfile -Command "'
                    f"$s = Get-Service -Name '{pat}' -ErrorAction SilentlyContinue | Where-Object {{$_.Status -eq 'Running'}}; "
                    f"if ($s) {{ 'active' }} else {{ 'inactive' }}\""
                )
            code, stdout, _ = await executor.run(cmd)
            return code == 0 and stdout.strip().lower() == "active"

        code, stdout, _ = await executor.run(f"systemctl is-active {service_name}")
        return code == 0 and stdout.strip() == "active"

    @staticmethod
    async def is_installed(executor: Executor, service_name: str) -> bool:
        """Vérifie si un service existe sur le système."""
        if await executor.is_windows():
            if service_name == "melodi":
                cmd = (
                    'powershell -NoProfile -Command "'
                    "$s = Get-Service -Name 'melodi' -ErrorAction SilentlyContinue; "
                    "$t = Get-ScheduledTask -TaskName 'MELODI_ERP' -ErrorAction SilentlyContinue; "
                    "if ($s -or $t) { 'yes' } else { 'no' }\""
                )
            else:
                pat = await SystemdManager._win_service_pattern(service_name)
                cmd = (
                    f'powershell -NoProfile -Command "'
                    f"$s = Get-Service -Name '{pat}' -ErrorAction SilentlyContinue; "
                    f"if ($s) {{ 'yes' }} else {{ 'no' }}\""
                )
            code, stdout, _ = await executor.run(cmd)
            return code == 0 and stdout.strip().lower() == "yes"

        code, stdout, _ = await executor.run(f"systemctl list-unit-files {service_name}.service")
        return code == 0 and service_name in stdout

    @staticmethod
    async def start(executor: Executor, service_name: str, on_output: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
        """Démarre un service (systemd sous Linux, Start-Service / Start-ScheduledTask sous Windows)."""
        if await executor.is_windows():
            if service_name == "melodi":
                cmd = (
                    'powershell -NoProfile -Command "'
                    "$s = Get-Service -Name 'melodi' -ErrorAction SilentlyContinue; "
                    "if ($s) { Start-Service -Name 'melodi' } else { Start-ScheduledTask -TaskName 'MELODI_ERP' }\""
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
            if service_name == "melodi":
                cmd = (
                    'powershell -NoProfile -Command "'
                    "$s = Get-Service -Name 'melodi' -ErrorAction SilentlyContinue; "
                    "if ($s) { Stop-Service -Name 'melodi' -Force } else { Stop-ScheduledTask -TaskName 'MELODI_ERP' }\""
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
            if service_name == "melodi":
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
    async def get_logs(executor: Executor, service_name: str, lines: int = 100) -> List[str]:
        """Extrait les logs récents (journalctl sous Linux, fichier log / EventLog sous Windows)."""
        if await executor.is_windows():
            if service_name == "melodi":
                cmd = (
                    f'powershell -NoProfile -Command "'
                    f"if (Test-Path 'C:\\melodi\\melodi.log') {{ Get-Content -Path 'C:\\melodi\\melodi.log' -Tail {lines} }} "
                    f"else {{ 'No log file found at C:\\melodi\\melodi.log' }}\""
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
