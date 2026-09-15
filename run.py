#!/usr/bin/env python3
"""
MELODI Launcher Application Entry Point.
Runs the ASGI app with Hypercorn.
"""

import asyncio
import sys
from hypercorn.config import Config
from hypercorn.asyncio import serve
from app import create_app

app = create_app()

def main():
    settings = app.config["SETTINGS"]
    host = settings.get("server", "host", "127.0.0.1")
    port = settings.get("server", "port", 8080)
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

if __name__ == "__main__":
    main()
