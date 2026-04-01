import customtkinter as ctk
import subprocess
import threading
import sys
import os
import platform
import webbrowser
import shutil
from PIL import Image, ImageTk
from tkinter import messagebox

# Configuration globale
ctk.set_appearance_mode("Dark")  # Modes: "System", "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue", "green", "dark-blue"

import sys

def resource_path(relative_path):
    """ Retourne le chemin absolu vers la ressource, compatible dev et PyInstaller """
    try:
        # PyInstaller crée un dossier temporaire _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)

class MelodiLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("MELODI ERP - Panneau de Contrôle")
        self.geometry("450x300")
        self.resizable(False, False)
        
        # Icône de la fenêtre
        icon_path = resource_path("assets/icon.png")
        print(icon_path)
        
        if os.path.exists(icon_path):
            icon_image = Image.open(icon_path)
            self._icon_photo = ImageTk.PhotoImage(icon_image)
            self.iconphoto(True, self._icon_photo)
        
        self.erp_process = None
        self.is_running = False

        # Attacher l'événement pour la fermeture de la fenêtre
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Construction de l'interface
        self.setup_ui()

    def setup_ui(self):
        # En-tête avec icône + titre
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(pady=(25, 10))

        # Icône à côté du nom
        icon_path = resource_path("assets/icon.png")
        if os.path.exists(icon_path):
            icon_img = Image.open(icon_path).resize((36, 36), Image.LANCZOS)
            self._header_icon = ctk.CTkImage(light_image=icon_img, dark_image=icon_img, size=(36, 36))
            self.icon_label = ctk.CTkLabel(self.header_frame, image=self._header_icon, text="")
            self.icon_label.pack(side="left", padx=(0, 10))

        # Titre principal
        self.title_label = ctk.CTkLabel(
            self.header_frame, 
            text="MELODI ERP", 
            font=ctk.CTkFont(size=28, weight="bold")
        )
        self.title_label.pack(side="left")

        # Zone Statut
        self.status_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.status_frame.pack(pady=10)

        # Cercle d'indication : on utilise un petit bouton inactif avec les coins arrondis pour faire un rond parfait
        self.status_indicator = ctk.CTkButton(
            self.status_frame, 
            text="", 
            width=18, 
            height=18, 
            corner_radius=9, 
            fg_color="gray", 
            hover=False, 
            state="disabled"
        )
        self.status_indicator.pack(side="left", padx=(0, 10))

        self.status_label = ctk.CTkLabel(
            self.status_frame, 
            text="Statut : Éteint", 
            font=ctk.CTkFont(size=14)
        )
        self.status_label.pack(side="left")

        # Gros bouton dynamique (Start/Stop)
        self.action_button = ctk.CTkButton(
            self, 
            text="Démarrer MELODI", 
            command=self.toggle_erp,
            fg_color="#28a745", # Vert
            hover_color="#218838",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            width=250
        )
        self.action_button.pack(pady=(20, 10))
        
        # Bouton Navigateur (caché par défaut)
        self.browser_button = ctk.CTkButton(
            self,
            text="Ouvrir dans le navigateur",
            command=self.open_browser,
            fg_color="#007bff",
            hover_color="#0056b3",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            width=250
        )

    def update_ui_state(self, is_running):
        """Met à jour l'interface en fonction de l'état du processus."""
        self.is_running = is_running
        if self.is_running:
            self.action_button.configure(
                text="Arrêter MELODI", 
                fg_color="#dc3545", # Rouge
                hover_color="#c82333"
            )
            self.status_indicator.configure(fg_color="#28a745") # Indicateur vert
            self.status_label.configure(text="Statut : En cours")
            self.browser_button.pack(pady=(0, 10))
        else:
            self.action_button.configure(
                text="Démarrer MELODI", 
                fg_color="#28a745", # Vert
                hover_color="#218838"
            )
            self.status_indicator.configure(fg_color="gray") # Indicateur gris
            self.status_label.configure(text="Statut : Éteint")
            self.action_button.configure(state="normal") # Réactiver le bouton en cas de crash
            self.browser_button.pack_forget()

    def open_browser(self):
        """Ouvre le navigateur à l'adresse de l'application."""
        port = 8080 
        if self._is_dev_mode():
            port = 5000
        webbrowser.open(f"http://127.0.0.1:{port}")

    def toggle_erp(self):
        """Démarre ou arrête l'ERP selon l'état actuel."""
        if not self.is_running:
            self.start_erp()
        else:
            self.stop_erp()

    def start_erp(self):
        """Lance l'application MELODI en arrière-plan."""
        if self.erp_process is not None and self.erp_process.poll() is None:
            return # Sécurité : Déjà en cours

        self.action_button.configure(state="disabled") # Désactiver pour éviter le double-clic
        
        # On utilise un thread pour ne pas freezer l'interface Tkinter
        threading.Thread(target=self._run_erp_process, daemon=True).start()

    def _run_erp_process(self):
        """Méthode threadée pour gérer le sous-processus."""
        try:
            base_dir = self._get_base_dir()
            cwd_path = base_dir
            
            # Détection du système d'exploitation
            current_os = platform.system()
            prefix_script_name = "prod"
            
            if self._is_dev_mode():
                prefix_script_name = "dev"

            # Mode PROD : lancer le script prod.bat ou prod.sh
            if current_os == "Windows":
                script_name = prefix_script_name + ".bat"
                script_path = os.path.join(base_dir, script_name)
                if not os.path.exists(script_path):
                    raise FileNotFoundError(f"Le fichier '{script_name}' est introuvable dans :\n{base_dir}")
                cmd = [script_path]
            else:
                # Linux / macOS
                script_name = prefix_script_name + ".sh"
                script_path = os.path.join(base_dir, script_name)
                if not os.path.exists(script_path):
                    raise FileNotFoundError(f"Le fichier '{script_name}' est introuvable dans :\n{base_dir}")
                # S'assurer que le script est exécutable
                os.chmod(script_path, 0o755)
                cmd = ["bash", script_path]
            
            # On écrit les logs dans un fichier pour éviter que le pipe stdout/stderr bloque l'application
            log_handle = open(os.path.join(base_dir, "melodi_launcher.log"), "a")
            log_handle.write(f"=== Démarrage de MELODI ({current_os} - {script_name}) ===\n")
            log_handle.flush()

            self.erp_process = subprocess.Popen(
                cmd,
                cwd=cwd_path,
                stdout=log_handle,
                stderr=subprocess.STDOUT
            )
            
            # Mise à jour de l'interface via after (Tkinter n'est pas thread-safe pour les modifs directes depuis un autre thread)
            self.after(0, self.update_ui_state, True)
            self.after(0, lambda: self.action_button.configure(state="normal"))

            # On attend la fin du processus
            self.erp_process.wait()

            log_handle.write(f"=== Arrêt de MELODI (Code de retour : {self.erp_process.returncode}) ===\n")
            log_handle.close()

            # Processus terminé de lui-même, crash, ou fermé via le stop
            self.after(0, self.update_ui_state, False)
            self.erp_process = None
            
        except Exception as e:
            self.after(0, self.update_ui_state, False)
            print(f"Erreur lors du lancement : {e}")
            # self.after(0, lambda: messagebox.showerror("Erreur de lancement", f"Impossible de démarrer MELODI:\n{e}"))

    def stop_erp(self):
        """Arrête l'application MELODI et tue le processus."""
        if self.erp_process is not None and self.erp_process.poll() is None:
            self.action_button.configure(state="disabled") # On désactive pendant l'extinction
            try:
                self.erp_process.terminate() # Envoi du signal SIGTERM
            except Exception as e:
                print(f"Erreur lors de l'arrêt: {e}")
            
            # Le _run_erp_process.wait() qui tourne dans le thread va se débloquer et remettre l'état à False
            # Optionnellement on peut ajouter self.erp_process.kill() après un timer si l'application refuse de s'arrêter

    def on_closing(self):
        """Gère la fermeture de la fenêtre du Launcher."""
        if self.is_running and self.erp_process is not None and self.erp_process.poll() is None:
            # Demande confirmation avec avertissement tkMessageBox
            if messagebox.askokcancel("Quitter", "L'ERP MELODI est en cours d'exécution.\nVoulez-vous l'arrêter et quitter le launcher ?"):
                self.stop_erp()
                # On attend une demi-seconde pour laisser le temps au process de shutdown proprement avant de fermer la fenêtre
                self.after(500, self.destroy)
        else:
            self.destroy()

    def _get_base_dir(self):
        """Retourne le chemin de base de l'application."""
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        else:
            return os.path.dirname(os.path.abspath(__file__))

    def _is_dev_mode(self):
        """Vérifie si le mode DEV est activé."""
        base_dir = self._get_base_dir()
        dev_mode_flag = os.path.join(base_dir, "launcher_dev_mode.txt")
        return os.path.exists(dev_mode_flag)

if __name__ == "__main__":
    app = MelodiLauncher()
    app.mainloop()
