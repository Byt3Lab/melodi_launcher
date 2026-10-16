"""
Tests for pgAdmin and ZIP deployment capabilities.
"""

import pytest
import os
import tempfile
import zipfile
from app.application import create_app
from app.remote.local_executor import LocalExecutor
from app.installers.melodi import MelodiInstaller
from app.installers.pgadmin import PgAdminInstaller

@pytest.fixture
def app():
    return create_app()

@pytest.mark.asyncio
async def test_services_and_installers_registered(app):
    services = app.config["SERVICES_MAP"]
    installers = app.config["INSTALLERS_MAP"]

    expected = ["melodi", "postgresql", "redis", "pgadmin"]
    for name in expected:
        assert name in services, f"Service {name} doit être enregistré"
        assert name in installers, f"Installer {name} doit être enregistré"

@pytest.mark.asyncio
async def test_upload_api_endpoint(app):
    test_client = app.test_client()

    # Créer un petit fichier zip fictif
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        tmp_path = tmp.name
        with zipfile.ZipFile(tmp_path, 'w') as zf:
            zf.writestr("main.py", "print('hello melodi')")

    with open(tmp_path, "rb") as f:
        file_bytes = f.read()

    os.remove(tmp_path)

    from quart.datastructures import FileStorage
    import io

    file_storage = FileStorage(
        stream=io.BytesIO(file_bytes),
        filename="melodi_source.zip",
        content_type="application/zip"
    )

    response = await test_client.post(
        "/api/servers/local/upload",
        files={"file": file_storage}
    )


    data = await response.get_json()
    assert response.status_code == 200
    assert data["success"] is True
    assert "file_path" in data
    assert os.path.exists(data["file_path"])
    # Nettoyage
    try:
        os.remove(data["file_path"])
    except OSError:
        pass
