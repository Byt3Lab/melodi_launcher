// --- Fine-grain reactivity primitives regroupées ---
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
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g = Object.create((typeof Iterator === "function" ? Iterator : Object).prototype);
    return g.next = verb(0), g["throw"] = verb(1), g["return"] = verb(2), typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
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
// Réactivité fine-grain par instance d’application
var MelodiReactive = /** @class */ (function () {
    function MelodiReactive() {
        this._currentEffect = null;
    }
    MelodiReactive.prototype.createSignal = function (value) {
        var v = value;
        var subscribers = new Set();
        var self = this;
        function read() {
            if (self._currentEffect)
                subscribers.add(self._currentEffect);
            return v;
        }
        function write(next) {
            // For primitives, use strict equality
            // For objects/arrays (including Proxies), always trigger to catch mutations
            var isPrimitive = next === null || (typeof next !== 'object' && typeof next !== 'function');
            if (isPrimitive && v === next)
                return;
            v = next;
            subscribers.forEach(function (fn) {
                if (typeof fn === 'function')
                    fn();
            });
        }
        return [read, write];
    };
    MelodiReactive.prototype.createEffect = function (fn) {
        var self = this;
        function effect() {
            self._currentEffect = effect;
            try {
                fn();
            }
            finally {
                self._currentEffect = null;
            }
        }
        effect();
        // Return a dispose function (basic implementation)
        return function () {
            // In a full implementation, we would remove 'effect' from all signals it subscribed to.
            // For this lightweight version, we can't easily remove from signals without double-linking.
            // But we can at least flag it to not run anymore if we wrap it.
            // For now, this is a placeholder for the API.
            // To do it properly requires changing createSignal to return a unsubscribe.
        };
    };
    // Improved createEffect with cleanup support
    MelodiReactive.prototype.createEffectWithCleanup = function (fn) {
        var self = this;
        var cleanup = null;
        var execute = function () {
            self._currentEffect = execute;
            try {
                if (cleanup && typeof cleanup === 'function')
                    cleanup();
                cleanup = fn();
            }
            finally {
                self._currentEffect = null;
            }
        };
        execute();
        return function () {
            if (cleanup && typeof cleanup === 'function')
                cleanup();
        };
    };
    MelodiReactive.prototype.createMemo = function (fn) {
        var _a = __read(this.createSignal(undefined), 2), read = _a[0], write = _a[1];
        this.createEffect(function () {
            write(fn());
        });
        return read;
    };
    return MelodiReactive;
}());
// Minimal reactive component library (tiny Vue-like)
var MelodiJS = /** @class */ (function () {
    function MelodiJS(options) {
        this.options = options || {};
        this.root = null;
        this.components = this.options.components || {};
        this._mountedComponents = [];
        this.reactivity = new MelodiReactive();
        // Store is now fine-grained reactive
        this.store = this._makeReactiveStore(this.options.store || {});
        this._plugins = new Set();
        // Register built-in components
        this.components['transition'] = {
            props: ['name'],
            template: '<div :data-melodi-transition="name"><slot></slot></div>'
        };
    }
    MelodiJS.prototype.use = function (plugin, options) {
        if (this._plugins.has(plugin)) {
            console.warn('Plugin has already been installed.');
            return this;
        }
        this._plugins.add(plugin);
        plugin.install(this, options);
        return this;
    };
    MelodiJS.prototype.mount = function (target) {
        var _this = this;
        this.root = typeof target === 'string' ? document.querySelector(target) : target;
        if (!this.root)
            throw new Error('Mount target not found');
        var promises = [];
        // Check if this is a root component app (Vue-like)
        var isRootComponent = !!(this.options.data || this.options.methods || this.options.computed || this.options.watch || this.options.template);
        if (isRootComponent) {
            // Create and mount a root component
            var rootComponentDef = {
                data: this.options.data,
                methods: this.options.methods,
                computed: this.options.computed,
                watch: this.options.watch,
                template: this.options.template,
                delimiters: this.options.delimiters,
                hooks: this.options.hooks,
                components: this.components // Use this.components which includes plugin-registered components
            };
            var rootComp_1 = new Component(rootComponentDef);
            var p = rootComp_1.mount(this.root, this).then(function () {
                _this.root.__melodijs_mounted = true;
                _this.root.__melodijs_root = rootComp_1;
            });
            promises.push(p);
        }
        else {
            // Legacy mode: mount registered components
            var tags_1 = Object.keys(this.components);
            Object.keys(this.components).forEach(function (tag) {
                if (!_this.root)
                    return;
                var nodes = Array.from(_this.root.querySelectorAll(tag));
                nodes.forEach(function (node) {
                    if (node.__melodijs_mounted)
                        return;
                    if (_this._isDescendantOfCustom(node, tags_1))
                        return;
                    var compDef = _this.components[tag];
                    var comp = new Component(compDef);
                    var p = comp.mount(node, _this).then(function () { node.__melodijs_mounted = true; });
                    promises.push(p);
                });
            });
        }
        return Promise.all(promises);
    };
    MelodiJS.prototype._isDescendantOfCustom = function (node, customTags) {
        var p = node.parentElement;
        while (p) {
            var tag = p.tagName && p.tagName.toLowerCase();
            if (tag && customTags.indexOf(tag) !== -1)
                return true;
            p = p.parentElement;
        }
        return false;
    };
    MelodiJS.prototype._makeReactiveStore = function (initial) {
        var e_1, _a;
        // Use the same logic as Component._makeReactive but for the store
        var state = {};
        try {
            for (var _b = __values(Object.keys(initial)), _c = _b.next(); !_c.done; _c = _b.next()) {
                var key = _c.value;
                var _d = __read(this.reactivity.createSignal(initial[key]), 2), getter = _d[0], setter = _d[1];
                Object.defineProperty(state, key, {
                    get: getter,
                    set: setter,
                    enumerable: true,
                    configurable: true
                });
            }
        }
        catch (e_1_1) { e_1 = { error: e_1_1 }; }
        finally {
            try {
                if (_c && !_c.done && (_a = _b.return)) _a.call(_b);
            }
            finally { if (e_1) throw e_1.error; }
        }
        return state;
    };
    return MelodiJS;
}());
var Component = /** @class */ (function () {
    function Component(def) {
        this._slotSource = null;
        this._fragment = null;
        this._postMountEffects = [];
        this._signals = {};
        this.reactivity = null;
        this._parent = null;
        this.template = def.template || '';
        this.delimiters = def.delimiters || null;
        this.dataFn = def.data || function () { return {}; };
        this.methodsDef = def.methods || {};
        // props can be an array of names or an object with detailed defs
        this.propsDef = def.props || null;
        // lifecycle hooks: prefer explicit hooks, fallback to methods (migrated below)
        this.hooks = def.hooks || {};
        this.components = def.components || {};
        this.computedDef = def.computed || {};
        this.watchDef = def.watch || {};
        this.el = null;
        this.app = null;
        this.state = null;
        this.methods = {};
        this._listeners = [];
        this._effects = []; // Track effects for cleanup
        this._events = {};
    }
    Component.prototype.mount = function (el, app) {
        var _this = this;
        this.el = el;
        this.app = app;
        this.delimiters = this.delimiters || (app && app.options && app.options.delimiters) || ['{{', '}}'];
        try {
            console.debug && console.debug('Component.mount start for', el && el.tagName);
        }
        catch (e) { }
        // capture the light DOM (children) to support <slot>
        // move original children into a detached container so we can re-read on every render
        try {
            this._slotSource = document.createElement('div');
            while (el.firstChild) {
                this._slotSource.appendChild(el.firstChild);
            }
        }
        catch (e) {
            this._slotSource = document.createElement('div');
        }
        // obtain props from element attributes
        var props = this._readPropsFromEl(el);
        // (lifecycle hooks should be provided in `hooks` or top-level keys in component def)
        // initialize data and merge props (props override) but only pass declared props
        var initial = this.dataFn.call(props) || {};
        // only include declared props
        var declared = this._gatherDeclaredProps();
        if (declared) {
            Object.keys(declared).forEach(function (key) {
                var def = declared[key];
                if (props.hasOwnProperty(key)) {
                    initial[key] = _this._coercePropValue(props[key], def);
                }
                else if (def && def.hasOwnProperty('default')) {
                    initial[key] = (typeof def.default === 'function') ? def.default() : def.default;
                }
            });
        }
        else {
            Object.assign(initial, props);
        }
        // attach $store to raw data so methods/state can access it
        initial.$store = app.store;
        // Inject router BEFORE creating reactive state (so computed can access it)
        if (app.router) {
            initial.$router = app.router;
        }
        // create reactive state
        this.reactivity = app.reactivity;
        this.state = this._makeReactive(initial);
        // inject references into state for convenience (element, app, root)
        try {
            this.state.__lastEl = this.el;
            this.state.__slotSourceEl = this.el;
            this.state.$app = app;
            this.state.$root = document;
        }
        catch (e) { }
        // event API helpers available on state
        try {
            var comp_1 = this;
            // register event listener on this component
            this.state.$on = function (eventName, handler) {
                if (!eventName || typeof handler !== 'function')
                    return;
                comp_1._events[eventName] = comp_1._events[eventName] || [];
                comp_1._events[eventName].push(handler);
                // return unregister
                return function () {
                    var arr = comp_1._events[eventName] || [];
                    var idx = arr.indexOf(handler);
                    if (idx !== -1)
                        arr.splice(idx, 1);
                };
            };
            // emit event: call local handlers, then bubble up to ancestor components
            this.state.$emit = function (eventName, payload) {
                try {
                    var local = comp_1._events[eventName] || [];
                    local.forEach(function (h) { try {
                        h.call(comp_1.state, payload);
                    }
                    catch (e) { } });
                    // bubble
                    // first try DOM parent chain
                    var p = comp_1.el.parentElement;
                    var _loop_1 = function () {
                        var parentComp = p.__melodijs_instance;
                        if (parentComp) {
                            var handlers = parentComp._events[eventName] || [];
                            handlers.forEach(function (h) { try {
                                h.call(parentComp.state, payload);
                            }
                            catch (e) { } });
                            // stop if handled? keep bubbling to allow multiple ancestors
                        }
                        p = p.parentElement;
                    };
                    while (p) {
                        _loop_1();
                    }
                    // also support logical parent chain (set when mounting nested components)
                    try {
                        var lp_1 = comp_1._parent;
                        while (lp_1) {
                            var handlers = lp_1._events[eventName] || [];
                            handlers.forEach(function (h) { try {
                                h.call(lp_1.state, payload);
                            }
                            catch (e) { } });
                            lp_1 = lp_1._parent;
                        }
                    }
                    catch (e) { }
                }
                catch (e) { }
            };
        }
        catch (e) { }
        // bind methods to state
        try {
            // debug: ensure methodsDef is iterable
            // console.debug('binding methodsDef', Object.keys(this.methodsDef || {}))
            Object.keys(this.methodsDef || {}).forEach(function (name) {
                _this.methods[name] = _this.methodsDef[name].bind(_this.state);
            });
            // expose methods directly on state so methods can call each other via `this.someMethod()`
            Object.keys(this.methods).forEach(function (name) {
                try {
                    _this.state[name] = _this.methods[name];
                }
                catch (e) { }
            });
        }
        catch (e) {
            console.error('Error binding methods:', e);
        }
        // Setup watchers
        try {
            Object.keys(this.watchDef).forEach(function (key) {
                var watchSpec = _this.watchDef[key];
                var handler;
                var immediate = false;
                var deep = false;
                if (typeof watchSpec === 'function') {
                    handler = watchSpec;
                }
                else {
                    handler = watchSpec.handler;
                    immediate = watchSpec.immediate || false;
                    deep = watchSpec.deep || false;
                }
                // Bind handler to state
                var boundHandler = handler.bind(_this.state);
                // Get the signal for this property
                var signal = _this._signals[key];
                if (!signal) {
                    console.warn("Watch: property '".concat(key, "' not found in data"));
                    return;
                }
                var _a = __read(signal, 1), getter = _a[0];
                var oldValue = getter();
                var isFirstRun = true;
                // Create effect to watch changes
                _this._createEffect(function () {
                    var newValue = getter();
                    // Skip first run unless immediate is true
                    if (isFirstRun) {
                        isFirstRun = false;
                        if (immediate) {
                            try {
                                boundHandler(newValue, undefined);
                            }
                            catch (e) {
                                console.error("Error in immediate watcher for '".concat(key, "':"), e);
                            }
                        }
                        oldValue = newValue;
                        return;
                    }
                    // Only trigger if value actually changed
                    if (newValue !== oldValue || deep) {
                        var prevValue = oldValue;
                        oldValue = newValue;
                        // Call handler with new and old values
                        try {
                            boundHandler(newValue, prevValue);
                        }
                        catch (e) {
                            console.error("Error in watcher for '".concat(key, "':"), e);
                        }
                    }
                });
            });
        }
        catch (e) {
            console.error('Error setting up watchers:', e);
        }
        // register component on app so store updates can notify
        app._mountedComponents = app._mountedComponents || [];
        app._mountedComponents.push(this);
        // mark instance on element for parent-child lookup
        try {
            this.el.__melodijs_instance = this;
        }
        catch (e) { }
        // initial render (handle async template resolution)
        return this._render(true);
    };
    Component.prototype._readPropsFromEl = function (el) {
        var _this = this;
        var props = {};
        Array.from(el.attributes).forEach(function (attr) {
            // ignore special attributes
            if (/^v-|^@|^:/.test(attr.name))
                return;
            // only include declared props if propsDef exists
            var name = attr.name;
            var declared = _this._gatherDeclaredProps();
            if (declared) {
                if (declared.hasOwnProperty(name)) {
                    props[name] = _this._coerceAttrValue(attr.value);
                }
            }
            else {
                props[name] = _this._coerceAttrValue(attr.value);
            }
        });
        return props;
    };
    Component.prototype._coerceAttrValue = function (val) {
        // try number and boolean coercion
        if (val === 'true')
            return true;
        if (val === 'false')
            return false;
        if (!isNaN(val) && val.trim() !== '')
            return Number(val);
        return val;
    };
    Component.prototype._gatherDeclaredProps = function () {
        // returns an object map of propName -> def (if array provided, returns names with undefined defs)
        if (!this.propsDef)
            return null;
        if (Array.isArray(this.propsDef)) {
            var out_1 = {};
            this.propsDef.forEach(function (n) { return out_1[n] = {}; });
            return out_1;
        }
        // assume object
        return this.propsDef;
    };
    Component.prototype._coercePropValue = function (val, def) {
        if (!def || !def.type)
            return val;
        var t = def.type;
        if (t === Number)
            return Number(val);
        if (t === Boolean)
            return (val === '' || val === true || val === 'true');
        if (t === String)
            return String(val);
        return val;
    };
    // Fine-grain reactivity: wrap each property in a signal
    Component.prototype._makeReactive = function (obj) {
        var e_2, _a;
        var _this = this;
        var state = {};
        this._signals = {};
        if (!this.reactivity)
            return state; // Should not happen
        var _loop_2 = function (key) {
            var initialValue = obj[key];
            var _d = __read(this_1.reactivity.createSignal(initialValue), 2), getter = _d[0], setter = _d[1];
            // Wrap arrays in a Proxy to intercept mutations
            if (Array.isArray(initialValue)) {
                var proxyArray = this_1._makeReactiveArray(initialValue, setter);
                setter(proxyArray);
                Object.defineProperty(state, key, {
                    get: getter,
                    set: function (newVal) {
                        if (Array.isArray(newVal)) {
                            setter(_this._makeReactiveArray(newVal, setter));
                        }
                        else {
                            setter(newVal);
                        }
                    },
                    enumerable: true,
                    configurable: true
                });
            }
            else {
                Object.defineProperty(state, key, {
                    get: getter,
                    set: setter,
                    enumerable: true,
                    configurable: true
                });
            }
            this_1._signals[key] = [getter, setter];
        };
        var this_1 = this;
        try {
            for (var _b = __values(Object.keys(obj)), _c = _b.next(); !_c.done; _c = _b.next()) {
                var key = _c.value;
                _loop_2(key);
            }
        }
        catch (e_2_1) { e_2 = { error: e_2_1 }; }
        finally {
            try {
                if (_c && !_c.done && (_a = _b.return)) _a.call(_b);
            }
            finally { if (e_2) throw e_2.error; }
        }
        // Initialize computed properties
        if (this.computedDef) {
            Object.keys(this.computedDef).forEach(function (key) {
                var fn = _this.computedDef[key].bind(state);
                var memo = _this.reactivity.createMemo(fn);
                Object.defineProperty(state, key, {
                    get: memo,
                    enumerable: true,
                    configurable: true
                });
            });
        }
        return state;
    };
    Component.prototype._makeReactiveArray = function (arr, setter) {
        var mutatingMethods = ['push', 'pop', 'shift', 'unshift', 'splice', 'sort', 'reverse'];
        var proxy = new Proxy(arr, {
            get: function (target, prop) {
                var value = target[prop];
                // Intercept mutating methods
                if (typeof prop === 'string' && mutatingMethods.includes(prop)) {
                    return function () {
                        var args = [];
                        for (var _i = 0; _i < arguments.length; _i++) {
                            args[_i] = arguments[_i];
                        }
                        var result = Array.prototype[prop].apply(target, args);
                        // Trigger reactivity - setter will always trigger for objects
                        setter(proxy);
                        return result;
                    };
                }
                return value;
            },
            set: function (target, prop, value) {
                target[prop] = value;
                // Trigger reactivity on index assignment
                setter(proxy);
                return true;
            }
        });
        return proxy;
    };
    Component.prototype._evalExpression = function (expr, scope) {
        // Evaluate JS expressions with access to state (getters on `this.state` will register effects)
        try {
            if (!expr || typeof expr !== 'string')
                return '';
            var expression = expr.trim();
            var fn = new Function('state', 'scope', 'with(state){ with(scope || {}){ try { return (' + expression + ') } catch(e){ return "" } } }');
            var res = fn(this.state || {}, scope || {});
            return (res === undefined || res === null) ? '' : res;
        }
        catch (e) {
            return '';
        }
    };
    // --- Fine-grained DOM Creation & Update ---
    Component.prototype._render = function (isInitial) {
        return __awaiter(this, void 0, void 0, function () {
            var maxIterations, iterations, effects;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        if (!isInitial) return [3 /*break*/, 3];
                        this._postMountEffects = []; // Queue for effects that need parentNode
                        // 1. Compile: Create the initial DOM structure from template
                        return [4 /*yield*/, this._compile()];
                    case 1:
                        // 1. Compile: Create the initial DOM structure from template
                        _a.sent();
                        // 2. Mount hooks
                        try {
                            if (typeof this.hooks.beforeMount === 'function')
                                this.hooks.beforeMount.call(this.state);
                        }
                        catch (e) { }
                        // 3. Append to DOM
                        if (this.el && this._fragment) {
                            this.el.appendChild(this._fragment);
                        }
                        maxIterations = 10;
                        iterations = 0;
                        while (this._postMountEffects.length > 0 && iterations < maxIterations) {
                            effects = this._postMountEffects;
                            this._postMountEffects = []; // Clear before running
                            effects.forEach(function (fn) { return fn(); });
                            iterations++;
                        }
                        this._postMountEffects = []; // Ensure clear
                        // 5. Mount nested components
                        return [4 /*yield*/, this._mountNestedComponents()];
                    case 2:
                        // 5. Mount nested components
                        _a.sent();
                        try {
                            if (typeof this.hooks.mounted === 'function')
                                this.hooks.mounted.call(this.state);
                        }
                        catch (e) { }
                        _a.label = 3;
                    case 3: return [2 /*return*/, true];
                }
            });
        });
    };
    Component.prototype._compile = function () {
        return __awaiter(this, void 0, void 0, function () {
            var tpl, tempDiv, node, resp, e_3, slotEls;
            var _this = this;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        tpl = this.template;
                        if (!!tpl) return [3 /*break*/, 1];
                        // If no template, use the slot source (which contains the original HTML)
                        // This allows root components to work without explicit template
                        if (this._slotSource && this._slotSource.childNodes.length > 0) {
                            this._fragment = this._processNodeList(Array.from(this._slotSource.childNodes));
                        }
                        else {
                            // Completely empty
                            this._fragment = document.createDocumentFragment();
                        }
                        return [3 /*break*/, 8];
                    case 1:
                        if (!(typeof tpl === 'object')) return [3 /*break*/, 7];
                        if (!tpl.el) return [3 /*break*/, 2];
                        node = document.querySelector(tpl.el);
                        tpl = node ? node.innerHTML : '';
                        return [3 /*break*/, 7];
                    case 2:
                        if (!tpl.url) return [3 /*break*/, 7];
                        _a.label = 3;
                    case 3:
                        _a.trys.push([3, 6, , 7]);
                        return [4 /*yield*/, fetch(tpl.url)];
                    case 4:
                        resp = _a.sent();
                        return [4 /*yield*/, resp.text()];
                    case 5:
                        tpl = _a.sent();
                        return [3 /*break*/, 7];
                    case 6:
                        e_3 = _a.sent();
                        tpl = '';
                        return [3 /*break*/, 7];
                    case 7:
                        tempDiv = document.createElement('div');
                        tempDiv.innerHTML = tpl || '';
                        // --- Slot Distribution ---
                        if (this._slotSource) {
                            slotEls = Array.from(tempDiv.querySelectorAll('slot'));
                            slotEls.forEach(function (slotEl) {
                                var name = slotEl.getAttribute('name');
                                var inserted = false;
                                var fragment = document.createDocumentFragment();
                                if (name) {
                                    // Named slot
                                    var nodes = Array.from(_this._slotSource.querySelectorAll('[slot="' + name + '"]'));
                                    if (nodes.length) {
                                        nodes.forEach(function (n) { return fragment.appendChild(n.cloneNode(true)); });
                                        inserted = true;
                                    }
                                }
                                else {
                                    // Default slot
                                    var nodes = Array.from(_this._slotSource.childNodes).filter(function (n) {
                                        return !(n.nodeType === 1 && n.hasAttribute && n.hasAttribute('slot'));
                                    });
                                    if (nodes.length) {
                                        nodes.forEach(function (n) { return fragment.appendChild(n.cloneNode(true)); });
                                        inserted = true;
                                    }
                                }
                                if (inserted) {
                                    if (slotEl.parentNode)
                                        slotEl.parentNode.replaceChild(fragment, slotEl);
                                }
                                else {
                                    // Fallback content: keep what's inside the slot tag, but unwrap the slot tag itself?
                                    // Usually <slot>fallback</slot> -> fallback
                                    // We need to replace <slot> with its children.
                                    while (slotEl.firstChild) {
                                        if (slotEl.parentNode)
                                            slotEl.parentNode.insertBefore(slotEl.firstChild, slotEl);
                                    }
                                    if (slotEl.parentNode)
                                        slotEl.parentNode.removeChild(slotEl);
                                }
                            });
                        }
                        this._fragment = this._processNodeList(Array.from(tempDiv.childNodes));
                        if (this.el)
                            this.el.innerHTML = ''; // Clear host element
                        _a.label = 8;
                    case 8: return [2 /*return*/];
                }
            });
        });
    };
    Component.prototype._processNodeList = function (nodes, scope) {
        if (scope === void 0) { scope = {}; }
        var fragment = document.createDocumentFragment();
        var nodesArray = Array.from(nodes);
        for (var i = 0; i < nodesArray.length; i++) {
            var node = nodesArray[i];
            // Check for v-if start
            if (node.nodeType === 1 && node.hasAttribute('v-if')) {
                var _a = this._handleConditional(node, nodesArray, i, scope), anchor = _a.anchor, nextIndex = _a.nextIndex;
                fragment.appendChild(anchor);
                i = nextIndex - 1; // Skip consumed nodes
                continue;
            }
            var processed = this._walk(node, scope);
            if (Array.isArray(processed)) {
                processed.forEach(function (n) { return fragment.appendChild(n); });
            }
            else if (processed) {
                fragment.appendChild(processed);
            }
        }
        return fragment;
    };
    Component.prototype._walk = function (node, scope) {
        var _this = this;
        // 1. Handle Text Nodes (Interpolation)
        if (node.nodeType === 3) {
            var text = node.nodeValue || '';
            if (text.trim() === '')
                return node.cloneNode(true);
            var delims = this.delimiters || (this.app && this.app.options && this.app.options.delimiters) || ['{{', '}}'];
            var open_1 = delims[0].replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            var close_1 = delims[1].replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            var splitRegex = new RegExp('(' + open_1 + '[\\s\\S]+?' + close_1 + ')', 'g');
            var matchRegex_1 = new RegExp('^' + open_1 + '\\s*([\\s\\S]+?)\\s*' + close_1 + '$');
            var parts = text.split(splitRegex);
            if (parts.length > 1) {
                var frag_1 = document.createDocumentFragment();
                parts.forEach(function (part) {
                    var m = part.match(matchRegex_1);
                    if (m) {
                        var expr_1 = m[1];
                        var textNode_1 = document.createTextNode('');
                        _this._createEffect(function () {
                            var val = _this._evalExpression(expr_1, scope);
                            textNode_1.nodeValue = (val === undefined || val === null) ? '' : String(val);
                        });
                        frag_1.appendChild(textNode_1);
                    }
                    else {
                        frag_1.appendChild(document.createTextNode(part));
                    }
                });
                return frag_1;
            }
            return node.cloneNode(true);
        }
        // 2. Handle Elements
        if (node.nodeType === 1) {
            var elNode = node;
            // Check for v-pre
            if (elNode.hasAttribute('v-pre')) {
                var clone = elNode.cloneNode(true);
                clone.removeAttribute('v-pre');
                return clone;
            }
            // Check for v-if - REMOVED (Handled in _processNodeList)
            // if (elNode.hasAttribute('v-if')) {
            //    return this._handleVIf(elNode, scope);
            // }
            // Check for v-for
            if (elNode.hasAttribute('v-for')) {
                return this._handleVFor(elNode, scope);
            }
            // Clone element
            var el_1 = elNode.cloneNode(false);
            // Handle v-show
            if (el_1.hasAttribute('v-show')) {
                var expr_2 = el_1.getAttribute('v-show');
                el_1.removeAttribute('v-show');
                this._createEffect(function () {
                    var show = !!_this._evalExpression(expr_2, scope);
                    el_1.style.display = show ? '' : 'none';
                });
            }
            // Handle v-model
            if (el_1.hasAttribute('v-model')) {
                var prop_1 = el_1.getAttribute('v-model').trim();
                el_1.removeAttribute('v-model');
                if (el_1.tagName === 'INPUT' || el_1.tagName === 'TEXTAREA' || el_1.tagName === 'SELECT') {
                    var inputEl_1 = el_1;
                    // Two-way binding
                    // 1. Model -> View
                    this._createEffect(function () {
                        var val = _this.state[prop_1];
                        if (inputEl_1.type === 'checkbox') {
                            inputEl_1.checked = !!val;
                        }
                        else {
                            inputEl_1.value = (val == null) ? '' : val;
                        }
                    });
                    // 2. View -> Model
                    var handler = function (e) {
                        var val = (inputEl_1.type === 'checkbox') ? inputEl_1.checked : inputEl_1.value;
                        _this.state[prop_1] = val;
                    };
                    el_1.addEventListener('input', handler);
                    // Also listen to change for some inputs
                    if (el_1.tagName === 'SELECT' || inputEl_1.type === 'checkbox' || inputEl_1.type === 'radio') {
                        el_1.addEventListener('change', handler);
                    }
                    this._listeners.push({ node: el_1, ev: 'input', fn: handler });
                }
            }
            // Handle Attributes & Events
            Array.from(elNode.attributes).forEach(function (attr) {
                var name = attr.name;
                var value = attr.value;
                // Events: @click, v-on:click
                if (name.startsWith('@') || name.startsWith('v-on:')) {
                    var rawEventName = name.startsWith('@') ? name.slice(1) : name.slice(5);
                    var parts = rawEventName.split('.');
                    var eventName = parts[0];
                    var isStop_1 = parts.includes('stop');
                    var isPrevent_1 = parts.includes('prevent');
                    el_1.removeAttribute(name);
                    var handlerName_1 = value.trim();
                    var handlerFn = function (e) {
                        if (isStop_1 && e && typeof e.stopPropagation === 'function')
                            e.stopPropagation();
                        if (isPrevent_1 && e && typeof e.preventDefault === 'function')
                            e.preventDefault();
                        // Try to find method first (simple name like "increment")
                        if (_this.methods[handlerName_1]) {
                            _this.methods[handlerName_1](e);
                        }
                        else {
                            // Try eval with $event and methods
                            // Add methods to scope so they're accessible in expressions
                            var evalScope = Object.assign({}, scope, _this.methods, { $event: e });
                            try {
                                // Evaluate with both state and scope (which includes methods)
                                var fn = new Function('state', 'scope', 'with(state){ with(scope){ return ' + handlerName_1 + ' } }');
                                fn(_this.state, evalScope);
                            }
                            catch (err) {
                                console.error('Error evaluating handler:', handlerName_1, err);
                                console.error('Scope was:', evalScope);
                            }
                        }
                    };
                    el_1.addEventListener(eventName, handlerFn);
                    _this._listeners.push({ node: el_1, ev: eventName, fn: handlerFn });
                    return;
                }
                // Bindings: :attr, v-bind:attr
                if (name.startsWith(':') || name.startsWith('v-bind:')) {
                    var attrName_1 = name.startsWith(':') ? name.slice(1) : name.slice(7);
                    el_1.removeAttribute(name);
                    _this._createEffect(function () {
                        var val = _this._evalExpression(value, scope);
                        if (attrName_1 === 'class') {
                            if (typeof val === 'object' && val !== null) {
                                Object.keys(val).forEach(function (cls) {
                                    if (val[cls])
                                        el_1.classList.add(cls);
                                    else
                                        el_1.classList.remove(cls);
                                });
                            }
                            else {
                                el_1.setAttribute('class', val);
                            }
                        }
                        else if (val === false || val === null || val === undefined) {
                            el_1.removeAttribute(attrName_1);
                        }
                        else {
                            el_1.setAttribute(attrName_1, val);
                        }
                    });
                }
            });
            // Process children
            var childrenFrag = this._processNodeList(Array.from(elNode.childNodes), scope);
            el_1.appendChild(childrenFrag);
            return el_1;
        }
        return node.cloneNode(true);
    };
    Component.prototype._handleConditional = function (startNode, nodes, startIndex, scope) {
        var _this = this;
        var _a;
        var anchor = document.createComment('v-if-chain');
        var branches = [];
        // First node is always v-if
        branches.push({
            type: 'if',
            condition: startNode.getAttribute('v-if'),
            node: startNode
        });
        var currentIndex = startIndex + 1;
        while (currentIndex < nodes.length) {
            var node = nodes[currentIndex];
            // Skip text nodes (whitespace) and comment nodes between branches
            if (node.nodeType === 8 || (node.nodeType === 3 && !((_a = node.nodeValue) === null || _a === void 0 ? void 0 : _a.trim()))) {
                currentIndex++;
                continue;
            }
            if (node.nodeType === 1) {
                var el = node;
                if (el.hasAttribute('v-else-if')) {
                    branches.push({
                        type: 'else-if',
                        condition: el.getAttribute('v-else-if'),
                        node: el
                    });
                    currentIndex++;
                    continue;
                }
                else if (el.hasAttribute('v-else')) {
                    branches.push({
                        type: 'else',
                        node: el
                    });
                    currentIndex++;
                    // v-else must be the last one
                    break;
                }
            }
            // If we reach here, it's not part of the chain
            break;
        }
        // 2. Create Effect
        var currentEl = null;
        var effectFn = function () {
            _this._createEffect(function () {
                var e_4, _a;
                var activeBranch = null;
                try {
                    // Find first matching branch
                    for (var branches_1 = __values(branches), branches_1_1 = branches_1.next(); !branches_1_1.done; branches_1_1 = branches_1.next()) {
                        var branch = branches_1_1.value;
                        if (branch.type === 'else') {
                            activeBranch = branch;
                            break;
                        }
                        var val = _this._evalExpression(branch.condition, scope);
                        if (!!val) {
                            activeBranch = branch;
                            break;
                        }
                    }
                }
                catch (e_4_1) { e_4 = { error: e_4_1 }; }
                finally {
                    try {
                        if (branches_1_1 && !branches_1_1.done && (_a = branches_1.return)) _a.call(branches_1);
                    }
                    finally { if (e_4) throw e_4.error; }
                }
                // Render logic
                if (activeBranch) {
                    // If we are already showing this branch's node (cloned), do nothing?
                    // No, we need to re-render if data changed, but _walk handles that recursion.
                    // However, we are in an effect. If activeBranch changes, we swap.
                    // If activeBranch is same, we might need to update? 
                    // Actually, since we are inside an effect, if any dependency changes, this whole block runs.
                    // We should check if the *rendered element* corresponds to the active branch.
                    // But we don't track which branch created currentEl easily.
                    // Simplest: Always unmount old, mount new. (Inefficient but correct for v1)
                    // Optimization: If same branch, don't destroy/recreate.
                    // For now, let's implement simple swap.
                    // Clean up previous
                    if (currentEl) {
                        var elToRemove = currentEl;
                        currentEl = null; // Clear ref first
                        if (elToRemove.parentNode) {
                            elToRemove.parentNode.removeChild(elToRemove);
                        }
                    }
                    // Mount new
                    var clone = activeBranch.node.cloneNode(true);
                    clone.removeAttribute('v-if');
                    clone.removeAttribute('v-else-if');
                    clone.removeAttribute('v-else');
                    var processed = _this._walk(clone, scope);
                    if (processed.nodeType === 11) {
                        // Fragment handling
                        // We need a single reference for currentEl to remove it later.
                        // If fragment, we might need a wrapper or track all nodes.
                        // For simplicity in this fix, let's assume single element or wrap in text?
                        // _walk returns Node | DocumentFragment.
                        // If fragment, we can't easily track "currentEl" as a single node.
                        // But v-if usually is on an Element, so _walk(element) usually returns Element.
                        // Unless the element contains only text? No, _walk(element) returns element.
                        currentEl = processed;
                    }
                    else {
                        currentEl = processed;
                    }
                    if (anchor.parentNode && currentEl) {
                        anchor.parentNode.insertBefore(currentEl, anchor);
                    }
                    // Run any new effects generated by _walk (e.g. nested v-for)
                    if (_this._postMountEffects.length > 0) {
                        var effects = _this._postMountEffects;
                        _this._postMountEffects = [];
                        effects.forEach(function (fn) { return fn(); });
                    }
                    // Mount nested components in newly inserted content
                    if (currentEl && currentEl.nodeType === 1) {
                        _this._mountComponentsIn(currentEl);
                    }
                }
                else {
                    // No branch active
                    if (currentEl) {
                        if (currentEl.parentNode)
                            currentEl.parentNode.removeChild(currentEl);
                        currentEl = null;
                    }
                }
            });
        };
        this._postMountEffects.push(effectFn);
        return { anchor: anchor, nextIndex: currentIndex };
    };
    Component.prototype._handleVFor = function (node, scope) {
        var _this = this;
        var anchor = document.createComment('v-for');
        var expr = node.getAttribute('v-for');
        var inMatch = expr.match(/^\s*(?:\(([^,]+)\s*,\s*([^\)]+)\)|([^\s]+))\s+in\s+(.+)$/);
        if (!inMatch)
            return anchor;
        var itemName, indexName, listExpr;
        if (inMatch[1]) {
            itemName = inMatch[1].trim();
            indexName = inMatch[2].trim();
            listExpr = inMatch[4].trim();
        }
        else {
            itemName = inMatch[3].trim();
            listExpr = inMatch[4].trim();
        }
        // Check if :key attribute is present
        var keyExpr = node.getAttribute(':key') || node.getAttribute('v-bind:key');
        var hasKey = !!keyExpr;
        // Map to track items by key: key -> { element, item, index }
        var itemMap = new Map();
        var effectFn = function () {
            _this._createEffect(function () {
                var list = _this._evalExpression(listExpr, scope);
                var parent = anchor.parentNode;
                if (!parent)
                    return;
                if (!hasKey) {
                    // Fallback: No :key specified - use old behavior (recreate all)
                    itemMap.forEach(function (_a) {
                        var element = _a.element;
                        element.parentNode && element.parentNode.removeChild(element);
                    });
                    itemMap.clear();
                    var renderItem_1 = function (item, index) {
                        var newScope = Object.assign({}, scope);
                        newScope[itemName] = item;
                        if (indexName)
                            newScope[indexName] = index;
                        var clone = node.cloneNode(true);
                        clone.removeAttribute('v-for');
                        clone.removeAttribute(':key');
                        clone.removeAttribute('v-bind:key');
                        var processed = _this._walk(clone, newScope);
                        if (processed.nodeType === 11) {
                            // Fragment - insert all children
                            var children = Array.from(processed.childNodes);
                            children.forEach(function (child) {
                                parent.insertBefore(child, anchor);
                            });
                            // For fragments, track first child
                            if (children.length > 0) {
                                itemMap.set(index, { element: children[0], item: item, index: index });
                            }
                            // Mount nested components in each child
                            children.forEach(function (child) {
                                if (child.nodeType === 1) {
                                    _this._mountComponentsIn(child);
                                }
                            });
                        }
                        else {
                            parent.insertBefore(processed, anchor);
                            itemMap.set(index, { element: processed, item: item, index: index });
                            // Mount nested components in newly inserted element
                            if (processed.nodeType === 1) {
                                _this._mountComponentsIn(processed);
                            }
                        }
                    };
                    if (Array.isArray(list)) {
                        list.forEach(function (item, i) { return renderItem_1(item, i); });
                    }
                    else if (typeof list === 'object' && list !== null) {
                        Object.keys(list).forEach(function (key, i) { return renderItem_1(list[key], key); });
                    }
                }
                else {
                    // Optimized: :key specified - use diffing algorithm
                    var newItemMap_1 = new Map();
                    var newKeys_1 = [];
                    // Build new item map
                    if (Array.isArray(list)) {
                        list.forEach(function (item, i) {
                            var newScope = Object.assign({}, scope);
                            newScope[itemName] = item;
                            if (indexName)
                                newScope[indexName] = i;
                            var key = _this._evalExpression(keyExpr, newScope);
                            if (key === null || key === undefined) {
                                console.warn('v-for :key evaluated to null/undefined for item:', item);
                                return;
                            }
                            if (newItemMap_1.has(key)) {
                                console.warn('Duplicate key in v-for:', key);
                            }
                            newKeys_1.push(key);
                            newItemMap_1.set(key, { item: item, index: i, scope: newScope });
                        });
                    }
                    else if (typeof list === 'object' && list !== null) {
                        Object.keys(list).forEach(function (objKey, i) {
                            var item = list[objKey];
                            var newScope = Object.assign({}, scope);
                            newScope[itemName] = item;
                            if (indexName)
                                newScope[indexName] = objKey;
                            var key = _this._evalExpression(keyExpr, newScope);
                            if (key === null || key === undefined) {
                                console.warn('v-for :key evaluated to null/undefined for item:', item);
                                return;
                            }
                            if (newItemMap_1.has(key)) {
                                console.warn('Duplicate key in v-for:', key);
                            }
                            newKeys_1.push(key);
                            newItemMap_1.set(key, { item: item, index: objKey, scope: newScope });
                        });
                    }
                    // Diff algorithm: reuse, move, add, remove
                    var oldKeys = Array.from(itemMap.keys());
                    var keysToRemove = oldKeys.filter(function (k) { return !newItemMap_1.has(k); });
                    // const keysToAdd = newKeys.filter(k => !itemMap.has(k)); // Unused
                    // Remove old items
                    keysToRemove.forEach(function (key) {
                        var element = itemMap.get(key).element;
                        if (element && element.parentNode) {
                            element.parentNode.removeChild(element);
                        }
                        itemMap.delete(key);
                    });
                    // Process new items in order
                    var previousElement_1 = null;
                    newKeys_1.forEach(function (key, i) {
                        var newData = newItemMap_1.get(key);
                        if (itemMap.has(key)) {
                            // Reuse existing element
                            var element = itemMap.get(key).element;
                            // Move element to correct position if needed
                            // Insert after previousElement (or at start if previousElement is null)
                            if (previousElement_1) {
                                // Insert after previousElement
                                if (element.nextSibling !== previousElement_1.nextSibling) {
                                    parent.insertBefore(element, previousElement_1.nextSibling);
                                }
                            }
                            else {
                                // Insert at start (before anchor's previous sibling or at parent's first position)
                                var firstChild = parent.firstChild;
                                if (firstChild !== element) {
                                    parent.insertBefore(element, firstChild);
                                }
                            }
                            previousElement_1 = element;
                        }
                        else {
                            // Create new element
                            var clone = node.cloneNode(true);
                            clone.removeAttribute('v-for');
                            clone.removeAttribute(':key');
                            clone.removeAttribute('v-bind:key');
                            var processed = _this._walk(clone, newData.scope);
                            var elementToTrack = void 0;
                            if (processed.nodeType === 11) {
                                // Fragment - insert all children
                                var children = Array.from(processed.childNodes);
                                children.forEach(function (child) {
                                    if (previousElement_1) {
                                        parent.insertBefore(child, previousElement_1.nextSibling);
                                        previousElement_1 = child;
                                    }
                                    else {
                                        parent.insertBefore(child, parent.firstChild);
                                        previousElement_1 = child;
                                    }
                                });
                                // Track first child for positioning
                                elementToTrack = children[0];
                            }
                            else {
                                if (previousElement_1) {
                                    parent.insertBefore(processed, previousElement_1.nextSibling);
                                }
                                else {
                                    parent.insertBefore(processed, parent.firstChild);
                                }
                                elementToTrack = processed;
                                previousElement_1 = processed;
                            }
                            itemMap.set(key, { element: elementToTrack, item: newData.item, index: newData.index });
                            // Mount nested components in newly created element
                            if (elementToTrack && elementToTrack.nodeType === 1) {
                                _this._mountComponentsIn(elementToTrack);
                            }
                        }
                    });
                }
            });
        };
        this._postMountEffects.push(effectFn);
        return anchor;
    };
    Component.prototype._escape = function (v) {
        if (v == null)
            return '';
        return String(v)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    };
    Component.prototype._bindEvents = function () {
        var _this = this;
        var el = this.el;
        if (!el)
            return;
        // find elements with attributes starting with data-on-
        var all = el.querySelectorAll('[data-on-click], [data-on-input], [data-on-change], [data-on-submit]');
        all.forEach(function (node) {
            Array.from(node.attributes).forEach(function (attr) {
                if (!attr.name.startsWith('data-on-'))
                    return;
                var ev = attr.name.slice('data-on-'.length);
                var handler = attr.value.trim();
                if (!handler)
                    return;
                var fn = _this.methods[handler];
                if (typeof fn === 'function') {
                    var bound = function (e) { fn(e); };
                    node.addEventListener(ev, bound);
                    _this._listeners.push({ node: node, ev: ev, fn: bound });
                }
            });
        });
    };
    Component.prototype._bindModels = function () {
        var _this = this;
        var el = this.el;
        if (!el)
            return;
        var nodes = el.querySelectorAll('[data-model]');
        nodes.forEach(function (node) {
            var prop = node.getAttribute('data-model').trim();
            if (!prop)
                return;
            if (node.tagName === 'INPUT' || node.tagName === 'TEXTAREA' || node.tagName === 'SELECT') {
                var inputEl_2 = node;
                var updateInput = function () {
                    if (inputEl_2.type === 'checkbox') {
                        inputEl_2.checked = !!_this.state[prop];
                    }
                    else {
                        inputEl_2.value = _this.state[prop] == null ? '' : _this.state[prop];
                    }
                };
                _this._createEffect(updateInput);
                var bound = function (e) {
                    var val = (inputEl_2.type === 'checkbox') ? inputEl_2.checked : inputEl_2.value;
                    _this.state[prop] = val;
                };
                node.addEventListener('input', bound);
                _this._listeners.push({ node: node, ev: 'input', fn: bound });
            }
            else {
                var htmlEl_1 = node;
                var updateText = function () {
                    htmlEl_1.innerText = _this.state[prop] == null ? '' : _this.state[prop];
                };
                _this._createEffect(updateText);
            }
        });
    };
    Component.prototype.unmount = function () {
        // call unmounted hook
        try {
            if (typeof this.hooks.unmounted === 'function')
                this.hooks.unmounted.call(this.state);
        }
        catch (e) { }
        // remove event listeners
        this._listeners.forEach(function (l) {
            try {
                l.node.removeEventListener(l.ev, l.fn);
            }
            catch (e) { }
        });
        this._listeners = [];
        // cleanup effects
        this._effects.forEach(function (fn) { try {
            fn();
        }
        catch (e) { } });
        this._effects = [];
        // remove from app mounted list
        try {
            if (this.app && Array.isArray(this.app._mountedComponents)) {
                var idx = this.app._mountedComponents.indexOf(this);
                if (idx !== -1)
                    this.app._mountedComponents.splice(idx, 1);
            }
        }
        catch (e) { }
        // unmark DOM
        try {
            if (this.el) {
                this.el.__melodijs_mounted = false;
                this.el.innerHTML = '';
            }
        }
        catch (e) { }
    };
    Component.prototype._mountNestedComponents = function () {
        return __awaiter(this, void 0, void 0, function () {
            var globalComponents, localComponents, allComponents, tags, tags_2, tags_2_1, tag, nodes, nodes_1, nodes_1_1, node, parent_1, skip, t, compDef, comp, e_5, e_6_1, e_7_1;
            var e_7, _a, e_6, _b;
            return __generator(this, function (_c) {
                switch (_c.label) {
                    case 0:
                        if (!this.app || !this.el)
                            return [2 /*return*/];
                        globalComponents = this.app.components || {};
                        localComponents = this.components || {};
                        allComponents = __assign(__assign({}, globalComponents), localComponents);
                        tags = Object.keys(allComponents);
                        _c.label = 1;
                    case 1:
                        _c.trys.push([1, 14, 15, 16]);
                        tags_2 = __values(tags), tags_2_1 = tags_2.next();
                        _c.label = 2;
                    case 2:
                        if (!!tags_2_1.done) return [3 /*break*/, 13];
                        tag = tags_2_1.value;
                        nodes = Array.from(this.el.querySelectorAll(tag));
                        _c.label = 3;
                    case 3:
                        _c.trys.push([3, 10, 11, 12]);
                        nodes_1 = (e_6 = void 0, __values(nodes)), nodes_1_1 = nodes_1.next();
                        _c.label = 4;
                    case 4:
                        if (!!nodes_1_1.done) return [3 /*break*/, 9];
                        node = nodes_1_1.value;
                        if (node.__melodijs_mounted)
                            return [3 /*break*/, 8];
                        parent_1 = node.parentElement;
                        skip = false;
                        while (parent_1 && parent_1 !== this.el) {
                            t = parent_1.tagName && parent_1.tagName.toLowerCase();
                            if (t && tags.indexOf(t) !== -1) {
                                // Found a custom element parent
                                // Skip only if it's NOT mounted yet
                                if (!parent_1.__melodijs_mounted) {
                                    skip = true;
                                    break;
                                }
                                // If it IS mounted, we should NOT skip - this handles slot content
                                // The parent component is already set up, so we can mount this child
                            }
                            parent_1 = parent_1.parentElement;
                        }
                        if (skip)
                            return [3 /*break*/, 8];
                        compDef = allComponents[tag];
                        comp = new Component(compDef);
                        // set logical parent so events can bubble even if DOM structure differs
                        try {
                            comp._parent = this;
                        }
                        catch (e) { }
                        _c.label = 5;
                    case 5:
                        _c.trys.push([5, 7, , 8]);
                        return [4 /*yield*/, comp.mount(node, this.app)];
                    case 6:
                        _c.sent();
                        node.__melodijs_mounted = true;
                        return [3 /*break*/, 8];
                    case 7:
                        e_5 = _c.sent();
                        console.error('Error mounting nested component:', tag, e_5);
                        return [3 /*break*/, 8];
                    case 8:
                        nodes_1_1 = nodes_1.next();
                        return [3 /*break*/, 4];
                    case 9: return [3 /*break*/, 12];
                    case 10:
                        e_6_1 = _c.sent();
                        e_6 = { error: e_6_1 };
                        return [3 /*break*/, 12];
                    case 11:
                        try {
                            if (nodes_1_1 && !nodes_1_1.done && (_b = nodes_1.return)) _b.call(nodes_1);
                        }
                        finally { if (e_6) throw e_6.error; }
                        return [7 /*endfinally*/];
                    case 12:
                        tags_2_1 = tags_2.next();
                        return [3 /*break*/, 2];
                    case 13: return [3 /*break*/, 16];
                    case 14:
                        e_7_1 = _c.sent();
                        e_7 = { error: e_7_1 };
                        return [3 /*break*/, 16];
                    case 15:
                        try {
                            if (tags_2_1 && !tags_2_1.done && (_a = tags_2.return)) _a.call(tags_2);
                        }
                        finally { if (e_7) throw e_7.error; }
                        return [7 /*endfinally*/];
                    case 16: return [2 /*return*/];
                }
            });
        });
    };
    /**
     * Mount nested components within a specific DOM node.
     * This is called after v-for or v-if dynamically inserts new nodes.
     */
    Component.prototype._mountComponentsIn = function (node) {
        return __awaiter(this, void 0, void 0, function () {
            var globalComponents, localComponents, allComponents, tags, tags_3, tags_3_1, tag, compDef, comp, e_8, nodes, nodes_2, nodes_2_1, childNode, parent_2, skip, t, compDef, comp, e_9, e_10_1, e_11_1;
            var e_11, _a, e_10, _b;
            return __generator(this, function (_c) {
                switch (_c.label) {
                    case 0:
                        if (!this.app || !node)
                            return [2 /*return*/];
                        globalComponents = this.app.components || {};
                        localComponents = this.components || {};
                        allComponents = __assign(__assign({}, globalComponents), localComponents);
                        tags = Object.keys(allComponents);
                        _c.label = 1;
                    case 1:
                        _c.trys.push([1, 18, 19, 20]);
                        tags_3 = __values(tags), tags_3_1 = tags_3.next();
                        _c.label = 2;
                    case 2:
                        if (!!tags_3_1.done) return [3 /*break*/, 17];
                        tag = tags_3_1.value;
                        if (!(node.tagName && node.tagName.toLowerCase() === tag)) return [3 /*break*/, 6];
                        if (!!node.__melodijs_mounted) return [3 /*break*/, 6];
                        compDef = allComponents[tag];
                        comp = new Component(compDef);
                        try {
                            comp._parent = this;
                        }
                        catch (e) { }
                        _c.label = 3;
                    case 3:
                        _c.trys.push([3, 5, , 6]);
                        return [4 /*yield*/, comp.mount(node, this.app)];
                    case 4:
                        _c.sent();
                        node.__melodijs_mounted = true;
                        return [3 /*break*/, 6];
                    case 5:
                        e_8 = _c.sent();
                        console.error('Error mounting component:', tag, e_8);
                        return [3 /*break*/, 6];
                    case 6:
                        nodes = Array.from(node.querySelectorAll(tag));
                        _c.label = 7;
                    case 7:
                        _c.trys.push([7, 14, 15, 16]);
                        nodes_2 = (e_10 = void 0, __values(nodes)), nodes_2_1 = nodes_2.next();
                        _c.label = 8;
                    case 8:
                        if (!!nodes_2_1.done) return [3 /*break*/, 13];
                        childNode = nodes_2_1.value;
                        if (childNode.__melodijs_mounted)
                            return [3 /*break*/, 12];
                        parent_2 = childNode.parentElement;
                        skip = false;
                        while (parent_2 && parent_2 !== node) {
                            t = parent_2.tagName && parent_2.tagName.toLowerCase();
                            if (t && tags.indexOf(t) !== -1) {
                                // Found a custom element parent - skip only if NOT mounted yet
                                if (!parent_2.__melodijs_mounted) {
                                    skip = true;
                                    break;
                                }
                            }
                            parent_2 = parent_2.parentElement;
                        }
                        if (skip)
                            return [3 /*break*/, 12];
                        compDef = allComponents[tag];
                        comp = new Component(compDef);
                        try {
                            comp._parent = this;
                        }
                        catch (e) { }
                        _c.label = 9;
                    case 9:
                        _c.trys.push([9, 11, , 12]);
                        return [4 /*yield*/, comp.mount(childNode, this.app)];
                    case 10:
                        _c.sent();
                        childNode.__melodijs_mounted = true;
                        return [3 /*break*/, 12];
                    case 11:
                        e_9 = _c.sent();
                        console.error('Error mounting nested component:', tag, e_9);
                        return [3 /*break*/, 12];
                    case 12:
                        nodes_2_1 = nodes_2.next();
                        return [3 /*break*/, 8];
                    case 13: return [3 /*break*/, 16];
                    case 14:
                        e_10_1 = _c.sent();
                        e_10 = { error: e_10_1 };
                        return [3 /*break*/, 16];
                    case 15:
                        try {
                            if (nodes_2_1 && !nodes_2_1.done && (_b = nodes_2.return)) _b.call(nodes_2);
                        }
                        finally { if (e_10) throw e_10.error; }
                        return [7 /*endfinally*/];
                    case 16:
                        tags_3_1 = tags_3.next();
                        return [3 /*break*/, 2];
                    case 17: return [3 /*break*/, 20];
                    case 18:
                        e_11_1 = _c.sent();
                        e_11 = { error: e_11_1 };
                        return [3 /*break*/, 20];
                    case 19:
                        try {
                            if (tags_3_1 && !tags_3_1.done && (_a = tags_3.return)) _a.call(tags_3);
                        }
                        finally { if (e_11) throw e_11.error; }
                        return [7 /*endfinally*/];
                    case 20: return [2 /*return*/];
                }
            });
        });
    };
    Component.prototype._createEffect = function (fn) {
        var cleanup = this.reactivity.createEffect(fn);
        if (typeof cleanup === 'function')
            this._effects.push(cleanup);
        return cleanup;
    };
    return Component;
}());
export { Component };
// small helper to create app (Vue-like)
function createApp(options) {
    return new MelodiJS(options);
}
export { createApp, MelodiJS };
