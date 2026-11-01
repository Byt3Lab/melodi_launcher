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
var __spreadArray = (this && this.__spreadArray) || function (to, from, pack) {
    if (pack || arguments.length === 2) for (var i = 0, l = from.length, ar; i < l; i++) {
        if (ar || !(i in from)) {
            if (!ar) ar = Array.prototype.slice.call(from, 0, i);
            ar[i] = from[i];
        }
    }
    return to.concat(ar || Array.prototype.slice.call(from));
};
var MelodiStore = /** @class */ (function () {
    function MelodiStore(options) {
        var _this = this;
        this._app = null;
        this._actions = {};
        this._getters = {};
        // Initialize state (will be made reactive during install)
        this._state = options.state ? options.state() : {};
        // Setup actions
        if (options.actions) {
            Object.keys(options.actions).forEach(function (key) {
                _this._actions[key] = options.actions[key];
            });
        }
        // Setup getters (will be made reactive during install)
        if (options.getters) {
            Object.keys(options.getters).forEach(function (key) {
                var getterFn = options.getters[key];
                // We'll bind this later when we have reactivity
                _this._getters[key] = getterFn;
            });
        }
    }
    Object.defineProperty(MelodiStore.prototype, "state", {
        get: function () {
            return this._state;
        },
        enumerable: false,
        configurable: true
    });
    MelodiStore.prototype.install = function (app) {
        var e_1, _a;
        var _this = this;
        this._app = app;
        // Make state reactive using app's reactivity system
        var reactiveState = {};
        var _loop_1 = function (key) {
            var _d = __read(app.reactivity.createSignal(this_1._state[key]), 2), getter = _d[0], setter = _d[1];
            // Handle array reactivity
            var initialValue = this_1._state[key];
            if (Array.isArray(initialValue)) {
                initialValue = this_1._makeReactiveArray(initialValue, setter);
                setter(initialValue); // Update signal to hold proxy
            }
            Object.defineProperty(reactiveState, key, {
                get: getter,
                set: function (newValue) {
                    if (Array.isArray(newValue)) {
                        newValue = _this._makeReactiveArray(newValue, setter);
                    }
                    setter(newValue);
                },
                enumerable: true,
                configurable: true
            });
        };
        var this_1 = this;
        try {
            for (var _b = __values(Object.keys(this._state)), _c = _b.next(); !_c.done; _c = _b.next()) {
                var key = _c.value;
                _loop_1(key);
            }
        }
        catch (e_1_1) { e_1 = { error: e_1_1 }; }
        finally {
            try {
                if (_c && !_c.done && (_a = _b.return)) _a.call(_b);
            }
            finally { if (e_1) throw e_1.error; }
        }
        this._state = reactiveState;
        // Make getters reactive
        var computedGetters = {};
        Object.keys(this._getters).forEach(function (key) {
            var getterFn = _this._getters[key];
            var memo = app.reactivity.createMemo(function () { return getterFn(_this._state); });
            Object.defineProperty(computedGetters, key, {
                get: memo,
                enumerable: true,
                configurable: true
            });
        });
        // Create store object with state, getters, and dispatch
        var store = {
            state: this._state,
            getters: computedGetters,
            dispatch: function (actionName) {
                var args = [];
                for (var _i = 1; _i < arguments.length; _i++) {
                    args[_i - 1] = arguments[_i];
                }
                var action = _this._actions[actionName];
                if (!action) {
                    console.error("Action '".concat(actionName, "' not found in store"));
                    return;
                }
                var context = {
                    state: _this._state,
                    dispatch: store.dispatch
                };
                return action.call.apply(action, __spreadArray([context], __read(args), false));
            }
        };
        // Replace the simple store with our MelodiStore
        app.store = store;
    };
    MelodiStore.prototype._makeReactiveArray = function (arr, setter) {
        var mutatingMethods = ['push', 'pop', 'shift', 'unshift', 'splice', 'sort', 'reverse'];
        var self = this;
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
                        // If pushing objects, we might want to wrap them? 
                        // But for now, just let them be added. 
                        // Accessing them later via get() will wrap them.
                        var result = Array.prototype[prop].apply(target, args);
                        setter(proxy); // Trigger reactivity
                        return result;
                    };
                }
                // Deep reactivity: if value is object, wrap it
                if (value && typeof value === 'object') {
                    return self._makeDeepReactive(value, function () { return setter(proxy); });
                }
                return value;
            },
            set: function (target, prop, value) {
                target[prop] = value;
                setter(proxy); // Trigger reactivity
                return true;
            }
        });
        return proxy;
    };
    MelodiStore.prototype._makeDeepReactive = function (obj, trigger) {
        // Avoid re-wrapping proxies
        if (obj.__isProxy)
            return obj;
        return new Proxy(obj, {
            get: function (target, prop) {
                var value = target[prop];
                if (prop === '__isProxy')
                    return true;
                // Recursive deep reactivity
                if (value && typeof value === 'object') {
                    return new Proxy(value, {
                        get: function (t, p) {
                            if (p === '__isProxy')
                                return true;
                            return t[p];
                        },
                        set: function (t, p, v) {
                            t[p] = v;
                            trigger();
                            return true;
                        }
                    });
                }
                return value;
            },
            set: function (target, prop, value) {
                target[prop] = value;
                trigger();
                return true;
            }
        });
    };
    return MelodiStore;
}());
export { MelodiStore };
