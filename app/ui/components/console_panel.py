"""
ConsolePanel: Console de logs intégrée et barre de progression pour les opérations système.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import time
from app.ui.theme import (
    COLOR_CONSOLE_BG, COLOR_CARD, COLOR_BORDER, COLOR_TEXT_MAIN,
    COLOR_TEXT_MUTED, COLOR_PRIMARY, COLOR_SUCCESS, COLOR_DANGER,
    COLOR_WARNING, FONT_MONO, FONT_BODY_BOLD
)

class ConsolePanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Card.TFrame")

        self._build_header()
        self._build_progress()
        self._build_terminal()

    def _build_header(self):
        header_frame = ttk.Frame(self, style="Card.TFrame")
        header_frame.pack(fill=tk.X, padx=10, pady=(8, 4))

        title_lbl = ttk.Label(
            header_frame,
            text="💻 Console d'exécution & Logs en direct",
            font=FONT_BODY_BOLD,
            foreground=COLOR_PRIMARY,
            style="Card.TLabel"
        )
        title_lbl.pack(side=tk.LEFT)

        btn_box = ttk.Frame(header_frame, style="Card.TFrame")
        btn_box.pack(side=tk.RIGHT)

        copy_btn = ttk.Button(btn_box, text="📋 Copier", command=self.copy_logs, width=9)
        copy_btn.pack(side=tk.LEFT, padx=3)

        save_btn = ttk.Button(btn_box, text="💾 Sauvegarder", command=self.save_logs, width=12)
        save_btn.pack(side=tk.LEFT, padx=3)

        clear_btn = ttk.Button(btn_box, text="🧹 Effacer", command=self.clear_logs, width=8)
        clear_btn.pack(side=tk.LEFT, padx=3)

    def _build_progress(self):
        progress_frame = ttk.Frame(self, style="Card.TFrame")
        progress_frame.pack(fill=tk.X, padx=10, pady=(2, 6))

        self.step_label = ttk.Label(
            progress_frame,
            text="Prêt",
            foreground=COLOR_TEXT_MUTED,
            style="CardMuted.TLabel"
        )
        self.step_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.percent_label = ttk.Label(
            progress_frame,
            text="0%",
            font=FONT_BODY_BOLD,
            foreground=COLOR_PRIMARY,
            style="Card.TLabel"
        )
        self.percent_label.pack(side=tk.RIGHT, padx=(6, 0))

        self.progress_bar = ttk.Progressbar(
            self,
            orient="horizontal",
            mode="determinate",
            style="Horizontal.TProgressbar"
        )
        self.progress_bar.pack(fill=tk.X, padx=10, pady=(0, 6))

    def _build_terminal(self):
        term_frame = tk.Frame(self, bg=COLOR_CONSOLE_BG, bd=1, relief=tk.SOLID, highlightbackground=COLOR_BORDER)
        term_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        scrollbar = ttk.Scrollbar(term_frame, orient="vertical")
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.text_area = tk.Text(
            term_frame,
            bg=COLOR_CONSOLE_BG,
            fg=COLOR_TEXT_MAIN,
            insertbackground=COLOR_PRIMARY,
            font=FONT_MONO,
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set,
            bd=0,
            padx=10,
            pady=8
        )
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.text_area.yview)

        # Configuration des tags de coloration
        self.text_area.tag_config("stdout", foreground="#cbd5e1")
        self.text_area.tag_config("info", foreground=COLOR_PRIMARY)
        self.text_area.tag_config("success", foreground=COLOR_SUCCESS)
        self.text_area.tag_config("warning", foreground=COLOR_WARNING)
        self.text_area.tag_config("error", foreground=COLOR_DANGER)
        self.text_area.tag_config("step", foreground="#c084fc", font=(FONT_MONO[0], FONT_MONO[1], "bold"))
        self.text_area.tag_config("timestamp", foreground="#64748b")

        # Rendre le widget non éditable par défaut
        self.text_area.config(state=tk.DISABLED)

    def set_progress(self, percent: int, step_desc: str = ""):
        """Met à jour la barre de progression et le libellé."""
        p = max(0, min(100, int(percent)))
        self.progress_bar["value"] = p
        self.percent_label.config(text=f"{p}%")
        if step_desc:
            self.step_label.config(text=step_desc)

    def append_log(self, text: str, level: str = "stdout"):
        """Ajoute du texte dans la console avec horodatage et niveau de coloration."""
        if not text:
            return

        self.text_area.config(state=tk.NORMAL)
        ts = time.strftime("[%H:%M:%S] ")

        # Détection automatique du tag selon le contenu
        lower = text.lower()
        if "✓" in text or "succès" in lower or "success" in lower:
            tag = "success"
        elif "❌" in text or "erreur" in lower or "error" in lower or "failed" in lower:
            tag = "error"
        elif "⚠️" in text or "avertissement" in lower or "warning" in lower:
            tag = "warning"
        elif "==>" in text or "étape" in lower or "step" in lower:
            tag = "step"
        else:
            tag = level

        lines = text.splitlines() if "\n" in text else [text]
        for line in lines:
            cleaned = line.rstrip("\r\n")
            if cleaned:
                self.text_area.insert(tk.END, ts, "timestamp")
                self.text_area.insert(tk.END, cleaned + "\n", tag)

        self.text_area.see(tk.END)
        self.text_area.config(state=tk.DISABLED)

    def clear_logs(self):
        """Efface la console."""
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete("1.0", tk.END)
        self.text_area.config(state=tk.DISABLED)
        self.set_progress(0, "Prêt")

    def copy_logs(self):
        """Copie le texte dans le presse-papier."""
        content = self.text_area.get("1.0", tk.END).strip()
        if content:
            self.clipboard_clear()
            self.clipboard_append(content)
            messagebox.showinfo("Presse-papier", "Logs copiés dans le presse-papier !")

    def save_logs(self):
        """Sauvegarde les logs dans un fichier."""
        content = self.text_area.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("Sauvegarde", "La console est vide.")
            return

        fpath = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("Fichiers de logs", "*.log"), ("Texte brut", "*.txt"), ("Tous les fichiers", "*.*")],
            title="Enregistrer les logs"
        )
        if fpath:
            try:
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(content)
                messagebox.showinfo("Sauvegarde", f"Logs enregistrés dans :\n{fpath}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible d'enregistrer le fichier:\n{e}")
