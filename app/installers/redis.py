"""
RedisInstaller: Automated installer for Redis In-Memory Data Store.
"""

from app.i18n import t
from app.installers.base import BaseInstaller
from app.remote.executor import Executor
from app.core.task_manager import TaskProgress
from app.system.package_manager import PackageManager
from app.system.systemd_manager import SystemdManager


class RedisInstaller(BaseInstaller):
    def __init__(self):
        super().__init__(name="redis", display_name="Redis In-Memory Data Store")

    async def install(self, executor: Executor, task: TaskProgress, **kwargs):
        await self._install_native(executor, task)

    async def _install_native(self, executor: Executor, task: TaskProgress):
        task.update(10, t("installer.redis.checking"))
        if await PackageManager.is_installed(executor, "redis-server"):
            task.complete(t("installer.redis.already"))
            return

        task.update(35, t("installer.redis.installing"))
        res = await PackageManager.install(executor, "redis-server", on_output=task.append_log)
        if not res["success"]:
            task.fail(t("installer.redis.apt_failed", error=res.get("stderr", "")))
            return

        task.update(75, t("installer.redis.starting"))
        start_res = await SystemdManager.start(executor, "redis-server", on_output=task.append_log)
        if not start_res["success"]:
            task.fail(start_res["message"])
            return

        task.complete(t("installer.redis.done"))
