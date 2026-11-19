"""
PackageManager: Cross-platform package management (apt on Linux, winget on Windows).
"""

from typing import Dict, Any, Optional, Callable
from app.i18n import t
from app.remote.executor import Executor

WINDOWS_WINGET_MAP = {
    "postgresql": "PostgreSQL.PostgreSQL",
    "postgresql postgresql-contrib": "PostgreSQL.PostgreSQL",
    "python3": "Python.Python.3.12",
    "git": "Git.Git",
}


class PackageManager:
    @staticmethod
    async def is_installed(executor: Executor, package_name: str) -> bool:
        """Vérifie si un paquet OS est installé (dpkg sous Linux, PowerShell/winget sous Windows)."""
        if await executor.is_windows():
            if "postgresql" in package_name.lower():
                code, stdout, _ = await executor.run(
                    'powershell -NoProfile -Command "(Get-Service -Name \'postgresql*\' -ErrorAction SilentlyContinue).Count"'
                )
                if code == 0 and stdout.strip().isdigit() and int(stdout.strip()) > 0:
                    return True
                code_p, _, _ = await executor.run("where psql")
                return code_p == 0
            if "python" in package_name.lower():
                code, _, _ = await executor.run("where python")
                return code == 0
            winget_id = WINDOWS_WINGET_MAP.get(package_name, package_name)
            code, stdout, _ = await executor.run(f"winget list --id {winget_id} --exact")
            return code == 0 and winget_id.lower() in stdout.lower()

        code, stdout, _ = await executor.run(f"dpkg -s {package_name}")
        return code == 0 and "Status: install ok installed" in stdout

    @staticmethod
    async def install(
        executor: Executor,
        package_name: str,
        on_output: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """Installe un paquet via apt-get (Linux) ou winget (Windows)."""
        if await executor.is_windows():
            winget_id = WINDOWS_WINGET_MAP.get(package_name, package_name)
            cmd = (
                f"winget install --id {winget_id} --exact --silent "
                f"--accept-package-agreements --accept-source-agreements"
            )
            code, stdout, stderr = await executor.run(cmd, timeout=600.0, on_output=on_output)
            return {
                "success": code == 0,
                "stdout": stdout,
                "stderr": stderr,
                "message": t("package.installed", name=package_name) if code == 0 else t("package.install_failed", name=package_name, error=stderr.strip() or stdout.strip())
            }

        cmd = f"DEBIAN_FRONTEND=noninteractive apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y {package_name}"
        code, stdout, stderr = await executor.run_sudo(cmd, timeout=300.0, on_output=on_output)
        return {
            "success": code == 0,
            "stdout": stdout,
            "stderr": stderr,
            "message": t("package.installed", name=package_name) if code == 0 else t("package.install_failed", name=package_name, error=stderr.strip())
        }
