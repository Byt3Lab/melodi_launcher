"""
ServerManager: Managing registered servers (local and remote SSH) and their Executors.
"""

import json
import os
from typing import Dict, List, Optional, Any
from app.i18n import t
from app.remote.executor import Executor
from app.remote.local_executor import LocalExecutor
from app.remote.ssh_executor import SSHExecutor
from app.remote.credential_manager import CredentialManager
from app.utils.helpers import get_project_root

DEFAULT_SERVERS = [
    {
        "id": "local",
        "name": "Localhost (Machine locale)",
        "type": "local",
        "host": "127.0.0.1",
        "port": 22,
        "username": "",
        "key_path": "",
        "auth_method": "none",
        "is_default": True
    }
]

class ServerManager:
    def __init__(self, servers_file_path: Optional[str] = None):
        if servers_file_path is None:
            servers_file_path = os.path.join(get_project_root(), "config", "servers.json")
        self.servers_file_path = servers_file_path
        self.credentials = CredentialManager()
        self._servers: Dict[str, Dict[str, Any]] = {}
        self._executors: Dict[str, Executor] = {}
        self.load()

    def _extract_and_store_secrets(self, server_id: str, data: Dict[str, Any]) -> bool:
        """Migre les mots de passe hors du dictionnaire JSON vers le trousseau système."""
        migrated = False
        for key in ("password", "sudo_password"):
            val = data.pop(key, None)
            if val:
                self.credentials.store_secret(server_id, key, val)
                migrated = True
        return migrated

    def load(self):
        """Charge les serveurs depuis servers.json ou initialise avec localhost."""
        migrated_any = False
        if os.path.exists(self.servers_file_path):
            try:
                with open(self.servers_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "id" in item:
                            sid = item["id"]
                            if self._extract_and_store_secrets(sid, item):
                                migrated_any = True
                            self._servers[sid] = item
            except Exception as e:
                print(f"[ServerManager] Error loading servers.json ({e}), using default localhost.")

        if "local" not in self._servers:
            self._servers["local"] = dict(DEFAULT_SERVERS[0])
            self.save()
        elif migrated_any:
            self.save()

        # Instancier l'exécuteur local avec mot de passe éventuel
        local_pass = self.credentials.get_secret("local", "sudo_password") or self.credentials.get_secret("local", "password")
        self._executors["local"] = LocalExecutor(password=local_pass)

    def save(self) -> bool:
        """Sauvegarde la liste des serveurs dans servers.json sans secrets en clair."""
        try:
            os.makedirs(os.path.dirname(self.servers_file_path), exist_ok=True)
            sanitized = []
            for srv in self._servers.values():
                clean = {k: v for k, v in srv.items() if k not in ("password", "sudo_password")}
                sanitized.append(clean)
            with open(self.servers_file_path, "w", encoding="utf-8") as f:
                json.dump(sanitized, f, indent=4, ensure_ascii=False)
            try:
                os.chmod(self.servers_file_path, 0o600)
            except OSError:
                pass
            return True
        except Exception as e:
            print(f"[ServerManager] Save error: {e}")
            return False

    def get_all_servers(self) -> List[Dict[str, Any]]:
        """Retourne la liste de tous les serveurs enregistrés."""
        return list(self._servers.values())

    def get_server(self, server_id: str) -> Optional[Dict[str, Any]]:
        """Récupère la configuration d'un serveur spécifique."""
        return self._servers.get(server_id)

    def get_executor(self, server_id: str) -> Executor:
        """Retourne l'instance Executor (LocalExecutor ou SSHExecutor) pour le serveur donné."""
        if server_id in self._executors:
            return self._executors[server_id]

        srv = self.get_server(server_id)
        pwd = self.credentials.get_secret(server_id, "password")
        sudo_pwd = self.credentials.get_secret(server_id, "sudo_password")

        if not srv or srv.get("type") == "local":
            executor = LocalExecutor(password=sudo_pwd or pwd)
        else:
            auth_method = srv.get("auth_method", "key")
            key_path = srv.get("key_path") if auth_method == "key" or not srv.get("auth_method") else None
            ssh_password = pwd if auth_method == "password" else None
            sudo_password = sudo_pwd or pwd

            executor = SSHExecutor(
                host=srv.get("host", "127.0.0.1"),
                port=srv.get("port", 22),
                username=srv.get("username", "root"),
                key_path=key_path,
                password=ssh_password,
                sudo_password=sudo_password
            )
        self._executors[server_id] = executor
        return executor

    def set_server_sudo_password(self, server_id: str, sudo_password: str, save: bool = True) -> bool:
        """Définit le mot de passe sudo pour le serveur et synchronise l'exécuteur."""
        srv = self.get_server(server_id)
        if not srv:
            return False

        self.credentials.store_secret(server_id, "sudo_password", sudo_password)
        self.credentials.store_secret(server_id, "password", sudo_password)

        if server_id in self._executors:
            executor = self._executors[server_id]
            executor.sudo_password = sudo_password
            executor.password = sudo_password

        if save:
            self.save()
        return True

    def add_server(self, server_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ajoute un nouveau serveur distant."""
        data = dict(server_data)
        server_id = data.get("id") or f"srv_{int(os.urandom(3).hex(), 16)}"
        data["id"] = server_id
        data["type"] = data.get("type", "ssh")
        self._extract_and_store_secrets(server_id, data)

        self._servers[server_id] = data
        self.save()
        return {"success": True, "server": data}

    def update_server(self, server_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Met à jour les détails d'un serveur et réinitialise son exécuteur."""
        if server_id not in self._servers:
            return {"success": False, "message": t("server_mgr.not_found")}

        upd = dict(updates)
        self._extract_and_store_secrets(server_id, upd)
        self._servers[server_id].update(upd)
        self.save()

        # Invalider l'ancien exécuteur s'il existe
        if server_id in self._executors:
            del self._executors[server_id]

        return {"success": True, "server": self._servers[server_id]}

    def delete_server(self, server_id: str) -> Dict[str, Any]:
        """Supprime un serveur distant (localhost ne peut pas être supprimé)."""
        if server_id == "local":
            return {"success": False, "message": t("server_mgr.cannot_delete_local")}

        if server_id in self._servers:
            del self._servers[server_id]
            if server_id in self._executors:
                del self._executors[server_id]
            self.credentials.delete_secret(server_id, "password")
            self.credentials.delete_secret(server_id, "sudo_password")
            self.save()
            return {"success": True, "message": t("server_mgr.deleted")}

        return {"success": False, "message": t("server_mgr.unknown")}

    async def test_server_connection(self, server_id: str) -> Dict[str, Any]:
        """Teste la connectivité réseau/SSH d'un serveur."""
        executor = self.get_executor(server_id)
        return await executor.test_connection()
