function settingsComponent() {
        return {
            form: {
                server: { host: '127.0.0.1', port: 8080 },
                melodi: { path: '', python: '', command: ['python3', 'main.py'], port: 5000 },
                melodi_websocket: { path: '', python: '', command: ['python3', 'websocket_server.py'], port: 8001 },
                melodi_process_manager: { path: '', python: '', command: ['python3', 'process_manager.py'], port: 5002 },
                logging: { file_path: 'logs/melodi.log' }
            },
            isSaving: false,

            updateCommand(service, value) {
                try {
                    this.form[service].command = JSON.parse(value);
                } catch (error) {
                    console.warn(`Invalid JSON command for ${service}:`, error);
                }
            },

            init() {
                this.loadSettings();
            },

            async loadSettings() {
                try {
                    const res = await apiRequest('/api/settings');
                    const data = await res.json();
                    if (data.success) {
                        this.form = {
                            ...this.form,
                            ...data.settings,
                            melodi_websocket: { ...this.form.melodi_websocket, ...(data.settings.melodi_websocket || {}) },
                            melodi_process_manager: { ...this.form.melodi_process_manager, ...(data.settings.melodi_process_manager || {}) }
                        };
                    }
                } catch (e) {
                    console.error("Erreur chargement settings:", e);
                }
            },

            async saveSettings() {
                this.isSaving = true;
                try {
                    const res = await apiRequest('/api/settings', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(this.form)
                    });
                    const data = await res.json();
                    alert(data.message);
                } catch (e) {
                    alert("Erreur de sauvegarde des paramètres");
                } finally {
                    this.isSaving = false;
                }
            }
        }
    }
