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

