"""
Settings Manager for MELODI Launcher.
Handles reading, writing, and validating configuration settings stored in JSON.
"""

import json
import os
from typing import Any, Dict
from app.utils.helpers import resource_path, get_project_root

DEFAULT_CONFIG: Dict[str, Any] = {
    "server": {
        "host": "127.0.0.1",
        "port": 8080,
        "debug": False
    },
    "melodi": {
        "name": "MELODI ERP",
        "path": "",
        "python": "",
        "command": ["python3", "main.py"],
        "port": 5000,
        "auto_start": False
    },
    "melodi_websocket": {
        "name": "MELODI WebSocket",
        "path": "",
        "python": "",
        "command": ["python3", "websocket_server.py"],
        "port": 8001,
        "auto_start": False
    },
    "melodi_process_manager": {
        "name": "MELODI Process Manager",
        "path": "",
        "python": "",
        "command": ["python3", "process_manager.py"],
        "port": 5002,
        "auto_start": False
    },
    "logging": {
        "file_path": "logs/melodi.log",
        "max_history_lines": 500
    }
}

class SettingsManager:
    def __init__(self, config_file_path: str = None):
        if config_file_path is None:
            config_file_path = os.path.join(get_project_root(), "config", "config.json")
        self.config_file_path = config_file_path
        self._config: Dict[str, Any] = {}
        self.load()

    def _deep_merge(self, base: dict, override: dict) -> dict:
        """Fusionne récursivement override dans base."""
        merged = base.copy()
        for key, value in override.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._deep_merge(merged[key], value)
            else:
                merged[key] = value
        return merged

    def load(self) -> Dict[str, Any]:
        """Charge la configuration depuis le fichier JSON ou initialise avec les valeurs par défaut."""
        if os.path.exists(self.config_file_path):
            try:
                with open(self.config_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._config = self._deep_merge(DEFAULT_CONFIG, data)
            except Exception as e:
                print(f"[SettingsManager] Error loading config ({e}), falling back to defaults.")
                self._config = json.loads(json.dumps(DEFAULT_CONFIG))
        else:
            self._config = json.loads(json.dumps(DEFAULT_CONFIG))
            self.save()

        # Remplir le chemin par défaut de MELODI s'il est vide
        if not self._config["melodi"].get("path"):
            self._config["melodi"]["path"] = get_project_root()

        return self._config

    def save(self) -> bool:
        """Sauvegarde la configuration actuelle dans le fichier JSON."""
        try:
            os.makedirs(os.path.dirname(self.config_file_path), exist_ok=True)
            with open(self.config_file_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[SettingsManager] Failed to save config: {e}")
            return False

    def get_all(self) -> Dict[str, Any]:
        """Retourne toute la configuration."""
        return self._config

    def get(self, section: str, key: str = None, default: Any = None) -> Any:
        """Récupère une section ou une clé spécifique de la configuration."""
        sec = self._config.get(section, {})
        if key is None:
            return sec
        return sec.get(key, default)

    def update(self, updates: Dict[str, Any]) -> bool:
        """Met à jour les paramètres et sauvegarde la configuration."""
        self._config = self._deep_merge(self._config, updates)
        return self.save()

    def get_melodi_working_dir(self) -> str:
        """Retourne le répertoire de travail configuré pour MELODI."""
        path = self._config.get("melodi", {}).get("path")
        if path and os.path.exists(path):
            return path
        return get_project_root()

    def get_log_file_path(self) -> str:
        """Retourne le chemin absolu du fichier de log."""
        log_path = self._config.get("logging", {}).get("file_path", "logs/melodi.log")
        if os.path.isabs(log_path):
            return log_path
        return os.path.join(get_project_root(), log_path)
