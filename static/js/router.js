var __assign = (this && this.__assign) || function () {
    __assign = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign.apply(this, arguments);
};
var __read = (this && this.__read) || function (o, n) {
    var m = typeof Symbol === "function" && o[Symbol.iterator];
    if (!m) return o;
    var i = m.call(o), r, ar = [], e;
    try {
        while ((n === void 0 || n-- > 0) && !(r = i.next()).done) ar.push(r.value);
    }
    catch (error) { e = { error: error }; }
    finally {
        try {
            if (r && !r.done && (m = i["return"])) m.call(i);
        }
        finally { if (e) throw e.error; }
    }
    return ar;
};
var __values = (this && this.__values) || function(o) {
    var s = typeof Symbol === "function" && Symbol.iterator, m = s && o[s], i = 0;
    if (m) return m.call(o);
    if (o && typeof o.length === "number") return {
        next: function () {
            if (o && i >= o.length) o = void 0;
            return { value: o && o[i++], done: !o };
        }
    };
    throw new TypeError(s ? "Object is not iterable." : "Symbol.iterator is not defined.");
};
import { Component } from './melodijs.js';
var MelodiRouter = /** @class */ (function () {
    function MelodiRouter(options) {
        this.beforeEachHook = null;
        this.routes = options.routes;
        this.mode = options.mode || 'hash'; // Default to hash mode
        this.currentRoute = null;
        this.setRoute = null;
        this.params = null;
        this.setParams = null;
        this.query = null;
        this.setQuery = null;
        this.matched = null;
        this.setMatched = null;
    }
    MelodiRouter.prototype.beforeEach = function (hook) {
        this.beforeEachHook = hook;
    };
    MelodiRouter.prototype.install = function (app) {
        var _this = this;
        // Create reactive signals
        var _a = __read(app.reactivity.createSignal(this._getCurrentPath()), 2), readRoute = _a[0], writeRoute = _a[1];
        var _b = __read(app.reactivity.createSignal({}), 2), readParams = _b[0], writeParams = _b[1];
        var _c = __read(app.reactivity.createSignal({}), 2), readQuery = _c[0], writeQuery = _c[1];
        var _d = __read(app.reactivity.createSignal([]), 2), readMatched = _d[0], writeMatched = _d[1];
        this.currentRoute = readRoute;
        this.setRoute = writeRoute;
        this.params = readParams;
        this.setParams = writeParams;
        this.query = readQuery;
        this.setQuery = writeQuery;
        this.matched = readMatched;
        this.setMatched = writeMatched;
        // Listen to route changes based on mode
        if (this.mode === 'history') {
            window.addEventListener('popstate', function () {
                _this._handleRouteChange();
            });
        }
        else {
            window.addEventListener('hashchange', function () {
                _this._handleRouteChange();
            });
        }
        // Initial route
        this._handleRouteChange();
        // Register global components
        app.components['router-link'] = this._createRouterLink();
        app.components['router-view'] = this._createRouterView(app);
        // Expose router on app and make it available in components via $router
        app.router = this;
        // Add $router to component instances
        var originalMount = app.mount.bind(app);
        app.mount = function (target) {
            var result = originalMount(target);
            // Access root component and add $router
            var root = (typeof target === 'string' ? document.querySelector(target) : target);
            if (root && root.__melodijs_root) {
                var comp = root.__melodijs_root;
                if (comp.state) {
                    comp.state.$router = app.router;
                }
            }
            return result;
        };
    };
    MelodiRouter.prototype._getCurrentPath = function () {
        if (this.mode === 'history') {
            return window.location.pathname || '/';
        }
        var hash = window.location.hash.slice(1);
        return hash.split('?')[0] || '/';
    };
    MelodiRouter.prototype._getCurrentQuery = function () {
        var queryString;
        if (this.mode === 'history') {
            queryString = window.location.search.slice(1); // Remove leading '?'
        }
        else {
            var hash = window.location.hash.slice(1);
            queryString = hash.split('?')[1] || '';
        }
        if (!queryString)
            return {};
        var query = {};
        queryString.split('&').forEach(function (pair) {
            var _a = __read(pair.split('='), 2), key = _a[0], value = _a[1];
            if (key)
                query[decodeURIComponent(key)] = decodeURIComponent(value || '');
        });
        return query;
    };
    MelodiRouter.prototype.push = function (path) {
        if (this.mode === 'history') {
            window.history.pushState({}, '', path);
            this._handleRouteChange();
        }
        else {
            window.location.hash = path;
        }
    };
    MelodiRouter.prototype.replace = function (path) {
        if (this.mode === 'history') {
            window.history.replaceState({}, '', path);
            this._handleRouteChange();
        }
        else {
            var url = window.location.href.split('#')[0];
            window.location.replace(url + '#' + path);
        }
    };
    MelodiRouter.prototype._handleRouteChange = function () {
        var _this = this;
        var newPath = this._getCurrentPath();
        var oldPath = this.currentRoute ? this.currentRoute() : null;
        var next = function (redirectPath) {
            if (redirectPath) {
                _this.push(redirectPath);
                return;
            }
            // Proceed with navigation
            _this.setRoute(newPath);
            var _a = _this._matchRoute(newPath), matched = _a.matched, params = _a.params;
            _this.setMatched(matched);
            _this.setParams(params || {});
            _this.setQuery(_this._getCurrentQuery());
            // Scroll to top
            window.scrollTo(0, 0);
        };
        if (this.beforeEachHook) {
            this.beforeEachHook(newPath, oldPath, next);
        }
        else {
            next();
        }
    };
    MelodiRouter.prototype._matchRoute = function (path) {
        var _this = this;
        var matched = [];
        var params = {};
        var findMatch = function (routes, currentPath, parentPath) {
            var e_1, _a;
            if (parentPath === void 0) { parentPath = ''; }
            try {
                for (var routes_1 = __values(routes), routes_1_1 = routes_1.next(); !routes_1_1.done; routes_1_1 = routes_1.next()) {
                    var route = routes_1_1.value;
                    // Construct full path for this route
                    var fullPath = (parentPath + '/' + route.path).replace(/\/+/g, '/');
                    if (fullPath !== '/' && fullPath.endsWith('/'))
                        fullPath = fullPath.slice(0, -1);
                    // Check if this route matches the beginning of the current path
                    var routeParams = _this._extractParams(fullPath, currentPath, !!route.children);
                    if (routeParams !== null) {
                        matched.push(route);
                        params = __assign(__assign({}, params), routeParams);
                        if (route.children) {
                            // Continue matching children
                            // The remaining path for children is the currentPath itself, as we matched a prefix
                            // We need to ensure the child matching continues from the *currentPath* not a truncated one
                            // The `_extractParams` for children will handle the full path matching
                            if (findMatch(route.children, currentPath, fullPath)) {
                                return true;
                            }
                            else {
                                // If children didn't match, this route itself might be the final match
                                // But if it has children, it's usually meant to be a parent.
                                // For exact match, we need to check if currentPath is exactly fullPath
                                if (!route.children && fullPath === currentPath) {
                                    return true;
                                }
                                // If it has children but no child matched, and it's not an exact match for itself, backtrack
                                matched.pop();
                                // Remove params specific to this route if backtracking
                                for (var key in routeParams) {
                                    delete params[key];
                                }
                                continue; // Try next sibling route
                            }
                        }
                        // If no children, we found a match!
                        // The _extractParams check already ensured that the path matches the pattern (including params)
                        // and that the lengths are correct (unless partial match was requested, but here we are at a leaf).
                        return true;
                    }
                }
            }
            catch (e_1_1) { e_1 = { error: e_1_1 }; }
            finally {
                try {
                    if (routes_1_1 && !routes_1_1.done && (_a = routes_1.return)) _a.call(routes_1);
                }
                finally { if (e_1) throw e_1.error; }
            }
            return false;
        };
        findMatch(this.routes, path);
        console.log('Router Match:', path, matched);
        return { matched: matched, params: params };
    };
    MelodiRouter.prototype._extractParams = function (pattern, path, partial) {
        if (partial === void 0) { partial = false; }
        var patternParts = pattern.split('/').filter(function (p) { return p; });
        var pathParts = path.split('/').filter(function (p) { return p; });
        if (!partial && patternParts.length !== pathParts.length) {
            return null;
        }
        if (partial && pathParts.length < patternParts.length) {
            return null;
        }
        var params = {};
        for (var i = 0; i < patternParts.length; i++) {
            var patternPart = patternParts[i];
            var pathPart = pathParts[i];
            if (patternPart === '*') {
                params['pathMatch'] = '/' + pathParts.slice(i).join('/');
                return params;
            }
            if (patternPart.startsWith(':')) {
                var paramName = patternPart.slice(1);
                if (pathPart === undefined)
                    return null; // Path is shorter than pattern for a param
                params[paramName] = pathPart;
            }
            else if (patternPart !== pathPart) {
                return null;
            }
        }
        // If partial match, ensure the matched part is a prefix of the path
        if (partial && patternParts.length < pathParts.length) {
            // Check if the matched pattern is a prefix of the path
            var matchedPathSegment = pathParts.slice(0, patternParts.length).join('/');
            var fullPathSegment = patternParts.map(function (p, i) { return p.startsWith(':') ? pathParts[i] : p; }).join('/');
            if (matchedPathSegment !== fullPathSegment) {
                return null;
            }
        }
        else if (!partial && patternParts.length !== pathParts.length) {
            // If not partial, lengths must be exactly equal
            return null;
        }
        return params;
    };
    MelodiRouter.prototype._createRouterLink = function () {
        var router = this;
        return {
            props: ['to'],
            template: '<a :href="href" @click="navigate"><slot></slot></a>',
            computed: {
                href: function () {
                    if (router.mode === 'history') {
                        return this.to;
                    }
                    return '#' + this.to;
                }
            },
            methods: {
                navigate: function (e) {
                    if (router.mode === 'history') {
                        e.preventDefault();
                        router.push(this.to);
                    }
                    // In hash mode, default browser behavior handles navigation
                }
            }
        };
    };
    MelodiRouter.prototype._createRouterView = function (app) {
        var router = this;
        return {
            template: '<div class="router-view-container"></div>',
            hooks: {
                mounted: function () {
                    var state = this;
                    var el = state.__lastEl;
                    if (!el) {
                        console.error('router-view: Could not find element');
                        return;
                    }
                    var container = el.querySelector('.router-view-container');
                    if (!container) {
                        console.error('router-view: Could not find container');
                        return;
                    }
                    // Determine depth
                    var depth = 0;
                    var p = el.parentElement;
                    while (p) {
                        // Check if p has class router-view-container, then we are inside one.
                        if (p.classList.contains('router-view-container')) {
                            depth++;
                        }
                        p = p.parentElement;
                    }
                    console.log('RouterView mounted. Depth:', depth);
                    var currentComponent = null;
                    var currentWrapper = null;
                    // Create an effect that runs whenever matched routes change
                    app.reactivity.createEffect(function () {
                        var matched = router.matched();
                        console.log('RouterView update. Depth:', depth, 'Matched:', matched);
                        var route = matched[depth];
                        var transitionName = route ? route.transition : null;
                        // Function to mount new component
                        var mountNew = function (wrapper) {
                            if (route) {
                                try {
                                    var comp = new Component(route.component);
                                    comp.mount(wrapper, app);
                                    return comp;
                                }
                                catch (e) {
                                    console.error('Error mounting route component:', e);
                                    wrapper.innerHTML = '<div>Error loading component</div>';
                                    return null;
                                }
                            }
                            return null;
                        };
                        if (transitionName) {
                            // --- Transition Logic ---
                            // 1. Prepare new component
                            var newWrapper_1 = document.createElement('div');
                            newWrapper_1.className = "route-wrapper";
                            // Add enter classes
                            newWrapper_1.classList.add("".concat(transitionName, "-enter-from"));
                            newWrapper_1.classList.add("".concat(transitionName, "-enter-active"));
                            container.appendChild(newWrapper_1);
                            var newComp = mountNew(newWrapper_1);
                            // 2. Handle old component (Leave)
                            if (currentWrapper) {
                                var oldWrapper_1 = currentWrapper;
                                var oldComp_1 = currentComponent;
                                oldWrapper_1.classList.add("".concat(transitionName, "-leave-from"));
                                oldWrapper_1.classList.add("".concat(transitionName, "-leave-active"));
                                // Force reflow
                                void oldWrapper_1.offsetWidth;
                                // Next frame
                                requestAnimationFrame(function () {
                                    oldWrapper_1.classList.remove("".concat(transitionName, "-leave-from"));
                                    oldWrapper_1.classList.add("".concat(transitionName, "-leave-to"));
                                });
                                // Cleanup after transition
                                var onTransitionEnd = function () {
                                    if (oldWrapper_1.parentNode === container) {
                                        container.removeChild(oldWrapper_1);
                                    }
                                    if (oldComp_1) {
                                        try {
                                            oldComp_1.unmount();
                                        }
                                        catch (e) { }
                                    }
                                };
                                // Fallback timeout
                                setTimeout(onTransitionEnd, 500); // Default fallback
                                oldWrapper_1.addEventListener('transitionend', onTransitionEnd, { once: true });
                            }
                            // 3. Handle new component (Enter)
                            // Force reflow
                            void newWrapper_1.offsetWidth;
                            requestAnimationFrame(function () {
                                newWrapper_1.classList.remove("".concat(transitionName, "-enter-from"));
                                newWrapper_1.classList.add("".concat(transitionName, "-enter-to"));
                                var onEnterEnd = function () {
                                    newWrapper_1.classList.remove("".concat(transitionName, "-enter-active"));
                                    newWrapper_1.classList.remove("".concat(transitionName, "-enter-to"));
                                };
                                setTimeout(onEnterEnd, 500);
                                newWrapper_1.addEventListener('transitionend', onEnterEnd, { once: true });
                            });
                            currentComponent = newComp;
                            currentWrapper = newWrapper_1;
                        }
                        else {
                            // --- No Transition (Instant) ---
                            // Clear previous content
                            container.innerHTML = '';
                            if (currentComponent) {
                                try {
                                    currentComponent.unmount();
                                }
                                catch (e) {
                                    console.error('Error unmounting component:', e);
                                }
                                currentComponent = null;
                            }
                            currentWrapper = null;
                            if (route) {
                                var wrapper = document.createElement('div');
                                wrapper.className = 'route-wrapper';
                                container.appendChild(wrapper);
                                currentComponent = mountNew(wrapper);
                                currentWrapper = wrapper;
                            }
                        }
                    });
                }
            }
        };
    };
    return MelodiRouter;
}());
export { MelodiRouter };
