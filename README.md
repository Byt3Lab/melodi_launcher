# MELODI Launcher (Desktop 100% Tkinter)

MELODI Launcher est l’application de bureau d’administration et d’orchestration pour **MELODI ERP**. Conçue en **Python et 100% Tkinter**, elle permet de gérer des environnements locaux et distants (SSH), de superviser les services associés et d’installer ou mettre à jour la plateforme MELODI en quelques clics.

---

## ✨ Points Forts & Fonctionnalités

- **100% Application Bureau Native** : Aucune dépendance à un serveur web (ni Quart, ni Hypercorn, ni Jinja2), aucun conflit de port HTTP, aucun navigateur requis. Démarrage instantané.
- **Déploiement en 1 Clic (Local ou Distant)** :
  - Installation sur la **machine locale** (localhost).
  - Déploiement sur un **serveur distant via SSH** (authentification par clé privée ou mot de passe).
  - Prise en charge des archives locales `.zip` ou de téléchargements par URL directe.
  - Déploiement automatisé : environnement virtuel Python (`venv`), dépendances `pip`, unité systemd (`melodi.service`).
- **Composants d'infrastructure intégrés** :
  - Déploiement et configuration de **PostgreSQL** (base de données SQL).
  - Déploiement et configuration de **Redis Server** (gestion du cache et des files de tâches).
- **Console d'Exécution & Logs en Temps Réel** :
  - Suivi pas à pas avec barre de progression.
  - Console intégrée avec coloration syntaxique (succès en vert, erreurs en rouge, étapes en violet).
  - Boutons pour copier ou exporter les logs d'installation.
- **Pilotage des Services Système** :
  - Contrôle en un clic : Démarrer, Arrêter, Redémarrer pour MELODI ERP, PostgreSQL et Redis.
  - Consultation des logs `journalctl` récents pour chaque service.
  - Bouton direct pour ouvrir l'ERP dans le navigateur par défaut (`http://<serveur>:5000`).
- **Métriques et Santé Système** :
  - Surveillance du CPU, de la mémoire RAM, de l'espace disque et de l'uptime du serveur.

---

## 🚀 Démarrage Rapide

### Prérequis
- Python 3.10+
- Tkinter (`sudo apt-get install python3-tk` sur Debian / Ubuntu si non installé)

### Installation des dépendances

```bash
# Cloner le dépôt et créer un environnement virtuel
python3 -m venv .venv
source .venv/bin/activate

# Installer les dépendances légères
pip install -r requirements.txt
```

### Lancement de l'application

```bash
python3 gui_launcher.py
# ou
python3 run.py
```

---

## 📦 Compilation en Exécutable Autonome (PyInstaller)

Vous pouvez packager l'application en un binaire unique et autonome pour Linux :

```bash
./build.sh
```

L'exécutable standalone sera généré dans le répertoire `dist/melodi-launcher`.

---

## 🏗️ Architecture du Projet

```text
melodi_launcher/
│
├── app/
│   ├── ui/                     # Interface graphique 100% Tkinter
│   │   ├── main_window.py      # Fenêtre principale et navigation par onglets
│   │   ├── async_worker.py     # Pont asynchrone non-bloquant (Thread + asyncio loop)
│   │   ├── theme.py            # Styles ttk et palette sombre (Slate / Tailwind)
│   │   └── components/         # Composants d'interface
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
└── requirements.txt            # Dépendances Python allégées
```

---

## 🧪 Tests

Pour exécuter la suite de tests automatisés :

```bash
pytest tests/
```
