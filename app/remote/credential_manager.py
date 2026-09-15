"""
CredentialManager: Managing SSH key paths and credential security.
"""

import os
from typing import List, Dict, Any

class CredentialManager:
    def __init__(self):
        self.ssh_dir = os.path.expanduser("~/.ssh")

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
