"""
Tests for SettingsManager
"""

import os
import json
import pytest
from app.config.settings import SettingsManager

def test_settings_default_fallback(tmp_path):
    config_file = os.path.join(tmp_path, "config.json")
    sm = SettingsManager(config_file)
    cfg = sm.get_all()
    
    assert cfg["server"]["host"] == "127.0.0.1"
    assert cfg["server"]["port"] == 8080
    assert cfg["melodi"]["port"] == 5000
    assert os.path.exists(config_file)

def test_settings_update(tmp_path):
    config_file = os.path.join(tmp_path, "config.json")
    sm = SettingsManager(config_file)
    
    success = sm.update({
        "server": {"port": 9090},
        "melodi": {"name": "Test ERP"}
    })
    
    assert success is True
    assert sm.get("server", "port") == 9090
    assert sm.get("melodi", "name") == "Test ERP"
    
    # Reload from disk
    sm2 = SettingsManager(config_file)
    assert sm2.get("server", "port") == 9090
