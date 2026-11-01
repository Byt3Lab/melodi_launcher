const SERVICES_DATA = {
        melodi: {
            id: 'melodi',
            title: 'MELODI ERP',
            subtitle: 'Application Principale & Logique Métier',
            category: 'Application ERP',
            badge: 'M',
            colorClass: 'bg-gradient-to-tr from-emerald-500 to-teal-400 text-slate-950',
            btnColorClass: 'bg-emerald-600 hover:bg-emerald-500',
            unitFile: 'melodi.service',
            port: 5000,
            description: "Déploie l'application serveur centrale de MELODI ERP via extraction ZIP sur la machine hôte avec environnement virtuel Python et service systemd.",
            paths: {
                app: '/opt/melodi',
                config: '/opt/melodi/config/config.json',
                logs: '/var/log/melodi.log'
            },
            steps: [
                { title: "1. Dépendances système", description: "Installation de Python 3, venv, unzip et outils de compilation.", cmd: "apt-get install -y python3 python3-venv unzip git" },
                { title: "2. Décompression du ZIP source", description: "Extraction de l'archive ZIP fournie par l'utilisateur vers /opt/melodi.", cmd: "unzip archive.zip -d /opt/melodi" },
                { title: "3. Environnement virtuel Python", description: "Création du venv et installation des dépendances pip.", cmd: "/opt/melodi/venv/bin/pip install -r requirements.txt" },
                { title: "4. Activation Systemd", description: "Enregistrement de melodi.service pour démarrage automatique.", cmd: "systemctl enable --now melodi" }
            ]
        },
        melodi_websocket: {
            id: 'melodi_websocket',
            title: 'MELODI WebSocket',
            subtitle: 'Serveur WebSocket Temps Réel & Notifications',
            category: 'Temps Réel MELODI',
            badge: 'WS',
            colorClass: 'bg-cyan-500/20 border border-cyan-500/30 text-cyan-400',
            btnColorClass: 'bg-cyan-600 hover:bg-cyan-500',
            unitFile: 'melodi-websocket.service',
            port: 8001,
            description: "Déploie et configure le serveur WebSocket temps réel de MELODI ERP pour la diffusion instantanée des événements et notifications aux utilisateurs connectés.",
            paths: {
                app: '/opt/melodi',
                config: '/opt/melodi/websocket_server.py',
                logs: '/var/log/melodi-websocket.log'
            },
            steps: [
                { title: "1. Vérification de l'environnement", description: "Vérifie Python 3, venv et le dossier /opt/melodi.", cmd: "python3 -m venv /opt/melodi/venv" },
                { title: "2. Extraction ZIP (si fourni)", description: "Mise à jour des fichiers WebSocket dans /opt/melodi.", cmd: "unzip -o archive.zip -d /opt/melodi" },
                { title: "3. Dépendances Python", description: "Installation des paquets requis dans le virtualenv.", cmd: "/opt/melodi/venv/bin/pip install -r requirements.txt" },
                { title: "4. Service Systemd", description: "Création et activation de melodi-websocket.service.", cmd: "systemctl enable --now melodi-websocket" }
            ]
        },
        melodi_process_manager: {
            id: 'melodi_process_manager',
            title: 'MELODI Process Manager',
            subtitle: 'Gestionnaire de Processus & Tâches Asynchrones',
            category: 'Orchestration MELODI',
            badge: 'PM',
            colorClass: 'bg-amber-500/20 border border-amber-500/30 text-amber-400',
            btnColorClass: 'bg-amber-600 hover:bg-amber-500',
            unitFile: 'melodi-process-manager.service',
            port: 5002,
            description: "Déploie et configure le gestionnaire de processus de MELODI ERP chargé de superviser les workers, files d'attente et traitements planifiés en arrière-plan.",
            paths: {
                app: '/opt/melodi',
                config: '/opt/melodi/process_manager.py',
                logs: '/var/log/melodi-process-manager.log'
            },
            steps: [
                { title: "1. Vérification de l'environnement", description: "Vérifie Python 3, venv et le dossier /opt/melodi.", cmd: "python3 -m venv /opt/melodi/venv" },
                { title: "2. Extraction ZIP (si fourni)", description: "Mise à jour des fichiers Process Manager dans /opt/melodi.", cmd: "unzip -o archive.zip -d /opt/melodi" },
                { title: "3. Dépendances Python", description: "Installation des paquets requis dans le virtualenv.", cmd: "/opt/melodi/venv/bin/pip install -r requirements.txt" },
                { title: "4. Service Systemd", description: "Création et activation de melodi-process-manager.service.", cmd: "systemctl enable --now melodi-process-manager" }
            ]
        },
        pgadmin: {
            id: 'pgadmin',
            title: 'pgAdmin 4 (Web)',
            subtitle: 'Gestionnaire Web de Base de Données',
            category: 'Gestion Base de données',
            badge: '🐘',
            colorClass: 'bg-blue-500/20 border border-blue-500/30 text-blue-400',
            btnColorClass: 'bg-blue-600 hover:bg-blue-500',
            unitFile: 'pgadmin4-web',
            port: 5050,
            description: "Interface web officielle et complète d'administration pour vos bases PostgreSQL (exploration des tables, requêtes SQL interactives, création de schémas et suivi des performances).",
            paths: {
                app: '/var/lib/pgadmin',
                config: '/etc/pgadmin/config.py',
                logs: '/var/log/pgadmin4.log'
            },
            steps: [
                { title: "1. Dépôt pgAdmin officiel", description: "Configuration des clés APT officielles PostgreSQL / pgAdmin.", cmd: "curl -fsS https://www.pgadmin.org/... | gpg" },
                { title: "2. Installation APT", description: "Installation du paquet pgadmin4-web.", cmd: "apt-get install -y pgadmin4-web" }
            ]
        },
        postgresql: {
            id: 'postgresql',
            title: 'PostgreSQL Database',
            subtitle: 'Moteur Relationnel SQL Persistant',
            category: 'Base de données',
            badge: 'PG',
            colorClass: 'bg-indigo-500/20 border border-indigo-500/30 text-indigo-400',
            btnColorClass: 'bg-indigo-600 hover:bg-indigo-500',
            unitFile: 'postgresql.service',
            port: 5432,
            description: "Système de gestion de base de données relationnelle objet performant et sécurisé, stockage principal des entités et transactions de MELODI ERP.",
            paths: {
                app: '/var/lib/postgresql',
                config: '/etc/postgresql/*/main/postgresql.conf',
                logs: '/var/log/postgresql/'
            },
            steps: [
                { title: "1. Vérification des paquets", description: "Vérifie si PostgreSQL est présent.", cmd: "dpkg -s postgresql" },
                { title: "2. Installation via APT", description: "Installation de postgresql et postgresql-contrib.", cmd: "apt-get install -y postgresql postgresql-contrib" },
                { title: "3. Activation", description: "Démarrage immédiat et activation au boot.", cmd: "systemctl enable --now postgresql" }
            ]
        },
        redis: {
            id: 'redis',
            title: 'Redis Server',
            subtitle: 'Cache Mémoire & Courtier de Messages',
            category: 'Cache & Queue',
            badge: 'RD',
            colorClass: 'bg-rose-500/20 border border-rose-500/30 text-rose-400',
            btnColorClass: 'bg-rose-600 hover:bg-rose-500',
            unitFile: 'redis-server.service',
            port: 6379,
            description: "Structure de données en mémoire ultra-rapide servant de cache applicatif, gestionnaire de sessions et broker de messages pour Celery.",
            paths: {
                app: '/var/lib/redis',
                config: '/etc/redis/redis.conf',
                logs: '/var/log/redis/redis-server.log'
            },
            steps: [
                { title: "1. Installation APT", description: "Installation du paquet redis-server.", cmd: "apt-get install -y redis-server" },
                { title: "2. Démarrage", description: "Activation et démarrage immédiat.", cmd: "systemctl enable --now redis-server" }
            ]
        }
    };

    function serviceInstallComponent(initialService) {
        return {
            currentServiceId: initialService,
            serviceMeta: SERVICES_DATA[initialService] || SERVICES_DATA.melodi,
            allServices: [
                { id: 'melodi', label: 'MELODI ERP' },
                { id: 'melodi_websocket', label: 'WebSocket' },
                { id: 'melodi_process_manager', label: 'Process Manager' },
                { id: 'postgresql', label: 'PostgreSQL' },
                { id: 'redis', label: 'Redis' },
                { id: 'pgadmin', label: 'pgAdmin 4' }
            ],
            statusInfo: {
                is_installed: false,
                is_running: false,
                status_text: 'Vérification...'
            },
            autoScroll: true,
            showSudoModal: false,
            sudoPasswordInput: '',
            showSudoText: false,
            rememberSudoPassword: true,
            sudoServerName: '',
            pendingPayload: null,
            uploadedZipPath: null,
            uploadedZipName: null,
            sourceType: 'file',
            downloadUrl: '',
            destinationDir: '/opt',
            deleteZipAfterExtract: true,
            isDeployOnly: false,
            isUploading: false,
            isCancelling: false,
            activeTask: null,
            activeTaskId: null,
            timer: null,

            init() {
                this.loadStatus();
                this.__intervals.push(setInterval(() => {
                    if (!this.activeTaskId) {
                        this.loadStatus();
                    }
                }, 3000));
            },

            async loadStatus() {
                const activeServerId = localStorage.getItem('melodi_active_server_id') || 'local';
                try {
                    const res = await apiRequest(`/api/servers/${activeServerId}/installers/${this.currentServiceId}`);
                    const data = await res.json();
                    if (data.success && data.service) {
                        this.statusInfo = data.service;
                    }
                } catch (e) { console.error("Launcher request failed:", e); }
            },

            async handleFileSelect(e) {
                const file = e.target.files[0];
                if (!file) return;

                const activeServerId = localStorage.getItem('melodi_active_server_id') || 'local';
                const formData = new FormData();
                formData.append('file', file);

                this.isUploading = true;
                try {
                    const res = await apiRequest(`/api/servers/${activeServerId}/upload`, {
                        method: 'POST',
                        body: formData
                    });
                    const data = await res.json();
                    if (data.success) {
                        this.uploadedZipPath = data.file_path;
                        this.uploadedZipName = data.filename;
                    } else {
                        alert(data.message || "Erreur de téléversement");
                    }
                } catch (err) {
                    alert("Échec du téléversement du fichier ZIP");
                } finally {
                    this.isUploading = false;
                }
            },

            triggerDeployArchive() {
                const activeServerId = localStorage.getItem('melodi_active_server_id') || 'local';
                if (this.sourceType === 'url' && !this.downloadUrl.trim()) {
                    alert("Veuillez saisir une URL de téléchargement valide.");
                    return;
                }
                if (this.sourceType === 'file' && !this.uploadedZipPath) {
                    alert("Veuillez d'abord sélectionner une archive ZIP à téléverser.");
                    return;
                }
                if (!confirm(`Confirmer le déploiement de l'archive MELODI ERP dans ${this.destinationDir || '/opt'} ?`)) return;

                const payload = {
                    source_type: this.sourceType,
                    url: this.downloadUrl.trim() || null,
                    zip_path: this.uploadedZipPath,
                    destination_dir: this.destinationDir || '/opt',
                    delete_zip: this.deleteZipAfterExtract
                };
                this.isDeployOnly = true;
                this.pendingPayload = payload;
                this.executeDeploy(payload);
            },

            executeDeploy(payload) {
                const activeServerId = localStorage.getItem('melodi_active_server_id') || 'local';

                apiRequest(`/api/servers/${activeServerId}/melodi/deploy`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                })
                .then(res => res.json())
                .then(data => {
                    if (data.requires_sudo) {
                        this.sudoServerName = data.server_name || activeServerId;
                        this.showSudoModal = true;
                        return;
                    }

                    if (data.success) {
                        this.showSudoModal = false;
                        this.activeTaskId = data.task_id;
                        this.pollTask();
                        if (this.timer) clearInterval(this.timer);
                        this.timer = setInterval(() => this.pollTask(), 600);
                    } else {
                        alert(data.message || "Erreur de déploiement.");
                    }
                })
                .catch(e => alert("Erreur réseau lors du déploiement de l'archive."));
            },

            triggerInstall() {
                const activeServerId = localStorage.getItem('melodi_active_server_id') || 'local';
                if (this.sourceType === 'url' && !this.downloadUrl.trim()) {
                    if (!confirm("Aucune URL spécifiée. Continuer l'installation sans télécharger de nouvelle archive ?")) return;
                }
                if (!confirm(`Confirmer le lancement de l'installation de ${this.serviceMeta.title} sur le serveur sélectionné ?`)) return;

                const payload = {
                    source_type: this.sourceType,
                    url: this.downloadUrl.trim() || null,
                    zip_path: this.uploadedZipPath,
                    destination_dir: this.destinationDir || '/opt',
                    delete_zip: this.deleteZipAfterExtract
                };
                this.isDeployOnly = false;
                this.pendingPayload = payload;
                this.executeInstall(payload);
            },

            executeInstall(payload) {
                const activeServerId = localStorage.getItem('melodi_active_server_id') || 'local';

                apiRequest(`/api/servers/${activeServerId}/installers/${this.currentServiceId}/install`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                })
                .then(res => res.json())
                .then(data => {
                    if (data.requires_sudo) {
                        this.sudoServerName = data.server_name || activeServerId;
                        this.showSudoModal = true;
                        return;
                    }

                    if (data.success) {
                        this.showSudoModal = false;
                        this.activeTaskId = data.task_id;
                        this.pollTask();
                        if (this.timer) clearInterval(this.timer);
                        this.timer = setInterval(() => this.pollTask(), 600);
                    } else {
                        alert(data.message);
                    }
                })
                .catch(e => alert("Erreur au lancement de l'installation."));
            },

            confirmSudoAndInstall() {
                if (!this.sudoPasswordInput) return;
                const payload = {
                    ...(this.pendingPayload || {}),
                    sudo_password: this.sudoPasswordInput,
                    save_password: this.rememberSudoPassword
                };
                if (this.isDeployOnly) {
                    this.executeDeploy(payload);
                } else {
                    this.executeInstall(payload);
                }
            },

            async cancelTask(taskId) {
                if (!taskId) return;
                if (!confirm("Êtes-vous sûr de vouloir interrompre cette opération en cours ?")) return;
                try {
                    this.isCancelling = true;
                    const res = await apiRequest(`/api/tasks/${taskId}/cancel`, { method: 'POST' });
                    const data = await res.json();
                    if (data.success) {
                        await this.pollTask();
                    } else {
                        alert(data.message || "Impossible d'interrompre la tâche.");
                    }
                } catch (e) {
                    alert("Erreur lors de l'interruption de la tâche.");
                } finally {
                    this.isCancelling = false;
                }
            },

            async pollTask() {
                if (!this.activeTaskId) return;
                try {
                    const res = await apiRequest(`/api/tasks/${this.activeTaskId}`);
                    const data = await res.json();
                    if (data.success) {
                        this.activeTask = data.task;
                        if (this.autoScroll) {
                            setTimeout(() => {
                                const container = document.getElementById('taskLogsContainer');
                                if (container) {
                                    container.scrollTop = container.scrollHeight;
                                }
                            });
                        }
                        if (this.activeTask.status === 'SUCCESS' || this.activeTask.status === 'FAILED' || this.activeTask.status === 'CANCELLED') {
                            if (this.timer) clearInterval(this.timer);
                            this.activeTaskId = null;
                            this.loadStatus();
                        }
                    }
                } catch (e) { console.error("Launcher request failed:", e); }
            }
        }
    }
