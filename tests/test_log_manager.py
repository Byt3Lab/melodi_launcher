"""
Tests for LogManager
"""

import os
import pytest
from app.config.settings import SettingsManager
from app.services.log_manager import LogManager

def test_log_manager_tail_and_clear(tmp_path):
    config_file = os.path.join(tmp_path, "config.json")
    log_file = os.path.join(tmp_path, "logs", "test.log")
    
    sm = SettingsManager(config_file)
    sm.update({"logging": {"file_path": log_file}})
    
    lm = LogManager(sm)
    lm.ensure_log_dir_exists()
    
    # Write test log lines
    with open(log_file, "w", encoding="utf-8") as f:
        for i in range(50):
            f.write(f"Line {i}\n")
            
    recent = lm.get_recent_logs(lines=10)
    assert len(recent) == 10
    assert recent[-1] == "Line 49"
    assert recent[0] == "Line 40"
    
    info = lm.get_log_info()
    assert info["exists"] is True
    assert info["size_bytes"] > 0
    
    # Test clearing logs
    lm.clear_logs()
    assert len(lm.get_recent_logs()) == 0
