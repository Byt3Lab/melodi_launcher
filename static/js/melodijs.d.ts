type SignalRead<T> = () => T;
type SignalWrite<T> = (next: T) => void;
type EffectFn = () => void | (() => void);
type CleanupFn = () => void;
type WatchCallback = (this: any, newVal: any, oldVal: any) => void;
interface WatchOptions {
    handler: WatchCallback;
    immediate?: boolean;
    deep?: boolean;
}
export interface MelodiOptions {
    components?: Record<string, ComponentDef>;
    store?: Record<string, any>;
    data?: () => Record<string, any>;
    methods?: Record<string, (this: any, ...args: any[]) => any>;
    computed?: Record<string, (this: any) => any>;
    watch?: Record<string, WatchCallback | WatchOptions>;
    hooks?: Record<string, (this: any) => void>;
    delimiters?: [string, string];
    template?: string | {
        el?: string;
        url?: string;
    };
}
export interface ComponentDef {
    template?: string | {
        el?: string;
        url?: string;
    };
    delimiters?: [string, string];
    data?: () => Record<string, any>;
    methods?: Record<string, (this: any, ...args: any[]) => any>;
    props?: string[] | Record<string, PropDef>;
    hooks?: Record<string, (this: any) => void>;
    components?: Record<string, ComponentDef>;
    computed?: Record<string, (this: any) => any>;
    watch?: Record<string, WatchCallback | WatchOptions>;
}
export interface PropDef {
    type?: any;
    default?: any;
}
declare class MelodiReactive {
    private _currentEffect;
    constructor();
    createSignal<T>(value: T): [SignalRead<T>, SignalWrite<T>];
    createEffect(fn: EffectFn): CleanupFn;
    createEffectWithCleanup(fn: () => CleanupFn | void): CleanupFn;
    createMemo<T>(fn: () => T): SignalRead<T>;
}
export interface Plugin {
    install: (app: MelodiJS, options?: any) => void;
}
declare class MelodiJS {
    options: MelodiOptions;
    root: Element | null;
    components: Record<string, ComponentDef>;
    _mountedComponents: Component[];
    reactivity: MelodiReactive;
    store: any;
    _plugins: Set<Plugin>;
    constructor(options: MelodiOptions);
    use(plugin: Plugin, options?: any): this;
    mount(target: string | Element): Promise<any[]>;
    _isDescendantOfCustom(node: Element, customTags: string[]): boolean;
    _makeReactiveStore(initial: Record<string, any>): any;
}
export declare class Component {
    template: string | {
        el?: string;
        url?: string;
    };
    delimiters?: [string, string] | null;
    dataFn: (this: any) => Record<string, any>;
    methodsDef: Record<string, (this: any, ...args: any[]) => any>;
    propsDef: string[] | Record<string, PropDef> | null;
    hooks: Record<string, (this: any) => void>;
    components: Record<string, ComponentDef>;
    computedDef: Record<string, (this: any) => any>;
    watchDef: Record<string, WatchCallback | WatchOptions>;
    el: Element | null;
    app: MelodiJS | null;
    state: any;
    methods: Record<string, Function>;
    _listeners: {
        node: Element;
        ev: string;
        fn: EventListener;
    }[];
    _effects: CleanupFn[];
    _events: Record<string, Function[]>;
    _slotSource: Element | null;
    _fragment: DocumentFragment | null;
    _postMountEffects: (() => void)[];
    _signals: Record<string, [SignalRead<any>, SignalWrite<any>]>;
    reactivity: MelodiReactive | null;
    _parent: Component | null;
    constructor(def: ComponentDef);
    mount(el: Element, app: MelodiJS): Promise<boolean>;
    _readPropsFromEl(el: Element): Record<string, any>;
    _coerceAttrValue(val: string): any;
    _gatherDeclaredProps(): Record<string, PropDef> | null;
    _coercePropValue(val: any, def: PropDef): any;
    _makeReactive(obj: any): any;
    _makeReactiveArray(arr: any[], setter: SignalWrite<any>): any[];
    _evalExpression(expr: string, scope: any): any;
    _render(isInitial: boolean): Promise<boolean>;
    _compile(): Promise<void>;
    _processNodeList(nodes: NodeListOf<ChildNode> | Node[], scope?: any): DocumentFragment;
    _walk(node: Node, scope: any): Node | DocumentFragment;
    _handleConditional(startNode: Element, nodes: Node[], startIndex: number, scope: any): {
        anchor: Comment;
        nextIndex: number;
    };
    _handleVFor(node: Element, scope: any): Comment;
    _escape(v: any): string;
    _bindEvents(): void;
    _bindModels(): void;
    unmount(): void;
    _mountNestedComponents(): Promise<void>;
    /**
     * Mount nested components within a specific DOM node.
     * This is called after v-for or v-if dynamically inserts new nodes.
     */
    _mountComponentsIn(node: Element): Promise<void>;
    _createEffect(fn: EffectFn): CleanupFn;
}
declare function createApp(options: MelodiOptions): MelodiJS;
export { createApp, MelodiJS };
