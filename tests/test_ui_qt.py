"""
Tests automatisés de l'interface PySide6 (pytest-qt), du déploiement depuis un dossier local et de la sécurité.
"""

import json
import os
import pytest
from app.core.server_manager import ServerManager
from app.core.task_manager import TaskProgress
from app.installers.melodi import MelodiInstaller
from app.remote.local_executor import LocalExecutor
from app.ui.app_context import AppContext
from app.ui.main_window import MainWindow


@pytest.fixture
def isolated_ctx(tmp_path):
    servers_file = os.path.join(tmp_path, "servers.json")
    sm = ServerManager(servers_file)
    return AppContext(server_manager=sm)


def test_main_window_navigation_and_theme(qtbot, isolated_ctx):
    win = MainWindow(ctx=isolated_ctx)
    qtbot.addWidget(win)

    assert win.stack.currentWidget() is win.pages["dashboard"]

    for key in ("install", "services", "logs", "servers", "dashboard"):
        win.sidebar.select_page(key)
        assert win.stack.currentWidget() is win.pages[key]

    assert isolated_ctx.theme_name == "dark"
    isolated_ctx.toggle_theme()
    assert isolated_ctx.theme_name == "light"
    isolated_ctx.toggle_theme()
    assert isolated_ctx.theme_name == "dark"


def test_install_wizard_validation_and_steps(qtbot, isolated_ctx, tmp_path):
    win = MainWindow(ctx=isolated_ctx)
    qtbot.addWidget(win)
    win.sidebar.select_page("install")
    wiz = win.pages["install"]

    # Step 0: Cible -> Suivant actif
    assert wiz._step == 0
    assert wiz.next_btn.isEnabled() is True
    wiz._go_next()

    # Step 1: Source -> chemin vide ou inexistant désactive Suivant
    assert wiz._step == 1
    wiz.rb_folder.setChecked(True)
    assert wiz.next_btn.isEnabled() is False

    wiz.source_edit.setText(os.path.join(tmp_path, "missing_folder"))
    assert wiz.next_btn.isEnabled() is False

    # Dossier source local existant réactive Suivant
    src_dir = tmp_path / "melodi_source"
    src_dir.mkdir()
    (src_dir / "main.py").write_text("print('melodi')", encoding="utf-8")
    wiz.source_edit.setText(str(src_dir))
    assert wiz.next_btn.isEnabled() is True

    # Mode URL invalide puis valide
    wiz.rb_url.setChecked(True)
    wiz.url_edit.setText("not-a-url")
    assert wiz.next_btn.isEnabled() is False
    wiz.url_edit.setText("https://example.com/melodi.zip")
    assert wiz.next_btn.isEnabled() is True

    wiz._go_next()
    assert wiz._step == 2

    # Step 2: Options (PostgreSQL + venv + service de démarrage automatique)
    assert wiz.chk_pg.isChecked() is True
    assert wiz.chk_venv.isChecked() is True
    assert wiz.chk_service.isChecked() is True
    assert wiz.next_btn.isEnabled() is True

    wiz._go_next()
    assert wiz._step == 3
    assert "MELODI ERP" in wiz.summary_label.text()
    assert "PostgreSQL" in wiz.summary_label.text()


@pytest.mark.asyncio
async def test_melodi_installer_deploy_source_folder_in_place(tmp_path):
    src_dir = tmp_path / "melodi_app"
    src_dir.mkdir()
    (src_dir / "main.py").write_text("print('hello')", encoding="utf-8")

    installer = MelodiInstaller()
    executor = LocalExecutor()
    task = TaskProgress("t1", "Deploy folder", "local")

    res = await installer.deploy_source_folder(executor, task, str(src_dir), str(src_dir))
    assert res == str(src_dir)
    assert not task.is_failed()


def test_toast_and_logs(qtbot, isolated_ctx):
    win = MainWindow(ctx=isolated_ctx)
    qtbot.addWidget(win)
    win.resize(1100, 720)

    isolated_ctx.show_toast("Opération réussie", "success")
    assert len(win.toast_manager._active) == 1

    isolated_ctx.emit_log("✓ Test log line")
    assert "Test log line" in win.pages["logs"].live_view.editor.toPlainText()


def test_servers_json_never_stores_plaintext_passwords(tmp_path):
    servers_file = os.path.join(tmp_path, "servers.json")
    sm = ServerManager(servers_file)
    sm.add_server({
        "name": "Secure SSH",
        "host": "10.0.0.10",
        "port": 22,
        "username": "deploy",
        "auth_method": "password",
        "password": "SuperSecretPassword123!",
        "sudo_password": "SuperSecretSudo456!",
    })

    with open(servers_file, "r", encoding="utf-8") as f:
        raw = f.read()

    assert "SuperSecretPassword123!" not in raw
    assert "SuperSecretSudo456!" not in raw
    data = json.loads(raw)
    assert all("password" not in item and "sudo_password" not in item for item in data)


def test_server_change_reloads_all_pages(qtbot, isolated_ctx):
    res = isolated_ctx.server_manager.add_server({
        "name": "Remote Test",
        "host": "10.0.0.50",
        "port": 22,
        "username": "root",
        "auth_method": "key",
    })
    remote_id = res["server"]["id"]

    win = MainWindow(ctx=isolated_ctx)
    qtbot.addWidget(win)
    win._switch_page("services")
    old_pages = dict(win.pages)

    isolated_ctx.set_current_server(remote_id)

    for key, old_page in old_pages.items():
        assert win.pages[key] is not old_page
    assert win.stack.currentWidget() is win.pages["services"]
