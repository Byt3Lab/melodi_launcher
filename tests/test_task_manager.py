"""
Tests for TaskManager
"""

import asyncio
import pytest
from app.core.task_manager import TaskManager, TaskProgress

@pytest.mark.asyncio
async def test_task_manager_execution():
    tm = TaskManager()

    async def dummy_job(task: TaskProgress):
        task.update(50, "Étape intermédiaire...")
        await asyncio.sleep(0.1)
        task.complete("Job terminé.")

    task = tm.create_task("Test Job", "local", dummy_job)
    assert task.task_id is not None

    await asyncio.sleep(0.2)
    status = tm.get_task(task.task_id)
    assert status["status"] == "SUCCESS"
    assert status["progress"] == 100

@pytest.mark.asyncio
async def test_task_manager_cancellation():
    tm = TaskManager()

    cancelled_event = asyncio.Event()

    async def long_running_job(task: TaskProgress):
        task.update(10, "Démarrage job long...")
        try:
            await asyncio.sleep(10.0)
        except asyncio.CancelledError:
            cancelled_event.set()
            raise

    task = tm.create_task("Long Job", "local", long_running_job)
    assert task.task_id is not None

    await asyncio.sleep(0.05)
    status = tm.get_task(task.task_id)
    assert status["status"] == "RUNNING"

    # Annulation
    cancelled = tm.cancel_task(task.task_id)
    assert cancelled is True

    await asyncio.sleep(0.05)
    status_after = tm.get_task(task.task_id)
    assert status_after["status"] == "CANCELLED"
    assert cancelled_event.is_set()
    assert any("interrompue" in log.lower() for log in status_after["logs"])
