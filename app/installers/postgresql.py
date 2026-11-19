"""
PostgreSQLInstaller: Automated installer for PostgreSQL.
"""

from app.i18n import t
from app.installers.base import BaseInstaller
from app.remote.executor import Executor
from app.core.task_manager import TaskProgress
from app.system.package_manager import PackageManager
from app.system.systemd_manager import SystemdManager


class PostgreSQLInstaller(BaseInstaller):
    def __init__(self):
        super().__init__(name="postgresql", display_name="PostgreSQL Database")

    async def install(self, executor: Executor, task: TaskProgress, **kwargs):
        await self._install_native(executor, task)

    async def _install_native(self, executor: Executor, task: TaskProgress):
        task.update(10, t("installer.pg.checking"))
        if await PackageManager.is_installed(executor, "postgresql"):
            task.complete(t("installer.pg.already"))
            return

        task.update(30, t("installer.pg.installing"))
        res = await PackageManager.install(executor, "postgresql postgresql-contrib", on_output=task.append_log)
        if not res["success"]:
            task.fail(t("installer.pg.apt_failed", error=res.get("stderr", "")))
            return

        task.update(75, t("installer.pg.starting"))
        start_res = await SystemdManager.start(executor, "postgresql", on_output=task.append_log)
        if not start_res["success"]:
            task.fail(start_res["message"])
            return

        task.complete(t("installer.pg.done"))
