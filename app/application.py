"""
Application Factory for MELODI Control Center (Quart).
"""

from quart import Quart
from app.utils.helpers import resource_path
from app.config.settings import SettingsManager
from app.core.server_manager import ServerManager
from app.core.task_manager import TaskManager
from app.services.service_manager import ServiceManager
from app.services.process_manager import ProcessManager
from app.services.log_manager import LogManager
from app.remote.credential_manager import CredentialManager

# Services
from app.services.melodi import MelodiService
from app.services.postgresql import PostgreSQLService
from app.services.redis import RedisService
from app.services.nginx import NginxService
from app.services.celery import CeleryService

# Installers
from app.installers.melodi import MelodiInstaller
from app.installers.postgresql import PostgreSQLInstaller
from app.installers.redis import RedisInstaller
from app.installers.nginx import NginxInstaller

# Routes
from app.routes.web import web_bp
from app.routes.api import api_bp

def create_app(config_file_path: str = None) -> Quart:
    """
    Factory construisant et configurant le MELODI Control Center (Quart).
    """
    template_dir = resource_path("templates")
    static_dir = resource_path("static")

    app = Quart(
        __name__,
        template_folder=template_dir,
        static_folder=static_dir
    )

    # 1. Managers principaux
    settings_manager = SettingsManager(config_file_path)
    server_manager = ServerManager()
    task_manager = TaskManager()
    credential_manager = CredentialManager()
    log_manager = LogManager(settings_manager)
    process_manager = ProcessManager(log_manager)

    app.config["SETTINGS"] = settings_manager
    app.config["SERVER_MANAGER"] = server_manager
    app.config["TASK_MANAGER"] = task_manager
    app.config["CREDENTIAL_MANAGER"] = credential_manager
    app.config["LOG_MANAGER"] = log_manager
    app.config["PROCESS_MANAGER"] = process_manager

    # 2. Services enregistrés
    services_map = {
        "melodi": MelodiService(settings_manager, process_manager),
        "postgresql": PostgreSQLService(),
        "redis": RedisService(),
        "nginx": NginxService(),
        "celery": CeleryService()
    }
    app.config["SERVICES_MAP"] = services_map

    # 3. Installateurs enregistrés
    installers_map = {
        "melodi": MelodiInstaller(),
        "postgresql": PostgreSQLInstaller(),
        "redis": RedisInstaller(),
        "nginx": NginxInstaller()
    }
    app.config["INSTALLERS_MAP"] = installers_map

    # 4. Enregistrer les Blueprints
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp)

    # 5. Cycle de vie Lifespan
    @app.while_serving
    async def lifespan():
        yield
        # Shutdown gracieux des processus locaux s'ils tournent
        proc_mgr = app.config.get("PROCESS_MANAGER")
        if proc_mgr and await proc_mgr.is_running():
            print("[MELODI Control Center] Extinction du sous-processus MELODI local...")
            await proc_mgr.stop(timeout=5.0)

    return app
