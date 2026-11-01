"""
Web Routes Blueprint for MELODI Control Center (HTML Jinja2 pages).
"""

from quart import Blueprint, render_template, request, send_from_directory
from app.utils.helpers import resource_path

web_bp = Blueprint("web", __name__)


@web_bp.route("/service-worker.js")
async def service_worker():
    response = await send_from_directory(
        resource_path("static"),
        "service-worker.js",
        mimetype="application/javascript",
    )
    response.headers["Service-Worker-Allowed"] = "/"
    response.headers["Cache-Control"] = "no-cache"
    return response


async def _render_page(template: str, **context):
    context["render_partial"] = request.args.get("partial") == "1"
    return await render_template(template, **context)


@web_bp.route("/")
async def index():
    """Dashboard principal multi-serveurs."""
    return await _render_page("dashboard.html", active_page="dashboard")

@web_bp.route("/servers")
async def servers():
    """Gestion des serveurs (Localhost & Distants SSH)."""
    return await _render_page("servers.html", active_page="servers")

@web_bp.route("/services")
async def services():
    """Vue détaillée des services (MELODI, PostgreSQL, Redis, pgAdmin)."""
    return await _render_page("services.html", active_page="services")

@web_bp.route("/installation")
async def installation():
    """Assistant d'installation global (vue d'ensemble)."""
    return await _render_page("installation.html", active_page="installation")

@web_bp.route("/installation/<service_name>")
async def installation_service(service_name: str):
    """Page d'installation dédiée pour un service spécifique."""
    valid_services = ["melodi", "melodi_websocket", "melodi_process_manager", "postgresql", "redis", "pgadmin"]
    if service_name not in valid_services:
        return await _render_page("installation.html", active_page="installation")
    
    return await _render_page(
        "service_installation.html",
        active_page="installation",
        service_name=service_name
    )

@web_bp.route("/logs")
async def logs():
    """Console de visualisation des logs."""
    return await _render_page("logs.html", active_page="logs")

@web_bp.route("/settings")
async def settings():
    """Paramètres globaux du Control Center."""
    return await _render_page("settings.html", active_page="settings")
