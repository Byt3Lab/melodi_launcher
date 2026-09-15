"""
Abstract Base Class Executor for local and remote SSH command execution.
"""

from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any

class Executor(ABC):
    def __init__(self, name: str = "Local"):
        self.name = name

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

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """Teste la connectivité et retourne des métriques de diagnostic."""
        pass
