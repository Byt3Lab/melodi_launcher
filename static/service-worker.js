const CACHE_NAME = "melodi-launcher-v2";
const APP_SHELL = [
    "/",
    "/static/manifest.webmanifest",
    "/static/css/custom.css",
    "/static/images/icon.png",
    "/static/js/api.js",
    "/static/js/index.js",
    "/static/js/launcher.js",
    "/static/js/melodijs.js",
    "/static/js/router.js",
    "/static/js/store.js",
    "/static/js/views/global.js",
    "/static/js/views/dashboard.js",
    "/static/js/views/servers.js",
    "/static/js/views/services.js",
    "/static/js/views/installation.js",
    "/static/js/views/service_installation.js",
    "/static/js/views/logs.js",
    "/static/js/views/settings.js",
    "/?partial=1",
    "/servers?partial=1",
    "/services?partial=1",
    "/installation?partial=1",
    "/installation/melodi?partial=1",
    "/installation/melodi_websocket?partial=1",
    "/installation/melodi_process_manager?partial=1",
    "/installation/postgresql?partial=1",
    "/installation/redis?partial=1",
    "/installation/pgadmin?partial=1",
    "/logs?partial=1",
    "/settings?partial=1"
];

self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => cache.addAll(APP_SHELL))
            .then(() => self.skipWaiting())
    );
});

self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches.keys()
            .then((keys) => Promise.all(
                keys.filter((key) => key.startsWith("melodi-launcher-") && key !== CACHE_NAME)
                    .map((key) => caches.delete(key))
            ))
            .then(() => self.clients.claim())
    );
});

self.addEventListener("fetch", (event) => {
    const request = event.request;
    const url = new URL(request.url);
    if (request.method !== "GET" || url.origin !== self.location.origin || url.pathname.startsWith("/api/")) return;

    if (request.mode === "navigate") {
        event.respondWith(
            fetch(request)
                .then((response) => {
                    if (response.ok) {
                        const copy = response.clone();
                        caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
                    }
                    return response;
                })
                .catch(async () => (await caches.match(request)) || (await caches.match("/")))
        );
        return;
    }

    event.respondWith(
        caches.match(request).then((cached) => cached || fetch(request).then((response) => {
            if (response.ok) {
                const copy = response.clone();
                caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
            }
            return response;
        }))
    );
});
