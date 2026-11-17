"""
SystemPanel: Affichage des métriques et de la santé système (CPU, RAM, Disque, Uptime).
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional
from app.remote.executor import Executor
from app.system.system_info import SystemInfo
from app.ui.theme import (
    COLOR_CARD, COLOR_TEXT_MAIN, COLOR_TEXT_MUTED, COLOR_PRIMARY,
    COLOR_SUCCESS, FONT_SUBTITLE, FONT_BODY_BOLD, FONT_TITLE
)

class SystemPanel(ttk.Frame):
    def __init__(self, parent, get_current_executor: Callable[[], Executor], console_panel, async_worker):
        super().__init__(parent, style="Card.TFrame")
        self.get_current_executor = get_current_executor
        self.console_panel = console_panel
        self.async_worker = async_worker

        self._build_ui()

    def _build_ui(self):
        top_bar = ttk.Frame(self, style="Card.TFrame")
        top_bar.pack(fill=tk.X, padx=10, pady=(10, 8))

        ttk.Label(
            top_bar,
            text="📊 Ressources et Santé Système",
            font=FONT_SUBTITLE,
            foreground=COLOR_PRIMARY,
            style="Card.TLabel"
        ).pack(side=tk.LEFT)

        refresh_btn = ttk.Button(top_bar, text="🔄 Actualiser les métriques", command=self.refresh_metrics)
        refresh_btn.pack(side=tk.RIGHT)

        cards_container = ttk.Frame(self, style="Card.TFrame")
        cards_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 4 Cartes de métriques : CPU, RAM, Disque, Uptime
        self.cpu_card = self._create_metric_card(cards_container, "⚡ Processeur (CPU)", "0 %", "Utilisation actuelle")
        self.cpu_card["frame"].grid(row=0, column=0, padx=8, pady=8, sticky="nsew")

        self.ram_card = self._create_metric_card(cards_container, "🧠 Mémoire Vive (RAM)", "0 / 0 Go", "0 % utilisé")
        self.ram_card["frame"].grid(row=0, column=1, padx=8, pady=8, sticky="nsew")

        self.disk_card = self._create_metric_card(cards_container, "💾 Espace Disque", "0 / 0 Go", "0 % occupé")
        self.disk_card["frame"].grid(row=1, column=0, padx=8, pady=8, sticky="nsew")

        self.uptime_card = self._create_metric_card(cards_container, "⏱️ Uptime Système", "--", "Temps d'activité")
        self.uptime_card["frame"].grid(row=1, column=1, padx=8, pady=8, sticky="nsew")

        cards_container.grid_columnconfigure(0, weight=1)
        cards_container.grid_columnconfigure(1, weight=1)
        cards_container.grid_rowconfigure(0, weight=1)
        cards_container.grid_rowconfigure(1, weight=1)

    def _create_metric_card(self, parent, title: str, value: str, subtitle: str):
        card = ttk.LabelFrame(parent, text=f" {title} ", padding=15)

        val_lbl = ttk.Label(
            card,
            text=value,
            font=FONT_TITLE,
            foreground=COLOR_PRIMARY,
            style="Card.TLabel"
        )
        val_lbl.pack(anchor=tk.W, pady=(5, 5))

        pbar = ttk.Progressbar(card, orient="horizontal", mode="determinate", style="Horizontal.TProgressbar")
        pbar.pack(fill=tk.X, pady=(0, 6))

        sub_lbl = ttk.Label(card, text=subtitle, style="CardMuted.TLabel")
        sub_lbl.pack(anchor=tk.W)

        return {
            "frame": card,
            "val_lbl": val_lbl,
            "pbar": pbar,
            "sub_lbl": sub_lbl
        }

    def refresh_metrics(self):
        executor = self.get_current_executor()
        if not executor:
            return

        async def _fetch():
            return await SystemInfo.get_metrics(executor)

        def _on_done(metrics):
            if not metrics:
                return

            cpu_pct = metrics.get("cpu_percent", 0)
            self.cpu_card["val_lbl"].config(text=f"{cpu_pct} %")
            self.cpu_card["pbar"]["value"] = cpu_pct
            self.cpu_card["sub_lbl"].config(text=f"Charge CPU globale : {cpu_pct}%")

            ram_used = metrics.get("ram_used_gb", 0)
            ram_total = metrics.get("ram_total_gb", 0)
            ram_pct = metrics.get("ram_percent", 0)
            self.ram_card["val_lbl"].config(text=f"{ram_used} / {ram_total} Go")
            self.ram_card["pbar"]["value"] = ram_pct
            self.ram_card["sub_lbl"].config(text=f"RAM utilisée : {ram_pct}%")

            disk_used = metrics.get("disk_used_gb", 0)
            disk_total = metrics.get("disk_total_gb", 0)
            disk_pct = metrics.get("disk_percent", 0)
            self.disk_card["val_lbl"].config(text=f"{disk_used} / {disk_total} Go")
            self.disk_card["pbar"]["value"] = disk_pct
            self.disk_card["sub_lbl"].config(text=f"Stockage racine : {disk_pct}%")

            uptime_str = metrics.get("uptime_formatted", "--")
            self.uptime_card["val_lbl"].config(text=uptime_str)
            self.uptime_card["pbar"]["value"] = 100
            self.uptime_card["sub_lbl"].config(text="Système opérationnel")

        def _on_error(exc):
            self.console_panel.append_log(f"Impossible de récupérer les métriques: {exc}", "warning")

        self.async_worker.run_coroutine(_fetch(), on_done=_on_done, on_error=_on_error)
