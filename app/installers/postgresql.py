"""
PostgreSQLInstaller: Automated installer for PostgreSQL.
Supports standard system PostgreSQL (port 5432) and isolated multi-port PostgreSQL instances.
"""

import shlex
from app.core.instance_manager import slugify_pg_service_name
from app.i18n import t
from app.installers.base import BaseInstaller
from app.remote.executor import Executor
from app.core.task_manager import TaskProgress
from app.system.package_manager import PackageManager
from app.system.systemd_manager import SystemdManager

PG_SYSTEMD_UNIT_TEMPLATE = """[Unit]
Description=PostgreSQL Isolated Instance ({service_name} on port {port})
After=network.target

[Service]
Type=simple
User=postgres
Group=postgres
ExecStart={pg_bin}/postgres -D {data_dir} -p {port}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""


class PostgreSQLInstaller(BaseInstaller):
    def __init__(self):
        super().__init__(name="postgresql", display_name="PostgreSQL Database")

    async def install(self, executor: Executor, task: TaskProgress, **kwargs):
        port = int(kwargs.get("port") or 5432)
        service_name = kwargs.get("service_name") or slugify_pg_service_name(port)
        data_dir = kwargs.get("data_dir")
        if await executor.is_windows():
            await self._install_windows(executor, task, port=port, service_name=service_name, data_dir=data_dir)
        else:
            await self._install_native(executor, task, port=port, service_name=service_name, data_dir=data_dir)

    async def _install_native(self, executor: Executor, task: TaskProgress, port: int = 5432, service_name: str = "postgresql", data_dir: str | None = None):
        task.update(10, t("installer.pg.checking"))
        if not await PackageManager.is_installed(executor, "postgresql"):
            task.update(20, t("installer.pg.installing"))
            res = await PackageManager.install(executor, "postgresql postgresql-contrib", on_output=task.append_log)
            if not res["success"]:
                task.fail(t("installer.pg.apt_failed", error=res.get("stderr", "")))
                return

        if port == 5432 and service_name == "postgresql":
            task.update(35, t("installer.pg.starting"))
            start_res = await SystemdManager.start(executor, "postgresql", on_output=task.append_log)
            if not start_res["success"]:
                task.fail(start_res["message"])
                return
            task.complete(t("installer.pg.done"))
            return

        # Instance PostgreSQL isolée sur un port dédié
        target_data = data_dir or f"/var/lib/postgresql/melodi-{port}"
        code_bin, out_bin, _ = await executor.run("dirname $(ls /usr/lib/postgresql/*/bin/postgres 2>/dev/null | sort -V | tail -n 1)")
        pg_bin = out_bin.strip() if code_bin == 0 and out_bin.strip() else "/usr/bin"

        task.update(25, f"Initialisation du cluster PostgreSQL ({target_data}, port {port})...")
        init_cmd = (
            f"mkdir -p {shlex.quote(target_data)} && "
            f"chown -R postgres:postgres {shlex.quote(target_data)} && "
            f"(test -f {shlex.quote(target_data)}/PG_VERSION || "
            f"su - postgres -c '{pg_bin}/initdb -D {target_data}') && "
            f"grep -q '^port =' {shlex.quote(target_data)}/postgresql.conf "
            f"&& sed -i 's/^port =.*/port = {port}/' {shlex.quote(target_data)}/postgresql.conf "
            f"|| echo 'port = {port}' >> {shlex.quote(target_data)}/postgresql.conf"
        )
        code, _, stderr = await executor.run_sudo(init_cmd, on_output=task.append_log)
        if code != 0:
            task.fail(f"Échec initialisation PostgreSQL ({port}) : {stderr.strip()}")
            return

        task.update(35, t("installer.pg.starting"))
        unit_content = PG_SYSTEMD_UNIT_TEMPLATE.format(
            service_name=service_name,
            port=port,
            pg_bin=pg_bin,
            data_dir=target_data,
        )
        escaped_unit = unit_content.replace('"', '\\"')
        unit_cmd = (
            f'echo "{escaped_unit}" | tee /etc/systemd/system/{shlex.quote(service_name)}.service > /dev/null && '
            f"systemctl daemon-reload && systemctl enable --now {shlex.quote(service_name)}"
        )
        code, _, stderr = await executor.run_sudo(unit_cmd, on_output=task.append_log)
        if code != 0:
            task.fail(t("systemd.start_failed", name=service_name, error=stderr.strip()))
            return

        task.complete(t("installer.pg.done"))

    async def _install_windows(self, executor: Executor, task: TaskProgress, port: int = 5432, service_name: str = "postgresql", data_dir: str | None = None):
        task.update(10, t("installer.pg.checking"))
        if not await PackageManager.is_installed(executor, "postgresql"):
            task.update(20, t("installer.pg.installing"))
            res = await PackageManager.install(executor, "postgresql postgresql-contrib", on_output=task.append_log)
            if not res["success"]:
                task.fail(t("installer.pg.apt_failed", error=res.get("stderr", "")))
                return

        if port == 5432 and service_name == "postgresql":
            task.update(35, t("installer.pg.starting"))
            start_res = await SystemdManager.start(executor, "postgresql", on_output=task.append_log)
            if not start_res["success"]:
                task.fail(start_res["message"])
                return
            task.complete(t("installer.pg.done"))
            return

        target_data = data_dir or f"C:\\postgresql-{port}\\data"
        ps_cmd = (
            f'powershell -NoProfile -Command "'
            f"$bin = (Get-ChildItem 'C:\\Program Files\\PostgreSQL\\*\\bin\\pg_ctl.exe' | Select-Object -Last 1).DirectoryName; "
            f"if (-not (Test-Path '{target_data}\\PG_VERSION')) {{ "
            f"New-Item -ItemType Directory -Force -Path '{target_data}' | Out-Null; "
            f"& \\\"$bin\\initdb.exe\\\" -D '{target_data}' -U postgres }}; "
            f"Add-Content -Path '{target_data}\\postgresql.conf' -Value 'port = {port}'; "
            f"& \\\"$bin\\pg_ctl.exe\\\" register -N '{service_name}' -D '{target_data}'; "
            f"Start-Service -Name '{service_name}'\""
        )
        code, _, stderr = await executor.run(ps_cmd, on_output=task.append_log)
        if code != 0:
            task.fail(t("systemd.start_failed", name=service_name, error=stderr.strip()))
            return
        task.complete(t("installer.pg.done"))
