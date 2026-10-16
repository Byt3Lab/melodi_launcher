"""
SSHExecutor: Implémentation de Executor pour les serveurs distants via SSH (Support clés & mots de passe).
"""

import asyncio
import time
from typing import Tuple, Dict, Any, Optional, Callable
import asyncssh
from app.remote.executor import Executor

class SSHExecutor(Executor):
    def __init__(
        self,
        host: str,
        port: int = 22,
        username: str = "root",
        key_path: Optional[str] = None,
        password: Optional[str] = None,
        sudo_password: Optional[str] = None
    ):
        super().__init__(name=f"SSH ({username}@{host}:{port})")
        self.host = host
        self.port = port
        self.username = username
        self.key_path = key_path
        self.password = password
        self.sudo_password = sudo_password or password
        self._conn: Optional[asyncssh.SSHClientConnection] = None
        self._lock = asyncio.Lock()

    async def connect(self) -> bool:
        """Établit la connexion SSH avec clé ou mot de passe."""
        async with self._lock:
            if self._conn is not None:
                return True
            try:
                kwargs = {
                    "host": self.host,
                    "port": self.port,
                    "username": self.username,
                    "known_hosts": None, # En prod, valider les empreintes
                    "login_timeout": 10.0
                }
                if self.key_path:
                    kwargs["client_keys"] = [self.key_path]
                    if self.password:
                        kwargs["passphrase"] = self.password
                elif self.password:
                    kwargs["password"] = self.password

                self._conn = await asyncio.wait_for(
                    asyncssh.connect(**kwargs),
                    timeout=12.0
                )
                return True
            except Exception as e:
                print(f"[SSHExecutor] Connection failed to {self.host}: {e}")
                self._conn = None
                return False

    async def disconnect(self) -> None:
        """Ferme la connexion SSH."""
        async with self._lock:
            if self._conn:
                try:
                    self._conn.close()
                    await self._conn.wait_closed()
                except Exception:
                    pass
                self._conn = None

    async def is_connected(self) -> bool:
        """Vérifie si le socket SSH est ouvert."""
        return self._conn is not None

    async def run(
        self,
        command: str,
        timeout: Optional[float] = None,
        on_output: Optional[Callable[[str], None]] = None
    ) -> Tuple[int, str, str]:
        """Exécute une commande distante via le canal SSH ouvert avec streaming temps réel."""
        if not await self.is_connected():
            connected = await self.connect()
            if not connected:
                return (-1, "", f"Impossible d'établir la connexion SSH avec {self.host}:{self.port}")

        try:
            assert self._conn is not None

            # Mode rapide sans streaming si pas de callback
            if on_output is None:
                try:
                    if timeout is not None and timeout > 0:
                        result = await asyncio.wait_for(
                            self._conn.run(command, check=False),
                            timeout=timeout
                        )
                    else:
                        result = await self._conn.run(command, check=False)

                    return (
                        result.exit_status or 0,
                        str(result.stdout or ""),
                        str(result.stderr or "")
                    )
                except asyncio.TimeoutError:
                    return (-1, "", f"Timeout SSH après {timeout}s sur la commande: {command}")

            # Mode streaming temps réel via process
            proc = await self._conn.create_process(command, encoding="utf-8")
            stdout_lines: list[str] = []
            stderr_lines: list[str] = []

            async def _stream_reader(reader, accumulator: list[str]):
                while True:
                    line = await reader.readline()
                    if not line:
                        break
                    accumulator.append(line)
                    try:
                        clean_line = line.rstrip("\r\n")
                        if clean_line and on_output:
                            on_output(clean_line)
                    except Exception:
                        pass

            try:
                gather_coro = asyncio.gather(
                    _stream_reader(proc.stdout, stdout_lines),
                    _stream_reader(proc.stderr, stderr_lines),
                    proc.wait()
                )
                if timeout is not None and timeout > 0:
                    await asyncio.wait_for(gather_coro, timeout=timeout)
                else:
                    await gather_coro

                exit_code = proc.exit_status if proc.exit_status is not None else 0
                return (
                    exit_code,
                    "".join(stdout_lines),
                    "".join(stderr_lines)
                )
            except asyncio.TimeoutError:
                try:
                    proc.terminate()
                    await proc.wait()
                except Exception:
                    pass
                return (-1, "".join(stdout_lines), f"Timeout SSH après {timeout}s sur la commande: {command}")
            except asyncio.CancelledError:
                try:
                    proc.terminate()
                    await proc.wait()
                except Exception:
                    pass
                raise
        except asyncio.CancelledError:
            raise
        except Exception as e:
            await self.disconnect()
            return (-1, "", f"Erreur SSH: {str(e)}")

    async def test_connection(self) -> Dict[str, Any]:
        """Teste la réactivité SSH et l'authentification."""
        start = time.time()
        success = await self.connect()
        if not success:
            return {
                "success": False,
                "latency_ms": 0,
                "system_uname": "",
                "error": f"Connexion SSH impossible à {self.username}@{self.host}:{self.port}"
            }

        code, stdout, stderr = await self.run("uname -a", timeout=5.0)
        latency = round((time.time() - start) * 1000, 2)

        # Tester sudo
        sudo_ok = False
        sudo_code, _, _ = await self.run_sudo("whoami", timeout=5.0)
        if sudo_code == 0:
            sudo_ok = True

        return {
            "success": code == 0,
            "latency_ms": latency,
            "system_uname": stdout.strip() if code == 0 else "",
            "sudo_ready": sudo_ok,
            "error": stderr.strip() if code != 0 else (None if sudo_ok else "Attention: sudo requiert un mot de passe ou NOPASSWD")
        }

