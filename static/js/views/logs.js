function logsComponent() {
        return {
            logs: [],
            logInfo: {},
            linesCount: 200,
            autoScroll: true,
            init() {
                this.fetchLogs();
                this.__intervals.push(setInterval(() => this.fetchLogs(), 2000));
            },
            async fetchLogs() {
                try {
                    const res = await apiRequest(`/api/logs?lines=${this.linesCount}`);
                    const data = await res.json();
                    if (data.success) {
                        this.logs = data.logs;
                        this.logInfo = data.info;
                        if (this.autoScroll) {
                            setTimeout(() => {
                                const container = document.getElementById('terminalContainer');
                                if (container) container.scrollTop = container.scrollHeight;
                            });
                        }
                    }
                } catch (e) { console.error("Launcher request failed:", e); }
            },
            async clearLogs() {
                if (!confirm("Voulez-vous vraiment effacer l'historique des logs ?")) return;
                try {
                    const res = await apiRequest('/api/logs', { method: 'DELETE' });
                    const data = await res.json();
                    if (data.success) {
                        this.logs = [];
                        await this.fetchLogs();
                    } else {
                        alert(data.message);
                    }
                } catch (e) {
                    alert("Erreur lors de l'effacement des logs.");
                }
            }
        }
    }
