"""
LocalExecutor: Implémentation de Executor pour la machine locale hôte.
"""

import asyncio
import time
from typing import Tuple, Dict, Any
from app.remote.executor import Executor

class LocalExecutor(Executor):
    def __init__(self, password: str = None):
        super().__init__(name="Localhost")
        self.password = password


    async def connect(self) -> bool:
        return True

    async def disconnect(self) -> None:
        pass

    async def is_connected(self) -> bool:
        return True

    async def run(self, command: str, timeout: float = 30.0) -> Tuple[int, str, str]:
        """Exécute une commande shell locale de manière asynchrone."""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            try:
                stdout_data, stderr_data = await asyncio.wait_for(process.communicate(), timeout=timeout)
                return (
                    process.returncode or 0,
                    stdout_data.decode("utf-8", errors="replace"),
                    stderr_data.decode("utf-8", errors="replace")
                )
            except asyncio.TimeoutError:
                try:
                    process.kill()
                except Exception:
                    pass
                return (-1, "", f"Timeout de la commande après {timeout}s")
        except Exception as e:
            return (-1, "", f"Erreur d'exécution locale: {str(e)}")

    async def test_connection(self) -> Dict[str, Any]:
        start = time.time()
        code, stdout, stderr = await self.run("uname -a")
        latency = round((time.time() - start) * 1000, 2)

        # Tester également l'élévation sudo
        sudo_ok = False
        sudo_code, _, sudo_err = await self.run_sudo("whoami", timeout=5.0)
        if sudo_code == 0:
            sudo_ok = True

        return {
            "success": code == 0,
            "latency_ms": latency,
            "system_uname": stdout.strip() if code == 0 else "",
            "sudo_ready": sudo_ok,
            "error": stderr.strip() if code != 0 else (None if sudo_ok else "Sudo requiert un mot de passe non configuré")
        }

