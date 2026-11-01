function servicesComponent() {
        return {
            services: [],
            busyService: null,

            init() {
                this.loadServices();
                this.__intervals.push(setInterval(() => this.loadServices(), 2500));
            },
            async loadServices() {
                const activeServerId = localStorage.getItem('melodi_active_server_id') || 'local';
                try {
                    const res = await apiRequest(`/api/servers/${activeServerId}/services`);
                    const data = await res.json();
                    if (data.success) {
                        this.services = data.services;
                    }
                } catch (e) { console.error("Launcher request failed:", e); }
            },
            async controlService(name, action) {
                const activeServerId = localStorage.getItem('melodi_active_server_id') || 'local';
                this.busyService = name;
                try {
                    const res = await apiRequest(`/api/servers/${activeServerId}/services/${name}/${action}`, { method: 'POST' });
                    const data = await res.json();
                    if (window.globalApp && typeof window.globalApp().showToast === 'function') {
                        // Toast if available
                    }
                    await this.loadServices();
                } catch (e) {
                    alert("Erreur lors de la commande du service");
                } finally {
                    this.busyService = null;
                }
            }
        }
    }
