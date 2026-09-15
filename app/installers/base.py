"""
BaseInstaller: Abstract Base Class for software installers.
"""

from abc import ABC, abstractmethod
from app.remote.executor import Executor
from app.core.task_manager import TaskProgress

class BaseInstaller(ABC):
    def __init__(self, name: str, display_name: str):
        self.name = name
        self.display_name = display_name

    @abstractmethod
    async def install(self, executor: Executor, task: TaskProgress):
        pass
