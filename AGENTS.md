# Guide pour les Agents IA (AGENTS.md) - MELODI Launcher

Ce document a pour but de fournir le contexte, l'architecture et les règles essentielles concernant le projet **MELODI Launcher**. Il est destiné à guider tout agent IA intervenant sur le code de cette application.

## 📌 Contexte du Projet
**MELODI Launcher** est une interface graphique (GUI) de panneau de contrôle conçue pour faciliter le démarrage, la surveillance et l'arrêt du serveur du logiciel **MELODI ERP**, sans avoir besoin de passer par la ligne de commande. 
L'application est développée en **Python** et utilise exclusivement la bibliothèque standard **Tkinter** pour son interface graphique (suite à une migration visant à retirer la dépendance à `CustomTkinter`).

## 🗂️ Structure et Architecture

Le dépôt est volontairement minimaliste, centré autour d'un script principal :

- `launcher.py` : C'est le cœur de l'application. Ce fichier définit la classe `MelodiLauncher` héritant de `tk.Tk`. Il gère :
  - L'interface graphique (bouton dynamique start/stop, indicateur visuel de statut dessiné sur un `tk.Canvas`).
  - L'invocation du serveur MELODI. Le serveur est lancé en ciblant un fichier `main.py` qui doit se trouver au même niveau que le launcher. L'exécution se fait via le module `subprocess`.
  - Le multithreading (module `threading`) pour lancer le serveur sans bloquer la boucle principale d'événements de Tkinter (`app.mainloop()`).
  - L'arrêt propre du processus du serveur (`terminate()`).
- `build.sh` : Script Bash contenant la commande de compilation pour générer un exécutable autonome (standalone) via PyInstaller (`pyinstaller --noconsole --onefile launcher.py`).
- `melodi_launcher.log` : Fichier généré automatiquement par l'application pour capter les sorties standards (`stdout` et `stderr`) du processus enfant MELODI, évitant ainsi le blocage des pipes de communication Unix/Windows.

## 🚀 Mécanismes Clés
1. **Interface Utilisateur (UI)** :
   - Thème sombre implémenté manuellement via les configurations des widgets (`bg="#2b2b2b"`, `fg="white"`) pour conserver une esthétique moderne et cohérente.
   - **Thread Safety** : Les modifications d'état de l'UI provenant du thread exécutant le serveur s'effectuent obligatoirement via la méthode `self.after(0, fonction)` de l'application principale, Tkinter n'étant pas thread-safe.

2. **Gestion du Sous-processus (ERP)** :
   - Le chemin du processus cible est une constante évaluée dynamiquement à partir de la position du script actuel : `os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")`.
   - L'appel `subprocess.Popen` est surveillé par un thread dédié `_run_erp_process` pour ne pas figer l'interface. Au démarrage ou à la sortie (prévue ou sur erreur), l'IU intercepte cet état.

3. **Compilation et Déploiement** :
   - Le fichier `build.sh` doit avoir les permissions d'exécution (ex: `chmod +x build.sh`) pour fonctionner.

## ⚠️ Règles et Recommandations pour l'IA
- **Dépendances graphiques limitées** : Maintenir l'utilisation exclusive de **Tkinter**. Ne pas rajouter de dépendances externes d'UI (`PyQt`, `customtkinter`, `Kivy`, etc).
- **Modification de Tkinter depuis un Thread Secondaire** : Ne **JAMAIS** modifier directement l'interface Tkinter de `launcher.py` depuis un appel asynchrone ou un `Thread`. Utiliser les mécanismes de queue (via `after()` ou `Queue`) pour synchroniser les variables avec le thread principal.
- **Démons Process/Processes affamés** : En cas de modification sur l'arrêt ou le démarrage du sous-processus de l'ERP (`subprocess.Popen`), prendre des garanties pour éviter la création de processus orphelins (zombies). Une fermeture gracieuse ("Graceful Shutdown") est gérée dans la fonction `on_closing()`.
- **Canal de Log** : Pour débuguer MELODI, rediriger toute nouvelle écriture vers le point d'ancrage du fichier local `melodi_launcher.log`, ce qui évite la saturation du shell en arrière-plan.
