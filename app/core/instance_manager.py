"""
InstanceManager: Gestion des installations multiples (MELODI ERP et PostgreSQL) par serveur,
avec ports dédiés, dossiers isolés et services système associés.
"""

import json
import os
import re
import unicodedata
from typing import Dict, List, Optional, Any
from app.utils.helpers import get_project_root


def slugify_service_name(name: str) -> str:
    """Génère un identifiant de service sûr commençant par 'melodi' (ex: 'melodi-filiale-b')."""
    normalized = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
    if not slug or slug in ("melodi", "melodi-erp"):
        return "melodi"
    if not slug.startswith("melodi-"):
        slug = f"melodi-{slug}"
    return slug


def slugify_pg_service_name(port: int, name: str = "") -> str:
    """Génère un identifiant de service PostgreSQL ('postgresql' pour 5432, 'postgresql-<port>' sinon)."""
    if int(port) == 5432 and (not name or name.strip().lower() in ("postgresql", "postgresql 5432")):
        return "postgresql"
    return f"postgresql-{int(port)}"


def win_task_name_for_service(service_name: str) -> str:
    """Convertit un nom de service MELODI en nom de tâche planifiée Windows."""
    if not service_name or service_name == "melodi":
        return "MELODI_ERP"
    suffix = service_name[len("melodi-"):] if service_name.startswith("melodi-") else service_name
    clean = re.sub(r"[^A-Za-z0-9]+", "_", suffix).strip("_").upper()
    return f"MELODI_ERP_{clean}" if clean else "MELODI_ERP"


class InstanceManager:
    def __init__(self, instances_file_path: Optional[str] = None):
        if instances_file_path is None:
            instances_file_path = os.path.join(get_project_root(), "config", "instances.json")
        self.instances_file_path = instances_file_path
        self._instances: Dict[str, Dict[str, Any]] = {}
        self.load()

    def load(self) -> None:
        self._instances.clear()
        if os.path.exists(self.instances_file_path):
            try:
                with open(self.instances_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "id" in item:
                            item.setdefault("kind", "melodi")
                            self._instances[item["id"]] = item
            except Exception as exc:
                print(f"[InstanceManager] Error loading instances.json: {exc}")

    def save(self) -> bool:
        try:
            os.makedirs(os.path.dirname(self.instances_file_path), exist_ok=True)
            with open(self.instances_file_path, "w", encoding="utf-8") as f:
                json.dump(list(self._instances.values()), f, indent=4, ensure_ascii=False)
            return True
        except Exception as exc:
            print(f"[InstanceManager] Save error: {exc}")
            return False

    def get_instances(self, server_id: str, kind: str = "melodi") -> List[Dict[str, Any]]:
        """Retourne les installations enregistrées sur un serveur pour le type donné ('melodi' ou 'postgresql')."""
        items = [
            i for i in self._instances.values()
            if i.get("server_id") == server_id and i.get("kind", "melodi") == kind
        ]
        return sorted(items, key=lambda x: (int(x.get("port", 5000)), x.get("name", "")))

    def get_pg_instances(self, server_id: str) -> List[Dict[str, Any]]:
        """Retourne les instances PostgreSQL enregistrées pour un serveur."""
        return self.get_instances(server_id, kind="postgresql")

    def get_by_service_name(self, server_id: str, service_name: str) -> Optional[Dict[str, Any]]:
        for inst in self._instances.values():
            if inst.get("server_id") == server_id and inst.get("service_name") == service_name:
                return inst
        return None

    def is_port_used(
        self,
        server_id: str,
        port: int,
        exclude_service_name: Optional[str] = None,
        kind: Optional[str] = None,
    ) -> bool:
        """Vérifie si un port est déjà utilisé par une autre installation sur ce serveur."""
        for inst in self._instances.values():
            if inst.get("server_id") != server_id:
                continue
            if kind and inst.get("kind", "melodi") != kind:
                continue
            if exclude_service_name and inst.get("service_name") == exclude_service_name:
                continue
            if int(inst.get("port", 0)) == int(port):
                return True
        return False

    def suggest_next_port(self, server_id: str, base_port: int = 5000, kind: str = "melodi") -> int:
        """Retourne le premier port libre à partir de base_port pour ce serveur."""
        used = {
            int(i.get("port", 0))
            for i in self._instances.values()
            if i.get("server_id") == server_id and i.get("kind", "melodi") == kind
        }
        port = base_port
        while port in used and port < 65535:
            port += 1
        return port

    def add_or_update_instance(
        self,
        server_id: str,
        name: str,
        port: int,
        install_dir: str,
        service_name: Optional[str] = None,
        kind: str = "melodi",
        pg_port: Optional[int] = None,
        pg_service_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Ajoute ou met à jour une installation (MELODI ERP ou PostgreSQL) sur le serveur donné."""
        if kind == "postgresql":
            svc = service_name or slugify_pg_service_name(port, name)
        else:
            svc = service_name or slugify_service_name(name)
        port = int(port)

        if self.is_port_used(server_id, port, exclude_service_name=svc, kind=kind):
            return {"success": False, "message": f"Port {port} already used"}

        existing_id = None
        for iid, inst in self._instances.items():
            if inst.get("server_id") == server_id and inst.get("service_name") == svc and inst.get("kind", "melodi") == kind:
                existing_id = iid
                break

        iid = existing_id or f"{'pg' if kind == 'postgresql' else 'inst'}_{os.urandom(3).hex()}"
        record = {
            "id": iid,
            "kind": kind,
            "server_id": server_id,
            "name": name.strip() or ("PostgreSQL" if kind == "postgresql" else "MELODI ERP"),
            "service_name": svc,
            "port": port,
            "install_dir": install_dir,
            "is_default": False,
        }
        if kind == "melodi" and pg_port is not None:
            record["pg_port"] = int(pg_port)
            record["pg_service_name"] = pg_service_name or slugify_pg_service_name(pg_port)

        self._instances[iid] = record
        self.save()
        return {"success": True, "instance": record}

    def delete_instance(self, instance_id: str) -> Dict[str, Any]:
        if instance_id in self._instances:
            del self._instances[instance_id]
            self.save()
            return {"success": True}
        return {"success": False}
