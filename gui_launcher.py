#!/usr/bin/env python3
"""
MELODI Launcher Desktop: Application native PySide6 + qasync pour l'orchestration de MELODI ERP.
"""

import sys
import asyncio
from PySide6.QtWidgets import QApplication
from qasync import QEventLoop
from app.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("MELODI Control Center")

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = MainWindow()
    window.show()

    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()
