"""
Abstract Base Class Executor for local and remote SSH command execution.
Includes run_sudo helper to execute elevated commands safely with or without NOPASSWD / password stdin.
"""

from abc import ABC, abstractmethod
import shlex
from typing import Tuple, Dict, Any, Optional, Callable

class Executor(ABC):
    def __init__(self, name: str = "Local"):
        self.name = name
        self.password: Optional[str] = None
        self.sudo_password: Optional[str] = None
        self._os_family: Optional[str] = None

    async def detect_os(self) -> str:
        """Détecte automatiquement l'OS de la cible ('windows', 'linux', 'darwin')."""
        if self._os_family:
            return self._os_family
        code, stdout, _ = await self.run("uname -s", timeout=5.0)
        if code == 0:
            low = stdout.strip().lower()
            if "linux" in low:
                self._os_family = "linux"
                return self._os_family
            if "darwin" in low:
                self._os_family = "darwin"
                return self._os_family
            if "mingw" in low or "msys" in low or "cygwin" in low:
                self._os_family = "windows"
                return self._os_family
        code_w, stdout_w, _ = await self.run("ver", timeout=5.0)
        if code_w == 0 and "windows" in stdout_w.lower():
            self._os_family = "windows"
            return self._os_family
        self._os_family = "linux"
        return self._os_family

    async def is_windows(self) -> bool:
        """Retourne True si la machine cible tourne sous Windows."""
        return (await self.detect_os()) == "windows"

    @abstractmethod
    async def connect(self) -> bool:
        """Établit la connexion si nécessaire."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Ferme la connexion si active."""
        pass

    @abstractmethod
    async def is_connected(self) -> bool:
        """Vérifie si la connexion/l'exécuteur est prêt."""
        pass

    @abstractmethod
    async def run(
        self,
        command: str,
        timeout: Optional[float] = None,
        on_output: Optional[Callable[[str], None]] = None
    ) -> Tuple[int, str, str]:
        """
        Exécute une commande et retourne (exit_code, stdout, stderr).
        Transmet les lignes en temps réel à on_output si fourni.
        Si timeout est None ou <= 0, s'exécute sans limite de temps.
        """
        pass

    async def run_sudo(
        self,
        command: str,
        timeout: Optional[float] = None,
        on_output: Optional[Callable[[str], None]] = None
    ) -> Tuple[int, str, str]:
        """
        Exécute une commande avec privilèges administrateur (sudo sous Linux, direct sous Windows).
        Gère intelligemment l'utilisateur root, sudo -n (NOPASSWD) et sudo -S (mot de passe).
        Transmet les sorties en temps réel via on_output.
        """
        # 0. Sous Windows, pas de sudo/bash : exécuter directement
        if await self.is_windows():
            return await self.run(command, timeout=timeout, on_output=on_output)

        # 1. Vérifier si l'utilisateur courant est déjà root
        code_root, stdout_root, _ = await self.run("whoami", timeout=5.0)
        if code_root == 0 and stdout_root.strip() == "root":
            return await self.run(command, timeout=timeout, on_output=on_output)

        # 2. Essayer sudo non-interactif (sudo -n) pour le mode NOPASSWD
        sudo_n_cmd = f"sudo -n bash -c {shlex.quote(command)}"
        code, stdout, stderr = await self.run(sudo_n_cmd, timeout=timeout, on_output=on_output)

        if code == 0:
            return code, stdout, stderr

        # 3. Si un mot de passe est configuré sur l'exécuteur, utiliser sudo -S via stdin
        password = getattr(self, "sudo_password", None) or getattr(self, "password", None)
        if password:
            sudo_s_cmd = f"echo {shlex.quote(password)} | sudo -S -p '' bash -c {shlex.quote(command)}"
            return await self.run(sudo_s_cmd, timeout=timeout, on_output=on_output)

        # 4. Sinon, retourner un message explicatif clair si le mot de passe est demandé
        err_msg = (
            "Privilèges administrateur (sudo) requis.\n"
            "Conseil: Spécifiez le mot de passe sudo dans la configuration du serveur."
        )
        if "password" in stderr.lower() or "terminal" in stderr.lower() or "askpass" in stderr.lower() or "sudo" in stderr.lower():
            if on_output:
                on_output(f"❌ {err_msg}")
            return (1, stdout, err_msg)

        return code, stdout, stderr

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """Teste la connectivité et retourne des métriques de diagnostic."""
        pass

    @abstractmethod
    async def upload_file(
        self,
        local_path: str,
        remote_path: str,
        on_progress: Optional[Callable[[int, int], None]] = None
    ) -> Tuple[bool, str]:
        """
        Transfère un fichier local vers la machine cible (locale ou distante via SFTP).
        Retourne (success, error_message).
        """
        pass

    @abstractmethod
    async def download_file(
        self,
        url: str,
        destination_path: str,
        on_output: Optional[Callable[[str], None]] = None
    ) -> Tuple[bool, str]:
        """
        Télécharge un fichier distant depuis une URL vers la machine cible.
        Retourne (success, error_message).
        """
        pass

