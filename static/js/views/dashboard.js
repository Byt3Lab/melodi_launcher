function dashboardComponent() {
        return {
            serverName: 'Localhost',
            metrics: {},
            services: [],
            init() {
                this.loadDashboardData();
                this.__intervals.push(setInterval(() => this.loadDashboardData(), 2000));
            },
            async loadDashboardData() {
                const activeServerId = localStorage.getItem('melodi_active_server_id') || 'local';
                try {
                    const [resMetrics, resServices] = await Promise.all([
                        apiRequest(`/api/servers/${activeServerId}/system`),
                        apiRequest(`/api/servers/${activeServerId}/services`)
                    ]);
                    const dataMetrics = await resMetrics.json();
                    const dataServices = await resServices.json();

                    if (dataMetrics.success) this.metrics = dataMetrics.metrics;
                    if (dataServices.success) this.services = dataServices.services;
                } catch (e) { console.error("Launcher request failed:", e); }
            },
            async controlService(name, action) {
                const activeServerId = localStorage.getItem('melodi_active_server_id') || 'local';
                try {
                    const res = await apiRequest(`/api/servers/${activeServerId}/services/${name}/${action}`, { method: 'POST' });
                    const data = await res.json();
                    alert(data.message);
                    await this.loadDashboardData();
                } catch (e) {
                    alert("Erreur lors du contrôle du service.");
                }
            }
        }
    }
