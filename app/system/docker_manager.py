"""
DockerManager: Abstraction for managing Docker containers and images.
Executes via Executor (Local or Remote SSH) with run_sudo fallback.
"""

from typing import Dict, Any, List, Optional
from app.remote.executor import Executor

class DockerManager:
    @staticmethod
    async def is_installed(executor: Executor) -> bool:
        """Vérifie si la commande docker est présente."""
        code, stdout, _ = await executor.run("which docker")
        return code == 0 and len(stdout.strip()) > 0

    @staticmethod
    async def is_running(executor: Executor) -> bool:
        """Vérifie si le démon docker est actif."""
        code, _, _ = await executor.run_sudo("docker info")
        return code == 0

    @staticmethod
    async def container_status(executor: Executor, container_name: str) -> Dict[str, Any]:
        """Inspecte l'état d'un conteneur spécifique."""
        if not await DockerManager.is_installed(executor):
            return {"exists": False, "running": False, "status": "Docker non installé"}

        cmd = f"docker inspect -f '{{{{.State.Status}}}}|{{{{.State.Running}}}}' {container_name}"
        code, stdout, _ = await executor.run_sudo(cmd)
        if code != 0 or not stdout.strip():
            return {"exists": False, "running": False, "status": "Non déployé"}

        parts = stdout.strip().replace("'", "").split("|")
        status_text = parts[0] if len(parts) > 0 else "unknown"
        is_running = parts[1].lower() == "true" if len(parts) > 1 else False

        return {
            "exists": True,
            "running": is_running,
            "status": status_text
        }

    @staticmethod
    async def start_container(executor: Executor, container_name: str) -> Dict[str, Any]:
        """Démarre un conteneur arrêté."""
        code, stdout, stderr = await executor.run_sudo(f"docker start {container_name}")
        return {
            "success": code == 0,
            "message": f"Conteneur '{container_name}' démarré." if code == 0 else f"Erreur démarrage: {stderr.strip()}"
        }

    @staticmethod
    async def stop_container(executor: Executor, container_name: str) -> Dict[str, Any]:
        """Arrête un conteneur en cours d'exécution."""
        code, stdout, stderr = await executor.run_sudo(f"docker stop {container_name}")
        return {
            "success": code == 0,
            "message": f"Conteneur '{container_name}' arrêté." if code == 0 else f"Erreur arrêt: {stderr.strip()}"
        }

    @staticmethod
    async def restart_container(executor: Executor, container_name: str) -> Dict[str, Any]:
        """Redémarre un conteneur."""
        code, stdout, stderr = await executor.run_sudo(f"docker restart {container_name}")
        return {
            "success": code == 0,
            "message": f"Conteneur '{container_name}' redémarré." if code == 0 else f"Erreur redémarrage: {stderr.strip()}"
        }

    @staticmethod
    async def get_logs(executor: Executor, container_name: str, lines: int = 100) -> List[str]:
        """Extrait les logs récents d'un conteneur."""
        code, stdout, stderr = await executor.run_sudo(f"docker logs --tail {lines} {container_name}")
        output = stdout if stdout.strip() else stderr
        if code == 0:
            return output.splitlines()
        return [f"Impossible d'extraire les logs docker pour {container_name}: {stderr.strip()}"]

    @staticmethod
    async def run_container(
        executor: Executor,
        name: str,
        image: str,
        ports: Dict[str, str] = None,
        volumes: Dict[str, str] = None,
        env: Dict[str, str] = None,
        restart_policy: str = "always",
        cmd_args: str = ""
    ) -> Dict[str, Any]:
        """Supprime l'éventuel conteneur existant du même nom puis crée et démarre le conteneur."""
        await executor.run_sudo(f"docker rm -f {name}")

        args = [f"docker run -d --name {name} --restart {restart_policy}"]
        if ports:
            for host_p, cont_p in ports.items():
                args.append(f"-p {host_p}:{cont_p}")
        if volumes:
            for host_v, cont_v in volumes.items():
                args.append(f"-v {host_v}:{cont_v}")
        if env:
            for k, v in env.items():
                args.append(f"-e {k}='{v}'")

        args.append(image)
        if cmd_args:
            args.append(cmd_args)

        full_cmd = " ".join(args)
        code, stdout, stderr = await executor.run_sudo(full_cmd)
        return {
            "success": code == 0,
            "stdout": stdout.strip(),
            "stderr": stderr.strip(),
            "message": f"Conteneur '{name}' créé et démarré avec succès." if code == 0 else f"Échec de déploiement Docker: {stderr.strip()}"
        }
