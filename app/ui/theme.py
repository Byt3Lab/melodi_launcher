"""
Theme: Définition de la palette de couleurs sombres et des styles ttk pour MELODI Launcher.
"""

import tkinter as tk
from tkinter import ttk

# Palette moderne Slate / Tailwind
COLOR_BG_DARK = "#0f172a"        # Fond principal (Slate 900)
COLOR_CARD = "#1e293b"           # Cartes / Panneaux (Slate 800)
COLOR_CARD_HOVER = "#334155"     # Cartes survolées (Slate 700)
COLOR_BORDER = "#334155"         # Bordures
COLOR_INPUT_BG = "#0b0f19"       # Champs de saisie
COLOR_TEXT_MAIN = "#f8fafc"      # Texte blanc cassé (Slate 50)
COLOR_TEXT_MUTED = "#94a3b8"     # Texte secondaire (Slate 400)
COLOR_TEXT_DIM = "#64748b"       # Texte discret (Slate 500)

COLOR_PRIMARY = "#38bdf8"        # Cyan / Accentuation principale
COLOR_PRIMARY_HOVER = "#0ea5e9"  # Cyan hover
COLOR_PRIMARY_DARK = "#0369a1"

COLOR_SUCCESS = "#22c55e"        # Vert émeraude
COLOR_SUCCESS_HOVER = "#16a34a"

COLOR_DANGER = "#ef4444"         # Rouge alerte
COLOR_DANGER_HOVER = "#dc2626"

COLOR_WARNING = "#f59e0b"        # Ambre / Attention
COLOR_CONSOLE_BG = "#020617"      # Noir ardoise profond pour terminal

FONT_FAMILY = "Inter" if "Inter" in tk.Tk().tk.call("font", "families") else "DejaVu Sans"
FONT_TITLE = (FONT_FAMILY, 14, "bold")
FONT_SUBTITLE = (FONT_FAMILY, 11, "bold")
FONT_BODY = (FONT_FAMILY, 9)
FONT_BODY_BOLD = (FONT_FAMILY, 9, "bold")
FONT_MONO = ("Consolas" if "Consolas" in tk.Tk().tk.call("font", "families") else "monospace", 9)


def apply_theme(root: tk.Tk):
    """Applique le thème sombre global à l'application Tkinter."""
    root.configure(bg=COLOR_BG_DARK)

    style = ttk.Style(root)
    # Tenter d'utiliser un thème de base moderne comme clam
    if "clam" in style.theme_names():
        style.theme_use("clam")

    # Configuration générale
    style.configure(".", background=COLOR_BG_DARK, foreground=COLOR_TEXT_MAIN, font=FONT_BODY)

    # Frames & Labelframes
    style.configure("TFrame", background=COLOR_BG_DARK)
    style.configure("Card.TFrame", background=COLOR_CARD, relief="solid", borderwidth=1)

    style.configure(
        "TLabelframe",
        background=COLOR_CARD,
        foreground=COLOR_PRIMARY,
        font=FONT_SUBTITLE,
        relief="solid",
        borderwidth=1,
        bordercolor=COLOR_BORDER
    )
    style.configure("TLabelframe.Label", background=COLOR_CARD, foreground=COLOR_PRIMARY, font=FONT_SUBTITLE)

    # Notebook (Onglets)
    style.configure(
        "TNotebook",
        background=COLOR_BG_DARK,
        borderwidth=0,
        tabmargins=[2, 5, 2, 0]
    )
    style.configure(
        "TNotebook.Tab",
        background=COLOR_CARD,
        foreground=COLOR_TEXT_MUTED,
        padding=[14, 8],
        font=FONT_SUBTITLE,
        borderwidth=0
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", COLOR_PRIMARY_DARK), ("active", COLOR_CARD_HOVER)],
        foreground=[("selected", COLOR_TEXT_MAIN), ("active", COLOR_TEXT_MAIN)]
    )

    # Boutons standards
    style.configure(
        "TButton",
        background=COLOR_CARD,
        foreground=COLOR_TEXT_MAIN,
        font=FONT_BODY_BOLD,
        borderwidth=1,
        focuscolor="none",
        padding=[10, 6]
    )
    style.map(
        "TButton",
        background=[("active", COLOR_CARD_HOVER), ("pressed", COLOR_BORDER), ("disabled", COLOR_CARD)],
        foreground=[("disabled", COLOR_TEXT_DIM)]
    )

    # Bouton Primaire (Action forte - vert ou cyan)
    style.configure(
        "Primary.TButton",
        background="#0284c7",
        foreground="#ffffff",
        font=FONT_SUBTITLE,
        padding=[14, 8],
        borderwidth=0
    )
    style.map(
        "Primary.TButton",
        background=[("active", "#0369a1"), ("pressed", "#075985"), ("disabled", "#334155")],
        foreground=[("disabled", "#64748b")]
    )

    # Bouton Vert (Succès / Démarrer)
    style.configure(
        "Success.TButton",
        background="#15803d",
        foreground="#ffffff",
        font=FONT_BODY_BOLD,
        padding=[10, 6],
        borderwidth=0
    )
    style.map(
        "Success.TButton",
        background=[("active", "#166534"), ("disabled", "#334155")]
    )

    # Bouton Rouge (Danger / Arrêter)
    style.configure(
        "Danger.TButton",
        background="#b91c1c",
        foreground="#ffffff",
        font=FONT_BODY_BOLD,
        padding=[10, 6],
        borderwidth=0
    )
    style.map(
        "Danger.TButton",
        background=[("active", "#991b1b"), ("disabled", "#334155")]
    )

    # Labels
    style.configure("TLabel", background=COLOR_BG_DARK, foreground=COLOR_TEXT_MAIN, font=FONT_BODY)
    style.configure("Card.TLabel", background=COLOR_CARD, foreground=COLOR_TEXT_MAIN, font=FONT_BODY)
    style.configure("CardMuted.TLabel", background=COLOR_CARD, foreground=COLOR_TEXT_MUTED, font=FONT_BODY)
    style.configure("Title.TLabel", background=COLOR_BG_DARK, foreground=COLOR_TEXT_MAIN, font=FONT_TITLE)
    style.configure("Subtitle.TLabel", background=COLOR_BG_DARK, foreground=COLOR_PRIMARY, font=FONT_SUBTITLE)

    # Entry & Combobox
    style.configure(
        "TEntry",
        fieldbackground=COLOR_INPUT_BG,
        foreground=COLOR_TEXT_MAIN,
        insertcolor=COLOR_TEXT_MAIN,
        padding=6
    )
    style.configure(
        "TCombobox",
        fieldbackground=COLOR_INPUT_BG,
        background=COLOR_CARD,
        foreground=COLOR_TEXT_MAIN,
        arrowcolor=COLOR_PRIMARY,
        padding=5
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", COLOR_INPUT_BG)],
        selectbackground=[("readonly", COLOR_CARD_HOVER)]
    )

    # Checkbutton & Radiobutton
    style.configure("TCheckbutton", background=COLOR_CARD, foreground=COLOR_TEXT_MAIN, font=FONT_BODY)
    style.map("TCheckbutton", background=[("active", COLOR_CARD)])
    style.configure("TRadiobutton", background=COLOR_CARD, foreground=COLOR_TEXT_MAIN, font=FONT_BODY)
    style.map("TRadiobutton", background=[("active", COLOR_CARD)])

    # Progressbar
    style.configure(
        "Horizontal.TProgressbar",
        troughcolor=COLOR_INPUT_BG,
        background=COLOR_PRIMARY,
        lightcolor=COLOR_PRIMARY,
        darkcolor=COLOR_PRIMARY,
        bordercolor=COLOR_BORDER,
        thickness=10
    )

    # Treeview
    style.configure(
        "Treeview",
        background=COLOR_CARD,
        fieldbackground=COLOR_CARD,
        foreground=COLOR_TEXT_MAIN,
        font=FONT_BODY,
        rowheight=28,
        borderwidth=0
    )
    style.configure(
        "Treeview.Heading",
        background=COLOR_BG_DARK,
        foreground=COLOR_PRIMARY,
        font=FONT_BODY_BOLD,
        relief="flat"
    )
    style.map("Treeview", background=[("selected", COLOR_PRIMARY_DARK)], foreground=[("selected", "#ffffff")])
