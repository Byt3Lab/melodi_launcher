"""
ProcessManager: Abstraction responsible for launching, monitoring, and stopping background processes cleanly.
"""

import asyncio
import os
import signal
import time
from typing import Dict, Any, Optional
from app.services.log_manager import LogManager

class ProcessManager:
    def __init__(self, log_manager: LogManager):
        self.log_manager = log_manager
        self.process: Optional[asyncio.subprocess.Process] = None
        self.start_time: Optional[float] = None
        self._lock = asyncio.Lock()
        self._log_file_handle = None

    async def is_running(self) -> bool:
        """Vérifie si le processus est actuellement en cours d'exécution."""
        if self.process is None:
            return False
        if self.process.returncode is not None:
            return False
        # Vérification complémentaire de santé du PID
        try:
            os.kill(self.process.pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False

    def get_pid(self) -> Optional[int]:
        """Retourne le PID du processus s'il est actif."""
        if self.process and self.process.returncode is None:
            return self.process.pid
        return None

    def get_uptime_seconds(self) -> float:
        """Retourne la durée de fonctionnement en secondes."""
        if self.start_time and self.process and self.process.returncode is None:
            return time.time() - self.start_time
        return 0.0

    def get_formatted_uptime(self) -> str:
        """Retourne l'Uptime formaté sous forme HH:MM:SS."""
        seconds = int(self.get_uptime_seconds())
        if seconds <= 0:
            return "00:00:00"
        hours, remainder = divmod(seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    async def start(self, command: list, cwd: str) -> Dict[str, Any]:
        """
        Démarre le sous-processus de manière sécurisée avec protection anti-doublon.
        """
        async with self._lock:
            if await self.is_running():
                return {
                    "success": False,
                    "message": "Le processus est déjà en cours d'exécution.",
                    "pid": self.get_pid()
                }

            if not command or not isinstance(command, list):
                return {
                    "success": False,
                    "message": "Commande de démarrage invalide.",
                    "pid": None
                }

            if not os.path.exists(cwd):
                return {
                    "success": False,
                    "message": f"Le répertoire de travail '{cwd}' n'existe pas.",
                    "pid": None
                }

            try:
                self.log_manager.ensure_log_dir_exists()
                self._log_file_handle = open(self.log_manager.log_file_path, "a", encoding="utf-8")
                self._log_file_handle.write(f"\n=== [MELODI LAUNCHER] Démarrage du processus : {' '.join(command)} ===\n")
                self._log_file_handle.flush()

                # Attacher le stdout/stderr du sous-processus au fichier de log
                self.process = await asyncio.create_subprocess_exec(
                    *command,
                    cwd=cwd,
                    stdout=self._log_file_handle,
                    stderr=asyncio.subprocess.STDOUT,
                    start_new_session=True
                )
                self.start_time = time.time()

                # Vérifier brièvement si le processus s'arrête immédiatement en crash
                await asyncio.sleep(0.2)
                if self.process.returncode is not None:
                    return {
                        "success": False,
                        "message": f"Le processus a échoué au démarrage (Code de retour : {self.process.returncode}).",
                        "pid": None
                    }

                return {
                    "success": True,
                    "message": "Processus démarré avec succès.",
                    "pid": self.process.pid
                }

            except Exception as e:
                if self._log_file_handle and not self._log_file_handle.closed:
                    self._log_file_handle.write(f"=== [MELODI LAUNCHER] Erreur de lancement : {e} ===\n")
                    self._log_file_handle.flush()
                    self._log_file_handle.close()
                return {
                    "success": False,
                    "message": f"Erreur lors de l'exécution du processus : {str(e)}",
                    "pid": None
                }

    async def stop(self, timeout: float = 5.0) -> Dict[str, Any]:
        """
        Arrête proprement le processus (SIGTERM puis SIGKILL si nécessaire).
        """
        async with self._lock:
            if not await self.is_running():
                return {
                    "success": True,
                    "message": "Le processus n'était pas en cours d'exécution."
                }

            try:
                # Envoyer un signal SIGTERM au groupe de processus
                if hasattr(os, "killpg"):
                    try:
                        os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                    except Exception:
                        self.process.terminate()
                else:
                    self.process.terminate()

                # Attendre l'arrêt gracieux
                try:
                    await asyncio.wait_for(self.process.wait(), timeout=timeout)
                except asyncio.TimeoutError:
                    # Forcer l'arrêt par SIGKILL si le process ne répond pas
                    if hasattr(os, "killpg"):
                        try:
                            os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                        except Exception:
                            self.process.kill()
                    else:
                        self.process.kill()
                    await self.process.wait()

                returncode = self.process.returncode
                self.process = None
                self.start_time = None

                if self._log_file_handle and not self._log_file_handle.closed:
                    self._log_file_handle.write(f"=== [MELODI LAUNCHER] Processus arrêté (Code de retour : {returncode}) ===\n")
                    self._log_file_handle.flush()
                    self._log_file_handle.close()

                return {
                    "success": True,
                    "message": f"Processus arrêté avec succès (Code : {returncode})."
                }

            except Exception as e:
                return {
                    "success": False,
                    "message": f"Erreur lors de l'arrêt du processus : {str(e)}"
                }

    async def restart(self, command: list, cwd: str) -> Dict[str, Any]:
        """Arrête puis redémarre le processus."""
        stop_res = await self.stop()
        if not stop_res["success"]:
            return stop_res
        await asyncio.sleep(0.5)
        return await self.start(command, cwd)

    async def get_status_info(self) -> Dict[str, Any]:
        """Consolide les métriques actuelles du processus."""
        running = await self.is_running()
        return {
            "is_running": running,
            "pid": self.get_pid() if running else None,
            "uptime_seconds": round(self.get_uptime_seconds(), 1) if running else 0,
            "uptime_formatted": self.get_formatted_uptime() if running else "00:00:00",
            "return_code": self.process.returncode if self.process else None
        }
