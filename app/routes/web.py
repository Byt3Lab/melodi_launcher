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
    """Vue détaillée des services (MELODI, PostgreSQL, Redis, Nginx, Celery)."""
    return await render_template("services.html", active_page="services")

@web_bp.route("/installation")
async def installation():
    """Assistant d'installation guidée."""
    return await render_template("installation.html", active_page="installation")

@web_bp.route("/monitoring")
async def monitoring():
    """Surveillance des ressources système (CPU, RAM, Disque)."""
    return await render_template("monitoring.html", active_page="monitoring")

@web_bp.route("/logs")
async def logs():
    """Console de visualisation des logs."""
    return await render_template("logs.html", active_page="logs")

@web_bp.route("/settings")
async def settings():
    """Paramètres globaux du Control Center."""
    return await render_template("settings.html", active_page="settings")
