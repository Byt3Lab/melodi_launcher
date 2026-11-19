"""
Tests du système multilingue FR / EN (parité, placeholders, couverture, repli, détection, bascule à chaud UI).
"""

import json
import os
import re
import string
import pytest
from PySide6.QtCore import QSettings
from app import i18n
from app.core.server_manager import ServerManager
from app.ui.app_context import AppContext
from app.ui.main_window import MainWindow


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FR_PATH = os.path.join(ROOT, "locales", "fr.json")
EN_PATH = os.path.join(ROOT, "locales", "en.json")


def _load_json(path: str) -> dict[str, str]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _placeholders(text: str) -> set[str]:
    fmt = string.Formatter()
    return {fname for _, fname, _, _ in fmt.parse(text) if fname is not None}


def test_catalog_parity_and_non_empty():
    fr = _load_json(FR_PATH)
    en = _load_json(EN_PATH)

    assert set(fr.keys()) == set(en.keys()), f"Différence de clés: {set(fr.keys()) ^ set(en.keys())}"
    for key in fr:
        assert isinstance(fr[key], str) and fr[key].strip(), f"Valeur vide FR pour {key}"
        assert isinstance(en[key], str) and en[key].strip(), f"Valeur vide EN pour {key}"
        assert _placeholders(fr[key]) == _placeholders(en[key]), f"Placeholders différents pour {key}"


def test_all_used_keys_exist_in_catalogs():
    fr = _load_json(FR_PATH)
    en = _load_json(EN_PATH)
    pattern = re.compile(r'\bt\(\s*["\']([a-z0-9_.]+)["\']')

    used_keys = set()
    for dirpath, _, filenames in os.walk(os.path.join(ROOT, "app")):
        if "__pycache__" in dirpath:
            continue
        for fname in filenames:
            if fname.endswith(".py"):
                with open(os.path.join(dirpath, fname), "r", encoding="utf-8") as f:
                    used_keys.update(pattern.findall(f.read()))

    missing_fr = used_keys - set(fr.keys())
    missing_en = used_keys - set(en.keys())
    assert not missing_fr, f"Clés manquantes dans fr.json: {missing_fr}"
    assert not missing_en, f"Clés manquantes dans en.json: {missing_en}"


def test_fallback_and_interpolation():
    i18n.set_language("fr")
    assert i18n.t("systemd.started", name="melodi") == "Service « melodi » démarré."
    assert i18n.t("non.existent.key") == "non.existent.key"

    i18n.set_language("en")
    assert i18n.t("systemd.started", name="melodi") == 'Service "melodi" started.'


def test_detect_system_language(monkeypatch):
    monkeypatch.setenv("LC_ALL", "fr_FR.UTF-8")
    assert i18n.detect_system_language() == "fr"

    monkeypatch.setenv("LC_ALL", "de_DE.UTF-8")
    assert i18n.detect_system_language() == "en"


def test_hot_language_switch_and_persistence(qtbot, tmp_path):
    settings_path = os.path.join(tmp_path, "settings.ini")
    settings = QSettings(settings_path, QSettings.Format.IniFormat)
    settings.setValue("language", "fr")

    sm = ServerManager(os.path.join(tmp_path, "servers.json"))
    ctx = AppContext(server_manager=sm, settings=settings)
    win = MainWindow(ctx=ctx)
    qtbot.addWidget(win)

    assert win.windowTitle() == "MELODI Control Center"
    assert win.pages["dashboard"].title_lbl.text() == "Tableau de bord"
    assert "Installation" in win.sidebar._nav_buttons["install"][0].text()

    # Bascule à chaud vers l'anglais
    ctx.set_language("en")
    assert win.pages["dashboard"].title_lbl.text() == "Dashboard"
    assert "Install" in win.sidebar._nav_buttons["install"][0].text()
    assert win.pages["install"].title_lbl.text() == "Setup Wizard"
    assert win.pages["services"].title_lbl.text() == "Services (MELODI ERP & PostgreSQL)"

    # Vérification persistance QSettings
    assert settings.value("language") == "en"
