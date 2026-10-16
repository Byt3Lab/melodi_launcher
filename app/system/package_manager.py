"""
PackageManager: Abstraction for Linux package management (Debian/Ubuntu apt).
"""

from typing import Dict, Any, Optional, Callable
from app.remote.executor import Executor

class PackageManager:
    @staticmethod
    async def is_installed(executor: Executor, package_name: str) -> bool:
        """Vérifie si un paquet OS est installé (dpkg -s)."""
        code, stdout, _ = await executor.run(f"dpkg -s {package_name}")
        return code == 0 and "Status: install ok installed" in stdout

    @staticmethod
    async def install(
        executor: Executor,
        package_name: str,
        on_output: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """Installe un paquet via apt-get avec gestion sécurisée des privilèges sudo et streaming temps réel."""
        cmd = f"DEBIAN_FRONTEND=noninteractive apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y {package_name}"
        code, stdout, stderr = await executor.run_sudo(cmd, timeout=300.0, on_output=on_output)
        return {
            "success": code == 0,
            "stdout": stdout,
            "stderr": stderr,
            "message": f"Paquet '{package_name}' installé avec succès." if code == 0 else f"Échec d'installation de '{package_name}': {stderr.strip()}"
        }
