// Reducer + initialState do app — fora do componente para facilitar
// testes unitários e evitar acoplamento com App.jsx.

export const initialState = {
  bootstrapping: true,
  bootstrapStep: 'session',  // 'session' | 'config' | 'modules' | 'done'
  session: { active: false, mes_referencia: null, medicao: null, loadedAt: null },
  run: { lock: false, action: null, startedAt: null },
  modules: {
    treinamentos:  {},
    ferias:        {},
    atestados:     {},
    'validar-hr':  {},
    'validar-dist':{},
  },
  modulesMeta: {},  // { [id]: { enabled, reason } } — backend gating, source of truth
  config: {},
  logs: [],
  apiError: null,
  logsCollapsed: false,
};

export function reducer(state, ev) {
  switch (ev.type) {
    case 'BOOTSTRAP_STEP':
      return { ...state, bootstrapStep: ev.step };
    case 'BOOTSTRAP_DONE':
      return {
        ...state,
        bootstrapping: false,
        bootstrapStep: 'done',
        session: ev.session ?? state.session,
        modulesMeta: ev.modulesMeta ?? state.modulesMeta,
        config: ev.config ?? state.config,
      };
    case 'SESSION_LOADED':
      return { ...state, session: { active: true, mes_referencia: ev.mes, medicao: ev.medicao, loadedAt: new Date().toISOString() }, apiError: null };
    case 'SESSION_CLEARED':
      return { ...state, session: initialState.session, modules: initialState.modules };
    case 'RUN_START':
      return { ...state, run: { lock: true, action: ev.action, startedAt: Date.now() }, apiError: null };
    case 'RUN_END_OK':
      return {
        ...state,
        run: initialState.run,
        modules: ev.module
          ? { ...state.modules, [ev.module]: { ...state.modules[ev.module], lastRun: { ok: true, at: new Date().toISOString(), summary: ev.summary, output: ev.output || null } } }
          : state.modules,
      };
    case 'RUN_END_ERR':
      return {
        ...state,
        run: initialState.run,
        apiError: ev.error,
        modules: ev.module
          ? { ...state.modules, [ev.module]: { ...state.modules[ev.module], lastRun: { ok: false, at: new Date().toISOString(), error: ev.error.code } } }
          : state.modules,
      };
    case 'MODULE_RELATORIO':
      return { ...state, modules: { ...state.modules, [ev.module]: { ...state.modules[ev.module], relatorio: ev.file } } };
    case 'CONFIG_SAVED':
      return { ...state, config: { ...state.config, [ev.key]: { name: ev.file.name, caminho: ev.file.caminho || null, savedAt: new Date().toISOString() } } };
    case 'LOG':
      return { ...state, logs: [...state.logs.slice(-499), ev.entry] };
    case 'LOGS_CLEAR':
      return { ...state, logs: [] };
    case 'LOGS_TOGGLE':
      return { ...state, logsCollapsed: !state.logsCollapsed };
    case 'API_ERROR':
      return { ...state, apiError: ev.error };
    default: return state;
  }
}
