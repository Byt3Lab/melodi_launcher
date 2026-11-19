"""
i18n: Lightweight JSON-based internationalization module (FR / EN) with no Qt dependency.
"""

import json
import locale
import os
from typing import Callable, Dict
from app.utils.helpers import resource_path

SUPPORTED: Dict[str, str] = {
    "fr": "Français",
    "en": "English",
}
FALLBACK: str = "en"

_catalogs: Dict[str, Dict[str, str]] = {}
_listeners: list[Callable[[str], None]] = []


def _load(lang: str) -> Dict[str, str]:
    if lang not in _catalogs:
        path = resource_path(os.path.join("locales", f"{lang}.json"))
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                _catalogs[lang] = json.load(f)
        else:
            _catalogs[lang] = {}
    return _catalogs[lang]


def reload_catalogs() -> None:
    """Vide le cache des catalogues (utile pour les tests)."""
    _catalogs.clear()


def detect_system_language() -> str:
    """Détecte la langue du système (fr ou en par défaut)."""
    raw = ""
    for env_var in ("LC_ALL", "LANG", "LANGUAGE"):
        val = os.environ.get(env_var, "")
        if val and val != "C" and not val.startswith("C."):
            raw = val
            break
    if not raw:
        try:
            raw = locale.getlocale()[0] or ""
        except Exception:
            raw = ""
    code = raw.split("_")[0].split(".")[0].split("-")[0].lower()
    return code if code in SUPPORTED else FALLBACK


_current: str = detect_system_language()


def set_language(lang: str) -> None:
    """Définit la langue active et notifie les écouteurs."""
    global _current
    _current = lang if lang in SUPPORTED else FALLBACK
    for cb in list(_listeners):
        cb(_current)


def get_language() -> str:
    """Retourne le code de la langue active."""
    return _current


def t(key: str, **params) -> str:
    """Traduit une clé, avec repli sur l'anglais puis sur la clé brute."""
    text = _load(_current).get(key) or _load(FALLBACK).get(key) or key
    if params:
        try:
            return text.format(**params)
        except (KeyError, IndexError, ValueError):
            return text
    return text
