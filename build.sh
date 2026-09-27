#!/bin/bash
# Script de compilation de MELODI Launcher en exécutable standalone Linux (Interface Tkinter + Serveur Web)

echo "=== Compilation de MELODI Control Center ==="

# Activer l'environnement virtuel si présent
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# S'assurer que le dossier config existe avant la compilation
mkdir -p config

# Nettoyage des précédents builds
rm -rf build dist

# Compilation PyInstaller avec point d'entrée Tkinter GUI
pyinstaller \
    --name "launcher" \
    --onefile \
    --add-data "templates:templates" \
    --add-data "static:static" \
    --add-data "config:config" \
    --hidden-import=quart \
    --hidden-import=quart.templating \
    --hidden-import=quart.wrappers \
    --hidden-import=quart.routing \
    --hidden-import=quart.datastructures \
    --hidden-import=quart.ctx \
    --hidden-import=hypercorn \
    --hidden-import=hypercorn.asyncio \
    --hidden-import=hypercorn.config \
    --hidden-import=hypercorn.middleware \
    --hidden-import=hypercorn.protocol \
    --hidden-import=hypercorn.utils \
    --hidden-import=hypercorn.typing \
    --hidden-import=jinja2 \
    --hidden-import=jinja2.ext \
    --hidden-import=jinja2.defaults \
    --hidden-import=jinja2.utils \
    --hidden-import=tkinter \
    --hidden-import=asyncssh \
    --hidden-import=psutil \
    --hidden-import=multipart \
    --hidden-import=exceptiongroup \
    --hidden-import=pkg_resources.py2_warn \
    --collect-all=quart \
    --collect-all=hypercorn \
    gui_launcher.py

# Ajouter les droits d'exécution
chmod +x dist/launcher 2>/dev/null || true

echo "=== Compilation terminée ! Exécutable disponible dans dist/launcher ==="