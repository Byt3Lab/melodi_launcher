"""
Tests unitaires de la détection automatique Windows et des commandes Windows
(PackageManager, SystemdManager, MelodiInstaller, Executor.run_sudo).
"""

import pytest
from app.core.task_manager import TaskProgress
from app.installers.melodi import MelodiInstaller
from app.remote.executor import Executor
from app.system.package_manager import PackageManager
from app.system.systemd_manager import SystemdManager


class FakeWindowsExecutor(Executor):
    def __init__(self):
        super().__init__(name="SSH (admin@win-srv:22)")
        self.commands: list[str] = []

    async def connect(self) -> bool:
        return True

    async def disconnect(self) -> None:
        pass

    async def is_connected(self) -> bool:
        return True

    async def run(self, command: str, timeout=None, on_output=None):
        self.commands.append(command)
        if command == "uname -s":
            return (1, "", "'uname' is not recognized")
        if command == "ver":
            return (0, "Microsoft Windows [Version 10.0.22621]", "")
        if "Get-Service" in command and "'active'" in command:
            return (0, "active", "")
        if "Test-Path" in command and "requirements.txt" in command:
            return (0, "True", "")
        if "Test-Path" in command and "\\melodi" in command:
            return (0, "False", "")
        return (0, "OK", "")

    async def test_connection(self):
        return {"success": True}

    async def upload_file(self, local_path: str, remote_path: str):
        self.commands.append(f"UPLOAD {local_path} -> {remote_path}")
        return (True, "")

    async def download_file(self, url: str, destination_path: str, on_output=None):
        self.commands.append(f"DOWNLOAD {url} -> {destination_path}")
        return (True, "")


@pytest.mark.asyncio
async def test_windows_auto_detection_and_run_sudo():
    ex = FakeWindowsExecutor()
    assert await ex.detect_os() == "windows"
    assert await ex.is_windows() is True

    code, out, _ = await ex.run_sudo("echo hello")
    assert code == 0
    assert "echo hello" in ex.commands
    assert not any("sudo" in c for c in ex.commands)


@pytest.mark.asyncio
async def test_windows_package_manager_uses_winget():
    ex = FakeWindowsExecutor()
    res = await PackageManager.install(ex, "postgresql postgresql-contrib")
    assert res["success"] is True
    assert any("winget install --id PostgreSQL.PostgreSQL" in c for c in ex.commands)


@pytest.mark.asyncio
async def test_windows_service_manager_uses_powershell():
    ex = FakeWindowsExecutor()
    assert await SystemdManager.is_active(ex, "melodi") is True
    assert await SystemdManager.is_active(ex, "postgresql") is True

    start_res = await SystemdManager.start(ex, "melodi")
    assert start_res["success"] is True
    assert any("Start-ScheduledTask" in c for c in ex.commands)

    stop_res = await SystemdManager.stop(ex, "postgresql")
    assert stop_res["success"] is True
    assert any("Stop-Service" in c for c in ex.commands)


@pytest.mark.asyncio
async def test_windows_melodi_installer_flow():
    ex = FakeWindowsExecutor()
    task = TaskProgress("win1", "Install MELODI Windows", ex.name)
    installer = MelodiInstaller()

    await installer.install(
        ex,
        task,
        url="https://example.com/melodi.zip",
        source_type="url",
        destination_dir="C:\\melodi",
        setup_venv=True,
        setup_service=True,
    )

    assert not task.is_failed()
    assert any("DOWNLOAD https://example.com/melodi.zip" in c for c in ex.commands)
    assert any("Expand-Archive" in c for c in ex.commands)
    assert any('python -m venv "C:\\melodi\\venv"' in c for c in ex.commands)
    assert any("venv\\Scripts\\pip.exe" in c for c in ex.commands)
    assert any('schtasks /Create /TN "MELODI_ERP"' in c for c in ex.commands)
