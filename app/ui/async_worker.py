"""
AsyncWorker: Pont thread-safe entre la boucle d'événements asyncio et l'interface Tkinter.
Permet d'exécuter des coroutines (SSH, commandes système, transferts) sans jamais bloquer l'UI.
"""

import asyncio
import threading
from typing import Callable, Any, Optional
import tkinter as tk

class AsyncWorker:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._is_running = threading.Event()
        self._start_loop()

    def _start_loop(self):
        """Démarre le thread d'arrière-plan avec sa propre boucle asyncio."""
        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self._is_running.set()
            self.loop.run_forever()

        self._thread = threading.Thread(target=run_loop, daemon=True, name="MelodiAsyncWorker")
        self._thread.start()
        self._is_running.wait(timeout=2.0)

    def run_coroutine(
        self,
        coro,
        on_done: Optional[Callable[[Any], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None
    ):
        """
        Soumet une coroutine à la boucle asyncio d'arrière-plan.
        Les rappels on_done et on_error sont automatiquement exécutés sur le thread principal Tkinter.
        """
        if not self.loop or not self.loop.is_running():
            raise RuntimeError("La boucle d'événements asyncio n'est pas active.")

        async def _wrapper():
            try:
                result = await coro
                if on_done:
                    self.call_in_gui(on_done, result)
            except Exception as exc:
                if on_error:
                    self.call_in_gui(on_error, exc)
                else:
                    print(f"[AsyncWorker] Erreur non interceptée dans coroutine: {exc}")

        asyncio.run_coroutine_threadsafe(_wrapper(), self.loop)

    def call_in_gui(self, func: Callable, *args, **kwargs):
        """Planifie l'exécution d'une fonction sur le thread principal de Tkinter."""
        try:
            self.root.after_idle(lambda: func(*args, **kwargs))
        except Exception as e:
            print(f"[AsyncWorker] Erreur planification GUI: {e}")

    def stop(self):
        """Arrête proprement la boucle asyncio et annule les tâches pendantes."""
        if self.loop and self.loop.is_running():
            def _cancel_and_stop():
                try:
                    tasks = [t for t in asyncio.all_tasks(self.loop) if not t.done()]
                    for task in tasks:
                        task.cancel()
                except Exception:
                    pass
                self.loop.stop()

            self.loop.call_soon_threadsafe(_cancel_and_stop)

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
