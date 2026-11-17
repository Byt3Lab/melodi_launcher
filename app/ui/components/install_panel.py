"""
InstallPanel: Assistant de configuration et lancement de l'installation de MELODI ERP et de ses dépendances.
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Callable, Optional
from app.remote.executor import Executor
from app.core.task_manager import TaskProgress
from app.installers.melodi import MelodiInstaller
from app.installers.postgresql import PostgreSQLInstaller
from app.installers.redis import RedisInstaller
from app.ui.theme import (
    COLOR_CARD, COLOR_INPUT_BG, COLOR_PRIMARY, COLOR_SUCCESS,
    COLOR_DANGER, FONT_SUBTITLE, FONT_BODY_BOLD, FONT_TITLE
)

class InstallPanel(ttk.Frame):
    def __init__(self, parent, get_current_executor: Callable[[], Executor], console_panel, async_worker):
        super().__init__(parent, style="Card.TFrame")
        self.get_current_executor = get_current_executor
        self.console_panel = console_panel
        self.async_worker = async_worker

        self.source_mode_var = tk.StringVar(value="zip") # "zip" ou "url"
        self.zip_path_var = tk.StringVar(value="")
        self.url_var = tk.StringVar(value="")
        self.target_dir_var = tk.StringVar(value="/opt/melodi")

        self.install_melodi_var = tk.BooleanVar(value=True)
        self.install_pg_var = tk.BooleanVar(value=True)
        self.install_redis_var = tk.BooleanVar(value=True)
        self.deploy_only_var = tk.BooleanVar(value=False)

        self.is_installing = False
        self.current_task: Optional[TaskProgress] = None

        self._build_ui()

    def _build_ui(self):
        # 1. Source de MELODI ERP
        src_group = ttk.LabelFrame(self, text=" 📦 Source de l'application MELODI ERP ", padding=10)
        src_group.pack(fill=tk.X, padx=10, pady=(10, 6))

        mode_box = ttk.Frame(src_group, style="Card.TFrame")
        mode_box.pack(fill=tk.X, pady=(0, 6))

        ttk.Radiobutton(
            mode_box,
            text="Fichier Archive locale (.zip)",
            value="zip",
            variable=self.source_mode_var,
            command=self._on_source_mode_changed
        ).pack(side=tk.LEFT, padx=(0, 20))

        ttk.Radiobutton(
            mode_box,
            text="Téléchargement depuis une URL / Release Web",
            value="url",
            variable=self.source_mode_var,
            command=self._on_source_mode_changed
        ).pack(side=tk.LEFT)

        # Ligne Archive ZIP
        self.zip_box = ttk.Frame(src_group, style="Card.TFrame")
        self.zip_box.pack(fill=tk.X, pady=4)

        ttk.Label(self.zip_box, text="Archive ZIP :", width=16, style="Card.TLabel").pack(side=tk.LEFT)
        ttk.Entry(self.zip_box, textvariable=self.zip_path_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        ttk.Button(self.zip_box, text="Parcourir...", command=self._browse_zip).pack(side=tk.LEFT)

        # Ligne URL Web
        self.url_box = ttk.Frame(src_group, style="Card.TFrame")

        ttk.Label(self.url_box, text="URL (.zip / direct) :", width=16, style="Card.TLabel").pack(side=tk.LEFT)
        ttk.Entry(self.url_box, textvariable=self.url_var).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Répertoire d'installation
        dir_box = ttk.Frame(src_group, style="Card.TFrame")
        dir_box.pack(fill=tk.X, pady=(6, 2))

        ttk.Label(dir_box, text="Dossier cible :", width=16, style="Card.TLabel").pack(side=tk.LEFT)
        ttk.Entry(dir_box, textvariable=self.target_dir_var, width=30).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(dir_box, text="(Emplacement standard : /opt/melodi)", style="CardMuted.TLabel").pack(side=tk.LEFT)

        # 2. Composants & Services à installer
        comp_group = ttk.LabelFrame(self, text=" ⚙️ Composants à déployer ", padding=10)
        comp_group.pack(fill=tk.X, padx=10, pady=6)

        c1 = ttk.Checkbutton(
            comp_group,
            text="MELODI ERP (Environnement virtuel Python venv, requirements.txt, service systemd)",
            variable=self.install_melodi_var
        )
        c1.pack(anchor=tk.W, pady=2)

        c2 = ttk.Checkbutton(
            comp_group,
            text="Base de données PostgreSQL (Serveur SQL, service systemd postgresql)",
            variable=self.install_pg_var
        )
        c2.pack(anchor=tk.W, pady=2)

        c3 = ttk.Checkbutton(
            comp_group,
            text="Serveur In-Memory Redis (Gestion du cache et files asynchrones, service redis-server)",
            variable=self.install_redis_var
        )
        c3.pack(anchor=tk.W, pady=2)

        c4 = ttk.Checkbutton(
            comp_group,
            text="Extraire l'archive uniquement (sans reconfigurer le venv ni le service systemd)",
            variable=self.deploy_only_var
        )
        c4.pack(anchor=tk.W, pady=(6, 2))

        # 3. Boutons d'Action
        btn_frame = ttk.Frame(self, style="Card.TFrame")
        btn_frame.pack(fill=tk.X, padx=10, pady=(12, 10))

        self.start_btn = ttk.Button(
            btn_frame,
            text="🚀 Lancer l'installation de MELODI ERP",
            style="Primary.TButton",
            command=self.start_installation
        )
        self.start_btn.pack(side=tk.LEFT, padx=(0, 12))

        self.cancel_btn = ttk.Button(
            btn_frame,
            text="⏹️ Annuler",
            style="Danger.TButton",
            command=self.cancel_installation,
            state=tk.DISABLED
        )
        self.cancel_btn.pack(side=tk.LEFT)

    def _on_source_mode_changed(self):
        mode = self.source_mode_var.get()
        if mode == "zip":
            self.url_box.pack_forget()
            self.zip_box.pack(fill=tk.X, pady=4)
        else:
            self.zip_box.pack_forget()
            self.url_box.pack(fill=tk.X, pady=4)

    def _browse_zip(self):
        f = filedialog.askopenfilename(
            title="Sélectionner l'archive MELODI ERP",
            filetypes=[("Archives ZIP", "*.zip"), ("Tous les fichiers", "*.*")]
        )
        if f:
            self.zip_path_var.set(f)

    def start_installation(self):
        """Lance la séquence d'installation via le thread asynchrone."""
        if self.is_installing:
            return

        executor = self.get_current_executor()
        if not executor:
            messagebox.showerror("Erreur", "Aucune cible d'exécution sélectionnée.")
            return

        # Validation des entrées
        mode = self.source_mode_var.get()
        zip_p = self.zip_path_var.get().strip()
        url_p = self.url_var.get().strip()

        if mode == "zip" and zip_p and not os.path.exists(zip_p):
            messagebox.showerror("Erreur", f"Le fichier ZIP spécifié n'existe pas :\n{zip_p}")
            return

        target_dir = self.target_dir_var.get().strip() or "/opt/melodi"

        # Demander confirmation
        target_name = executor.name
        msg = f"Êtes-vous sûr de vouloir lancer l'installation sur :\n{target_name}\n\nDossier cible : {target_dir}"
        if not messagebox.askyesno("Confirmation d'installation", msg):
            return

        self.is_installing = True
        self.start_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.console_panel.clear_logs()
        self.console_panel.append_log(f"==> Début du processus d'installation sur {target_name}...", "step")

        task = TaskProgress("install_task", "Installation MELODI ERP", target_name)
        self.current_task = task

        # Callback pour streamer la progression vers la console GUI
        def update_gui_progress(pct: int, desc: str):
            self.console_panel.set_progress(pct, desc)

        def append_gui_log(line: str):
            self.console_panel.append_log(line)

        # Hook pour TaskProgress
        original_update = task.update
        def hook_update(pct: int, desc: str):
            original_update(pct, desc)
            self.async_worker.call_in_gui(update_gui_progress, pct, desc)
            self.async_worker.call_in_gui(append_gui_log, f"[{pct}%] {desc}")
        task.update = hook_update

        original_log = task.append_log
        def hook_log(text: str):
            original_log(text)
            self.async_worker.call_in_gui(append_gui_log, text)
        task.append_log = hook_log

        async def _install_sequence():
            # 1. Connexion initiale si SSH
            if hasattr(executor, "connect"):
                task.update(2, f"Connexion à la cible {target_name}...")
                conn_ok = await executor.connect()
                if not conn_ok:
                    task.fail(f"Impossible de se connecter à {target_name}")
                    return False

            # 2. Installer PostgreSQL si coché
            if self.install_pg_var.get():
                task.update(10, "Installation et configuration de la base PostgreSQL...")
                pg = PostgreSQLInstaller()
                await pg.install(executor, task)
                if task.is_failed():
                    return False

            # 3. Installer Redis si coché
            if self.install_redis_var.get():
                task.update(35, "Installation et configuration du cache Redis...")
                redis_inst = RedisInstaller()
                await redis_inst.install(executor, task)
                if task.is_failed():
                    return False

            # 4. Installer MELODI ERP si coché
            if self.install_melodi_var.get():
                task.update(50, "Déploiement de l'application MELODI ERP...")
                melodi_inst = MelodiInstaller()

                kwargs = {
                    "destination_dir": target_dir,
                    "deploy_only": self.deploy_only_var.get()
                }

                if mode == "zip" and zip_p:
                    # Si serveur distant, téléverser l'archive locale d'abord
                    if executor.name != "Localhost":
                        task.update(55, f"Téléversement de l'archive ({os.path.basename(zip_p)}) vers le serveur...")
                        remote_dest = f"/tmp/{os.path.basename(zip_p)}"
                        success_up, err_up = await executor.upload_file(zip_p, remote_dest, on_output=task.append_log)
                        if not success_up:
                            task.fail(f"Échec du téléversement de l'archive: {err_up}")
                            return False
                        kwargs["zip_path"] = remote_dest
                    else:
                        kwargs["zip_path"] = zip_p
                elif mode == "url" and url_p:
                    kwargs["url"] = url_p
                    kwargs["source_type"] = "url"

                await melodi_inst.install(executor, task, **kwargs)
                if task.is_failed():
                    return False

            task.complete("Installation terminée avec succès ! MELODI ERP est prêt.")
            return True

        def _on_done(success):
            self.is_installing = False
            self.start_btn.config(state=tk.NORMAL)
            self.cancel_btn.config(state=tk.DISABLED)
            if success:
                self.console_panel.set_progress(100, "Installation terminée avec succès !")
                messagebox.showinfo(
                    "Succès",
                    f"Félicitations !\nMELODI ERP a été installé et configuré avec succès sur {target_name}."
                )
            else:
                self.console_panel.set_progress(0, "Échec de l'installation.")
                messagebox.showerror(
                    "Échec",
                    f"Une erreur est survenue lors de l'installation.\nConsultez la console de logs pour les détails."
                )

        def _on_error(exc):
            self.is_installing = False
            self.start_btn.config(state=tk.NORMAL)
            self.cancel_btn.config(state=tk.DISABLED)
            self.console_panel.append_log(f"❌ Exception inattendue: {exc}", "error")
            messagebox.showerror("Erreur inattendue", f"Erreur critique lors de l'exécution :\n{exc}")

        self.async_worker.run_coroutine(_install_sequence(), on_done=_on_done, on_error=_on_error)

    def cancel_installation(self):
        if self.current_task:
            self.current_task.cancel()
            self.console_panel.append_log("⏹️ Annulation demandée par l'utilisateur...", "warning")
            self.cancel_btn.config(state=tk.DISABLED)
