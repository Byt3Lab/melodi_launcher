"""
ServicePanel: Surveillance et contrôle des services systemd (MELODI ERP, PostgreSQL, Redis).
"""

import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Dict, Any, List
from app.remote.executor import Executor
from app.system.systemd_manager import SystemdManager
from app.ui.theme import (
    COLOR_CARD, COLOR_TEXT_MAIN, COLOR_TEXT_MUTED, COLOR_PRIMARY,
    COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING, FONT_SUBTITLE, FONT_BODY_BOLD
)

SERVICES = [
    {
        "id": "melodi",
        "name": "MELODI ERP",
        "service_name": "melodi",
        "port": 5000,
        "description": "Application principale MELODI ERP"
    },
    {
        "id": "postgresql",
        "name": "PostgreSQL",
        "service_name": "postgresql",
        "port": 5432,
        "description": "Base de données relationnelle"
    },
    {
        "id": "redis",
        "name": "Redis Server",
        "service_name": "redis-server",
        "port": 6379,
        "description": "Cache en mémoire & files de tâches"
    }
]

class ServicePanel(ttk.Frame):
    def __init__(self, parent, get_current_executor: Callable[[], Executor], console_panel, async_worker):
        super().__init__(parent, style="Card.TFrame")
        self.get_current_executor = get_current_executor
        self.console_panel = console_panel
        self.async_worker = async_worker

        self.service_widgets: Dict[str, Dict[str, Any]] = {}

        self._build_ui()

    def _build_ui(self):
        # 1. Barre d'action supérieure
        top_bar = ttk.Frame(self, style="Card.TFrame")
        top_bar.pack(fill=tk.X, padx=10, pady=(10, 8))

        title_lbl = ttk.Label(
            top_bar,
            text="⚙️ État et Contrôle des Services Système",
            font=FONT_SUBTITLE,
            foreground=COLOR_PRIMARY,
            style="Card.TLabel"
        )
        title_lbl.pack(side=tk.LEFT)

        refresh_btn = ttk.Button(top_bar, text="🔄 Rafraîchir les statuts", command=self.refresh_statuses)
        refresh_btn.pack(side=tk.RIGHT, padx=5)

        open_browser_btn = ttk.Button(
            top_bar,
            text="🌐 Ouvrir MELODI ERP",
            style="Primary.TButton",
            command=self.open_melodi_browser
        )
        open_browser_btn.pack(side=tk.RIGHT, padx=5)

        # 2. Cartes de services
        for srv in SERVICES:
            card = ttk.LabelFrame(self, text=f" {srv['name']} (Port {srv['port']}) ", padding=10)
            card.pack(fill=tk.X, padx=10, pady=6)

            info_row = ttk.Frame(card, style="Card.TFrame")
            info_row.pack(fill=tk.X)

            desc_lbl = ttk.Label(info_row, text=srv["description"], style="CardMuted.TLabel")
            desc_lbl.pack(side=tk.LEFT)

            status_badge = ttk.Label(
                info_row,
                text="⚪ Statut : Inconnu",
                font=FONT_BODY_BOLD,
                foreground=COLOR_TEXT_MUTED,
                style="Card.TLabel"
            )
            status_badge.pack(side=tk.RIGHT)

            # Ligne de boutons d'action
            btn_row = ttk.Frame(card, style="Card.TFrame")
            btn_row.pack(fill=tk.X, pady=(8, 0))

            start_btn = ttk.Button(
                btn_row,
                text="▶ Démarrer",
                style="Success.TButton",
                command=lambda s=srv["service_name"]: self._control_service(s, "start")
            )
            start_btn.pack(side=tk.LEFT, padx=(0, 6))

            stop_btn = ttk.Button(
                btn_row,
                text="⏹ Arrêter",
                style="Danger.TButton",
                command=lambda s=srv["service_name"]: self._control_service(s, "stop")
            )
            stop_btn.pack(side=tk.LEFT, padx=(0, 6))

            restart_btn = ttk.Button(
                btn_row,
                text="🔄 Redémarrer",
                command=lambda s=srv["service_name"]: self._control_service(s, "restart")
            )
            restart_btn.pack(side=tk.LEFT, padx=(0, 6))

            logs_btn = ttk.Button(
                btn_row,
                text="📜 Voir Logs",
                command=lambda s=srv["service_name"]: self._view_service_logs(s)
            )
            logs_btn.pack(side=tk.LEFT)

            self.service_widgets[srv["id"]] = {
                "config": srv,
                "badge": status_badge,
                "start_btn": start_btn,
                "stop_btn": stop_btn,
                "restart_btn": restart_btn
            }

    def refresh_statuses(self):
        """Interroge l'état des services via systemctl is-active."""
        executor = self.get_current_executor()
        if not executor:
            return

        async def _check_all():
            results = {}
            for srv in SERVICES:
                s_name = srv["service_name"]
                is_active = await SystemdManager.is_active(executor, s_name)
                results[srv["id"]] = is_active
            return results

        def _on_done(results):
            for s_id, is_active in results.items():
                w = self.service_widgets.get(s_id)
                if w:
                    if is_active:
                        w["badge"].config(text="🟢 Actif (En cours d'exécution)", foreground=COLOR_SUCCESS)
                    else:
                        w["badge"].config(text="🔴 Inactif (Arrêté)", foreground=COLOR_DANGER)

        def _on_error(exc):
            self.console_panel.append_log(f"Avertissement lors de la vérification des services: {exc}", "warning")

        self.async_worker.run_coroutine(_check_all(), on_done=_on_done, on_error=_on_error)

    def _control_service(self, service_name: str, action: str):
        executor = self.get_current_executor()
        if not executor:
            messagebox.showerror("Erreur", "Aucune cible sélectionnée.")
            return

        self.console_panel.append_log(f"==> Exécution de {action} sur {service_name}...", "info")

        async def _do_action():
            if action == "start":
                return await SystemdManager.start(executor, service_name, on_output=self.console_panel.append_log)
            elif action == "stop":
                return await SystemdManager.stop(executor, service_name, on_output=self.console_panel.append_log)
            elif action == "restart":
                return await SystemdManager.restart(executor, service_name, on_output=self.console_panel.append_log)

        def _on_done(res):
            if res.get("success"):
                self.console_panel.append_log(f"✓ {res.get('message')}", "success")
            else:
                self.console_panel.append_log(f"❌ {res.get('message')}", "error")
            self.refresh_statuses()

        def _on_error(exc):
            self.console_panel.append_log(f"❌ Erreur: {exc}", "error")

        self.async_worker.run_coroutine(_do_action(), on_done=_on_done, on_error=_on_error)

    def _view_service_logs(self, service_name: str):
        executor = self.get_current_executor()
        if not executor:
            return

        self.console_panel.append_log(f"==> Récupération des logs journalctl pour {service_name}...", "info")

        async def _fetch_logs():
            return await SystemdManager.get_logs(executor, service_name, lines=60)

        def _on_done(lines: List[str]):
            for line in lines:
                self.console_panel.append_log(line)

        def _on_error(exc):
            self.console_panel.append_log(f"❌ Erreur logs: {exc}", "error")

        self.async_worker.run_coroutine(_fetch_logs(), on_done=_on_done, on_error=_on_error)

    def open_melodi_browser(self):
        """Ouvre l'ERP MELODI dans le navigateur web par défaut."""
        executor = self.get_current_executor()
        host = "localhost"
        if executor and hasattr(executor, "host") and executor.host not in ("127.0.0.1", "localhost"):
            host = executor.host
        url = f"http://{host}:5000"
        webbrowser.open(url)
