#!/bin/bash
# Script de compilation de MELODI Launcher en exécutable standalone Linux (Application 100% Tkinter)

echo "=== Compilation de MELODI Launcher (Desktop 100% Tkinter) ==="

# Activer l'environnement virtuel si présent
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# S'assurer que les dossiers config et assets existent
mkdir -p config assets

# Nettoyage des précédents builds
rm -rf build dist

# Compilation PyInstaller
pyinstaller \
    --name "melodi-launcher" \
    --onefile \
    --windowed \
    --add-data "config:config" \
    --add-data "assets:assets" \
    --hidden-import=tkinter \
    --hidden-import=asyncssh \
    --hidden-import=psutil \
    gui_launcher.py

# Ajouter les droits d'exécution
chmod +x dist/melodi-launcher 2>/dev/null || true

echo "=== Compilation terminée ! Exécutable disponible dans dist/melodi-launcher ==="
