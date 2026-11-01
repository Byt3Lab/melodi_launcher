function globalApp() {
            return {
                mobileMenuOpen: false,
                servers: [],
                activeServerId: localStorage.getItem('melodi_active_server_id') || 'local',
                currentServerName: 'Localhost',
                toasts: [],

                init() {
                    this.loadServers();
                },

                async loadServers() {
                    try {
                        const res = await apiRequest('/api/servers');
                        const data = await res.json();
                        if (data.success) {
                            this.servers = data.servers;
                            this.$store.state.servers = data.servers;
                            const active = this.servers.find(s => s.id === this.activeServerId);
                            if (active) {
                                this.currentServerName = active.name;
                            } else if (this.servers.length > 0) {
                                this.activeServerId = this.servers[0].id;
                                this.currentServerName = this.servers[0].name;
                            }
                        }
                    } catch (e) { console.error("Launcher request failed:", e); }
                },

                switchServer() {
                    localStorage.setItem('melodi_active_server_id', this.activeServerId);
                    this.$store.state.activeServerId = this.activeServerId;
                    const active = this.servers.find(s => s.id === this.activeServerId);
                    if (active) this.currentServerName = active.name;
                    const current = this.$router.currentRoute();
                    this.$router.push(`${current}?server=${encodeURIComponent(this.activeServerId)}&refresh=${Date.now()}`);
                },

                showToast(message, type = 'info') {
                    const id = Date.now();
                    this.toasts.push({ id, message, type });
                    setTimeout(() => {
                        this.toasts = this.toasts.filter(t => t.id !== id);
                    }, 4000);
                }
            }
        }
