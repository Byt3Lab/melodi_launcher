/**
 * MELODI ERP — Universal Frontend API Client, Cache Engine & Skeleton Toolkit
 * 
 * Provides:
 * 1. window.melodi.api (Universal fetch client, REST helpers, deduplication, auto-headers, toasts)
 * 2. window.melodi.cache (Configurable cache with Memory/Session/Local storage, SWR, TTL, Tag invalidation)
 * 3. window.melodi.skeleton (Pre-composed skeletons generator and loading state wrapper)
 */
(function (global) {
    'use strict';

    /* ═══════════════════════════════════════════════════════════════════════════
       1. MELODI API ERROR
       ═══════════════════════════════════════════════════════════════════════════ */
    class MelodiAPIError extends Error {
        constructor(message, options = {}) {
            super(message);
            this.name = 'MelodiAPIError';
            this.status = options.status || 500;
            this.code = options.code || 'API_ERROR';
            this.details = options.details || null;
            this.response = options.response || null;
            this.data = options.data || null;
        }
    }

    /* ═══════════════════════════════════════════════════════════════════════════
       2. MELODI CLIENT CACHE ENGINE
       ═══════════════════════════════════════════════════════════════════════════ */
    class MelodiCache {
        constructor(options = {}) {
            this.prefix = options.prefix || 'ml_cache_';
            this.memoryStore = new Map();
            this.customAdapters = new Map();
            this.defaultTTL = options.defaultTTL || 60000; // 1 minute default
            this.statsData = { hits: 0, misses: 0, writes: 0 };
        }

        /**
         * Register a custom storage adapter (e.g. IndexedDB, local store)
         */
        registerAdapter(name, adapter) {
            if (!adapter || typeof adapter.get !== 'function' || typeof adapter.set !== 'function') {
                throw new Error(`Invalid cache adapter '${name}': must implement get, set, delete, clear`);
            }
            this.customAdapters.set(name, adapter);
        }

        _getStorage(driver) {
            if (driver === 'session' && typeof window !== 'undefined' && window.sessionStorage) {
                return window.sessionStorage;
            }
            if (driver === 'local' && typeof window !== 'undefined' && window.localStorage) {
                return window.localStorage;
            }
            if (this.customAdapters.has(driver)) {
                return this.customAdapters.get(driver);
            }
            return null; // Fallback to memory
        }

        _serializeKey(key) {
            return `${this.prefix}${key}`;
        }

        /**
         * Retrieve an item from the cache
         */
        async get(key, storageDriver = 'memory') {
            const storage = this._getStorage(storageDriver);
            let entry = null;

            if (!storage) {
                entry = this.memoryStore.get(key);
            } else if (typeof storage.getItem === 'function') {
                const raw = storage.getItem(this._serializeKey(key));
                if (raw) {
                    try {
                        entry = JSON.parse(raw);
                    } catch (e) {
                        entry = null;
                    }
                }
            } else if (typeof storage.get === 'function') {
                entry = await storage.get(key);
            }

            if (!entry) {
                this.statsData.misses++;
                return null;
            }

            // Verify TTL
            const now = Date.now();
            if (entry.expiresAt && now > entry.expiresAt) {
                await this.delete(key, storageDriver);
                this.statsData.misses++;
                return null;
            }

            this.statsData.hits++;
            return entry.data;
        }

        /**
         * Store an item in the cache with options
         */
        async set(key, data, options = {}) {
            const ttl = typeof options.ttl === 'number' ? options.ttl : this.defaultTTL;
            const storageDriver = options.storage || 'memory';
            const tags = Array.isArray(options.tags) ? options.tags : [];
            const now = Date.now();

            const entry = {
                data: data,
                createdAt: now,
                expiresAt: ttl > 0 ? now + ttl : null,
                tags: tags
            };

            const storage = this._getStorage(storageDriver);

            if (!storage) {
                this.memoryStore.set(key, entry);
            } else if (typeof storage.setItem === 'function') {
                try {
                    storage.setItem(this._serializeKey(key), JSON.stringify(entry));
                } catch (e) {
                    console.warn(`[MelodiCache] Storage quota exceeded for ${storageDriver}:`, e);
                }
            } else if (typeof storage.set === 'function') {
                await storage.set(key, entry);
            }

            this.statsData.writes++;
            return data;
        }

        /**
         * Delete a specific cache key
         */
        async delete(key, storageDriver = 'all') {
            const drivers = storageDriver === 'all' ? ['memory', 'session', 'local', ...this.customAdapters.keys()] : [storageDriver];

            for (const driver of drivers) {
                const storage = this._getStorage(driver);
                if (!storage) {
                    this.memoryStore.delete(key);
                } else if (typeof storage.removeItem === 'function') {
                    storage.removeItem(this._serializeKey(key));
                } else if (typeof storage.delete === 'function') {
                    await storage.delete(key);
                }
            }
        }

        /**
         * Invalidate cache entries by tag
         */
        async invalidateTag(tag) {
            if (!tag) return;

            // 1. Memory store
            for (const [key, entry] of this.memoryStore.entries()) {
                if (entry && Array.isArray(entry.tags) && entry.tags.includes(tag)) {
                    this.memoryStore.delete(key);
                }
            }

            // 2. Web Storages (sessionStorage & localStorage)
            const webStorages = [
                typeof window !== 'undefined' ? window.sessionStorage : null,
                typeof window !== 'undefined' ? window.localStorage : null
            ].filter(Boolean);

            for (const store of webStorages) {
                const keysToRemove = [];
                for (let i = 0; i < store.length; i++) {
                    const fullKey = store.key(i);
                    if (fullKey && fullKey.startsWith(this.prefix)) {
                        try {
                            const entry = JSON.parse(store.getItem(fullKey));
                            if (entry && Array.isArray(entry.tags) && entry.tags.includes(tag)) {
                                keysToRemove.push(fullKey);
                            }
                        } catch (e) {}
                    }
                }
                keysToRemove.forEach(k => store.removeItem(k));
            }
        }

        /**
         * Invalidate cache entries by URL pattern (wildcard, e.g. /api/orders*)
         */
        async invalidatePattern(pattern) {
            if (!pattern) return;
            const regex = new RegExp('^' + pattern.replace(/\*/g, '.*') + '$');

            // 1. Memory store
            for (const key of this.memoryStore.keys()) {
                if (regex.test(key)) {
                    this.memoryStore.delete(key);
                }
            }

            // 2. Web Storages
            const webStorages = [
                typeof window !== 'undefined' ? window.sessionStorage : null,
                typeof window !== 'undefined' ? window.localStorage : null
            ].filter(Boolean);

            for (const store of webStorages) {
                const keysToRemove = [];
                for (let i = 0; i < store.length; i++) {
                    const fullKey = store.key(i);
                    if (fullKey && fullKey.startsWith(this.prefix)) {
                        const rawKey = fullKey.substring(this.prefix.length);
                        if (regex.test(rawKey)) {
                            keysToRemove.push(fullKey);
                        }
                    }
                }
                keysToRemove.forEach(k => store.removeItem(k));
            }
        }

        /**
         * Clear all cached data
         */
        async clear(storageDriver = 'all') {
            if (storageDriver === 'all' || storageDriver === 'memory') {
                this.memoryStore.clear();
            }

            if (typeof window !== 'undefined') {
                if ((storageDriver === 'all' || storageDriver === 'session') && window.sessionStorage) {
                    this._clearWebStorage(window.sessionStorage);
                }
                if ((storageDriver === 'all' || storageDriver === 'local') && window.localStorage) {
                    this._clearWebStorage(window.localStorage);
                }
            }

            for (const [name, adapter] of this.customAdapters.entries()) {
                if ((storageDriver === 'all' || storageDriver === name) && typeof adapter.clear === 'function') {
                    await adapter.clear();
                }
            }
        }

        _clearWebStorage(store) {
            const keysToRemove = [];
            for (let i = 0; i < store.length; i++) {
                const k = store.key(i);
                if (k && k.startsWith(this.prefix)) {
                    keysToRemove.push(k);
                }
            }
            keysToRemove.forEach(k => store.removeItem(k));
        }

        /**
         * Return cache usage statistics
         */
        stats() {
            return {
                ...this.statsData,
                memoryEntries: this.memoryStore.size,
                hitRate: this.statsData.hits + this.statsData.misses > 0
                    ? ((this.statsData.hits / (this.statsData.hits + this.statsData.misses)) * 100).toFixed(1) + '%'
                    : '0%'
            };
        }
    }

    /* ═══════════════════════════════════════════════════════════════════════════
       3. MELODI UNIVERSAL API CLIENT
       ═══════════════════════════════════════════════════════════════════════════ */
    class MelodiAPI {
        constructor(config = {}) {
            this.baseURL = config.baseURL || '';
            this.defaultTimeout = config.defaultTimeout || 30000;
            this.cache = config.cache || new MelodiCache();
            this.inFlightRequests = new Map(); // For request deduplication

            this.interceptors = {
                request: [],
                response: []
            };
        }

        /**
         * Helper to serialize object into query string
         */
        serializeParams(params) {
            if (!params) return '';
            const searchParams = new URLSearchParams();

            const appendValue = (key, value) => {
                if (value === null || value === undefined) return;
                if (Array.isArray(value)) {
                    value.forEach(item => appendValue(`${key}[]`, item));
                } else if (typeof value === 'object') {
                    searchParams.append(key, JSON.stringify(value));
                } else {
                    searchParams.append(key, String(value));
                }
            };

            for (const [key, val] of Object.entries(params)) {
                appendValue(key, val);
            }

            const str = searchParams.toString();
            return str ? `?${str}` : '';
        }

        /**
         * Extract CSRF Token from meta tag or cookie
         */
        getCSRFToken() {
            if (typeof document === 'undefined') return null;
            const meta = document.querySelector('meta[name="csrf-token"]');
            if (meta && meta.content) return meta.content;

            const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]+)/);
            return match ? decodeURIComponent(match[1]) : null;
        }

        /**
         * Extract Bearer JWT token if stored
         */
        getBearerToken() {
            if (typeof window === 'undefined') return null;
            try {
                return window.localStorage.getItem('melodi_token') ||
                       window.sessionStorage.getItem('melodi_token') ||
                       null;
            } catch (e) {
                return null;
            }
        }

        /**
         * Display a Design System Toast notification if available
         */
        notify(message, variant = 'info', title = '') {
            if (typeof window === 'undefined') return;
            if (typeof window.showDsToast === 'function') {
                window.showDsToast(message, variant, title);
            } else if (window.melodi && window.melodi.Toast && typeof window.melodi.Toast.notify === 'function') {
                window.melodi.Toast.notify({ message, variant, title });
            } else {
                console.log(`[Notification ${variant.toUpperCase()}] ${title ? title + ': ' : ''}${message}`);
            }
        }

        /**
         * Core Request Method
         */
        async request(endpoint, options = {}) {
            let config = { ...options };
            config.method = (config.method || 'GET').toUpperCase();
            config.headers = { ...config.headers };

            // Apply base URL & query params
            let url = endpoint;
            if (!url.startsWith('http://') && !url.startsWith('https://')) {
                url = `${this.baseURL}${url}`;
            }
            if (config.params) {
                const queryStr = this.serializeParams(config.params);
                url += (url.includes('?') ? '&' : '') + queryStr.replace(/^\?/, '');
            }

            // Run Request Interceptors
            for (const interceptor of this.interceptors.request) {
                if (typeof interceptor === 'function') {
                    config = (await interceptor(config)) || config;
                }
            }

            // Prepare Headers
            if (!config.headers['Accept']) {
                config.headers['Accept'] = 'application/json';
            }
            if (!config.headers['X-Requested-With']) {
                config.headers['X-Requested-With'] = 'XMLHttpRequest';
            }

            const csrfToken = this.getCSRFToken();
            if (csrfToken && !config.headers['X-CSRF-Token']) {
                config.headers['X-CSRF-Token'] = csrfToken;
            }

            const bearerToken = this.getBearerToken();
            if (bearerToken && !config.headers['Authorization']) {
                config.headers['Authorization'] = `Bearer ${bearerToken}`;
            }

            // Body serialization
            if (config.body && typeof config.body === 'object') {
                const isSpecialBody = (typeof FormData !== 'undefined' && config.body instanceof FormData) ||
                                      (typeof Blob !== 'undefined' && config.body instanceof Blob) ||
                                      (typeof URLSearchParams !== 'undefined' && config.body instanceof URLSearchParams);

                if (!isSpecialBody) {
                    if (!config.headers['Content-Type']) {
                        config.headers['Content-Type'] = 'application/json';
                    }
                    config.body = JSON.stringify(config.body);
                }
            }

            config.credentials = config.credentials || 'same-origin';

            // ── Cache & In-Flight Deduplication Handling (for GET requests) ──
            const isGet = config.method === 'GET';
            const cacheOptions = config.cache === true ? {} : (config.cache || null);
            const cacheKey = config.cacheKey || url;

            if (isGet && cacheOptions) {
                const strategy = cacheOptions.strategy || 'stale-while-revalidate';
                const storageDriver = cacheOptions.storage || 'memory';

                // Check cache
                const cachedData = await this.cache.get(cacheKey, storageDriver);

                // Strategy 1: Cache-First
                if (strategy === 'cache-first' && cachedData !== null) {
                    return cachedData;
                }

                // Strategy 2: Stale-While-Revalidate
                if (strategy === 'stale-while-revalidate' && cachedData !== null) {
                    // Trigger background revalidation
                    this._executeFetchWithDeduplication(url, config, cacheKey, cacheOptions)
                        .then(freshData => {
                            if (typeof cacheOptions.onUpdate === 'function') {
                                try {
                                    // Only notify if data changed
                                    if (JSON.stringify(freshData) !== JSON.stringify(cachedData)) {
                                        cacheOptions.onUpdate(freshData);
                                    }
                                } catch (e) {
                                    cacheOptions.onUpdate(freshData);
                                }
                            }
                        })
                        .catch(err => console.debug('[MelodiAPI] SWR background revalidation error:', err));

                    // Return stale cached data immediately (0ms)
                    return cachedData;
                }
            }

            // Normal fetch with deduplication
            return this._executeFetchWithDeduplication(url, config, cacheKey, cacheOptions);
        }

        async _executeFetchWithDeduplication(url, config, cacheKey, cacheOptions) {
            const isGet = config.method === 'GET';

            // Deduplicate concurrent in-flight GET requests
            if (isGet && this.inFlightRequests.has(cacheKey)) {
                return this.inFlightRequests.get(cacheKey);
            }

            const fetchPromise = this._executeRawFetch(url, config, cacheKey, cacheOptions);

            if (isGet) {
                this.inFlightRequests.set(cacheKey, fetchPromise);
                const cleanup = () => this.inFlightRequests.delete(cacheKey);
                fetchPromise.then(cleanup, cleanup);
            }

            return fetchPromise;
        }

        async _executeRawFetch(url, config, cacheKey, cacheOptions) {
            // Setup Timeout via AbortController
            const timeout = config.timeout || this.defaultTimeout;
            let timeoutId = null;
            let controller = null;

            // Prepare native fetch configuration.
            // In the Fetch API, 'cache' must be a valid RequestCache enum string ('default', 'no-store', etc.).
            // Custom Melodi cache objects (e.g. { ttl, strategy }) must NOT be passed to native fetch.
            const nativeConfig = { ...config };
            const validFetchCacheEnums = ['default', 'no-store', 'reload', 'no-cache', 'force-cache', 'only-if-cached'];
            if (!validFetchCacheEnums.includes(nativeConfig.cache)) {
                delete nativeConfig.cache;
            }

            if (!nativeConfig.signal && timeout > 0) {
                controller = new AbortController();
                nativeConfig.signal = controller.signal;
                timeoutId = setTimeout(() => {
                    controller.abort();
                }, timeout);
            }

            try {
                const response = await fetch(url, nativeConfig);

                if (timeoutId) clearTimeout(timeoutId);

                // Parse content
                let responseData;
                const contentType = response.headers.get('content-type') || '';
                if (contentType.includes('application/json')) {
                    responseData = await response.json();
                } else {
                    responseData = await response.text();
                }

                // Run Response Interceptors
                for (const interceptor of this.interceptors.response) {
                    if (typeof interceptor === 'function') {
                        responseData = (await interceptor(responseData, response)) || responseData;
                    }
                }

                // Check HTTP & Melodi Success Contract
                const isMelodiError = responseData && typeof responseData === 'object' && responseData.success === false;

                if (!response.ok || isMelodiError) {
                    const errorMsg = (responseData && responseData.error && responseData.error.message) ||
                                     (responseData && responseData.message) ||
                                     `Request failed with status ${response.status}`;
                    const errorCode = (responseData && responseData.error && responseData.error.code) || 'REQUEST_FAILED';
                    const errorDetails = (responseData && responseData.error && responseData.error.details) || null;

                    const apiError = new MelodiAPIError(errorMsg, {
                        status: response.status,
                        code: errorCode,
                        details: errorDetails,
                        response: response,
                        data: responseData
                    });

                    // Trigger toast notification if requested
                    if (config.notifyOnError !== false) {
                        this.notify(errorMsg, 'danger', 'Erreur');
                    }

                    throw apiError;
                }

                // If cache options are active, store response
                if (config.method === 'GET' && cacheOptions) {
                    await this.cache.set(cacheKey, responseData, cacheOptions);
                }

                // Automatic cache invalidation on state-mutating requests (POST, PUT, PATCH, DELETE)
                if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(config.method)) {
                    // Extract base resource URL (e.g. /api/orders/123 -> /api/orders*)
                    const cleanUrl = url.split('?')[0];
                    const segments = cleanUrl.split('/').filter(Boolean);
                    if (segments.length >= 2) {
                        const resourcePattern = `/${segments.slice(0, 2).join('/')}*`;
                        this.cache.invalidatePattern(resourcePattern);
                    }

                    // Invalidate specified tags
                    if (Array.isArray(config.invalidateTags)) {
                        for (const tag of config.invalidateTags) {
                            await this.cache.invalidateTag(tag);
                        }
                    }
                }

                // Success notification if requested
                if (config.notifyOnSuccess) {
                    const msg = typeof config.notifyOnSuccess === 'string'
                        ? config.notifyOnSuccess
                        : (responseData.message || 'Opération réussie !');
                    this.notify(msg, 'success', 'Succès');
                }

                return responseData;

            } catch (err) {
                if (timeoutId) clearTimeout(timeoutId);

                if (err.name === 'AbortError') {
                    const timeoutErr = new MelodiAPIError(`Request timed out after ${timeout}ms`, {
                        status: 408,
                        code: 'TIMEOUT'
                    });
                    if (config.notifyOnError !== false) {
                        this.notify('La requête a expiré (délai dépassé).', 'danger', 'Timeout');
                    }
                    throw timeoutErr;
                }

                // Network-first fallback
                if (config.method === 'GET' && cacheOptions && cacheOptions.strategy === 'network-first') {
                    const fallbackData = await this.cache.get(cacheKey, cacheOptions.storage || 'memory');
                    if (fallbackData !== null) {
                        console.warn('[MelodiAPI] Network failed, serving from network-first cache fallback:', err);
                        return fallbackData;
                    }
                }

                throw err;
            }
        }

        /* ── REST Method Shortcuts ────────────────────────────────────────── */
        get(url, options = {}) {
            return this.request(url, { ...options, method: 'GET' });
        }

        post(url, body = null, options = {}) {
            return this.request(url, { ...options, method: 'POST', body });
        }

        put(url, body = null, options = {}) {
            return this.request(url, { ...options, method: 'PUT', body });
        }

        patch(url, body = null, options = {}) {
            return this.request(url, { ...options, method: 'PATCH', body });
        }

        delete(url, options = {}) {
            return this.request(url, { ...options, method: 'DELETE' });
        }

        upload(url, formData, options = {}) {
            return this.request(url, {
                ...options,
                method: 'POST',
                body: formData
            });
        }
    }

    /* ═══════════════════════════════════════════════════════════════════════════
       4. MELODI SKELETON GENERATOR & CONTAINER TRANSITION TOOLKIT
       ═══════════════════════════════════════════════════════════════════════════ */
    class MelodiSkeleton {
        constructor() {}

        /**
         * Generate a table skeleton HTML string
         */
        table(options = {}) {
            const rows = options.rows || 5;
            const cols = options.cols || 4;
            const className = options.className || '';

            let theadThs = '';
            for (let c = 0; c < cols; c++) {
                theadThs += `<th><div class="ds-skeleton ds-skeleton-text ds-skeleton--w-50"></div></th>`;
            }

            let tbodyRows = '';
            for (let r = 0; r < rows; r++) {
                let tds = '';
                for (let c = 0; c < cols; c++) {
                    const widthClass = c === 0 ? 'ds-skeleton--w-75' : (c === cols - 1 ? 'ds-skeleton--w-33' : 'ds-skeleton--w-66');
                    tds += `<td><div class="ds-skeleton ds-skeleton-text ${widthClass}"></div></td>`;
                }
                tbodyRows += `<tr>${tds}</tr>`;
            }

            return `
                <table class="ds-skeleton-table ${className}" aria-hidden="true">
                    <thead><tr>${theadThs}</tr></thead>
                    <tbody>${tbodyRows}</tbody>
                </table>
            `;
        }

        /**
         * Generate a card skeleton HTML string
         */
        card(options = {}) {
            const className = options.className || '';
            const withImage = options.withImage || false;

            return `
                <div class="ds-skeleton-card ${className}" aria-hidden="true">
                    ${withImage ? '<div class="ds-skeleton ds-skeleton-thumbnail"></div>' : ''}
                    <div class="ds-skeleton-card__header">
                        <div class="ds-skeleton ds-skeleton-avatar ds-skeleton-avatar-md"></div>
                        <div style="flex: 1;">
                            <div class="ds-skeleton ds-skeleton-title" style="margin-bottom: 0.35rem;"></div>
                            <div class="ds-skeleton ds-skeleton-subtitle" style="margin-bottom: 0;"></div>
                        </div>
                    </div>
                    <div class="ds-skeleton-card__body">
                        <div class="ds-skeleton ds-skeleton-text ds-skeleton--w-100"></div>
                        <div class="ds-skeleton ds-skeleton-text ds-skeleton--w-75"></div>
                        <div class="ds-skeleton ds-skeleton-text ds-skeleton--w-50"></div>
                    </div>
                    <div class="ds-skeleton-card__footer">
                        <div class="ds-skeleton ds-skeleton-button"></div>
                    </div>
                </div>
            `;
        }

        /**
         * Generate a list skeleton HTML string
         */
        list(options = {}) {
            const items = options.items || 4;
            const className = options.className || '';

            let html = `<div class="ds-skeleton-list ${className}" aria-hidden="true">`;
            for (let i = 0; i < items; i++) {
                html += `
                    <div class="ds-skeleton-list-item">
                        <div class="ds-skeleton ds-skeleton-avatar ds-skeleton-avatar-sm"></div>
                        <div class="ds-skeleton-list-item__content">
                            <div class="ds-skeleton ds-skeleton-text ds-skeleton--w-50"></div>
                            <div class="ds-skeleton ds-skeleton-text ds-skeleton--w-33"></div>
                        </div>
                        <div class="ds-skeleton ds-skeleton-badge"></div>
                    </div>
                `;
            }
            html += `</div>`;
            return html;
        }

        /**
         * Generate a form skeleton HTML string
         */
        form(options = {}) {
            const fields = options.fields || 3;
            const className = options.className || '';

            let html = `<div class="ds-skeleton-form ${className}" aria-hidden="true">`;
            for (let i = 0; i < fields; i++) {
                html += `
                    <div class="ds-skeleton-form__field">
                        <div class="ds-skeleton ds-skeleton-text ds-skeleton--w-25"></div>
                        <div class="ds-skeleton ds-skeleton-input"></div>
                    </div>
                `;
            }
            html += `
                <div style="margin-top: 1rem; display: flex; gap: 0.5rem; justify-content: flex-end;">
                    <div class="ds-skeleton ds-skeleton-button ds-skeleton--w-25"></div>
                </div>
            </div>`;
            return html;
        }

        /**
         * Generate a KPI stat card skeleton HTML string
         */
        stat(options = {}) {
            const className = options.className || '';
            return `
                <div class="ds-skeleton-stat ${className}" aria-hidden="true">
                    <div class="ds-skeleton-stat__top">
                        <div class="ds-skeleton ds-skeleton-text ds-skeleton--w-50"></div>
                        <div class="ds-skeleton ds-skeleton-avatar ds-skeleton-avatar-sm"></div>
                    </div>
                    <div class="ds-skeleton ds-skeleton-stat__number"></div>
                    <div class="ds-skeleton ds-skeleton-text ds-skeleton--w-33"></div>
                </div>
            `;
        }

        /**
         * Wrap an asynchronous operation with automatic skeleton loading & transition
         * 
         * @param {string|HTMLElement} containerOrSelector
         * @param {Function} asyncCallback
         * @param {Object} options
         */
        async wrap(containerOrSelector, asyncCallback, options = {}) {
            const container = typeof containerOrSelector === 'string'
                ? document.querySelector(containerOrSelector)
                : containerOrSelector;

            if (!container) {
                console.warn('[MelodiSkeleton.wrap] Container not found:', containerOrSelector);
                return await asyncCallback();
            }

            container.classList.add('ds-loading-wrapper');
            container.classList.add('is-loading');
            container.setAttribute('data-loading', 'true');

            // Find or inject skeleton container
            let skeletonEl = container.querySelector('.ds-skeleton-target');
            let contentEl = container.querySelector('.ds-content-target');

            if (!skeletonEl && options.preset) {
                skeletonEl = document.createElement('div');
                skeletonEl.className = 'ds-skeleton-target';
                if (typeof this[options.preset] === 'function') {
                    skeletonEl.innerHTML = this[options.preset](options);
                }
                container.prepend(skeletonEl);
            }

            try {
                const result = await asyncCallback();
                return result;
            } finally {
                container.classList.remove('is-loading');
                container.removeAttribute('data-loading');
                if (skeletonEl && options.removeSkeletonOnComplete) {
                    skeletonEl.remove();
                }
            }
        }
    }

    /* ═══════════════════════════════════════════════════════════════════════════
       5. INSTANTIATION & GLOBAL EXPORTS
       ═══════════════════════════════════════════════════════════════════════════ */
    const defaultCache = new MelodiCache();
    const defaultApi = new MelodiAPI({ cache: defaultCache });
    const defaultSkeleton = new MelodiSkeleton();

    // Export Classes
    global.MelodiAPIError = MelodiAPIError;
    global.MelodiCache = MelodiCache;
    global.MelodiAPI = MelodiAPI;
    global.MelodiSkeleton = MelodiSkeleton;

    // Attach to window.melodi and window.mljs namespaces
    global.melodi = global.melodi || {};
    global.melodi.api = defaultApi;
    global.melodi.cache = defaultCache;
    global.melodi.skeleton = defaultSkeleton;

    global.mljs = global.mljs || {};
    global.mljs.api = defaultApi;
    global.mljs.cache = defaultCache;
    global.mljs.skeleton = defaultSkeleton;

})(typeof window !== 'undefined' ? window : this);
