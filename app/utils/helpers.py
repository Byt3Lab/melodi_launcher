"""
Utility functions for MELODI Launcher.
"""

import os
import sys

def get_project_root() -> str:
    """Retourne le répertoire racine du projet en dev ou sous PyInstaller."""
    if getattr(sys, 'frozen', False):
        # Sous PyInstaller executable, sys.executable est le binaire
        return os.path.dirname(sys.executable)
    # En mode dev: répertoire parent de app/
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(current_dir, "..", ".."))

def resource_path(relative_path: str) -> str:
    """
    Retourne le chemin absolu vers une ressource (templates, static, etc.),
    compatible avec le mode développement et le bundle PyInstaller (_MEIPASS).
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(get_project_root(), relative_path)
