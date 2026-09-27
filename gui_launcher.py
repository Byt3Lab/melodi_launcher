#!/usr/bin/env python3
"""
GUI Launcher Tkinter pour MELODI Control Center.
Application Bureau Tkinter qui gère le serveur Web Quart/Hypercorn en arrière-plan.
"""

import os
import sys
import time
import socket
import threading
import asyncio
import urllib.request
import webbrowser
import tkinter as tk
from tkinter import messagebox

from hypercorn.config import Config
from hypercorn.asyncio import serve
from app import create_app
from app.utils.helpers import resource_path


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
    port = start_port + 1
    for p in range(port, port + max_attempts):
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

        next_port = find_next_free_port(current_port)

        # Centrer la fenêtre modale par rapport au parent
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        self.geometry(f"+{parent_x + 20}+{parent_y + 20}")

        # En-tête / Titre
        title_label = tk.Label(
            self,
            text="⚠️ Port Occupé",
            font=("Inter", 14, "bold"),
            bg="#0f172a",
            fg="#f59e0b" # Amber 500
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

        # Zone du formulaire
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
            fg="#38bdf8", # Sky 400
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

        # Label de message d'erreur
        self.error_label = tk.Label(
            self,
            text="",
            font=("Inter", 9),
            bg="#0f172a",
            fg="#ef4444"
        )
        self.error_label.pack(pady=(4, 6))

        # Boutons d'action
        btn_frame = tk.Frame(self, bg="#0f172a")
        btn_frame.pack(pady=(5, 15))

        btn_submit = tk.Button(
            btn_frame,
            text="Valider & Démarrer",
            font=("Inter", 10, "bold"),
            bg="#3b82f6",
            fg="#ffffff",
            activebackground="#2563eb",
            activeforeground="#ffffff",
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self.validate
        )
        btn_submit.pack(side=tk.LEFT, padx=5)

        btn_cancel = tk.Button(
            btn_frame,
            text="Annuler",
            font=("Inter", 10),
            bg="#64748b",
            fg="#ffffff",
            activebackground="#475569",
            activeforeground="#ffffff",
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self.destroy
        )
        btn_cancel.pack(side=tk.LEFT, padx=5)

        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.wait_window()

    def validate(self):
        val = self.port_entry.get().strip()
        if not val.isdigit():
            self.error_label.config(text="Veuillez entrer un numéro de port valide.")
            return
        
        port_num = int(val)
        if port_num < 1024 or port_num > 65535:
            self.error_label.config(text="Le port doit être compris entre 1024 et 65535.")
            return

        if is_port_in_use(port_num):
            self.error_label.config(text=f"Le port {port_num} est également occupé !")
            return

        self.result = port_num
        self.destroy()


class MelodiDesktopGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MELODI Control Center")
        self.root.geometry("460x310")
        self.root.resizable(False, False)
        self.root.configure(bg="#0f172a") # Slate 900

        self.port = 8080
        self.url = f"http://127.0.0.1:{self.port}"
        self.is_running = False
        
        self.loop = None
        self.shutdown_event = None
        self.server_thread = None

        # Icône de la fenêtre si disponible
        self.load_icon()

        # Gestionnaire d'événement à la fermeture de la fenêtre
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Construction des éléments graphiques
        self.setup_ui()

        # Démarrer la boucle de vérification du statut HTTP
        self.check_status_loop()

    def load_icon(self):
        try:
            icon_path = resource_path("static/images/icon.png")
            if os.path.exists(icon_path):
                from PIL import Image, ImageTk
                img = Image.open(icon_path)
                self._icon_photo = ImageTk.PhotoImage(img)
                self.root.iconphoto(True, self._icon_photo)
        except Exception:
            pass

    def setup_ui(self):
        # En-tête
        header_frame = tk.Frame(self.root, bg="#0f172a")
        header_frame.pack(pady=(20, 5))

        title_label = tk.Label(
            header_frame,
            text="MELODI Control Center",
            font=("Inter", 18, "bold"),
            bg="#0f172a",
            fg="#f8fafc"
        )
        title_label.pack()

        subtitle_label = tk.Label(
            header_frame,
            text="Panneau de contrôle local web",
            font=("Inter", 10),
            bg="#0f172a",
            fg="#94a3b8"
        )
        subtitle_label.pack(pady=(2, 0))

        # Zone Statut
        status_frame = tk.Frame(self.root, bg="#0f172a")
        status_frame.pack(pady=8)

        self.status_canvas = tk.Canvas(status_frame, width=16, height=16, bg="#0f172a", highlightthickness=0)
        self.status_canvas.pack(side=tk.LEFT, padx=(0, 8))
        self.status_circle = self.status_canvas.create_oval(2, 2, 14, 14, fill="#64748b", outline="")

        self.status_label = tk.Label(
            status_frame,
            text="Statut : Éteint",
            font=("Inter", 11),
            bg="#0f172a",
            fg="#cbd5e1"
        )
        self.status_label.pack(side=tk.LEFT)

        # Zone Port Configuré & Option de Modification
        port_frame = tk.Frame(self.root, bg="#0f172a")
        port_frame.pack(pady=(0, 8))

        self.port_info_label = tk.Label(
            port_frame,
            text=f"Port HTTP : {self.port}",
            font=("Inter", 10),
            bg="#0f172a",
            fg="#94a3b8"
        )
        self.port_info_label.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_change_port = tk.Button(
            port_frame,
            text="Changer",
            font=("Inter", 8, "bold"),
            bg="#334155",
            fg="#f8fafc",
            activebackground="#475569",
            activeforeground="#ffffff",
            bd=0,
            padx=8,
            pady=2,
            cursor="hand2",
            command=self.open_port_dialog
        )
        self.btn_change_port.pack(side=tk.LEFT)

        # Bouton principal dynamique (Start / Stop)
        self.btn_toggle = tk.Button(
            self.root,
            text="Démarrer le Control Center",
            font=("Inter", 12, "bold"),
            bg="#10b981",
            fg="#ffffff",
            activebackground="#059669",
            activeforeground="#ffffff",
            bd=0,
            padx=20,
            pady=10,
            cursor="hand2",
            command=self.toggle_server
        )
        self.btn_toggle.pack(pady=(10, 5))

        # Bouton ouvrir navigateur
        self.btn_browser = tk.Button(
            self.root,
            text=f"Ouvrir dans le navigateur (127.0.0.1:{self.port})",
            font=("Inter", 10, "bold"),
            bg="#3b82f6",
            fg="#ffffff",
            activebackground="#2563eb",
            activeforeground="#ffffff",
            bd=0,
            padx=15,
            pady=6,
            cursor="hand2",
            command=self.open_browser
        )
        self.btn_browser.pack_forget()

    def set_port(self, new_port: int):
        """Met à jour le port configuré et l'URL associée."""
        self.port = new_port
        self.url = f"http://127.0.0.1:{self.port}"
        self.port_info_label.config(text=f"Port HTTP : {self.port}")
        self.btn_browser.config(text=f"Ouvrir dans le navigateur (127.0.0.1:{self.port})")

    def open_port_dialog(self):
        """Ouvre le formulaire modal de changement de port."""
        if self.is_running:
            messagebox.showwarning("Attention", "Veuillez arrêter le serveur avant de changer de port.")
            return
        dialog = PortSelectionDialog(self.root, self.port)
        if dialog.result:
            self.set_port(dialog.result)

    def check_server_ping(self) -> bool:
        """Vérifie la réactivité de l'API Quart sur le port actif."""
        try:
            req = urllib.request.Request(f"{self.url}/api/status", headers={'User-Agent': 'TkinterLauncher'})
            with urllib.request.urlopen(req, timeout=1.0) as response:
                return response.status == 200
        except Exception:
            return False

    def check_status_loop(self):
        """Vérification en arrière-plan sans bloquer la boucle Tkinter."""
        def worker():
            running = self.check_server_ping()
            self.root.after(0, self.update_ui_state, running)

        threading.Thread(target=worker, daemon=True).start()
        self.root.after(1500, self.check_status_loop)

    def update_ui_state(self, is_running):
        self.is_running = is_running
        if self.is_running:
            self.status_canvas.itemconfig(self.status_circle, fill="#10b981") # Vert
            self.status_label.config(text=f"Statut : Actif ({self.url})")
            self.btn_toggle.config(
                text="Arrêter le Control Center",
                bg="#ef4444",
                activebackground="#dc2626"
            )
            self.btn_browser.pack(pady=(5, 0))
        else:
            self.status_canvas.itemconfig(self.status_circle, fill="#64748b") # Gris
            self.status_label.config(text="Statut : Éteint")
            self.btn_toggle.config(
                text="Démarrer le Control Center",
                bg="#10b981",
                activebackground="#059669"
            )
            self.btn_browser.pack_forget()

    def toggle_server(self):
        if self.is_running:
            self.stop_server()
        else:
            self.start_server()

    def start_server(self):
        if self.is_running:
            return

        # Vérifier si le port est occupé par un autre processus
        if is_port_in_use(self.port):
            dialog = PortSelectionDialog(self.root, self.port)
            if dialog.result:
                self.set_port(dialog.result)
            else:
                self.status_label.config(text="Statut : Éteint (Port occupé)")
                return

        self.status_label.config(text="Démarrage en cours...")

        def run_hypercorn():
            try:
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
                self.shutdown_event = asyncio.Event()

                async def shutdown_trigger():
                    await self.shutdown_event.wait()

                app = create_app()
                config = Config()
                config.bind = [f"127.0.0.1:{self.port}"]
                config.accesslog = None
                config.errorlog = "-"
                config.shutdown_trigger = shutdown_trigger

                self.loop.run_until_complete(serve(app, config))
            except OSError as e:
                print(f"[Launcher GUI] Server bind error: {e}")
                self.root.after(0, self.handle_bind_error, e)
            except Exception as e:
                print(f"[Launcher GUI] Server error: {e}")
                import traceback
                traceback.print_exc()
                self.root.after(0, self._show_server_error, str(e))

        self.server_thread = threading.Thread(target=run_hypercorn, daemon=True)
        self.server_thread.start()

    def handle_bind_error(self, err):
        """Gère l'erreur d'occupation du port survenue pendant Hypercorn."""
        self.update_ui_state(False)
        self.status_label.config(text="Statut : Erreur de port")
        dialog = PortSelectionDialog(self.root, self.port)
        if dialog.result:
            self.set_port(dialog.result)
            self.start_server()

    def _show_server_error(self, error_msg: str):
        """Affiche dans l'UI une erreur de démarrage du serveur web."""
        self.update_ui_state(False)
        short_msg = (error_msg[:100] + "...") if len(error_msg) > 100 else error_msg
        self.status_label.config(text=f"Erreur : {short_msg}")
        messagebox.showerror(
            "Erreur de démarrage",
            f"Le serveur web n'a pas pu démarrer :\n\n{error_msg}\n\n"
            "Vérifiez la console ou les logs pour plus de détails."
        )

    def stop_server(self):
        if self.loop and self.shutdown_event:
            try:
                self.loop.call_soon_threadsafe(self.shutdown_event.set)
            except Exception as e:
                print(f"[Launcher GUI] Stop error: {e}")

    def open_browser(self):
        webbrowser.open(self.url)

    def on_closing(self):
        if self.is_running:
            if messagebox.askokcancel("Quitter", "Le MELODI Control Center est en cours d'exécution.\nVoulez-vous l'arrêter et quitter ?"):
                self.stop_server()
                self.root.after(300, self.root.destroy)
        else:
            self.root.destroy()


def main():
    root = tk.Tk()
    app = MelodiDesktopGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

