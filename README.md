# MELODI Launcher (Desktop PySide6)

MELODI Launcher est l’application de bureau native d’administration et d’orchestration pour **MELODI ERP**. Conçue avec **Python, PySide6 (Qt 6) et `qasync`**, elle offre une interface moderne (mode sombre et clair) pour gérer des environnements locaux et distants (SSH), superviser les services et déployer la plateforme MELODI étape par étape.

---

## ✨ Fonctionnalités

- **Application Bureau Native (PySide6 + qasync)** : Interface moderne avec navigation latérale, cartes, jauges circulaires, icônes vectorielles SVG, notifications toast non-intrusives et bascule de thème sombre/clair.
- **Tableau de bord en temps réel** : Jauges CPU, RAM, Disque, disponibilité (uptime) et résumé de l'état des services.
- **Assistant d'installation en 5 étapes** :
  1. Sélection de la cible (machine locale ou serveur distant SSH) avec test de connectivité.
  2. Choix de la source (archive `.zip` locale ou URL de téléchargement) et du répertoire cible.
  3. Sélection des composants (PostgreSQL, Redis, MELODI ERP).
  4. Récapitulatif clair avant déploiement.
  5. Suivi par liste d'étapes, barre de progression et détails dépliables.
- **Pilotage des Services** : Démarrer, arrêter, redémarrer ou consulter les logs `journalctl` pour MELODI ERP, PostgreSQL et Redis, avec ouverture directe dans le navigateur.
- **Journaux dédiés** : Console en direct ou consultation `journalctl` filtrable et exportable.
- **Sécurité des identifiants** : Mots de passe SSH et sudo stockés dans le trousseau sécurisé du système (`keyring`), jamais en clair dans `config/servers.json`.

---

## 🚀 Démarrage Rapide

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 gui_launcher.py
```

---

## 📦 Compilation PyInstaller

```bash
./build.sh
```

L'exécutable standalone est généré dans `dist/melodi-launcher`.

---

## 🧪 Tests

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/pytest tests/ -q
```

---

## 🌐 Ajouter une langue

1. Copier `locales/en.json` vers `locales/<code_langue>.json` (ex. `locales/es.json`) et traduire toutes les valeurs.
2. Ajouter `"<code_langue>": "<Nom natif>"` dans `SUPPORTED` dans `app/i18n.py`.
