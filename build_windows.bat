@echo off
REM Script de compilation de MELODI Launcher en executable standalone Windows (PySide6 + qasync)

echo === Compilation de MELODI Launcher (Windows Desktop PySide6) ===

if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

if not exist config mkdir config
if not exist assets mkdir assets
if not exist locales mkdir locales

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

pyinstaller launcher.spec

echo === Compilation terminee ! Executable disponible dans dist\melodi-launcher.exe ===
