#!/usr/bin/env python3
"""
MELODI Launcher Application Entry Point.
Runs the ASGI app with Hypercorn.
"""

import asyncio
import os
import sys
from hypercorn.config import Config
from hypercorn.asyncio import serve
from app import create_app

app = create_app()

def main():
    settings = app.config["SETTINGS"]
    host = os.environ.get("MELODI_HOST", settings.get("server", "host", "127.0.0.1"))
    port = os.environ.get("MELODI_PORT", settings.get("server", "port", 4000))
    debug = settings.get("server", "debug", False)

    config = Config()
    config.bind = [f"{host}:{port}"]
    config.use_reloader = debug
    config.accesslog = "-" if debug else None
    config.errorlog = "-"

    print("==================================================")
    print(f"🚀 MELODI Launcher actif sur http://{host}:{port}")
    print("==================================================")

    try:
        asyncio.run(serve(app, config))
    except (KeyboardInterrupt, SystemExit):
        print("\n[MELODI Launcher] Extinction demandée.")
    except OSError as e:
        if getattr(e, "errno", None) == 98 or "already in use" in str(e).lower() or "address already in use" in str(e).lower():
            print(f"\n❌ Erreur : Le port {port} est déjà utilisé par un autre processus.")
            print(f"👉 Fermez le serveur existant tournant sur http://{host}:{port} ou modifiez le port dans config/config.json.")
        else:
            print(f"\n❌ Erreur serveur : {e}")

if __name__ == "__main__":
    main()
