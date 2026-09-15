"""
Abstract base class for all managed services in MELODI Launcher.
Allows adding future services (Redis, Celery, PostgreSQL, etc.) easily.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseService(ABC):
    def __init__(self, name: str, display_name: str, description: str = ""):
        self.name = name
        self.display_name = display_name
        self.description = description

    @abstractmethod
    async def start(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def stop(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def restart(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def status(self) -> Dict[str, Any]:
        pass
