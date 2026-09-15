#!/bin/bash
# Script de compilation de MELODI Launcher en exécutable standalone Linux avec PyInstaller

echo "=== Compilation de MELODI Control Center ==="

# Activer l'environnement virtuel si présent
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# S'assurer que le dossier config existe avant la compilation
mkdir -p config

# Nettoyage des précédents builds
rm -rf build dist

# Compilation PyInstaller
pyinstaller \
    --name "launcher" \
    --onefile \
    --add-data "templates:templates" \
    --add-data "static:static" \
    --add-data "config:config" \
    --hidden-import=quart \
    --hidden-import=hypercorn \
    --hidden-import=hypercorn.asyncio \
    --hidden-import=jinja2 \
    run.py

echo "=== Compilation terminée ! Exécutable disponible dans dist/launcher ==="