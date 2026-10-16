"""
LocalExecutor: Implémentation de Executor pour la machine locale hôte.
"""

import asyncio
import time
from typing import Tuple, Dict, Any, Optional, Callable
from app.remote.executor import Executor

class LocalExecutor(Executor):
    def __init__(self, password: str = None):
        super().__init__(name="Localhost")
        self.password = password
        self.sudo_password = password

    async def connect(self) -> bool:
        return True

    async def disconnect(self) -> None:
        pass

    async def is_connected(self) -> bool:
        return True

    async def run(
        self,
        command: str,
        timeout: Optional[float] = None,
        on_output: Optional[Callable[[str], None]] = None
    ) -> Tuple[int, str, str]:
        """Exécute une commande shell locale de manière asynchrone avec streaming temps réel."""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout_lines: list[str] = []
            stderr_lines: list[str] = []

            async def _stream_reader(stream, accumulator: list[str]):
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    decoded = line.decode("utf-8", errors="replace")
                    accumulator.append(decoded)
                    if on_output:
                        try:
                            clean_line = decoded.rstrip("\r\n")
                            if clean_line:
                                on_output(clean_line)
                        except Exception:
                            pass

            try:
                gather_coro = asyncio.gather(
                    _stream_reader(process.stdout, stdout_lines),
                    _stream_reader(process.stderr, stderr_lines),
                    process.wait()
                )
                if timeout is not None and timeout > 0:
                    await asyncio.wait_for(gather_coro, timeout=timeout)
                else:
                    await gather_coro

                return (
                    process.returncode or 0,
                    "".join(stdout_lines),
                    "".join(stderr_lines)
                )
            except asyncio.TimeoutError:
                try:
                    process.kill()
                    await process.wait()
                except Exception:
                    pass
                return (-1, "".join(stdout_lines), f"Timeout de la commande après {timeout}s")
            except asyncio.CancelledError:
                try:
                    process.kill()
                    await process.wait()
                except Exception:
                    pass
                raise
        except asyncio.CancelledError:
            raise
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

