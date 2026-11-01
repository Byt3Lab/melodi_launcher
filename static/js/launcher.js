import { createApp, MelodiRouter, MelodiStore } from "./index.js";

window.apiRequest = async function (url, options = {}) {
    const config = { ...options };
    if (typeof config.body === "string" && (config.headers || {})["Content-Type"] === "application/json") {
        config.body = JSON.parse(config.body);
    }

    const data = await window.melodi.api.request(url, config);
    return { json: async () => data };
};

const pageRoutes = [
    { path: "/", url: "/", factory: "dashboardComponent", title: "Tableau de bord" },
    { path: "/servers", url: "/servers", factory: "serversComponent", title: "Serveurs" },
    { path: "/services", url: "/services", factory: "servicesComponent", title: "Services" },
    { path: "/installation", url: "/installation", factory: "installationComponent", title: "Installations" },
    { path: "/logs", url: "/logs", factory: "logsComponent", title: "Journaux" },
    { path: "/settings", url: "/settings", factory: "settingsComponent", title: "Paramètres" },
    ...["melodi", "melodi_websocket", "melodi_process_manager", "postgresql", "redis", "pgadmin"].map((service) => ({
        path: `/installation/${service}`,
        url: `/installation/${service}`,
        factory: "serviceInstallComponent",
        argument: service,
        title: `Installation ${service}`
    }))
];

function routeComponent(template, factoryName, argument) {
    const definition = window[factoryName](argument);
    const methods = {};
    const data = { __intervals: [] };
    let initialize = null;

    for (const [key, value] of Object.entries(definition)) {
        if (typeof value !== "function") {
            data[key] = value;
        } else if (key === "init") {
            initialize = value;
        } else {
            methods[key] = value;
        }
    }

    return {
        delimiters: ["[[", "]]"],
        template,
        data() {
            return { ...data, __intervals: [] };
        },
        methods,
        hooks: {
            mounted() {
                if (initialize) initialize.call(this);
            },
            unmounted() {
                this.__intervals.forEach((timer) => clearInterval(timer));
                if (this.timer) clearInterval(this.timer);
            }
        }
    };
}

async function loadRoute(route) {
    const response = await window.melodi.api.get(`${route.url}?partial=1`, {
        cache: { strategy: "network-first", ttl: 24 * 60 * 60 * 1000 }
    });
    const document = new DOMParser().parseFromString(response, "text/html");
    const view = document.querySelector("[data-melodi-component]");
    if (!view) throw new Error(`Missing page component in partial view '${route.url}'.`);

    return {
        path: route.path,
        component: routeComponent(view.outerHTML, route.factory, route.argument)
    };
}

window.addEventListener("DOMContentLoaded", async () => {
    try {
        const loadedRoutes = await Promise.all(pageRoutes.map(loadRoute));
        const store = new MelodiStore({
            state: () => ({
                activeServerId: localStorage.getItem("melodi_active_server_id") || "local",
                servers: []
            })
        });
        const router = new MelodiRouter({ routes: loadedRoutes, mode: "history" });
        const state = window.globalApp();
        const methods = {};
        const initialData = {};

        for (const [key, value] of Object.entries(state)) {
            if (typeof value === "function") methods[key] = value;
            else initialData[key] = value;
        }

        initialData.pageTitle = window.LAUNCHER_INITIAL_TITLE || "MELODI Control Center";
        initialData.installPromptAvailable = false;
        methods.isActiveRoute = function (path) {
            const current = router.currentRoute();
            return path === "/installation"
                ? current === path || current.startsWith("/installation/")
                : current === path;
        };
        methods.navigateTo = function (path) {
            this.mobileMenuOpen = false;
            router.push(path);
        };
        methods.installPWA = async function () {
            if (!window.__melodiInstallPrompt) return;
            window.__melodiInstallPrompt.prompt();
            await window.__melodiInstallPrompt.userChoice;
            window.__melodiInstallPrompt = null;
            this.installPromptAvailable = false;
        };

        router.beforeEach((to, from, next) => {
            const route = pageRoutes.find((item) => item.path === to);
            if (route && window.__melodiLauncherState) {
                window.__melodiLauncherState.pageTitle = route.title;
                document.title = `${route.title} - MELODI Control Center`;
            }
            next();
        });

        const app = createApp({
            delimiters: ["[[", "]]"],
            data() {
                return initialData;
            },
            methods,
            hooks: {
                mounted() {
                    window.__melodiLauncherState = this;
                    if (methods.init) methods.init.call(this);

                    window.addEventListener("beforeinstallprompt", (event) => {
                        event.preventDefault();
                        window.__melodiInstallPrompt = event;
                        this.installPromptAvailable = true;
                    });
                    window.addEventListener("appinstalled", () => {
                        window.__melodiInstallPrompt = null;
                        this.installPromptAvailable = false;
                    });

                    if ("serviceWorker" in navigator) {
                        navigator.serviceWorker.register("/service-worker.js")
                            .catch((error) => console.error("Service worker registration failed:", error));
                    }

                    document.addEventListener("click", (event) => {
                        const link = event.target.closest("a[href]");
                        if (!link || link.target || event.defaultPrevented) return;
                        const destination = new URL(link.href, window.location.href);
                        if (destination.origin !== window.location.origin) return;
                        const destinationPath = `${destination.pathname}${destination.search}`;
                        if (!pageRoutes.some((route) => route.path === destinationPath || route.path === destination.pathname)) return;
                        event.preventDefault();
                        router.push(destinationPath);
                    });
                }
            }
        });

        app.use(store);
        app.use(router);
        await app.mount(document.body);
        const activeRoute = pageRoutes.find((route) => route.path === router.currentRoute());
        if (activeRoute && document.body.__melodijs_root) {
            document.body.__melodijs_root.state.pageTitle = activeRoute.title;
            document.title = `${activeRoute.title} - MELODI Control Center`;
        }
        document.querySelectorAll("[data-melodi-cloak]").forEach((element) => {
            element.removeAttribute("data-melodi-cloak");
        });
    } catch (error) {
        console.error("MELODI Launcher failed to start:", error);
    }
});
