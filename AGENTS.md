# Guide pour les Agents IA (AGENTS.md) - MELODI Control Center

Ce document fournit le contexte, l'architecture et les règles essentielles concernant **MELODI Control Center**. Il guide tout agent IA intervenant sur cette base de code.

---

## 📌 Contexte du Projet

**MELODI Control Center** est une **application web locale d'administration et d'orchestration pour MELODI ERP**.
Elle permet de gérer des machines locales et des serveurs distants via des connexions SSH sécurisées non-bloquantes (`asyncssh`).

L'application écoute par défaut sur `127.0.0.1:8080`.

---

## 🗂️ Structure et Architecture Cible

```text
melodi_control_center/
│
├── app/
│   ├── application.py          # Application Factory (create_app)
│   ├── config/                 # SettingsManager
│   ├── routes/                 # Routes HTML (web.py) et API REST (api.py)
│   ├── core/                   # ServerManager, TaskManager, ProcessManager
│   ├── remote/                 # Executor, LocalExecutor, SSHExecutor, CredentialManager
│   ├── system/                 # PackageManager, SystemdManager, SystemInfo
│   ├── installers/             # BaseInstaller, MelodiInstaller, PG, Redis, Nginx
│   └── services/               # BaseService, Melodi, PG, Redis, Nginx, Celery
│
├── templates/                  # Layout Jinja2, Dashboard, Serveurs, Services, Install, Monitoring
├── static/                     # CSS et images
├── tests/                      # Suite de tests automatisés pytest
├── config/                     # config.json et servers.json
├── run.py                      # Point d'entrée Hypercorn / Asyncio
├── build.sh                    # Script PyInstaller
├── requirements.txt
├── README.md
└── AGENTS.md
```

---

## 🚀 Principes & Règles d'Architecture

1. **Abstraction d'Exécution Unifiée** :
   - Ne jamais appeler directement de commandes shell ou SSH brutes dans les routes ou la logique métier.
   - Toujours passer par l'interface `Executor` (`LocalExecutor` ou `SSHExecutor`) fournie par le `ServerManager`.

2. **Sécurité SSH & Privilèges** :
   - Écoute par défaut uniquement sur `127.0.0.1`.
   - Ne jamais enregistrer de mots de passe SSH ou de clés privées en clair dans les fichiers de configuration public.
   - Ne jamais exposer d'endpoint HTTP d'exécution arbitraire de commandes shell (`POST /api/execute`).

3. **Tâches d'Arrière-Plan Asynchrones** :
   - Les opérations longues (installations, sauvegardes) sont exécutées via `TaskManager` pour ne pas bloquer les requêtes HTTP.
   - Le frontend interroge `GET /api/tasks/<task_id>` pour afficher l'avancement.

4. **Compatibilité PyInstaller** :
   - Utiliser `resource_path("templates")` et `resource_path("static")` pour résoudre les ressources sous PyInstaller (`sys._MEIPASS`).
