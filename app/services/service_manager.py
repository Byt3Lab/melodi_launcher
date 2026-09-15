"""
ServiceManager: Registry holding and coordinating all system services.
"""

from typing import Dict, List, Optional, Any
from app.services.base_service import BaseService

class ServiceManager:
    def __init__(self):
        self._services: Dict[str, BaseService] = {}

    def register(self, service: BaseService):
        """Enregistre un nouveau service dans le manager."""
        self._services[service.name] = service

    def get_service(self, name: str) -> Optional[BaseService]:
        """Récupère un service par son nom."""
        return self._services.get(name)

    def get_all_services(self) -> List[BaseService]:
        """Retourne la liste de tous les services enregistrés."""
        return list(self._services.values())

    async def get_all_statuses(self) -> List[Dict[str, Any]]:
        """Retourne les statuts de tous les services enregistrés."""
        statuses = []
        for service in self._services.values():
            statuses.append(await service.status())
        return statuses
