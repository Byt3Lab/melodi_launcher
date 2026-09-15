"""
SystemInfo: Collecting system health metrics (CPU, RAM, Disk, Uptime) locally and remotely.
"""

import psutil
import time
from typing import Dict, Any
from app.remote.executor import Executor
from app.remote.local_executor import LocalExecutor

class SystemInfo:
    @staticmethod
    async def get_metrics(executor: Executor) -> Dict[str, Any]:
        """Récupère les métriques système (CPU, RAM, Disque, Uptime)."""
        if isinstance(executor, LocalExecutor):
            return SystemInfo._get_local_metrics()
        return await SystemInfo._get_remote_metrics(executor)

    @staticmethod
    def _get_local_metrics() -> Dict[str, Any]:
        cpu_pct = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        boot_time = psutil.boot_time()
        uptime_sec = time.time() - boot_time

        hours, remainder = divmod(int(uptime_sec), 3600)
        days, hours = divmod(hours, 24)
        minutes, _ = divmod(remainder, 60)

        uptime_str = f"{days}d {hours}h {minutes}m" if days > 0 else f"{hours}h {minutes}m"

        return {
            "cpu_percent": round(cpu_pct, 1),
            "ram_used_gb": round((mem.total - mem.available) / (1024**3), 2),
            "ram_total_gb": round(mem.total / (1024**3), 2),
            "ram_percent": round(mem.percent, 1),
            "disk_used_gb": round(disk.used / (1024**3), 2),
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "disk_percent": round(disk.percent, 1),
            "uptime_seconds": round(uptime_sec, 0),
            "uptime_formatted": uptime_str,
            "status": "online"
        }

    @staticmethod
    async def _get_remote_metrics(executor: Executor) -> Dict[str, Any]:
        # Exécuter un script léger en une seule commande SSH
        cmd = (
            "echo CPU: $(top -bn1 | grep 'Cpu(s)' | awk '{print $2 + $4}') && "
            "echo MEM: $(free -m | awk 'NR==2{printf \"%.1f %.1f %.1f\", $3/1024, $2/1024, $3*100/$2}') && "
            "echo DISK: $(df -h / | awk 'NR==2{printf \"%s %s %s\", $3, $2, $5}') && "
            "echo UPTIME: $(uptime -p || uptime)"
        )
        code, stdout, _ = await executor.run(cmd, timeout=5.0)
        if code != 0:
            return {
                "cpu_percent": 0.0,
                "ram_used_gb": 0.0,
                "ram_total_gb": 0.0,
                "ram_percent": 0.0,
                "disk_used_gb": "0",
                "disk_total_gb": "0",
                "disk_percent": 0.0,
                "uptime_formatted": "Indisponible",
                "status": "offline"
            }

        lines = stdout.splitlines()
        metrics = {
            "cpu_percent": 0.0,
            "ram_used_gb": 0.0,
            "ram_total_gb": 0.0,
            "ram_percent": 0.0,
            "disk_used_gb": "0",
            "disk_total_gb": "0",
            "disk_percent": 0.0,
            "uptime_formatted": "Actif",
            "status": "online"
        }

        for line in lines:
            if line.startswith("CPU:"):
                try: metrics["cpu_percent"] = float(line.split(":")[1].strip())
                except Exception: pass
            elif line.startswith("MEM:"):
                try:
                    parts = line.split(":")[1].strip().split()
                    metrics["ram_used_gb"] = float(parts[0])
                    metrics["ram_total_gb"] = float(parts[1])
                    metrics["ram_percent"] = float(parts[2])
                except Exception: pass
            elif line.startswith("DISK:"):
                try:
                    parts = line.split(":")[1].strip().split()
                    metrics["disk_used_gb"] = parts[0]
                    metrics["disk_total_gb"] = parts[1]
                    metrics["disk_percent"] = float(parts[2].replace("%", ""))
                except Exception: pass
            elif line.startswith("UPTIME:"):
                metrics["uptime_formatted"] = line.split(":", 1)[1].strip()

        return metrics
