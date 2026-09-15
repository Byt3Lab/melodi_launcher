"""
LogManager for reading, writing, and tailing process logs cleanly and efficiently.
"""

import os
from typing import List
from app.config.settings import SettingsManager

class LogManager:
    def __init__(self, settings: SettingsManager):
        self.settings = settings

    @property
    def log_file_path(self) -> str:
        return self.settings.get_log_file_path()

    def ensure_log_dir_exists(self):
        """S'assure que le dossier contenant le fichier de log existe."""
        os.makedirs(os.path.dirname(self.log_file_path), exist_ok=True)

    def get_recent_logs(self, lines: int = 200) -> List[str]:
        """
        Lit efficacement les dernières 'lines' lignes du fichier de log
        sans charger l'intégralité du fichier en mémoire.
        """
        file_path = self.log_file_path
        if not os.path.exists(file_path):
            return []

        try:
            with open(file_path, "rb") as f:
                f.seek(0, os.SEEK_END)
                file_size = f.tell()
                if file_size == 0:
                    return []

                buffer_size = 8192
                block = file_size
                lines_found = []
                remaining_bytes = file_size
                data = b""

                while remaining_bytes > 0 and len(lines_found) <= lines:
                    read_size = min(buffer_size, remaining_bytes)
                    block -= read_size
                    f.seek(block)
                    chunk = f.read(read_size)
                    data = chunk + data
                    remaining_bytes -= read_size
                    lines_found = data.splitlines()

                decoded_lines = [
                    line.decode("utf-8", errors="replace")
                    for line in lines_found[-lines:]
                ]
                return decoded_lines
        except Exception as e:
            return [f"Erreur lors de la lecture des logs: {e}"]

    def clear_logs(self) -> bool:
        """Vide le contenu du fichier de log."""
        file_path = self.log_file_path
        try:
            self.ensure_log_dir_exists()
            with open(file_path, "w", encoding="utf-8") as f:
                f.truncate(0)
            return True
        except Exception as e:
            print(f"[LogManager] Error clearing logs: {e}")
            return False

    def get_log_info(self) -> dict:
        """Retourne des informations sur le fichier de log (existence, taille, chemin)."""
        file_path = self.log_file_path
        exists = os.path.exists(file_path)
        size_bytes = os.path.getsize(file_path) if exists else 0
        return {
            "path": file_path,
            "exists": exists,
            "size_bytes": size_bytes,
            "size_kb": round(size_bytes / 1024, 2)
        }
