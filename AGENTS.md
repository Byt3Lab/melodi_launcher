# Guide pour les Agents IA (AGENTS.md) - MELODI Launcher

Ce document fournit le contexte, l'architecture et les règles essentielles concernant **MELODI Launcher**. Il guide tout agent IA intervenant sur cette base de code.

---

## 📌 Contexte du Projet

**MELODI Launcher** est une **application de bureau 100% Tkinter native d'administration et d'orchestration pour MELODI ERP**.
Elle permet de déployer et de gérer MELODI ERP sur une machine locale ou un serveur distant via des connexions SSH sécurisées non-bloquantes (`asyncssh`).

L'application ne dépend d'aucun serveur web, ne nécessite aucun navigateur et démarre instantanément en tant qu'application native.

---

## 🗂️ Structure et Architecture Cible

```text
melodi_launcher/
│
├── app/
│   ├── ui/                     # Interface graphique 100% Tkinter
│   │   ├── main_window.py      # Fenêtre principale et navigation par onglets
│   │   ├── async_worker.py     # Pont asynchrone non-bloquant (Thread + asyncio loop)
│   │   ├── theme.py            # Styles ttk et palette sombre (Slate / Tailwind)
│   │   └── components/         # Composants d'interface (Server, Install, Service, System, Console)
│   │       ├── server_panel.py   # Sélecteur Cible (Local vs SSH) et test de connexion
│   │       ├── install_panel.py  # Assistant déploiement MELODI ERP & dépendances
│   │       ├── service_panel.py  # Pilotage des services (melodi, postgres, redis)
│   │       ├── system_panel.py   # Métriques système (CPU, RAM, Disque, Uptime)
│   │       └── console_panel.py  # Console de logs en direct & barre de progression
│   │
│   ├── core/                   # ServerManager, TaskManager, ProcessManager
│   ├── remote/                 # Executor, LocalExecutor, SSHExecutor, CredentialManager
│   ├── system/                 # PackageManager, SystemdManager, SystemInfo
│   ├── installers/             # BaseInstaller, MelodiInstaller, Postgres, Redis
│   └── services/               # BaseService, Melodi, Postgres, Redis
│
├── assets/                     # Icônes et images
├── config/                     # servers.json (profils serveurs sauvegardés)
├── tests/                      # Suite de tests automatisés pytest
├── gui_launcher.py             # Point d'entrée principal Tkinter
├── run.py                      # Raccourci d'exécution
├── build.sh                    # Script PyInstaller
├── requirements.txt            # Dépendances Python allégées (asyncssh, psutil, pyinstaller, pytest)
├── README.md
└── AGENTS.md
```

---

## 🚀 Principes & Règles d'Architecture

1. **Non-Blocage de l'Interface Graphique (Tkinter Mainloop)** :
   - Tkinter s'exécute sur le thread principal.
   - Toutes les opérations longues (connexions SSH, commandes système, transferts SFTP, apt-get, pip) doivent impérativement être exécutées via `AsyncWorker.run_coroutine(...)`.
   - Les retours vers l'UI (mises à jour de logs, progression, messages) doivent transiter par `AsyncWorker.call_in_gui(...)` ou `root.after_idle(...)`.

2. **Abstraction d'Exécution Unifiée** :
   - Ne jamais appeler directement de commandes shell ou SSH brutes dans l'UI.
   - Toujours passer par l'interface `Executor` (`LocalExecutor` ou `SSHExecutor`) fournie par le `ServerPanel` ou le `ServerManager`.

3. **Sécurité SSH & Privilèges** :
   - Ne jamais enregistrer de clés privées ou de mots de passe en clair dans des fichiers publics.
   - Utiliser des permissions strictes sur les fichiers de configuration locaux (`servers.json`).

4. **Compatibilité PyInstaller** :
   - Utiliser `resource_path("config")` et `resource_path("assets")` pour résoudre les ressources sous PyInstaller (`sys._MEIPASS`).
