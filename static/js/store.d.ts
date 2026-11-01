import { MelodiJS, Plugin } from './melodijs.js';
export interface StoreOptions {
    state: () => Record<string, any>;
    actions?: Record<string, (this: StoreContext, ...args: any[]) => any>;
    getters?: Record<string, (state: any) => any>;
}
interface StoreContext {
    state: any;
    dispatch: (actionName: string, ...args: any[]) => any;
}
export declare class MelodiStore implements Plugin {
    private _state;
    private _actions;
    private _getters;
    private _app;
    constructor(options: StoreOptions);
    get state(): any;
    install(app: MelodiJS): void;
    private _makeReactiveArray;
    private _makeDeepReactive;
}
export {};
