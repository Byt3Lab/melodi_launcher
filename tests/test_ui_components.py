"""
Tests unitaires pour les composants UI Tkinter et le pont asynchrone de MELODI Launcher.
"""

import pytest
import tkinter as tk
from app.ui.theme import apply_theme
from app.ui.async_worker import AsyncWorker
from app.ui.components.console_panel import ConsolePanel
from app.ui.components.server_panel import ServerPanel
from app.ui.components.install_panel import InstallPanel
from app.ui.components.service_panel import ServicePanel
from app.ui.components.system_panel import SystemPanel
from app.ui.main_window import MainWindow
from app.core.server_manager import ServerManager
from app.remote.local_executor import LocalExecutor

@pytest.fixture(scope="module")
def root_window():
    """Initialise une racine Tkinter pour les tests en mode headless."""
    try:
        root = tk.Tk()
        root.withdraw() # Cacher la fenêtre
        apply_theme(root)
        yield root
        root.destroy()
    except tk.TclError:
        pytest.skip("Serveur d'affichage X11/Wayland non disponible pour tester Tkinter")

def test_async_worker_lifecycle(root_window):
    worker = AsyncWorker(root_window)
    assert worker.loop is not None
    assert worker.loop.is_running()
    worker.stop()

def test_console_panel(root_window):
    console = ConsolePanel(root_window)
    assert console.step_label["text"] == "Prêt"

    console.set_progress(45, "Étape de test")
    assert console.percent_label["text"] == "45%"
    assert console.step_label["text"] == "Étape de test"

    console.append_log("Test message de log", "info")
    content = console.text_area.get("1.0", tk.END)
    assert "Test message de log" in content

    console.clear_logs()
    content_cleared = console.text_area.get("1.0", tk.END).strip()
    assert content_cleared == ""

def test_server_panel(root_window):
    worker = AsyncWorker(root_window)
    server_mgr = ServerManager()
    server_panel = ServerPanel(root_window, server_mgr, worker)

    assert server_panel.target_type_var.get() == "local"
    executor = server_panel.get_executor()
    assert isinstance(executor, LocalExecutor)

    worker.stop()

def test_install_panel(root_window):
    worker = AsyncWorker(root_window)
    console = ConsolePanel(root_window)
    local_exec = LocalExecutor()

    install_panel = InstallPanel(root_window, lambda: local_exec, console, worker)
    assert install_panel.target_dir_var.get() == "/opt/melodi"
    assert install_panel.install_melodi_var.get() is True
    assert install_panel.install_pg_var.get() is True
    assert install_panel.install_redis_var.get() is True

    worker.stop()

def test_service_panel(root_window):
    worker = AsyncWorker(root_window)
    console = ConsolePanel(root_window)
    local_exec = LocalExecutor()

    service_panel = ServicePanel(root_window, lambda: local_exec, console, worker)
    assert "melodi" in service_panel.service_widgets
    assert "postgresql" in service_panel.service_widgets
    assert "redis" in service_panel.service_widgets

    worker.stop()

def test_system_panel(root_window):
    worker = AsyncWorker(root_window)
    console = ConsolePanel(root_window)
    local_exec = LocalExecutor()

    system_panel = SystemPanel(root_window, lambda: local_exec, console, worker)
    assert system_panel.cpu_card is not None
    assert system_panel.ram_card is not None
    assert system_panel.disk_card is not None
    assert system_panel.uptime_card is not None

    worker.stop()

def test_main_window_integration(root_window):
    import time
    # Instancier MainWindow avec root_window
    app = MainWindow(root_window)
    assert app.server_panel is not None
    assert app.install_panel is not None
    assert app.service_panel is not None
    assert app.system_panel is not None
    assert app.console_panel is not None
    assert app.get_current_executor() is not None

    # Test changement d'onglet sans erreur
    app.notebook.select(1)
    app._on_tab_changed(None)
    app.notebook.select(2)
    app._on_tab_changed(None)

    time.sleep(0.3)
    app.async_worker.stop()
