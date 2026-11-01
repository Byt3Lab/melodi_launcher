import { MelodiJS, Plugin, ComponentDef } from './melodijs.js';
export interface RouteDef {
    path: string;
    component: ComponentDef;
    children?: RouteDef[];
    transition?: string;
}
export interface RouterOptions {
    routes: RouteDef[];
    mode?: 'hash' | 'history';
}
export declare class MelodiRouter implements Plugin {
    routes: RouteDef[];
    mode: 'hash' | 'history';
    currentRoute: any;
    setRoute: any;
    params: any;
    setParams: any;
    query: any;
    setQuery: any;
    matched: any;
    setMatched: any;
    beforeEachHook: ((to: string, from: string, next: (path?: string) => void) => void) | null;
    constructor(options: RouterOptions);
    beforeEach(hook: (to: string, from: string, next: (path?: string) => void) => void): void;
    install(app: MelodiJS): void;
    _getCurrentPath(): string;
    _getCurrentQuery(): Record<string, string>;
    push(path: string): void;
    replace(path: string): void;
    _handleRouteChange(): void;
    _matchRoute(path: string): {
        matched: RouteDef[];
        params: Record<string, string>;
    };
    _extractParams(pattern: string, path: string, partial?: boolean): Record<string, string> | null;
    _createRouterLink(): ComponentDef;
    _createRouterView(app: MelodiJS): ComponentDef;
}
