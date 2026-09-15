"""
Abstract Base Class for all managed services (MELODI, PostgreSQL, Redis, Nginx, Celery).
Works with any Executor (Local or Remote SSH).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from app.remote.executor import Executor

class BaseService(ABC):
    def __init__(self, name: str, display_name: str, description: str = "", port: int = 0):
        self.name = name
        self.display_name = display_name
        self.description = description
        self.port = port

    @abstractmethod
    async def is_installed(self, executor: Executor) -> bool:
        pass

    @abstractmethod
    async def status(self, executor: Executor) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def start(self, executor: Executor) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def stop(self, executor: Executor) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def restart(self, executor: Executor) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_logs(self, executor: Executor, lines: int = 100) -> List[str]:
        pass
