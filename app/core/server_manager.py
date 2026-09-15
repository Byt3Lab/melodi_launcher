"""
ServerManager: Managing registered servers (local and remote SSH) and their Executors.
"""

import json
import os
from typing import Dict, List, Optional, Any
from app.remote.executor import Executor
from app.remote.local_executor import LocalExecutor
from app.remote.ssh_executor import SSHExecutor
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
        self._servers: Dict[str, Dict[str, Any]] = {}
        self._executors: Dict[str, Executor] = {}
        self.load()

    def load(self):
        """Charge les serveurs depuis servers.json ou initialise avec localhost."""
        if os.path.exists(self.servers_file_path):
            try:
                with open(self.servers_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "id" in item:
                            self._servers[item["id"]] = item
            except Exception as e:
                print(f"[ServerManager] Error loading servers.json ({e}), using default localhost.")

        if "local" not in self._servers:
            self._servers["local"] = DEFAULT_SERVERS[0]
            self.save()

        # Instancier l'exécuteur local
        self._executors["local"] = LocalExecutor()

    def save(self) -> bool:
        """Sauvegarde la liste des serveurs dans servers.json."""
        try:
            os.makedirs(os.path.dirname(self.servers_file_path), exist_ok=True)
            with open(self.servers_file_path, "w", encoding="utf-8") as f:
                json.dump(list(self._servers.values()), f, indent=4, ensure_ascii=False)
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
        if not srv or srv.get("type") == "local":
            executor = LocalExecutor()
        else:
            auth_method = srv.get("auth_method", "key")
            key_path = srv.get("key_path") if auth_method == "key" or not srv.get("auth_method") else None
            password = srv.get("password") if auth_method == "password" else None

            executor = SSHExecutor(
                host=srv.get("host", "127.0.0.1"),
                port=srv.get("port", 22),
                username=srv.get("username", "root"),
                key_path=key_path,
                password=password
            )
        self._executors[server_id] = executor
        return executor

    def add_server(self, server_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ajoute un nouveau serveur distant."""
        server_id = server_data.get("id") or f"srv_{int(os.urandom(3).hex(), 16)}"
        server_data["id"] = server_id
        server_data["type"] = server_data.get("type", "ssh")
        
        self._servers[server_id] = server_data
        self.save()
        return {"success": True, "server": server_data}

    def update_server(self, server_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Met à jour les détails d'un serveur et réinitialise son exécuteur."""
        if server_id not in self._servers:
            return {"success": False, "message": "Serveur non trouvé."}

        self._servers[server_id].update(updates)
        self.save()

        # Invalider l'ancien exécuteur s'il existe
        if server_id in self._executors:
            del self._executors[server_id]

        return {"success": True, "server": self._servers[server_id]}

    def delete_server(self, server_id: str) -> Dict[str, Any]:
        """Supprime un serveur distant (localhost ne peut pas être supprimé)."""
        if server_id == "local":
            return {"success": False, "message": "Impossible de supprimer le serveur local default."}

        if server_id in self._servers:
            del self._servers[server_id]
            if server_id in self._executors:
                del self._executors[server_id]
            self.save()
            return {"success": True, "message": "Serveur supprimé avec succès."}

        return {"success": False, "message": "Serveur introuvable."}

    async def test_server_connection(self, server_id: str) -> Dict[str, Any]:
        """Teste la connectivité réseau/SSH d'un serveur."""
        executor = self.get_executor(server_id)
        return await executor.test_connection()
