"""
CredentialManager: Managing SSH key paths and secure credential storage via OS keyring.
"""

import os
from typing import List, Dict, Any, Optional

try:
    import keyring
    from keyring.errors import KeyringError
except ImportError:  # pragma: no cover
    keyring = None
    KeyringError = Exception

SERVICE_NAME = "melodi-launcher"


class CredentialManager:
    def __init__(self):
        self.ssh_dir = os.path.expanduser("~/.ssh")
        self._fallback_store: Dict[str, str] = {}

    def discover_ssh_keys(self) -> List[Dict[str, Any]]:
        """Détecte les clés SSH privées disponibles dans ~/.ssh/"""
        keys = []
        if not os.path.exists(self.ssh_dir):
            return keys

        standard_key_names = ["id_ed25519", "id_rsa", "id_ecdsa", "id_dsa"]
        for name in standard_key_names:
            key_path = os.path.join(self.ssh_dir, name)
            if os.path.exists(key_path) and not key_path.endswith(".pub"):
                pub_path = key_path + ".pub"
                keys.append({
                    "name": name,
                    "path": key_path,
                    "has_public_key": os.path.exists(pub_path)
                })
        return keys

    def get_default_key_path(self) -> str:
        """Retourne la clé SSH par défaut si disponible."""
        keys = self.discover_ssh_keys()
        if keys:
            return keys[0]["path"]
        return os.path.expanduser("~/.ssh/id_rsa")

    def store_secret(self, server_id: str, kind: str, value: Optional[str]) -> None:
        """Stocke un secret (password / sudo_password) dans le trousseau système."""
        account = f"{server_id}:{kind}"
        if not value:
            self.delete_secret(server_id, kind)
            return
        self._fallback_store[account] = value
        if keyring is not None:
            try:
                keyring.set_password(SERVICE_NAME, account, value)
            except Exception:
                pass

    def get_secret(self, server_id: str, kind: str) -> Optional[str]:
        """Récupère un secret depuis le trousseau système (ou le cache mémoire)."""
        account = f"{server_id}:{kind}"
        if account in self._fallback_store:
            return self._fallback_store[account]
        if keyring is not None:
            try:
                val = keyring.get_password(SERVICE_NAME, account)
                if val is not None:
                    self._fallback_store[account] = val
                return val
            except Exception:
                return None
        return None

    def delete_secret(self, server_id: str, kind: str) -> None:
        """Supprime un secret du trousseau système."""
        account = f"{server_id}:{kind}"
        self._fallback_store.pop(account, None)
        if keyring is not None:
            try:
                keyring.delete_password(SERVICE_NAME, account)
            except Exception:
                pass
