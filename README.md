# MELODI Control Center

MELODI Control Center est l’interface d’administration et d’orchestration de MELODI. Elle permet de gérer des environnements locaux et distants, de superviser les services ERP et de déployer l’infrastructure nécessaire à l’exploitation d’une plateforme MELODI complète.

L’objectif de ce projet est de centraliser la gestion de l’ERP, des dépendances système et des serveurs, tout en offrant une expérience d’administration moderne, sécurisée et accessible depuis un navigateur.

---

## Vue d’ensemble

MELODI Control Center sert de centre de commandement pour :

- administrer des machines locales et des serveurs distants via SSH,
- installer et déployer facilement l’ERP MELODI et ses services directement en un clic,
- contrôler les services associés comme PostgreSQL, Redis, pgAdmin,
- consulter l'état des services et les ressources sur le tableau de bord,
- suivre les logs applicatifs et système en streaming temps réel.

Le produit est pensé pour les équipes techniques et les administrateurs système qui souhaitent piloter leur infrastructure MELODI sans passer par des outils disparates ou des procédures manuelles complexes.

---

## Fonctionnalités principales

### Gestion multi-serveurs

Le Control Center prend en charge plusieurs cibles d’administration :

- serveur local (localhost),
- hôtes distants accessibles via SSH,
- machines avec clés SSH préconfigurées.

Les connexions SSH peuvent être établies avec des identités comme :

- `~/.ssh/id_ed25519`
- `~/.ssh/id_rsa`

Cela permet de gérer plusieurs environnements de manière centralisée, sans avoir à ouvrir une session shell indépendante pour chaque serveur.

### Orchestration des services

L’application permet de démarrer, arrêter, redémarrer et surveiller les services essentiels à l’exploitation MELODI, notamment :

- MELODI ERP,
- PostgreSQL,
- Redis,
- pgAdmin 4.

Cette orchestration rend la gestion des environnements plus fiable et plus rapide, surtout lors des déploiements, des mises à jour ou des redémarrages de maintenance.

### Installateurs automatisés

Le Control Center inclut des assistants d’installation et de configuration pour déployer rapidement l’infrastructure minimale du projet :

- MELODI ERP,
- PostgreSQL,
- Redis,
- pgAdmin 4.

Les actions sont exécutées en arrière-plan afin de ne pas bloquer l’interface utilisateur. Cette approche simplifie l’installation et réduit les risques d’erreurs de configuration manuelle.

### Tableau de bord et métriques rapides

Le tableau de bord permet d’observer les ressources système importantes :

- CPU,
- mémoire RAM,
- utilisation du disque,
- uptime du serveur,
- état général des services.

Ces informations sont utiles pour diagnostiquer rapidement un ralentissement, une saturation ou une panne de service.

### Console de logs

L’application expose des flux de logs en temps réel couvrant :

- sortie standard (`stdout`),
- sortie d’erreur (`stderr`),
- journaux système (`journalctl`).

La console de logs permet de remonter rapidement les erreurs applicatives, de vérifier le bon déroulement des déploiements et de suivre les tâches en cours.

### Déploiement simplifié pour utilisateur
L'interface est conçue pour être accessible à un utilisateur sans compétences système avancées :
- Téléversement d'archive source MELODI (.zip) ou installation des dépendances système standard en un clic,
- Déploiement direct sans conteneurisation complexe ni dépendances lourdes,
- Suivi visuel pas-à-pas de l'avancement avec retour d'état clair et gestion transparente des privilèges sudo.

### Packaging autonome

Le projet peut être empaqueté sous forme d’exécutable autonome pour Linux via PyInstaller. Cela permet de distribuer l’application de manière plus simple, sans dépendre d’un environnement de développement complet.

---

## Architecture technique

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
               PostgreSQL / Redis / pgAdmin
```

### Stack technologique

- Backend : Python 3.10+, Quart, Hypercorn, `asyncssh`, `psutil`
- Frontend : HTML5, Jinja2, Tailwind CSS, Alpine.js
- Configuration : `config/config.json` et `config/servers.json`

Le backend est asynchrone et conçu pour gérer plusieurs connexions simultanées, ce qui est particulièrement adapté à la supervision de serveurs, à la collecte de logs et à la gestion de sessions SSH.

---

## Cas d’usage

MELODI Control Center est utile dans plusieurs situations :

- installation initiale d’un environnement MELODI sur un nouveau serveur,
- administration d’un parc de machines local ou distant,
- redémarrage rapide des services après une mise à jour,
- diagnostic d’un bug ou d’une panne applicative,
- supervision des ressources serveur,
- exécution de scripts ou commandes de maintenance sans sortir du navigateur,
- gestion des déploiements dans des environnements multi-serveurs.

---

## Installation et lancement

### 1. Mode développement

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 run.py
```

Puis ouvrez :

`http://127.0.0.1:8080`

### 2. Exécution des tests

```bash
pytest tests/
```

### 3. Packaging Linux autonome

```bash
chmod +x build.sh
./build.sh
```

L’exécutable généré est disponible dans `dist/launcher`.

### 4. Lancement avec Docker Compose

Docker et Docker Compose v2 doivent être installés.

```bash
docker compose up --build -d
```

Ensuite, ouvrez :

`http://127.0.0.1:8080`

Pour modifier le port exposé sur l’hôte, définissez `MELODI_HTTP_PORT` avant de lancer Compose. Par défaut, l’interface est restreinte à la machine locale ; si vous souhaitez l’exposer sur le réseau, définissez aussi `MELODI_HTTP_HOST=0.0.0.0`.

Compose conserve la configuration des serveurs et les journaux dans les volumes `melodi-config` et `melodi-logs`.

Pour arrêter l’application sans supprimer les données :

```bash
docker compose down
```

Le conteneur s’exécute sans privilèges élevés et ne contrôle pas directement les services de l’hôte. Il est destiné à administrer des serveurs distants via SSH. Les clés SSH doivent être accessibles au conteneur et correctement configurées dans l’application.

---

## Sécurité et bonnes pratiques

- Les accès distants passent par des mécanismes SSH sécurisés.
- Les identités SSH doivent être correctement provisionnées et protégées.
- Les données de configuration sont stockées localement dans les fichiers de config du projet.
- Le conteneur Docker ne doit pas être lancé avec des privilèges excessifs si l’objectif est simplement d’administrer des machines distantes.

---

## Licence

Ce projet est distribué sous licence MIT. Consultez [LICENSE](LICENSE) pour plus de détails.
