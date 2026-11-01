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
import { createApp as baseCreateApp, Component, MelodiJS } from './melodijs.js';
import { MelodiRouter } from './router.js';
import { MelodiStore } from './store.js';
export var DEFAULT_DELIMITERS = ['[[', ']]'];
/**
 * Helper officiel MELODI pour créer une application réactive MelodiJS
 * avec délimiteurs automatiquement configurés à ['[[', ']]'] (évitant les collisions avec Jinja2).
 *
 * @param options Options du composant racine (data, computed, methods, watch, hooks, etc.)
 * @returns Instance de l'application MelodiJS
 */
export function createApp(options) {
    if (options === void 0) { options = {}; }
    var mergedOptions = __assign({ delimiters: DEFAULT_DELIMITERS }, options);
    return baseCreateApp(mergedOptions);
}
/**
 * Helper pour définir un composant MelodiJS avec délimiteurs ['[[', ']]'] par défaut.
 *
 * @param def Définition du composant
 * @returns Définition avec délimiteurs configurés
 */
export function defineComponent(def) {
    if (def === void 0) { def = {}; }
    return __assign({ delimiters: DEFAULT_DELIMITERS }, def);
}
// Re-exports des primitives et sous-systèmes
export { baseCreateApp, Component, MelodiJS, MelodiRouter, MelodiStore };
// Export par défaut
var MelodiBundle = {
    createApp: createApp,
    defineComponent: defineComponent,
    baseCreateApp: baseCreateApp,
    Component: Component,
    MelodiJS: MelodiJS,
    MelodiRouter: MelodiRouter,
    MelodiStore: MelodiStore,
    DEFAULT_DELIMITERS: DEFAULT_DELIMITERS
};
// Exposition globale optionnelle pour l'environnement navigateur
if (typeof window !== 'undefined') {
    var globalWindow = window;
    globalWindow.melodi = globalWindow.melodi || {};
    globalWindow.melodi.createApp = createApp;
    globalWindow.melodi.defineComponent = defineComponent;
    globalWindow.melodi.MelodiRouter = MelodiRouter;
    globalWindow.melodi.MelodiStore = MelodiStore;
}
export default MelodiBundle;
