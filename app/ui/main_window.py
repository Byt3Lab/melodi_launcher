"""
MainWindow: Fenêtre principale 100% Tkinter pour MELODI Control Center.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from app.core.server_manager import ServerManager
from app.remote.executor import Executor
from app.ui.async_worker import AsyncWorker
from app.ui.theme import (
    apply_theme, COLOR_BG_DARK, COLOR_CARD, COLOR_PRIMARY,
    COLOR_TEXT_MAIN, COLOR_TEXT_MUTED, FONT_TITLE, FONT_SUBTITLE, FONT_BODY_BOLD
)
from app.ui.components.server_panel import ServerPanel
from app.ui.components.install_panel import InstallPanel
from app.ui.components.service_panel import ServicePanel
from app.ui.components.system_panel import SystemPanel
from app.ui.components.console_panel import ConsolePanel
from app.utils.helpers import resource_path

class MainWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("MELODI Control Center - Déploiement & Orchestration")
        self.root.geometry("1060x820")
        self.root.minsize(900, 700)

        # Appliquer l'icône si présente
        icon_path = resource_path("assets/icon.png")
        if os.path.exists(icon_path):
            try:
                img = tk.PhotoImage(file=icon_path)
                self.root.iconphoto(True, img)
            except Exception:
                pass

        apply_theme(self.root)

        # Worker asynchrone non-bloquant et gestionnaire de serveurs
        self.async_worker = AsyncWorker(self.root)
        self.server_manager = ServerManager()

        self._build_layout()

        # Protocole de fermeture propre
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Initialiser avec le serveur par défaut
        self.server_panel._notify_executor_change()

    def _build_layout(self):
        # 1. Header supérieur
        header = ttk.Frame(self.root, style="Card.TFrame")
        header.pack(fill=tk.X, padx=12, pady=(10, 6))

        title_box = ttk.Frame(header, style="Card.TFrame")
        title_box.pack(side=tk.LEFT, padx=12, pady=8)

        title_lbl = ttk.Label(
            title_box,
            text="🎵 MELODI Control Center",
            font=FONT_TITLE,
            foreground=COLOR_PRIMARY,
            style="Card.TLabel"
        )
        title_lbl.pack(anchor=tk.W)

        sub_lbl = ttk.Label(
            title_box,
            text="Orchestration & Déploiement Natif (Local & Distant SSH)",
            font=FONT_BODY_BOLD,
            foreground=COLOR_TEXT_MUTED,
            style="CardMuted.TLabel"
        )
        sub_lbl.pack(anchor=tk.W)

        self.target_badge = ttk.Label(
            header,
            text="Cible : Machine locale",
            font=FONT_BODY_BOLD,
            foreground=COLOR_TEXT_MAIN,
            style="Card.TLabel"
        )
        self.target_badge.pack(side=tk.RIGHT, padx=15, pady=8)

        # 2. Séparateur vertical ou PanedWindow pour un agencement flexible
        paned = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 10))

        # Moitié haute : Configuration et Onglets
        top_container = ttk.Frame(paned, style="TFrame")
        paned.add(top_container, weight=3)

        # Moitié basse : Console de logs temps-réel (instanciée avant les panneaux pour recevoir les logs)
        self.console_panel = ConsolePanel(paned)
        paned.add(self.console_panel, weight=2)

        # Panneau Cible (Local vs SSH)
        self.server_panel = ServerPanel(
            top_container,
            self.server_manager,
            self.async_worker,
            on_server_changed=self._on_server_changed
        )
        self.server_panel.pack(fill=tk.X, pady=(0, 8))

        # Onglets de fonctionnalités
        self.notebook = ttk.Notebook(top_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Vues associées aux onglets
        self.install_panel = InstallPanel(
            self.notebook,
            get_current_executor=self.get_current_executor,
            console_panel=self.console_panel,
            async_worker=self.async_worker
        )
        self.notebook.add(self.install_panel, text="  🚀 Installation & Déploiement  ")

        self.service_panel = ServicePanel(
            self.notebook,
            get_current_executor=self.get_current_executor,
            console_panel=self.console_panel,
            async_worker=self.async_worker
        )
        self.notebook.add(self.service_panel, text="  ⚙️ Services & Processus  ")

        self.system_panel = SystemPanel(
            self.notebook,
            get_current_executor=self.get_current_executor,
            console_panel=self.console_panel,
            async_worker=self.async_worker
        )
        self.notebook.add(self.system_panel, text="  📊 Santé Système  ")

        # Événement de changement d'onglet
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def get_current_executor(self) -> Executor:
        return self.server_panel.get_executor()

    def _on_server_changed(self, executor: Executor):
        name = executor.name if executor else "Inconnu"
        if hasattr(self, "target_badge"):
            self.target_badge.config(text=f"Cible active : {name}")
        if hasattr(self, "console_panel"):
            self.console_panel.append_log(f"Cible d'administration changée vers : {name}", "info")
        # Rafraîchir les statuts des services si on est sur l'onglet services
        if hasattr(self, "notebook") and hasattr(self, "service_panel"):
            try:
                if self.notebook.index("current") == 1:
                    self.service_panel.refresh_statuses()
            except Exception:
                pass

    def _on_tab_changed(self, event):
        idx = self.notebook.index("current")
        if idx == 1: # Onglet Services
            self.service_panel.refresh_statuses()
        elif idx == 2: # Onglet Santé Système
            self.system_panel.refresh_metrics()

    def on_close(self):
        """Arrêt propre des threads de fond et fermeture."""
        try:
            self.async_worker.stop()
        except Exception:
            pass
        self.root.destroy()
