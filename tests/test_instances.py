"""
Tests du support multi-instances MELODI ERP (ports distincts, isolation Linux/Windows et UI dynamique).
"""

import os
import pytest
from app.core.instance_manager import InstanceManager, slugify_service_name, slugify_pg_service_name, win_task_name_for_service
from app.core.server_manager import ServerManager
from app.core.task_manager import TaskProgress
from app.installers.melodi import MelodiInstaller
from app.installers.postgresql import PostgreSQLInstaller
from app.remote.executor import Executor
from app.system.systemd_manager import SystemdManager
from app.ui.app_context import AppContext
from app.ui.main_window import MainWindow


class DummyLinuxExecutor(Executor):
    def __init__(self):
        super().__init__(name="SSH (root@srv:22)")
        self._os_family = "linux"
        self.commands: list[str] = []

    async def connect(self) -> bool:
        return True

    async def disconnect(self) -> None:
        pass

    async def is_connected(self) -> bool:
        return True

    async def run(self, command: str, timeout=None, on_output=None):
        self.commands.append(command)
        if command == "whoami":
            return (0, "root", "")
        return (0, "ok", "")

    async def test_connection(self):
        return {"success": True}

    async def upload_file(self, local_path: str, remote_path: str):
        return (True, "")

    async def download_file(self, url: str, destination_path: str, on_output=None):
        return (True, "")


def test_slugify_and_windows_task_names():
    assert slugify_service_name("MELODI ERP") == "melodi"
    assert slugify_service_name("MELODI Filiale B") == "melodi-filiale-b"
    assert slugify_service_name("Boutique Été 2") == "melodi-boutique-ete-2"

    assert win_task_name_for_service("melodi") == "MELODI_ERP"
    assert win_task_name_for_service("melodi-filiale-b") == "MELODI_ERP_FILIALE_B"


def test_instance_manager_crud_and_ports(tmp_path):
    im = InstanceManager(os.path.join(tmp_path, "instances.json"))
    assert im.suggest_next_port("local") == 5000

    r1 = im.add_or_update_instance("local", "MELODI ERP", 5000, "/opt/melodi")
    assert r1["success"] is True
    assert im.suggest_next_port("local") == 5001

    # Conflit de port sur le même serveur
    conflict = im.add_or_update_instance("local", "MELODI Filiale B", 5000, "/opt/melodi-filiale-b")
    assert conflict["success"] is False

    # Port différent accepté
    r2 = im.add_or_update_instance("local", "MELODI Filiale B", 5001, "/opt/melodi-filiale-b")
    assert r2["success"] is True
    assert im.suggest_next_port("local") == 5002

    insts = im.get_instances("local")
    assert len(insts) == 2
    assert [i["port"] for i in insts] == [5000, 5001]

    # Suppression
    im.delete_instance(r2["instance"]["id"])
    assert len(im.get_instances("local")) == 1


@pytest.mark.asyncio
async def test_melodi_installer_distinct_systemd_services():
    ex = DummyLinuxExecutor()
    installer = MelodiInstaller()
    task = TaskProgress("t2", "Install instance 2", ex.name)

    await installer.install(
        ex,
        task,
        destination_dir="/opt/melodi-filiale-b",
        service_name="melodi-filiale-b",
        port=5001,
        setup_venv=True,
        setup_service=True,
    )

    assert not task.is_failed()
    joined = "\n".join(ex.commands)
    assert "/etc/systemd/system/melodi-filiale-b.service" in joined
    assert 'PORT=5001' in joined
    assert "systemctl enable --now melodi-filiale-b" in joined


def test_ui_multi_instances_and_port_validation(qtbot, tmp_path):
    sm = ServerManager(os.path.join(tmp_path, "servers.json"))
    im = InstanceManager(os.path.join(tmp_path, "instances.json"))
    im.add_or_update_instance("local", "MELODI Principal", 5000, "/opt/melodi", service_name="melodi")
    im.add_or_update_instance("local", "MELODI Boutique 2", 5001, "/opt/melodi-boutique-2", service_name="melodi-boutique-2")

    ctx = AppContext(server_manager=sm, instance_manager=im)
    win = MainWindow(ctx=ctx)
    qtbot.addWidget(win)

    # Dashboard & Services affichent les 2 instances + postgresql
    assert "melodi" in win.pages["dashboard"]._service_rows
    assert "melodi-boutique-2" in win.pages["dashboard"]._service_rows
    assert "postgresql" in win.pages["dashboard"]._service_rows

    assert "melodi" in win.pages["services"]._cards
    assert "melodi-boutique-2" in win.pages["services"]._cards
    assert "postgresql" in win.pages["services"]._cards

    # Logs combo contient live + 2 instances + postgresql = 4 entrées
    assert win.pages["logs"].source_combo.count() == 4

    # Wizard : port suggéré automatiquement = 5002, et 5000 bloqué en conflit
    wiz = win.pages["install"]
    assert wiz.port_spin.value() == 5002
    wiz._step = 1
    wiz._update_step_ui()
    src = tmp_path / "src_app"
    src.mkdir()
    wiz.source_edit.setText(str(src))
    wiz.instance_name_edit.setText("MELODI Boutique 3")

    wiz.port_spin.setValue(5000)
    assert wiz.next_btn.isEnabled() is False

    wiz.port_spin.setValue(5002)
    assert wiz.next_btn.isEnabled() is True


@pytest.mark.asyncio
async def test_linux_systemd_delete_service():
    ex = DummyLinuxExecutor()
    res = await SystemdManager.delete(ex, "melodi-filiale-b")
    assert res["success"] is True
    joined = "\n".join(ex.commands)
    assert "systemctl stop melodi-filiale-b" in joined
    assert "systemctl disable melodi-filiale-b" in joined
    assert "rm -f /etc/systemd/system/melodi-filiale-b.service" in joined
    assert "systemctl daemon-reload" in joined


@pytest.mark.asyncio
async def test_multi_postgresql_and_linked_melodi_service(tmp_path):
    im = InstanceManager(os.path.join(tmp_path, "instances.json"))
    assert im.suggest_next_port("local", 5432, kind="postgresql") == 5432
    im.add_or_update_instance("local", "PostgreSQL 5432", 5432, "/var/lib/postgresql", kind="postgresql")
    assert im.suggest_next_port("local", 5432, kind="postgresql") == 5433
    assert slugify_pg_service_name(5433) == "postgresql-5433"

    ex = DummyLinuxExecutor()
    task = TaskProgress("pg2", "Install PG 5433", ex.name)
    await PostgreSQLInstaller().install(ex, task, port=5433, service_name="postgresql-5433", data_dir="/var/lib/postgresql/melodi-5433")
    assert not task.is_failed()
    joined = "\n".join(ex.commands)
    assert "/etc/systemd/system/postgresql-5433.service" in joined
    assert "systemctl enable --now postgresql-5433" in joined

    ex2 = DummyLinuxExecutor()
    ok, _ = await MelodiInstaller.create_service(
        ex2,
        service_name="melodi-filiale-b",
        app_dir="/opt/melodi-filiale-b",
        port=5001,
        pg_service_name="postgresql-5433",
        pg_port=5433,
    )
    assert ok is True
    joined2 = "\n".join(ex2.commands)
    assert "PGPORT=5433" in joined2
    assert "PYTHONUNBUFFERED=1" in joined2
    assert "PYTHONDONTWRITEBYTECODE=1" in joined2
    assert (
        "-m scripts.start --plateform linux --env prod --port 5001 "
        "--service_name melodi-filiale-b --host 0.0.0.0"
    ) in joined2


@pytest.mark.asyncio
async def test_service_lifecycle_separate_from_source_installation(tmp_path):
    im = InstanceManager(os.path.join(tmp_path, "instances.json"))
    res = im.add_or_update_instance("local", "MELODI ERP", 5000, "/opt/melodi", service_name="melodi")
    assert res["success"] is True

    ex = DummyLinuxExecutor()
    # 1. Création du service à partir de la source (auto-détection venv)
    ok, _ = await MelodiInstaller.create_service(ex, "melodi", "/opt/melodi", port=5000)
    assert ok is True
    assert any("test -x /opt/melodi/venv/bin/python3" in c for c in ex.commands)
    assert any("systemctl enable --now melodi" in c for c in ex.commands)

    # 2. Suppression du service systemctl : l'installation source reste dans InstanceManager
    del_res = await SystemdManager.delete(ex, "melodi")
    assert del_res["success"] is True
    assert len(im.get_instances("local", kind="melodi")) == 1


@pytest.mark.asyncio
async def test_check_availability_and_create_service_dialog(qtbot, tmp_path):
    class BusyExecutor(DummyLinuxExecutor):
        async def run(self, command: str, timeout=None, on_output=None):
            if "systemctl list-unit-files melodi.service" in command:
                return (0, "melodi.service enabled", "")
            if "sport = :5000" in command:
                return (0, "used", "")
            if "sport = :5002" in command:
                return (0, "free", "")
            return await super().run(command, timeout=timeout, on_output=on_output)

    ex = BusyExecutor()
    taken = await SystemdManager.check_availability(ex, "melodi", 5000)
    assert taken["service_available"] is False
    assert taken["port_available"] is False
    assert taken["available"] is False

    free = await SystemdManager.check_availability(ex, "melodi-5002", 5002)
    assert free["service_available"] is True
    assert free["port_available"] is True
    assert free["available"] is True

    from app.ui.pages.services import CreateServiceDialog
    sm = ServerManager(os.path.join(tmp_path, "servers.json"))
    im = InstanceManager(os.path.join(tmp_path, "instances.json"))
    ctx = AppContext(server_manager=sm, instance_manager=im)
    meta = {
        "id": "melodi-5002",
        "name": "MELODI 5002",
        "port": 5002,
        "install_dir": "/opt/melodi-5002",
        "is_melodi": True,
        "is_default": False,
    }
    dlg = CreateServiceDialog(ctx, meta)
    qtbot.addWidget(dlg)
    assert dlg.svc_edit.text() == "melodi-5002"
    assert dlg.port_spin.value() == 5002

    # Tester le clic sur 'Tester la disponibilité' via une boucle qasync active
    import asyncio
    from PySide6.QtWidgets import QApplication
    from qasync import QEventLoop

    ctx.server_manager._executors["local"] = BusyExecutor()
    loop = QEventLoop(QApplication.instance())
    asyncio.set_event_loop(loop)

    async def _drive_dialog():
        await dlg._run_availability_check()
        assert "disponible" in dlg.status_pill.text().lower() or "available" in dlg.status_pill.text().lower()

    loop.run_until_complete(_drive_dialog())


def test_pack_source_zip_excludes_heavy_dirs(tmp_path):
    import zipfile
    from app.installers.melodi import _pack_source_zip_sync

    src = tmp_path / "melodi_src"
    (src / "venv" / "lib").mkdir(parents=True)
    (src / "venv" / "lib" / "huge.py").write_text("x" * 1000, encoding="utf-8")
    (src / ".git").mkdir()
    (src / ".git" / "config").write_text("git", encoding="utf-8")
    (src / "node_modules").mkdir()
    (src / "node_modules" / "pkg.js").write_text("js", encoding="utf-8")
    (src / "__pycache__").mkdir()
    (src / "__pycache__" / "main.cpython-312.pyc").write_bytes(b"pyc")
    (src / "main.py").write_text("print('melodi')", encoding="utf-8")
    (src / "requirements.txt").write_text("flask\n", encoding="utf-8")

    out_zip = tmp_path / "out.zip"
    size = _pack_source_zip_sync(str(src), str(out_zip))
    assert size > 0

    with zipfile.ZipFile(out_zip, "r") as zf:
        names = set(zf.namelist())

    assert "main.py" in names
    assert "requirements.txt" in names
    assert not any(n.startswith(("venv/", ".git/", "node_modules/", "__pycache__/")) for n in names)
