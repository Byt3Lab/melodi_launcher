"""
Tests for ProcessManager
"""

import os
import asyncio
import pytest
from app.config.settings import SettingsManager
from app.services.log_manager import LogManager
from app.services.process_manager import ProcessManager

@pytest.mark.asyncio
async def test_process_manager_start_stop(tmp_path):
    config_file = os.path.join(tmp_path, "config.json")
    log_file = os.path.join(tmp_path, "logs", "test.log")
    
    sm = SettingsManager(config_file)
    sm.update({"logging": {"file_path": log_file}})
    
    lm = LogManager(sm)
    pm = ProcessManager(lm)
    
    # Launch short-lived sleep command
    cmd = ["python3", "-c", "import time; time.sleep(10)"]
    start_res = await pm.start(command=cmd, cwd=str(tmp_path))
    
    assert start_res["success"] is True
    assert start_res["pid"] is not None
    assert await pm.is_running() is True
    
    # Double-start protection test
    start_again = await pm.start(command=cmd, cwd=str(tmp_path))
    assert start_again["success"] is False
    
    # Stop process
    stop_res = await pm.stop()
    assert stop_res["success"] is True
    assert await pm.is_running() is False
