"""
Tests for Quart API Endpoints in MELODI Control Center
"""

import os
import pytest
from app.application import create_app

@pytest.fixture
def app_instance(tmp_path):
    config_file = os.path.join(tmp_path, "config.json")
    app = create_app(config_file)
    app.config["TESTING"] = True
    return app

@pytest.mark.asyncio
async def test_api_servers_list_and_add(app_instance):
    client = app_instance.test_client()

    res = await client.get("/api/servers")
    assert res.status_code == 200
    data = await res.get_json()
    assert data["success"] is True
    assert len(data["servers"]) >= 1

    add_res = await client.post("/api/servers", json={
        "name": "Staging Server",
        "host": "10.0.0.5",
        "port": 22,
        "username": "ubuntu"
    })
    assert add_res.status_code == 200
    add_data = await add_res.get_json()
    assert add_data["success"] is True
    assert add_data["server"]["name"] == "Staging Server"

@pytest.mark.asyncio
async def test_api_system_metrics_local(app_instance):
    client = app_instance.test_client()

    res = await client.get("/api/servers/local/system")
    assert res.status_code == 200
    data = await res.get_json()
    assert data["success"] is True
    assert "cpu_percent" in data["metrics"]
    assert "ram_percent" in data["metrics"]

@pytest.mark.asyncio
async def test_api_services_list_local(app_instance):
    client = app_instance.test_client()

    res = await client.get("/api/servers/local/services")
    assert res.status_code == 200
    data = await res.get_json()
    assert data["success"] is True
    assert len(data["services"]) >= 6

@pytest.mark.asyncio
async def test_installation_web_pages(app_instance):
    client = app_instance.test_client()

    # Page d'installation globale
    res = await client.get("/installation")
    assert res.status_code == 200

    # Pages d'installation dédiées pour chaque service
    for service_name in ["melodi", "melodi_websocket", "melodi_process_manager", "postgresql", "redis", "pgadmin"]:
        svc_res = await client.get(f"/installation/{service_name}")
        assert svc_res.status_code == 200


@pytest.mark.asyncio
async def test_pwa_shell_partials_and_service_worker(app_instance):
    client = app_instance.test_client()

    partial = await client.get("/settings?partial=1")
    partial_html = await partial.get_data(as_text=True)
    assert partial.status_code == 200
    assert '<html' not in partial_html
    assert 'data-melodi-component="settingsComponent"' in partial_html

    service_partial = await client.get("/installation/redis?partial=1")
    service_html = await service_partial.get_data(as_text=True)
    assert service_partial.status_code == 200
    assert 'data-service-name="redis"' in service_html

    worker = await client.get("/service-worker.js")
    assert worker.status_code == 200
    assert worker.headers["Service-Worker-Allowed"] == "/"
    assert "addAll(APP_SHELL)" in await worker.get_data(as_text=True)

    manifest = await client.get("/static/manifest.webmanifest")
    assert manifest.status_code == 200
    assert (await manifest.get_json())["display"] == "standalone"

@pytest.mark.asyncio
async def test_installer_api_info_endpoint(app_instance):
    client = app_instance.test_client()

    for installer_name in ["melodi", "melodi_websocket", "melodi_process_manager", "postgresql", "redis", "pgadmin"]:
        res = await client.get(f"/api/servers/local/installers/{installer_name}")
        assert res.status_code == 200
        data = await res.get_json()
        assert data["success"] is True
        assert data["name"] == installer_name
        assert "service" in data

@pytest.mark.asyncio
async def test_task_cancel_endpoint(app_instance):
    import asyncio

    client = app_instance.test_client()
    tm = app_instance.config["TASK_MANAGER"]

    async def dummy_slow_task(task):
        task.update(10, "En cours...")
        await asyncio.sleep(5.0)

    task_prog = tm.create_task("Tâche Test API", "local", dummy_slow_task)
    task_id = task_prog.task_id

    # 1. Vérifier statut via GET /api/tasks/<task_id>
    res = await client.get(f"/api/tasks/{task_id}")
    assert res.status_code == 200
    data = await res.get_json()
    assert data["success"] is True
    assert data["task"]["status"] in ("PENDING", "RUNNING")

    # 2. Interrompre la tâche via POST /api/tasks/<task_id>/cancel
    cancel_res = await client.post(f"/api/tasks/{task_id}/cancel")
    assert cancel_res.status_code == 200
    cancel_data = await cancel_res.get_json()
    assert cancel_data["success"] is True

    # 3. Vérifier que le statut est devenu CANCELLED
    res_after = await client.get(f"/api/tasks/{task_id}")
    data_after = await res_after.get_json()
    assert data_after["task"]["status"] == "CANCELLED"

@pytest.mark.asyncio
async def test_upload_file_endpoint(app_instance, tmp_path):
    import io
    from quart.datastructures import FileStorage
    client = app_instance.test_client()

    fake_file = io.BytesIO(b"dummy zip content")
    fs = FileStorage(stream=fake_file, filename="melodi_test.zip", content_type="application/zip")

    res = await client.post("/api/servers/local/upload", files={"file": fs})
    assert res.status_code == 200
    res_data = await res.get_json()
    assert res_data["success"] is True
    assert "melodi_test.zip" in res_data["file_path"]
    assert os.path.exists(res_data["file_path"])
    # Nettoyage
    try:
        os.remove(res_data["file_path"])
    except Exception:
        pass

@pytest.mark.asyncio
async def test_melodi_deploy_archive_and_delete_zip(app_instance, tmp_path):
    import zipfile
    import asyncio

    # 1. Créer une archive ZIP factice
    zip_path = tmp_path / "melodi_release.zip"
    dest_dir = tmp_path / "opt_melodi"
    dest_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("main.py", "print('hello melodi')")
        zf.writestr("requirements.txt", "# requirements\nquart\n")

    assert zip_path.exists()

    # 2. Exécuter l'installateur Melodi via deploy_archive
    client = app_instance.test_client()
    installer = app_instance.config["INSTALLERS_MAP"]["melodi"]
    executor = app_instance.config["SERVER_MANAGER"].get_executor("local")
    tm = app_instance.config["TASK_MANAGER"]

    task_prog = tm.create_task(
        name="Test Deploy Melodi",
        server_id="local",
        async_func=lambda tp: installer.deploy_archive(
            executor,
            tp,
            zip_path=str(zip_path),
            destination_dir=str(dest_dir),
            delete_zip=True,
            deploy_only=True
        )
    )

    # Attendre la fin de la tâche
    for _ in range(50):
        if task_prog.status in ("SUCCESS", "FAILED"):
            break
        await asyncio.sleep(0.1)

    assert task_prog.status == "SUCCESS"
    # Vérifier que les fichiers sont décompressés dans dest_dir
    assert (dest_dir / "main.py").exists()
    assert (dest_dir / "requirements.txt").exists()
    # Vérifier que le fichier zip a été supprimé
    assert not zip_path.exists()

@pytest.mark.asyncio
async def test_api_melodi_deploy_endpoint(app_instance, tmp_path):
    import zipfile
    import asyncio

    zip_path = tmp_path / "api_test.zip"
    dest_dir = tmp_path / "api_extracted"
    dest_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("app_version.txt", "1.0.0")

    client = app_instance.test_client()
    tm = app_instance.config["TASK_MANAGER"]

    res = await client.post("/api/servers/local/melodi/deploy", json={
        "zip_path": str(zip_path),
        "destination_dir": str(dest_dir),
        "delete_zip": True
    })

    assert res.status_code == 200
    data = await res.get_json()
    assert data["success"] is True
    assert "task_id" in data

    task_id = data["task_id"]
    for _ in range(50):
        task_info = tm.get_task(task_id)
        if task_info and task_info["status"] in ("SUCCESS", "FAILED"):
            break
        await asyncio.sleep(0.1)

    task_final = tm.get_task(task_id)
    assert task_final["status"] == "SUCCESS"
    assert (dest_dir / "app_version.txt").exists()
    assert not zip_path.exists()

@pytest.mark.asyncio
async def test_api_melodi_deploy_via_url(app_instance, tmp_path):
    import zipfile
    import asyncio

    # Créer un zip source qui sera téléchargé via URL file://
    source_zip = tmp_path / "remote_release.zip"
    dest_dir = tmp_path / "url_extracted"
    dest_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(source_zip, "w") as zf:
        zf.writestr("melodi_online.py", "# online version")

    client = app_instance.test_client()
    tm = app_instance.config["TASK_MANAGER"]

    res = await client.post("/api/servers/local/melodi/deploy", json={
        "url": f"file://{source_zip.absolute()}",
        "destination_dir": str(dest_dir),
        "delete_zip": True
    })

    assert res.status_code == 200
    data = await res.get_json()
    assert data["success"] is True
    assert "task_id" in data

    task_id = data["task_id"]
    for _ in range(50):
        task_info = tm.get_task(task_id)
        if task_info and task_info["status"] in ("SUCCESS", "FAILED"):
            break
        await asyncio.sleep(0.1)

    task_final = tm.get_task(task_id)
    assert task_final["status"] == "SUCCESS"
    assert (dest_dir / "melodi_online.py").exists()
    # Le fichier temporaire téléchargé doit avoir été supprimé
    assert not os.path.exists("/tmp/melodi_download.zip")



