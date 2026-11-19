# Guide pour les Agents IA (AGENTS.md) - MELODI Launcher

Ce document fournit le contexte, l'architecture et les règles essentielles concernant **MELODI Launcher**. Il guide tout agent IA intervenant sur cette base de code.

---

## 📌 Contexte du Projet

**MELODI Launcher** est une **application de bureau native PySide6 (Qt 6) + `qasync` d'administration et d'orchestration pour MELODI ERP**.
Elle permet de déployer et de gérer MELODI ERP sur une machine locale ou un serveur distant via des connexions SSH sécurisées non-bloquantes (`asyncssh`).

L'application ne dépend d'aucun serveur web, ne nécessite aucun navigateur et intègre directement la boucle `asyncio` dans la boucle Qt via `qasync`.

---

## 🗂️ Structure et Architecture Cible

```text
melodi_launcher/
│
├── app/
│   ├── ui/                     # Interface graphique PySide6 + qasync
│   │   ├── main_window.py      # Fenêtre principale, navigation latérale et pile de pages
│   │   ├── sidebar.py          # Barre latérale, sélecteur de serveur et bascule de thème
│   │   ├── app_context.py      # État partagé, signaux Qt (logs, toasts, thème, serveur actif)
│   │   ├── theme/              # Design tokens & QSS (sombre et clair)
│   │   ├── widgets/            # Card, StatusPill, MetricGauge, Stepper, Toast, LogView, Icon
│   │   └── pages/              # Dashboard, InstallWizard (5 étapes), Services, Logs, Servers
│   │
│   ├── core/                   # ServerManager, TaskManager, ProcessManager
│   ├── remote/                 # Executor, LocalExecutor, SSHExecutor, CredentialManager (keyring)
│   ├── system/                 # PackageManager, SystemdManager, SystemInfo
│   ├── installers/             # BaseInstaller, MelodiInstaller, Postgres, Redis
│   └── services/               # BaseService, Melodi, Postgres, Redis
│
├── assets/                     # Icônes SVG (assets/icons/) et logo
├── config/                     # servers.json (sans mots de passe en clair)
├── tests/                      # Suite de tests pytest + pytest-qt
├── gui_launcher.py             # Point d'entrée principal PySide6 + qasync
├── run.py                      # Raccourci d'exécution
├── build.sh                    # Script PyInstaller (launcher.spec)
├── requirements.txt            # PySide6-Essentials, qasync, keyring, asyncssh, psutil
├── README.md
└── AGENTS.md
```

---

## 🚀 Principes & Règles d'Architecture

1. **Non-Blocage de l'Interface Graphique (Boucle unique `qasync`)** :
   - Les actions asynchrones dans les pages et dialogues utilisent `@asyncSlot()` de `qasync` et `await` directement les coroutines métier sans geler l'interface Qt.
   - Ne jamais exécuter d'opérations réseau ou système bloquantes dans le thread UI.

2. **Abstraction d'Exécution Unifiée** :
   - Ne jamais appeler directement de commandes shell ou SSH brutes dans l'UI.
   - Toujours passer par l'interface `Executor` (`LocalExecutor` ou `SSHExecutor`) fournie par `AppContext.executor` / `ServerManager`.

3. **Sécurité SSH & Privilèges** :
   - Ne jamais enregistrer de clés privées ou de mots de passe en clair dans `config/servers.json` ou tout autre fichier public.
   - Utiliser `CredentialManager` (trousseau système `keyring`) et des permissions `0o600` sur `servers.json`.

4. **Compatibilité PyInstaller** :
   - Utiliser `resource_path("config")`, `resource_path("assets")` et `resource_path("locales")` pour résoudre les ressources sous PyInstaller (`sys._MEIPASS`).

5. **Internationalisation (i18n FR / EN)** :
   - Aucune chaîne affichée à l'utilisateur en dur : toujours passer par `t("clé")` (`app/i18n.py`) et ajouter la clé dans `locales/fr.json` ET `locales/en.json`.
