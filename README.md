# MELODI Control Center

**MELODI Control Center** est une application web moderne d'administration et d'orchestration permettant de gérer des serveurs **Locaux (Localhost)** et **Distants (via SSH)**.

Elle permet d'installer, configurer et administrer **MELODI ERP** ainsi que l'ensemble de ses dépendances et services associés (**PostgreSQL**, **Redis**, **Nginx**, **Celery**).

---

## 🚀 Fonctionnalités Clés

- **Gestion Multi-Serveurs** : Administrez votre machine locale et vos serveurs distants via des connexions SSH sécurisées par clés (`~/.ssh/id_ed25519`, `~/.ssh/id_rsa`).
- **Orchestration des Services** : Démarrage, arrêt et redémarrage contrôlés pour MELODI ERP, PostgreSQL, Redis, Nginx et Celery.
- **Installateurs Automatisés en Arrière-Plan** : Assistant guidé d'installation par étapes pour déployer MELODI, PostgreSQL, Redis et Nginx sans bloquer l'interface.
- **Surveillance & Monitoring** : Visualisez l'utilisation du CPU, de la mémoire RAM, de l'espace disque et de l'Uptime du serveur sélectionné.
- **Console de Logs** : Extraction et défilement en direct des journaux d'exécution (`stdout`, `stderr` et `journalctl`).
- **Executable Autonome Standalone** : Packaging avec PyInstaller pour une exécution sans dépendance sous Linux.

---

## 🏗️ Architecture & Technologies

```text
                  MELODI CONTROL CENTER
                           │
                    Quart Web App
                           │
                 ┌─────────┴─────────┐
                 │                   │
              Local                Remote
                 │                   │
          Local Executor        SSH Executor (asyncssh)
                 │                   │
                 ▼                   ▼
             Machine             Serveur Distant
                 │                   │
          ┌──────┴──────┐     ┌──────┴──────┐
          │             │     │             │
       MELODI        Services MELODI     Services
                         │
               PostgreSQL / Redis / Nginx
```

- **Backend** : Python 3.10+, Quart (Framework Web Asynchrone), Hypercorn (Serveur ASGI), `asyncssh` (Client SSH asynchrone), `psutil`.
- **Frontend** : HTML5, Jinja2, Tailwind CSS, Alpine.js (Polling REST & notifications).
- **Stockage de Configuration** : `config/config.json` et `config/servers.json`.

---

## 🛠️ Installation & Lancement

### 1. Mode Développement
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 run.py
```
Accédez ensuite au Control Center dans votre navigateur sur :
👉 `http://127.0.0.1:8080`

### 2. Exécution des Tests Automatisés
```bash
pytest tests/
```

### 3. Packaging Standalone Linux
```bash
chmod +x build.sh
./build.sh
```
L'exécutable compilé est disponible dans `dist/launcher`.

---

## 📄 Licence
Ce projet est sous licence MIT. Voir [LICENSE](LICENSE) pour plus de détails.
