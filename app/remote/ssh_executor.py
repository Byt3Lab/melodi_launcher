"""
SSHExecutor: Implémentation de Executor pour les serveurs distants via SSH (Support clés & mots de passe).
"""

import asyncio
import time
from typing import Tuple, Dict, Any, Optional
import asyncssh
from app.remote.executor import Executor

class SSHExecutor(Executor):
    def __init__(
        self,
        host: str,
        port: int = 22,
        username: str = "root",
        key_path: Optional[str] = None,
        password: Optional[str] = None
    ):
        super().__init__(name=f"SSH ({username}@{host}:{port})")
        self.host = host
        self.port = port
        self.username = username
        self.key_path = key_path
        self.password = password
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
                if self.password:
                    kwargs["password"] = self.password
                elif self.key_path:
                    kwargs["client_keys"] = [self.key_path]

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

    async def run(self, command: str, timeout: float = 30.0) -> Tuple[int, str, str]:
        """Exécute une commande distante via le canal SSH ouvert."""
        if not await self.is_connected():
            connected = await self.connect()
            if not connected:
                return (-1, "", f"Impossible d'établir la connexion SSH avec {self.host}:{self.port}")

        try:
            assert self._conn is not None
            result = await asyncio.wait_for(
                self._conn.run(command, check=False),
                timeout=timeout
            )
            return (
                result.exit_status or 0,
                str(result.stdout or ""),
                str(result.stderr or "")
            )
        except asyncio.TimeoutError:
            return (-1, "", f"Timeout SSH après {timeout}s sur la commande: {command}")
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
        return {
            "success": code == 0,
            "latency_ms": latency,
            "system_uname": stdout.strip() if code == 0 else "",
            "error": stderr.strip() if code != 0 else None
        }
