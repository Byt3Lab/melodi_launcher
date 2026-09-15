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
