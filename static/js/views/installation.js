function installationComponent() {
        return {
            activeTask: null,
            activeTaskId: null,
            timer: null,
            isCancelling: false,
            autoScroll: true,

            init() {
                this.checkActiveTasks();
            },

            async checkActiveTasks() {
                // Poll any ongoing task
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
                                if (container) container.scrollTop = container.scrollHeight;
                            });
                        }
                        if (this.activeTask.status === 'SUCCESS' || this.activeTask.status === 'FAILED' || this.activeTask.status === 'CANCELLED') {
                            if (this.timer) clearInterval(this.timer);
                        }
                    }
                } catch (e) { console.error("Launcher request failed:", e); }
            }
        }
    }
