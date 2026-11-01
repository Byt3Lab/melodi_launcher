function serversComponent() {
        return {
            serversList: [],
            showModal: false,
            isEditing: false,
            testingServer: null,
            srvForm: { id: null, type: 'ssh', name: '', host: '', port: 22, username: 'ubuntu', auth_method: 'key', key_path: '', password: '' },

            init() {
                this.fetchServers();
            },
            async fetchServers() {
                try {
                    const res = await apiRequest('/api/servers');
                    const data = await res.json();
                    if (data.success) {
                        this.serversList = data.servers;
                    }
                } catch (e) { console.error("Launcher request failed:", e); }
            },
            openAddModal() {
                this.isEditing = false;
                this.srvForm = { id: null, type: 'ssh', name: '', host: '', port: 22, username: 'ubuntu', auth_method: 'key', key_path: '', password: '' };
                this.showModal = true;
            },
            openEditModal(srv) {
                this.isEditing = true;
                this.srvForm = {
                    id: srv.id,
                    type: srv.type || 'ssh',
                    name: srv.name || '',
                    host: srv.host || '127.0.0.1',
                    port: srv.port || 22,
                    username: srv.username || 'ubuntu',
                    auth_method: srv.auth_method || (srv.password ? 'password' : 'key'),
                    key_path: srv.key_path || '',
                    password: srv.password || ''
                };
                this.showModal = true;
            },
            async saveServer() {
                if (!this.srvForm.name) {
                    alert("Veuillez renseigner un nom.");
                    return;
                }
                if (this.srvForm.type !== 'local' && !this.srvForm.host) {
                    alert("Veuillez renseigner l'adresse IP de l'hôte.");
                    return;
                }

                try {
                    const url = this.isEditing ? `/api/servers/${this.srvForm.id}` : '/api/servers';
                    const method = this.isEditing ? 'PUT' : 'POST';

                    const res = await apiRequest(url, {
                        method: method,
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(this.srvForm)
                    });
                    const data = await res.json();
                    if (data.success) {
                        this.showModal = false;
                        await this.fetchServers();
                    } else {
                        alert(data.message);
                    }
                } catch (e) {
                    alert("Erreur lors de l'enregistrement du serveur.");
                }
            },
            async testConnection(serverId) {
                this.testingServer = serverId;
                try {
                    const res = await apiRequest(`/api/servers/${serverId}/test`, { method: 'POST' });
                    const data = await res.json();
                    if (data.success) {
                        const sudoStatus = data.sudo_ready ? "✓ Sudo Privilèges OK" : "⚠ Sudo non configuré";
                        alert(`✓ Connexion réussie ! (Latence: ${data.latency_ms} ms)\n\nSystème: ${data.system_uname}\nSudo: ${sudoStatus}`);
                    } else {
                        alert(`❌ Connexion échouée: ${data.error}`);
                    }
                } catch (e) {
                    alert("Erreur lors du test de connexion.");
                } finally {
                    this.testingServer = null;
                }
            },
            async deleteServer(serverId) {
                if (!confirm("Voulez-vous vraiment supprimer ce serveur ?")) return;
                try {
                    const res = await apiRequest(`/api/servers/${serverId}`, { method: 'DELETE' });
                    const data = await res.json();
                    if (data.success) {
                        await this.fetchServers();
                    } else {
                        alert(data.message);
                    }
                } catch (e) {
                    alert("Erreur lors de la suppression.");
                }
            }
        }
    }
