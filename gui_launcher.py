#!/usr/bin/env python3
"""
MELODI Launcher Desktop: Application 100% Tkinter pour l'orchestration et le déploiement de MELODI ERP.
Permet d'installer et d'administrer MELODI ERP en local ou sur un serveur distant via SSH.
"""

import sys
import tkinter as tk
from app.ui.main_window import MainWindow

def main():
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()
