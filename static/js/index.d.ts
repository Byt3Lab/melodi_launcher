import { createApp as baseCreateApp, Component, MelodiJS, MelodiOptions, ComponentDef } from './melodijs.js';
import { MelodiRouter, RouterOptions, RouteDef } from './router.js';
import { MelodiStore, StoreOptions } from './store.js';
export declare const DEFAULT_DELIMITERS: [string, string];
/**
 * Helper officiel MELODI pour créer une application réactive MelodiJS
 * avec délimiteurs automatiquement configurés à ['[[', ']]'] (évitant les collisions avec Jinja2).
 *
 * @param options Options du composant racine (data, computed, methods, watch, hooks, etc.)
 * @returns Instance de l'application MelodiJS
 */
export declare function createApp(options?: MelodiOptions): MelodiJS;
/**
 * Helper pour définir un composant MelodiJS avec délimiteurs ['[[', ']]'] par défaut.
 *
 * @param def Définition du composant
 * @returns Définition avec délimiteurs configurés
 */
export declare function defineComponent(def?: ComponentDef): ComponentDef;
export { baseCreateApp, Component, MelodiJS, MelodiRouter, MelodiStore };
export type { MelodiOptions, ComponentDef, RouterOptions, RouteDef, StoreOptions };
declare const MelodiBundle: {
    createApp: typeof createApp;
    defineComponent: typeof defineComponent;
    baseCreateApp: typeof baseCreateApp;
    Component: typeof Component;
    MelodiJS: typeof MelodiJS;
    MelodiRouter: typeof MelodiRouter;
    MelodiStore: typeof MelodiStore;
    DEFAULT_DELIMITERS: [string, string];
};
export default MelodiBundle;
