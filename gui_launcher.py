#!/usr/bin/env python3
"""
Launcher Desktop Tkinter pour MELODI Control Center.
Application Bureau Tkinter qui gère le serveur Web Quart/Hypercorn en arrière-plan.
"""

import os
import sys
import time
import socket
import threading
import asyncio
import webbrowser
import tkinter as tk
from tkinter import messagebox, ttk

from hypercorn.config import Config
from hypercorn.asyncio import serve
from app import create_app
from app.utils.helpers import resource_path, get_project_root


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Vérifie si un port TCP est déjà utilisé."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return False
        except OSError:
            return True


def find_next_free_port(start_port: int = 8080, max_attempts: int = 50) -> int:
    """Trouve le prochain port disponible à partir de start_port."""
    for p in range(start_port, start_port + max_attempts):
        if not is_port_in_use(p):
            return p
    return start_port + 1


class PortSelectionDialog(tk.Toplevel):
    """Formulaire modal permettant de choisir un nouveau port si le port actuel est occupé."""
    def __init__(self, parent, current_port):
        super().__init__(parent)
        self.title("Port Occupé - MELODI Control Center")
        self.geometry("420x260")
        self.resizable(False, False)
        self.configure(bg="#0f172a") # Slate 900
        self.transient(parent)
        self.grab_set()

        self.current_port = current_port
        self.result = None

        next_port = find_next_free_port(current_port + 1)

        # Centrer la fenêtre modale par rapport au parent
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        self.geometry(f"+{parent_x + 20}+{parent_y + 20}")

        title_label = tk.Label(
            self,
            text="⚠️ Port Occupé",
            font=("Inter", 14, "bold"),
            bg="#0f172a",
            fg="#f59e0b"
        )
        title_label.pack(pady=(18, 5))

        msg_label = tk.Label(
            self,
            text=f"Le port {current_port} est actuellement utilisé par un autre service.\nVoulez-vous choisir un autre port d'écoute ?",
            font=("Inter", 10),
            bg="#0f172a",
            fg="#cbd5e1",
            justify=tk.CENTER
        )
        msg_label.pack(pady=(0, 12))

        form_frame = tk.Frame(self, bg="#0f172a")
        form_frame.pack(pady=5)

        port_lbl = tk.Label(
            form_frame,
            text="Nouveau port HTTP :",
            font=("Inter", 10, "bold"),
            bg="#0f172a",
            fg="#f8fafc"
        )
        port_lbl.pack(side=tk.LEFT, padx=(0, 8))

        self.port_entry = tk.Entry(
            form_frame,
            font=("Inter", 11, "bold"),
            bg="#1e293b",
            fg="#38bdf8",
            insertbackground="#f8fafc",
            bd=1,
            relief=tk.SOLID,
            width=8,
            justify=tk.CENTER
        )
        self.port_entry.insert(0, str(next_port))
        self.port_entry.pack(side=tk.LEFT)
        self.port_entry.focus_set()
        self.port_entry.bind("<Return>", lambda e: self.validate())

        self.error_label = tk.Label(
            self,
            text="",
            font=("Inter", 9),
            bg="#0f172a",
            fg="#ef4444"
        )
        self.error_label.pack(pady=(4, 0))

        btn_frame = tk.Frame(self, bg="#0f172a")
        btn_frame.pack(pady=(12, 0))

        cancel_btn = tk.Button(
            btn_frame,
            text="Annuler",
            font=("Inter", 10),
            bg="#334155",
            fg="#f8fafc",
            activebackground="#475569",
            activeforeground="#ffffff",
            bd=0,
            padx=14,
            pady=6,
            cursor="hand2",
            command=self.cancel
        )
        cancel_btn.pack(side=tk.LEFT, padx=6)

        confirm_btn = tk.Button(
            btn_frame,
            text="Valider",
            font=("Inter", 10, "bold"),
            bg="#2563eb",
            fg="#ffffff",
            activebackground="#1d4ed8",
            activeforeground="#ffffff",
            bd=0,
            padx=14,
            pady=6,
            cursor="hand2",
            command=self.validate
        )
        confirm_btn.pack(side=tk.LEFT, padx=6)

    def validate(self):
        val = self.port_entry.get().strip()
        if not val.isdigit():
            self.error_label.config(text="Veuillez saisir un numéro de port valide.")
            return

        port = int(val)
        if port < 1024 or port > 65535:
            self.error_label.config(text="Le port doit être compris entre 1024 et 65535.")
            return

        if is_port_in_use(port):
            self.error_label.config(text=f"Le port {port} est également occupé.")
            return

        self.result = port
        self.destroy()

    def cancel(self):
        self.result = None
        self.destroy()


class MelodiDesktopGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("MELODI Control Center - Desktop Launcher")
        self.root.geometry("520x420")
        self.root.resizable(False, False)
        self.root.configure(bg="#0f172a") # Slate 900

        # Icône application si disponible
        try:
            icon_path = resource_path(os.path.join("assets", "icon.png"))
            if os.path.exists(icon_path):
                img = tk.PhotoImage(file=icon_path)
                self.root.iconphoto(True, img)
        except Exception:
            pass

        self.port = 8080
        self.url = f"http://127.0.0.1:{self.port}"
        self.is_running = False
        self.stop_event = threading.Event()
        self.server_thread = None

        self.create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Démarrage automatique du serveur au lancement
        self.start_server()

    def create_widgets(self):
        # En-tête
        header_frame = tk.Frame(self.root, bg="#1e293b", height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        title_lbl = tk.Label(
            header_frame,
            text="🚀 MELODI Control Center",
            font=("Inter", 16, "bold"),
            bg="#1e293b",
            fg="#f8fafc"
        )
        title_lbl.pack(pady=(16, 2))

        subtitle_lbl = tk.Label(
            header_frame,
            text="Console d'Administration & d'Orchestration ERP",
            font=("Inter", 9),
            bg="#1e293b",
            fg="#94a3b8"
        )
        subtitle_lbl.pack()

        # Zone centrale
        main_frame = tk.Frame(self.root, bg="#0f172a")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=24, pady=20)

        # Statut du serveur
        status_box = tk.Frame(main_frame, bg="#1e293b", bd=1, relief=tk.SOLID)
        status_box.pack(fill=tk.X, pady=(0, 20))

        self.status_dot = tk.Label(
            status_box,
            text="●",
            font=("Inter", 14),
            bg="#1e293b",
            fg="#ef4444"
        )
        self.status_dot.pack(side=tk.LEFT, padx=(16, 8), pady=12)

        self.status_label = tk.Label(
            status_box,
            text="Statut : Arrêté",
            font=("Inter", 11, "bold"),
            bg="#1e293b",
            fg="#f8fafc"
        )
        self.status_label.pack(side=tk.LEFT, pady=12)

        self.url_label = tk.Label(
            main_frame,
            text=f"Adresse locale : {self.url}",
            font=("Inter", 10, "bold"),
            bg="#0f172a",
            fg="#38bdf8"
        )
        self.url_label.pack(pady=(0, 20))

        # Bouton principal : Ouvrir Navigateur
        self.open_btn = tk.Button(
            main_frame,
            text="🌐 Ouvrir dans le Navigateur",
            font=("Inter", 12, "bold"),
            bg="#2563eb",
            fg="#ffffff",
            activebackground="#1d4ed8",
            activeforeground="#ffffff",
            bd=0,
            pady=12,
            cursor="hand2",
            command=self.open_browser
        )
        self.open_btn.pack(fill=tk.X, pady=(0, 14))

        # Zone boutons secondaires
        sec_btn_frame = tk.Frame(main_frame, bg="#0f172a")
        sec_btn_frame.pack(fill=tk.X)

        self.toggle_btn = tk.Button(
            sec_btn_frame,
            text="Arrêter le Serveur",
            font=("Inter", 10),
            bg="#334155",
            fg="#f8fafc",
            activebackground="#475569",
            activeforeground="#ffffff",
            bd=0,
            pady=8,
            cursor="hand2",
            command=self.toggle_server
        )
        self.toggle_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

        self.port_btn = tk.Button(
            sec_btn_frame,
            text="Changer de Port",
            font=("Inter", 10),
            bg="#334155",
            fg="#f8fafc",
            activebackground="#475569",
            activeforeground="#ffffff",
            bd=0,
            pady=8,
            cursor="hand2",
            command=self.change_port
        )
        self.port_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0))

        # Pied de page
        footer_label = tk.Label(
            self.root,
            text="MELODI Control Center v1.0.0 — Python Tkinter Launcher",
            font=("Inter", 8),
            bg="#0f172a",
            fg="#64748b"
        )
        footer_label.pack(side=tk.BOTTOM, pady=10)

    def set_port(self, new_port: int):
        self.port = new_port
        self.url = f"http://127.0.0.1:{self.port}"
        self.url_label.config(text=f"Adresse locale : {self.url}")

    def update_ui_state(self, running: bool):
        self.is_running = running
        if running:
            self.status_dot.config(fg="#22c55e")
            self.status_label.config(text="Statut : En cours d'exécution")
            self.toggle_btn.config(text="Arrêter le Serveur", bg="#dc2626")
            self.open_btn.config(state=tk.NORMAL, bg="#2563eb")
        else:
            self.status_dot.config(fg="#ef4444")
            self.status_label.config(text="Statut : Arrêté")
            self.toggle_btn.config(text="Démarrer le Serveur", bg="#16a34a")
            self.open_btn.config(state=tk.DISABLED, bg="#475569")

    def toggle_server(self):
        if self.is_running:
            self.stop_server()
        else:
            self.start_server()

    def change_port(self):
        was_running = self.is_running
        if was_running:
            self.stop_server()

        dialog = PortSelectionDialog(self.root, self.port)
        if dialog.result:
            self.set_port(dialog.result)

        if was_running:
            self.start_server()

    def start_server(self):
        if self.is_running:
            return

        if is_port_in_use(self.port):
            dialog = PortSelectionDialog(self.root, self.port)
            if dialog.result:
                self.set_port(dialog.result)
            else:
                self.update_ui_state(False)
                self.status_label.config(text="Statut : Port occupé")
                return

        self.status_label.config(text="Statut : Démarrage...")
        self.stop_event.clear()

        def run_hypercorn():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            shutdown_evt = asyncio.Event()

            async def shutdown_trigger():
                while not self.stop_event.is_set():
                    await asyncio.sleep(0.2)
                shutdown_evt.set()

            app = create_app()
            config = Config()
            config.bind = [f"127.0.0.1:{self.port}"]
            config.accesslog = None
            config.errorlog = "-"

            try:
                loop.run_until_complete(serve(app, config, shutdown_trigger=shutdown_trigger))
            except Exception as e:
                print(f"[Launcher GUI] Hypercorn server error: {e}")
                self.root.after(0, self.update_ui_state, False)
            finally:
                loop.close()

        self.server_thread = threading.Thread(target=run_hypercorn, daemon=True)
        self.server_thread.start()
        self.update_ui_state(True)

    def stop_server(self):
        if self.is_running:
            self.stop_event.set()
            self.update_ui_state(False)

    def open_browser(self):
        webbrowser.open(self.url)

    def on_closing(self):
        if self.is_running:
            if messagebox.askokcancel("Quitter", "Le MELODI Control Center est en cours d'exécution.\nVoulez-vous l'arrêter et quitter ?"):
                self.stop_server()
                self.root.after(200, self.root.destroy)
        else:
            self.root.destroy()


def main():
    root = tk.Tk()
    app = MelodiDesktopGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
