"""
Web Routes Blueprint for MELODI Control Center (HTML Jinja2 pages).
"""

from quart import Blueprint, render_template

web_bp = Blueprint("web", __name__)

@web_bp.route("/")
async def index():
    """Dashboard principal multi-serveurs."""
    return await render_template("dashboard.html", active_page="dashboard")

@web_bp.route("/servers")
async def servers():
    """Gestion des serveurs (Localhost & Distants SSH)."""
    return await render_template("servers.html", active_page="servers")

@web_bp.route("/services")
async def services():
    """Vue détaillée des services (MELODI, PostgreSQL, Redis, pgAdmin)."""
    return await render_template("services.html", active_page="services")

@web_bp.route("/installation")
async def installation():
    """Assistant d'installation global (vue d'ensemble)."""
    return await render_template("installation.html", active_page="installation")

@web_bp.route("/installation/<service_name>")
async def installation_service(service_name: str):
    """Page d'installation dédiée pour un service spécifique."""
    valid_services = ["melodi", "melodi_websocket", "melodi_process_manager", "postgresql", "redis", "pgadmin"]
    if service_name not in valid_services:
        return await render_template("installation.html", active_page="installation")
    
    return await render_template(
        "service_installation.html",
        active_page="installation",
        service_name=service_name
    )

@web_bp.route("/logs")
async def logs():
    """Console de visualisation des logs."""
    return await render_template("logs.html", active_page="logs")

@web_bp.route("/settings")
async def settings():
    """Paramètres globaux du Control Center."""
    return await render_template("settings.html", active_page="settings")

