#!/bin/bash
# Script de compilation de MELODI Launcher en exécutable standalone Linux (PySide6 + qasync)

echo "=== Compilation de MELODI Launcher (Desktop PySide6) ==="

if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

mkdir -p config assets
rm -rf build dist

pyinstaller launcher.spec

chmod +x dist/melodi-launcher 2>/dev/null || true
echo "=== Compilation terminée ! Exécutable disponible dans dist/melodi-launcher ==="
