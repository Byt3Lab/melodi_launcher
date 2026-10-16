"""
TaskManager: Async background task manager for long operations (Installers, Backups).
"""

import asyncio
import uuid
import time
from typing import Dict, Any, Optional, List, Callable

class TaskProgress:
    def __init__(self, task_id: str, name: str, server_id: str):
        self.task_id = task_id
        self.name = name
        self.server_id = server_id
        self.status = "PENDING"  # PENDING, RUNNING, SUCCESS, FAILED
        self.progress = 0  # 0 to 100
        self.current_step = "Initialisation..."
        self.logs: List[str] = []
        self.error: Optional[str] = None
        self.created_at = time.time()
        self.finished_at: Optional[float] = None

    def update(self, progress: int, step_description: str):
        self.progress = max(0, min(100, progress))
        self.current_step = step_description
        timestamp = time.strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] [{self.progress}%] {step_description}")

    def fail(self, error_message: str):
        self.status = "FAILED"
        self.error = error_message
        self.finished_at = time.time()
        timestamp = time.strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] ❌ ERREUR: {error_message}")

    def cancel(self, message: str = "Tâche interrompue par l'utilisateur."):
        self.status = "CANCELLED"
        self.error = message
        self.finished_at = time.time()
        timestamp = time.strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] ⏹️ {message}")

    def append_log(self, text: str):
        """Ajoute des sorties brutes de commandes ou terminal en direct."""
        if not text:
            return
        lines = text.splitlines() if "\n" in text else [text]
        for line in lines:
            cleaned = line.rstrip("\r\n")
            if cleaned:
                self.logs.append(cleaned)
        # Conserver un historique borné pour éviter l'épuisement mémoire
        if len(self.logs) > 2000:
            self.logs = self.logs[-2000:]

    def complete(self, message: str = "Tâche terminée avec succès."):
        self.status = "SUCCESS"
        self.progress = 100
        self.current_step = message
        self.finished_at = time.time()
        timestamp = time.strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] [100%] ✓ {message}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "server_id": self.server_id,
            "status": self.status,
            "progress": self.progress,
            "current_step": self.current_step,
            "logs": self.logs,
            "error": self.error,
            "created_at": self.created_at,
            "finished_at": self.finished_at,
            "duration_seconds": round((self.finished_at or time.time()) - self.created_at, 1)
        }

class TaskManager:
    def __init__(self):
        self._tasks: Dict[str, TaskProgress] = {}
        self._async_tasks: Dict[str, asyncio.Task] = {}

    def create_task(self, name: str, server_id: str, async_func: Callable[[TaskProgress], Any]) -> TaskProgress:
        """Crée et lance une tâche asynchrone en arrière-plan."""
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        task_progress = TaskProgress(task_id, name, server_id)
        self._tasks[task_id] = task_progress

        # Lancer le coroutine worker en tâche asyncio de fond
        async_task = asyncio.create_task(self._run_task_wrapper(task_progress, async_func))
        self._async_tasks[task_id] = async_task
        return task_progress

    async def _run_task_wrapper(self, task_progress: TaskProgress, async_func: Callable[[TaskProgress], Any]):
        task_progress.status = "RUNNING"
        try:
            await async_func(task_progress)
            if task_progress.status == "RUNNING":
                task_progress.complete()
        except asyncio.CancelledError:
            print(f"[TaskManager] Task {task_progress.task_id} was cancelled")
            if task_progress.status != "CANCELLED":
                task_progress.cancel("Opération interrompue par l'utilisateur.")
        except Exception as e:
            print(f"[TaskManager] Error in task {task_progress.task_id}: {e}")
            task_progress.fail(str(e))
        finally:
            self._async_tasks.pop(task_progress.task_id, None)

    def cancel_task(self, task_id: str) -> bool:
        """Interrompt une tâche en cours d'exécution."""
        task_progress = self._tasks.get(task_id)
        if not task_progress or task_progress.status not in ("PENDING", "RUNNING"):
            return False

        task_progress.cancel("Opération interrompue par l'utilisateur.")
        async_task = self._async_tasks.get(task_id)
        if async_task and not async_task.done():
            async_task.cancel()
        return True

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retourne l'état d'une tâche."""
        task = self._tasks.get(task_id)
        return task.to_dict() if task else None

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Retourne toutes les tâches actives et récentes."""
        return [t.to_dict() for t in self._tasks.values()]
