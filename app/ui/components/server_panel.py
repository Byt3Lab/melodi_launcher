"""
ServerPanel: Composant de configuration et sélection de la cible d'exécution (Localhost vs Serveur SSH distant).
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, Any, Optional, Callable
from app.core.server_manager import ServerManager
from app.remote.executor import Executor
from app.remote.local_executor import LocalExecutor
from app.remote.ssh_executor import SSHExecutor
from app.ui.theme import (
    COLOR_CARD, COLOR_INPUT_BG, COLOR_TEXT_MAIN, COLOR_TEXT_MUTED,
    COLOR_PRIMARY, COLOR_SUCCESS, COLOR_DANGER, FONT_SUBTITLE, FONT_BODY_BOLD
)

class ServerPanel(ttk.LabelFrame):
    def __init__(self, parent, server_manager: ServerManager, async_worker, on_server_changed: Optional[Callable[[Executor], None]] = None):
        super().__init__(parent, text=" 🖥️ Cible d'administration & Déploiement ", padding=10)
        self.server_manager = server_manager
        self.async_worker = async_worker
        self.on_server_changed = on_server_changed

        self.target_type_var = tk.StringVar(value="local") # "local" ou "ssh"
        self.host_var = tk.StringVar(value="")
        self.port_var = tk.StringVar(value="22")
        self.user_var = tk.StringVar(value="root")
        self.auth_mode_var = tk.StringVar(value="key") # "key" ou "password"
        self.key_path_var = tk.StringVar(value=os.path.expanduser("~/.ssh/id_rsa"))
        self.password_var = tk.StringVar(value="")
        self.sudo_password_var = tk.StringVar(value="")
        self.saved_servers_var = tk.StringVar()

        self.current_executor: Optional[Executor] = None

        self._build_ui()
        self._load_saved_servers()
        self._on_target_type_toggled()

    def _build_ui(self):
        # 1. Sélection Cible Local vs SSH
        type_frame = ttk.Frame(self, style="Card.TFrame")
        type_frame.pack(fill=tk.X, pady=(0, 10))

        lbl = ttk.Label(type_frame, text="Type de machine cible :", font=FONT_BODY_BOLD, style="Card.TLabel")
        lbl.pack(side=tk.LEFT, padx=(0, 15))

        rb_local = ttk.Radiobutton(
            type_frame,
            text="🏠 Machine Locale (Localhost)",
            value="local",
            variable=self.target_type_var,
            command=self._on_target_type_toggled
        )
        rb_local.pack(side=tk.LEFT, padx=(0, 15))

        rb_ssh = ttk.Radiobutton(
            type_frame,
            text="🌐 Serveur Distant (SSH)",
            value="ssh",
            variable=self.target_type_var,
            command=self._on_target_type_toggled
        )
        rb_ssh.pack(side=tk.LEFT)

        # 2. Panneau Paramètres SSH (Affiché si target_type == "ssh")
        self.ssh_frame = ttk.Frame(self, style="Card.TFrame")

        # Sélection rapide d'un serveur sauvegardé
        saved_box = ttk.Frame(self.ssh_frame, style="Card.TFrame")
        saved_box.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(saved_box, text="Profil enregistré :", width=18, style="Card.TLabel").pack(side=tk.LEFT)
        self.server_combo = ttk.Combobox(saved_box, textvariable=self.saved_servers_var, state="readonly", width=30)
        self.server_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.server_combo.bind("<<ComboboxSelected>>", self._on_saved_server_selected)

        save_btn = ttk.Button(saved_box, text="💾 Enregistrer ce serveur", command=self._save_current_server)
        save_btn.pack(side=tk.LEFT)

        # Ligne Hôte + Port + Utilisateur
        host_box = ttk.Frame(self.ssh_frame, style="Card.TFrame")
        host_box.pack(fill=tk.X, pady=4)

        ttk.Label(host_box, text="Adresse IP / Hôte :", width=18, style="Card.TLabel").pack(side=tk.LEFT)
        ttk.Entry(host_box, textvariable=self.host_var, width=24).pack(side=tk.LEFT, padx=(0, 15))

        ttk.Label(host_box, text="Port SSH :", style="Card.TLabel").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(host_box, textvariable=self.port_var, width=6).pack(side=tk.LEFT, padx=(0, 15))

        ttk.Label(host_box, text="Utilisateur :", style="Card.TLabel").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(host_box, textvariable=self.user_var, width=12).pack(side=tk.LEFT)

        # Authentification (Clé ou Mot de passe)
        auth_type_box = ttk.Frame(self.ssh_frame, style="Card.TFrame")
        auth_type_box.pack(fill=tk.X, pady=4)

        ttk.Label(auth_type_box, text="Authentification :", width=18, style="Card.TLabel").pack(side=tk.LEFT)
        ttk.Radiobutton(auth_type_box, text="Clé privée SSH", value="key", variable=self.auth_mode_var, command=self._on_auth_mode_toggled).pack(side=tk.LEFT, padx=(0, 15))
        ttk.Radiobutton(auth_type_box, text="Mot de passe", value="password", variable=self.auth_mode_var, command=self._on_auth_mode_toggled).pack(side=tk.LEFT)

        # Clé SSH
        self.key_box = ttk.Frame(self.ssh_frame, style="Card.TFrame")
        self.key_box.pack(fill=tk.X, pady=4)

        ttk.Label(self.key_box, text="Chemin clé privée :", width=18, style="Card.TLabel").pack(side=tk.LEFT)
        ttk.Entry(self.key_box, textvariable=self.key_path_var, width=40).pack(side=tk.LEFT, padx=(0, 8), fill=tk.X, expand=True)
        ttk.Button(self.key_box, text="Parcourir...", command=self._browse_key).pack(side=tk.LEFT)

        # Mot de passe SSH
        self.pass_box = ttk.Frame(self.ssh_frame, style="Card.TFrame")

        ttk.Label(self.pass_box, text="Mot de passe SSH :", width=18, style="Card.TLabel").pack(side=tk.LEFT)
        ttk.Entry(self.pass_box, textvariable=self.password_var, show="•", width=25).pack(side=tk.LEFT)

        # Mot de passe Sudo (optionnel)
        sudo_box = ttk.Frame(self.ssh_frame, style="Card.TFrame")
        sudo_box.pack(fill=tk.X, pady=4)

        ttk.Label(sudo_box, text="Mot de passe sudo :", width=18, style="Card.TLabel").pack(side=tk.LEFT)
        ttk.Entry(sudo_box, textvariable=self.sudo_password_var, show="•", width=25).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(sudo_box, text="(Laisser vide si compte root ou sudo sans mot de passe)", style="CardMuted.TLabel").pack(side=tk.LEFT)

        # 3. Barre de Statut & Test de Connexion
        action_bar = ttk.Frame(self, style="Card.TFrame")
        action_bar.pack(fill=tk.X, pady=(10, 0))

        self.test_btn = ttk.Button(action_bar, text="🔌 Tester la connexion", command=self.test_connection)
        self.test_btn.pack(side=tk.LEFT, padx=(0, 12))

        self.status_badge = ttk.Label(
            action_bar,
            text="⚪ Non testé",
            font=FONT_BODY_BOLD,
            foreground=COLOR_TEXT_MUTED,
            style="Card.TLabel"
        )
        self.status_badge.pack(side=tk.LEFT)

    def _on_target_type_toggled(self):
        t_type = self.target_type_var.get()
        if t_type == "ssh":
            self.ssh_frame.pack(fill=tk.X, pady=(5, 5))
            self._on_auth_mode_toggled()
        else:
            self.ssh_frame.pack_forget()

        self.status_badge.config(text="⚪ Prêt (Serveur local)", foreground=COLOR_TEXT_MUTED)
        self._notify_executor_change()

    def _on_auth_mode_toggled(self):
        mode = self.auth_mode_var.get()
        if mode == "key":
            self.pass_box.pack_forget()
            self.key_box.pack(fill=tk.X, pady=4)
        else:
            self.key_box.pack_forget()
            self.pass_box.pack(fill=tk.X, pady=4)

    def _browse_key(self):
        f = filedialog.askopenfilename(
            title="Sélectionner la clé privée SSH",
            initialdir=os.path.expanduser("~/.ssh"),
            filetypes=[("Clés SSH", "*id_* *key* *.pem"), ("Tous les fichiers", "*.*")]
        )
        if f:
            self.key_path_var.set(f)

    def _load_saved_servers(self):
        servers = self.server_manager.get_all_servers()
        ssh_servers = [s for s in servers if s.get("type") == "ssh"]
        names = [f"{s.get('name', 'Serveur')} ({s.get('host')})" for s in ssh_servers]
        self.server_combo["values"] = names
        if names:
            self.server_combo.current(0)
            self._on_saved_server_selected(None)

    def _on_saved_server_selected(self, event):
        idx = self.server_combo.current()
        if idx < 0:
            return
        servers = [s for s in self.server_manager.get_all_servers() if s.get("type") == "ssh"]
        if idx < len(servers):
            srv = servers[idx]
            self.host_var.set(srv.get("host", ""))
            self.port_var.set(str(srv.get("port", 22)))
            self.user_var.set(srv.get("username", "root"))
            self.password_var.set(srv.get("password", ""))
            self.sudo_password_var.set(srv.get("sudo_password", srv.get("password", "")))
            key_p = srv.get("key_path", "")
            if key_p:
                self.key_path_var.set(key_p)
                self.auth_mode_var.set("key")
            else:
                self.auth_mode_var.set("password")
            self._on_auth_mode_toggled()

    def _save_current_server(self):
        host = self.host_var.get().strip()
        if not host:
            messagebox.showwarning("Enregistrement", "Veuillez entrer une adresse d'hôte.")
            return

        name = f"Serveur {host}"
        srv_data = {
            "name": name,
            "type": "ssh",
            "host": host,
            "port": int(self.port_var.get().strip() or "22"),
            "username": self.user_var.get().strip() or "root",
            "auth_method": self.auth_mode_var.get(),
            "key_path": self.key_path_var.get().strip() if self.auth_mode_var.get() == "key" else "",
            "password": self.password_var.get(),
            "sudo_password": self.sudo_password_var.get() or self.password_var.get()
        }
        self.server_manager.add_server(srv_data)
        self._load_saved_servers()
        messagebox.showinfo("Enregistrement", f"Profil '{name}' sauvegardé dans servers.json !")

    def get_executor(self) -> Executor:
        """Retourne une instance de Executor (LocalExecutor ou SSHExecutor) selon les paramètres actuels."""
        t_type = self.target_type_var.get()
        if t_type == "local":
            return LocalExecutor(password=self.sudo_password_var.get() or None)

        host = self.host_var.get().strip()
        port = int(self.port_var.get().strip() or "22")
        username = self.user_var.get().strip() or "root"
        key_path = self.key_path_var.get().strip() if self.auth_mode_var.get() == "key" else None
        password = self.password_var.get() or None
        sudo_pass = self.sudo_password_var.get() or password

        return SSHExecutor(
            host=host,
            port=port,
            username=username,
            key_path=key_path,
            password=password,
            sudo_password=sudo_pass
        )

    def _notify_executor_change(self):
        self.current_executor = self.get_executor()
        if self.on_server_changed:
            self.on_server_changed(self.current_executor)

    def test_connection(self):
        """Teste la connexion avec la cible sélectionnée sans bloquer l'UI."""
        self.test_btn.config(state=tk.DISABLED)
        self.status_badge.config(text="⏳ Test en cours...", foreground=COLOR_PRIMARY)

        executor = self.get_executor()

        async def _test():
            if isinstance(executor, LocalExecutor):
                code, stdout, stderr = await executor.run("uname -a")
                return code == 0, stdout or stderr
            else:
                ok = await executor.connect()
                if not ok:
                    return False, "Impossible d'établir la connexion SSH."
                code, stdout, stderr = await executor.run("uname -a")
                await executor.disconnect()
                return code == 0, stdout or stderr

        def _on_done(result):
            success, msg = result
            self.test_btn.config(state=tk.NORMAL)
            if success:
                self.status_badge.config(text="🟢 Connexion Réussie", foreground=COLOR_SUCCESS)
                self._notify_executor_change()
            else:
                self.status_badge.config(text=f"🔴 Échec: {msg[:40]}", foreground=COLOR_DANGER)
                messagebox.showerror("Test de connexion", f"Échec de la connexion à la cible :\n\n{msg}")

        def _on_error(exc):
            self.test_btn.config(state=tk.NORMAL)
            self.status_badge.config(text=f"🔴 Erreur: {str(exc)[:40]}", foreground=COLOR_DANGER)
            messagebox.showerror("Erreur", f"Erreur lors du test de connexion :\n{exc}")

        self.async_worker.run_coroutine(_test(), on_done=_on_done, on_error=_on_error)
