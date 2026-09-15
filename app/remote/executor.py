"""
Abstract Base Class Executor for local and remote SSH command execution.
Includes run_sudo helper to execute elevated commands safely with or without NOPASSWD / password stdin.
"""

from abc import ABC, abstractmethod
import shlex
from typing import Tuple, Dict, Any, Optional

class Executor(ABC):
    def __init__(self, name: str = "Local"):
        self.name = name
        self.password: Optional[str] = None

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
    async def run(self, command: str, timeout: float = 30.0) -> Tuple[int, str, str]:
        """
        Exécute une commande et retourne (exit_code, stdout, stderr).
        """
        pass

    async def run_sudo(self, command: str, timeout: float = 30.0) -> Tuple[int, str, str]:
        """
        Exécute une commande avec privilèges administrateur (sudo).
        Gère intelligemment l'utilisateur root, sudo -n (NOPASSWD) et sudo -S (mot de passe).
        """
        # 1. Vérifier si l'utilisateur courant est déjà root
        code_root, stdout_root, _ = await self.run("whoami", timeout=5.0)
        if code_root == 0 and stdout_root.strip() == "root":
            return await self.run(command, timeout=timeout)

        # 2. Essayer sudo non-interactif (sudo -n) pour le mode NOPASSWD
        sudo_n_cmd = f"sudo -n bash -c {shlex.quote(command)}"
        code, stdout, stderr = await self.run(sudo_n_cmd, timeout=timeout)

        if code == 0:
            return code, stdout, stderr

        # 3. Si un mot de passe est configuré sur l'exécuteur, utiliser sudo -S via stdin
        password = getattr(self, "password", None)
        if password:
            sudo_s_cmd = f"echo {shlex.quote(password)} | sudo -S -p '' bash -c {shlex.quote(command)}"
            return await self.run(sudo_s_cmd, timeout=timeout)

        # 4. Sinon, retourner un message explicatif clair si le mot de passe est demandé
        err_msg = (
            "Privilèges administrateur (sudo) requis.\n"
            "Conseil: Spécifiez le mot de passe du serveur dans les paramètres du serveur, "
            "ou configurez l'utilisateur avec NOPASSWD dans /etc/sudoers."
        )
        if "password" in stderr.lower() or "terminal" in stderr.lower() or "askpass" in stderr.lower():
            return (1, stdout, err_msg)

        return code, stdout, stderr

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """Teste la connectivité et retourne des métriques de diagnostic."""
        pass
