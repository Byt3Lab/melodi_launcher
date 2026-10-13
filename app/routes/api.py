"""
REST API Blueprint for MELODI Control Center.
Supports Multi-Server Management, Service Control, Background Tasks, System Metrics & Logs.
"""

from quart import Blueprint, jsonify, request, websocket, current_app
from app.system.system_info import SystemInfo
import asyncio
import os
import pty
import fcntl
import termios
import struct
import asyncssh


api_bp = Blueprint("api", __name__, url_prefix="/api")

def get_server_manager():
    return current_app.config["SERVER_MANAGER"]

def get_task_manager():
    return current_app.config["TASK_MANAGER"]

def get_services_map():
    return current_app.config["SERVICES_MAP"]

def get_installers_map():
    return current_app.config["INSTALLERS_MAP"]

def get_credential_manager():
    return current_app.config["CREDENTIAL_MANAGER"]

def get_settings():
    return current_app.config["SETTINGS"]

def get_log_manager():
    return current_app.config["LOG_MANAGER"]


# =========================================================================
# 1. SERVERS ENDPOINTS
# =========================================================================

@api_bp.route("/servers", methods=["GET"])
async def list_servers():
    """Liste tous les serveurs enregistrés (Locaux & Distants SSH)."""
    sm = get_server_manager()
    return jsonify({"success": True, "servers": sm.get_all_servers()})

@api_bp.route("/servers", methods=["POST"])
async def add_server():
    """Ajoute un nouveau serveur SSH distant."""
    data = await request.get_json()
    if not data or "name" not in data or "host" not in data:
        return jsonify({"success": False, "message": "Nom et adresse hôte requis."}), 400

    sm = get_server_manager()
    result = sm.add_server(data)
    return jsonify(result)

@api_bp.route("/servers/<server_id>", methods=["GET"])
async def get_server(server_id):
    """Récupère les détails d'un serveur."""
    sm = get_server_manager()
    srv = sm.get_server(server_id)
    if not srv:
        return jsonify({"success": False, "message": "Serveur non trouvé."}), 404
    return jsonify({"success": True, "server": srv})

@api_bp.route("/servers/<server_id>", methods=["PUT"])
async def update_server(server_id):
    """Met à jour la configuration d'un serveur."""
    data = await request.get_json()
    sm = get_server_manager()
    result = sm.update_server(server_id, data)
    return jsonify(result)

@api_bp.route("/servers/<server_id>", methods=["DELETE"])
async def delete_server(server_id):
    """Supprime un serveur."""
    sm = get_server_manager()
    result = sm.delete_server(server_id)
    return jsonify(result)

@api_bp.route("/servers/<server_id>/test", methods=["POST"])
async def test_server(server_id):
    """Teste la connexion SSH/Locale à un serveur."""
    sm = get_server_manager()
    result = await sm.test_server_connection(server_id)
    return jsonify(result)

@api_bp.websocket("/servers/<server_id>/terminal")
async def server_terminal_ws(server_id):
    """Session de terminal interactif bidirectionnel en temps réel (WebSocket)."""
    sm = get_server_manager()
    srv = sm.get_server(server_id)
    if not srv:
        await websocket.send("Erreur: Serveur introuvable.\r\n")
        return

    # 1. CAS SERVEUR LOCAL : Pseudo-terminal pty natif
    if srv.get("type") == "local" or server_id == "local":
        master_fd, slave_fd = pty.openpty()

        env = os.environ.copy()
        env["TERM"] = "xterm-256color"
        env["COLORTERM"] = "truecolor"

        proc = await asyncio.create_subprocess_exec(
            "/bin/bash",
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            env=env,
            close_fds=True
        )
        os.close(slave_fd)

        # Définir master_fd en mode non-bloquant
        flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
        fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

        loop = asyncio.get_event_loop()

        async def pty_reader():
            while True:
                try:
                    await asyncio.sleep(0.02)
                    data = await loop.run_in_executor(None, lambda: os.read(master_fd, 4096) if master_fd else b"")
                    if data:
                        await websocket.send(data.decode("utf-8", errors="replace"))
                except (OSError, asyncio.CancelledError):
                    break
                except Exception:
                    break

        reader_task = asyncio.create_task(pty_reader())

        try:
            while True:
                msg = await websocket.receive()
                if msg is None:
                    break
                os.write(master_fd, msg.encode("utf-8", errors="replace"))
        except (asyncio.CancelledError, Exception):
            pass
        finally:
            reader_task.cancel()
            try:
                os.close(master_fd)
            except Exception:
                pass
            try:
                proc.terminate()
            except Exception:
                pass

    # 2. CAS SERVEUR DISTANT SSH : asyncssh interactive session
    else:
        executor = sm.get_executor(server_id)
        if not await executor.is_connected():
            connected = await executor.connect()
            if not connected:
                await websocket.send(f"\r\n❌ Impossible d'ouvrir la connexion SSH à {srv.get('host')}\r\n")
                return

        conn = getattr(executor, "_conn", None)
        if not conn:
            await websocket.send("\r\n❌ Connexion SSH indisponible.\r\n")
            return

        try:
            chan, session = await conn.create_session(
                asyncssh.SSHClientSession,
                term_type="xterm-256color",
                term_size=(80, 24)
            )

            async def ssh_reader():
                while True:
                    try:
                        data = await session.read(4096)
                        if not data:
                            break
                        await websocket.send(str(data))
                    except Exception:
                        break

            ssh_task = asyncio.create_task(ssh_reader())

            try:
                while True:
                    msg = await websocket.receive()
                    if msg is None:
                        break
                    session.write(msg)
            except Exception:
                pass
            finally:
                ssh_task.cancel()
                try:
                    chan.close()
                except Exception:
                    pass
        except Exception as e:
            await websocket.send(f"\r\n❌ Erreur session interactive SSH: {str(e)}\r\n")



# =========================================================================
# 2. SYSTEM MONITORING ENDPOINTS
# =========================================================================

@api_bp.route("/servers/<server_id>/system", methods=["GET"])
async def get_system_metrics(server_id):
    """Récupère les métriques système (CPU, RAM, Disque, Uptime) du serveur ciblé."""
    sm = get_server_manager()
    executor = sm.get_executor(server_id)
    metrics = await SystemInfo.get_metrics(executor)
    return jsonify({"success": True, "metrics": metrics})


# =========================================================================
# 3. SERVICES ENDPOINTS
# =========================================================================

@api_bp.route("/servers/<server_id>/services", methods=["GET"])
async def list_server_services(server_id):
    """Liste tous les services et leur statut sur le serveur ciblé."""
    sm = get_server_manager()
    executor = sm.get_executor(server_id)
    services_map = get_services_map()

    statuses = []
    for srv_obj in services_map.values():
        statuses.append(await srv_obj.status(executor))

    return jsonify({"success": True, "services": statuses})

@api_bp.route("/servers/<server_id>/services/<service_name>/status", methods=["GET"])
async def get_service_status(server_id, service_name):
    """Statut détaillé d'un service sur un serveur."""
    sm = get_server_manager()
    executor = sm.get_executor(server_id)
    services_map = get_services_map()
    service = services_map.get(service_name)

    if not service:
        return jsonify({"success": False, "message": f"Service '{service_name}' non reconnu."}), 404

    status_info = await service.status(executor)
    return jsonify({"success": True, "service": status_info})

@api_bp.route("/servers/<server_id>/services/<service_name>/<action>", methods=["POST"])
async def control_service(server_id, service_name, action):
    """Exécute 'start', 'stop' ou 'restart' sur un service."""
    if action not in ["start", "stop", "restart"]:
        return jsonify({"success": False, "message": "Action invalide."}), 400

    sm = get_server_manager()
    executor = sm.get_executor(server_id)
    services_map = get_services_map()
    service = services_map.get(service_name)

    if not service:
        return jsonify({"success": False, "message": f"Service '{service_name}' non reconnu."}), 404

    func = getattr(service, action)
    result = await func(executor)
    status_code = 200 if result.get("success") else 400
    return jsonify(result), status_code

@api_bp.route("/servers/<server_id>/services/<service_name>/logs", methods=["GET"])
async def get_service_logs(server_id, service_name):
    """Extrait les logs récents d'un service."""
    lines = request.args.get("lines", default=100, type=int)
    sm = get_server_manager()
    executor = sm.get_executor(server_id)
    services_map = get_services_map()
    service = services_map.get(service_name)

    if not service:
        return jsonify({"success": False, "message": f"Service '{service_name}' non reconnu."}), 404

    logs = await service.get_logs(executor, lines=lines)
    return jsonify({"success": True, "logs": logs})


# =========================================================================
# 4. INSTALLERS & BACKGROUND TASKS ENDPOINTS
# =========================================================================

@api_bp.route("/servers/<server_id>/installers/<installer_name>", methods=["GET"])
async def get_installer_info(server_id, installer_name):
    """Vérifie l'état d'installation et les détails du service/installateur."""
    installers_map = get_installers_map()
    services_map = get_services_map()
    installer = installers_map.get(installer_name)
    service = services_map.get(installer_name)

    if not installer:
        return jsonify({"success": False, "message": f"Installateur '{installer_name}' non reconnu."}), 404

    sm = get_server_manager()
    srv = sm.get_server(server_id)
    if not srv:
        return jsonify({"success": False, "message": "Serveur non trouvé."}), 404

    executor = sm.get_executor(server_id)
    service_status = await service.status(executor) if service else {}

    return jsonify({
        "success": True,
        "name": installer.name,
        "display_name": installer.display_name,
        "service": service_status
    })

@api_bp.route("/servers/<server_id>/upload", methods=["POST"])
async def upload_file(server_id):
    """Upload un fichier (ex: archive ZIP de MELODI ERP) sur le serveur local ou distant."""
    files = await request.files
    if "file" not in files:
        return jsonify({"success": False, "message": "Aucun fichier fourni."}), 400

    file = files["file"]
    if not file.filename:
        return jsonify({"success": False, "message": "Nom de fichier manquant."}), 400

    import os
    upload_dir = "/tmp/melodi_uploads"
    os.makedirs(upload_dir, exist_ok=True)
    local_path = os.path.join(upload_dir, file.filename)
    await file.save(local_path)

    sm = get_server_manager()
    srv = sm.get_server(server_id)
    if not srv:
        return jsonify({"success": False, "message": "Serveur non trouvé."}), 404

    # Si le serveur est distant SSH, transférer le fichier via SFTP/SCP
    if server_id != "local":
        executor = sm.get_executor(server_id)
        if hasattr(executor, "_conn") and executor._conn:
            try:
                import asyncssh
                async with executor._conn.start_sftp_client() as sftp:
                    remote_path = f"/tmp/{file.filename}"
                    await sftp.put(local_path, remote_path)
                    return jsonify({"success": True, "file_path": remote_path, "filename": file.filename})
            except Exception as e:
                return jsonify({"success": False, "message": f"Erreur transfert SSH: {str(e)}"}), 500

    return jsonify({"success": True, "file_path": local_path, "filename": file.filename})

@api_bp.route("/servers/<server_id>/installers/<installer_name>/install", methods=["POST"])
async def launch_installation(server_id, installer_name):
    """Lance une tâche d'installation en arrière-plan avec support des paramètres optionnels."""
    installers_map = get_installers_map()
    installer = installers_map.get(installer_name)

    if not installer:
        return jsonify({"success": False, "message": f"Installateur '{installer_name}' non reconnu."}), 404

    sm = get_server_manager()
    srv = sm.get_server(server_id)
    if not srv:
        return jsonify({"success": False, "message": "Serveur non trouvé."}), 404

    executor = sm.get_executor(server_id)
    tm = get_task_manager()

    options = {}
    if request.is_json:
        options = await request.get_json() or {}

    async def task_coro(task_progress):
        await installer.install(executor, task_progress, **options)

    task_prog = tm.create_task(
        name=f"Installation {installer.display_name} sur {srv['name']}",
        server_id=server_id,
        async_func=task_coro
    )

    return jsonify({"success": True, "task_id": task_prog.task_id, "message": "Installation lancée en arrière-plan."})

@api_bp.route("/tasks/<task_id>", methods=["GET"])
async def get_task_status(task_id):
    """Statut et progression d'une tâche d'arrière-plan."""
    tm = get_task_manager()
    task = tm.get_task(task_id)
    if not task:
        return jsonify({"success": False, "message": "Tâche non trouvée."}), 404
    return jsonify({"success": True, "task": task})

@api_bp.route("/tasks", methods=["GET"])
async def list_tasks():
    """Liste de toutes les tâches d'arrière-plan."""
    tm = get_task_manager()
    return jsonify({"success": True, "tasks": tm.get_all_tasks()})


# =========================================================================
# 5. CREDENTIALS & SETTINGS ENDPOINTS
# =========================================================================

@api_bp.route("/credentials/ssh-keys", methods=["GET"])
async def list_ssh_keys():
    """Liste les clés SSH privées détectées dans ~/.ssh/."""
    cm = get_credential_manager()
    return jsonify({"success": True, "keys": cm.discover_ssh_keys()})

@api_bp.route("/logs", methods=["GET"])
async def get_logs():
    lines_param = request.args.get("lines", default=200, type=int)
    log_manager = get_log_manager()
    logs = log_manager.get_recent_logs(lines=lines_param)
    info = log_manager.get_log_info()
    return jsonify({"success": True, "logs": logs, "info": info})

@api_bp.route("/logs", methods=["DELETE"])
async def clear_logs():
    log_manager = get_log_manager()
    success = log_manager.clear_logs()
    return jsonify({"success": success, "message": "Fichier de log effacé." if success else "Impossible d'effacer les logs."})

@api_bp.route("/settings", methods=["GET"])
async def get_settings_endpoint():
    settings = get_settings()
    return jsonify({"success": True, "settings": settings.get_all()})

@api_bp.route("/settings", methods=["POST"])
async def update_settings_endpoint():
    data = await request.get_json()
    if not data or not isinstance(data, dict):
        return jsonify({"success": False, "message": "Données invalides."}), 400
    settings = get_settings()
    success = settings.update(data)
    return jsonify({"success": success, "message": "Paramètres enregistrés avec succès." if success else "Erreur de sauvegarde."})


# =========================================================================
# 6. HEALTH CHECK
# =========================================================================

@api_bp.route("/status", methods=["GET"])
async def health_check():
    """Point de vérification de santé (ping) utilisé par le GUI Tkinter Launcher."""
    return jsonify({"success": True, "status": "running", "app": "MELODI Control Center"})
