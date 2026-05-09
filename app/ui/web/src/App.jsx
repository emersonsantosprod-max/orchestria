// Automação de Medição — React app
// Ported from data/entrada/ui_kits/automacao_medicao/App.jsx (Babel-standalone prototype)
// to a Vite ES-module project. Logic and visual structure unchanged.
//
// Architecture mirrors the backend execution model:
//   1. SESSION (medição mandatory) → activates session
//   2. MODULES (require active session, some require relatório or SQLite)
//   3. CONFIG (independent, persisted)
//   GLOBAL: run_lock (one execution at a time), WS log stream (read-only)
//
// UI rules:
//  - Modules disabled until session active.
//  - When run_lock is held: only the log panel is interactive; everything else freezes.
//  - File inputs scoped per concern: medição (session-global), relatório (per module),
//    config uploads (persistent base files).
//  - Errors come from the API only; UI never invents validation messages beyond
//    "did you load X first" gating.

import { useState, useRef, useEffect, useReducer } from 'react';
import {
  Header, SectionTitle, Card, Button, Spinner, StatusOrb,
  Chip, FileChip, RunDot, ApiErrorBanner,
} from './components/primitives.jsx';
import {
  bootPhase, SkelBar, SkelOrb, BootDot,
  SessionBlockSkeleton, ModuleRowSkeleton, ConfigRowSkeleton,
} from './components/skeletons.jsx';
import { fmtMes, fmtRelative } from './components/format.js';
import LogPanel from './components/LogPanel.jsx';
import Sidebar from './components/Sidebar.jsx';
import SessionBlock from './components/SessionBlock.jsx';
import ConfigCard from './components/ConfigCard.jsx';
import ConfigView from './components/ConfigView.jsx';
import ModuleRow from './components/ModuleRow.jsx';
import ExecucaoView from './components/ExecucaoView.jsx';

const BOOTSTRAP_MIN_MS = 1200;

// ─────────────────────────────────────────────────────────────
// Backend contract — endpoints that exist today.
// Modules without a route yield a clean RUN_NOT_IMPLEMENTED.
// ─────────────────────────────────────────────────────────────
const ENDPOINTS = {
  treinamentos:    { url: '/api/run/treinamentos',  relatorioField: 'catalogo' },
  ferias:          { url: '/api/run/ferias',        relatorioField: 'relatorio' },
  atestados:       { url: '/api/run/atestado',      relatorioField: 'relatorio' },
  'validar-dist':  { url: '/api/run/distribuicao',  relatorioField: null },
  // 'validar-hr': { url: '/api/run/validar-hr',    relatorioField: null },
};

async function fetchJSON(url, init) {
  const r = await fetch(url, init);
  if (!r.ok) {
    let msg = r.statusText;
    try { const j = await r.json(); msg = j.detail || j.message || msg; } catch { /* ignore */ }
    const err = new Error(msg); err.code = `HTTP_${r.status}`; throw err;
  }
  return r.json();
}

// ─────────────────────────────────────────────────────────────
// STATE MODEL
// ─────────────────────────────────────────────────────────────
const initialState = {
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
};

function reducer(state, ev) {
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
      return { ...state, config: { ...state.config, [ev.key]: { name: ev.file.name, savedAt: new Date().toISOString() } } };
    case 'LOG':
      return { ...state, logs: [...state.logs.slice(-499), ev.entry] };
    case 'LOGS_CLEAR':
      return { ...state, logs: [] };
    case 'API_ERROR':
      return { ...state, apiError: ev.error };
    default: return state;
  }
}

// ─────────────────────────────────────────────────────────────
// API — real backend (FastAPI in app/api/). Endpoints not yet implemented
// degrade with RUN_NOT_IMPLEMENTED so the UI stays usable as routes land.
// ─────────────────────────────────────────────────────────────
const CONFIG_ENDPOINTS = {
  base_treinamentos: '/api/config/catalogo',
};

export const API = {
  async loadMedicao(file) {
    const fd = new FormData();
    fd.append('arquivo', file);
    await fetchJSON('/api/config/medicao', { method: 'POST', body: fd });
    const initial = await fetchJSON('/api/initial-data');
    return {
      mes_referencia: initial.mes_referencia,
      medicao: { name: file.name, size: file.size },
    };
  },
  initialData() { return fetchJSON('/api/initial-data'); },

  run(action, { medicao, relatorio } = {}) {
    const cfg = ENDPOINTS[action];
    if (!cfg) {
      const err = new Error(`Endpoint /api/run/${action} ainda não implementado no backend.`);
      err.code = 'RUN_NOT_IMPLEMENTED';
      return Promise.reject(err);
    }
    if (!medicao) {
      const err = new Error('Carregue a medição antes de executar.');
      err.code = 'SESSION_NOT_INITIALIZED';
      return Promise.reject(err);
    }
    const fd = new FormData();
    fd.append('medicao', medicao);
    if (cfg.relatorioField && relatorio) fd.append(cfg.relatorioField, relatorio);
    return fetchJSON(cfg.url, { method: 'POST', body: fd });
  },

  async saveConfig(key, file) {
    const url = CONFIG_ENDPOINTS[key];
    if (!url) {
      const err = new Error(`POST /api/config/${key} ainda não implementado no backend.`);
      err.code = 'CONFIG_NOT_IMPLEMENTED';
      throw err;
    }
    const fd = new FormData();
    fd.append('arquivo', file);
    return fetchJSON(url, { method: 'POST', body: fd });
  },
};

// ─────────────────────────────────────────────────────────────
// LOG STREAM (simulates WS /ws/log)
// ─────────────────────────────────────────────────────────────
const LOG_SCRIPTS = {
  'session/medicao': [
    ['info', 'Lendo arquivo de medição…'],
    ['info', 'Validando estrutura da planilha (abas: Resumo, Folha, Eventos)'],
    ['info', 'Extraindo mes_referencia da célula Resumo!B2'],
    ['ok',   'Sessão ativada · mes_referencia = 2026-04'],
  ],
  treinamentos: [
    ['info', 'Carregando relatório SOC…'],
    ['info', 'Cruzando matrículas com base de cobrança'],
    ['info', '236 linhas válidas · 3 sem contrato ativo no período'],
    ['warn', '3 inconsistências serão exportadas para revisão'],
    ['ok',   'Lançamento aplicado · ver Validação para detalhes'],
  ],
  ferias: [
    ['info', 'Lendo relatório geral de férias'],
    ['info', '184 colaboradores · 218 períodos detectados'],
    ['info', '12 períodos aplicados na medição atual'],
    ['ok',   'Concluído'],
  ],
  atestados: [
    ['info', 'Lendo relatório de atestados'],
    ['info', '47 atestados encontrados'],
    ['warn', '1 atestado fora do período da medição'],
    ['ok',   'Lançamento concluído'],
  ],
  'validar-hr': [
    ['info', 'Comparando HR com base de cobrança'],
    ['info', 'Verificando datas de admissão/desligamento'],
    ['ok',   'Nenhuma divergência encontrada'],
  ],
  'validar-dist': [
    ['info', 'Lendo bd_distribuicao.sqlite'],
    ['info', 'Aplicando rateio por centro de custo'],
    ['warn', '2 contratos sem rateio definido'],
    ['ok',   'Validação concluída'],
  ],
};

function useLogStream(dispatch, run) {
  useEffect(() => {
    if (!run.lock) return;
    const action = run.action;
    const lines = LOG_SCRIPTS[action] || ['[idle]'];
    let i = 0;
    const id = setInterval(() => {
      if (i >= lines.length) { clearInterval(id); return; }
      const [level, msg] = lines[i++];
      dispatch({ type: 'LOG', entry: { ts: new Date().toISOString(), level, source: action, msg } });
    }, 180);
    return () => clearInterval(id);
  }, [run.lock, run.action, dispatch]);
}

// ─────────────────────────────────────────────────────────────
// MODULES & CONFIG descriptors
// ─────────────────────────────────────────────────────────────
export const MODULES = [
  { id: 'treinamentos',  label: 'Treinamentos',  deps: ['relatorio'], blurb: 'Aplica os lançamentos de treinamentos (SOC) na medição ativa.' },
  { id: 'ferias',        label: 'Férias',        deps: ['relatorio'], blurb: 'Aplica descontos e devoluções a partir do relatório geral de férias.' },
  { id: 'atestados',     label: 'Atestados',     deps: ['relatorio'], blurb: 'Aplica atestados emitidos no período da medição.' },
  { id: 'validar-hr',    label: 'Validar HR',    deps: [],            blurb: 'Verifica consistência entre HR e base de cobrança. Não requer arquivo.' },
  { id: 'validar-dist',  label: 'Validar Dist.', deps: ['sqlite'],    blurb: 'Cruza distribuição com bd_distribuicao.sqlite (Config).' },
];

const CONFIG_KEYS = [
  { key: 'base_cobranca',     label: 'Base de cobrança',     hint: 'Persistida. Usada por todos os módulos.', accept: '.xlsx,.xls' },
  { key: 'base_treinamentos', label: 'Base de treinamentos', hint: 'Catálogo de cursos e cargas horárias.',   accept: '.xlsx,.xls' },
  { key: 'bd_distribuicao',   label: 'BD Distribuição',      hint: 'SQLite. Requerido para Validar Dist.',     accept: '.sqlite,.db' },
];

// Pure helper: deterministic gating reason for a module run.
// Priority order is the source of truth for `canRun` UX.
export function getRunBlockReason(moduleId, state) {
  const mod = MODULES.find(x => x.id === moduleId);
  if (!mod) return { blocked: true, reason: 'Módulo desconhecido.' };
  const m = state.modules[moduleId] || {};
  const sessionOff = !state.session.active;
  const needsRel = mod.deps.includes('relatorio');
  const needsSqlite = mod.deps.includes('sqlite');
  const sqliteReady = !needsSqlite || !!state.config.bd_distribuicao;
  const relReady = !needsRel || !!m.relatorio;
  const baseTr = moduleId === 'treinamentos' ? !!state.config.base_treinamentos : true;
  const baseFe = moduleId === 'ferias'       ? !!state.config.base_cobranca    : true;
  const meta = state.modulesMeta?.[moduleId];

  if (sessionOff)            return { blocked: true, reason: 'Carregue a medição para liberar este módulo.' };
  if (!relReady)             return { blocked: true, reason: 'Selecione o relatório do módulo.' };
  if (!sqliteReady)          return { blocked: true, reason: 'Configure bd_distribuicao em Configurações.' };
  if (!baseTr)               return { blocked: true, reason: 'Configure Base de Treinamentos em Configurações.' };
  if (!baseFe)               return { blocked: true, reason: 'Configure Base de Férias em Configurações.' };
  if (meta && !meta.enabled) return { blocked: true, reason: meta.reason || 'Indisponível.' };
  return { blocked: false, reason: null };
}

// ─────────────────────────────────────────────────────────────
// APP SHELL
// ─────────────────────────────────────────────────────────────
export default function App() {
  const [state, dispatch] = useReducer(reducer, initialState);
  const [view, setView] = useState('execucao');
  // C5: keep actual File blobs in refs (reducer holds only metadata).
  const medicaoFileRef = useRef(null);
  const relatorioFilesRef = useRef({});
  useLogStream(dispatch, state.run);

  // Bootstrap — phased reveal while we probe DB state via /api/initial-data.
  // BOOTSTRAP_DONE is gated on both the API result AND a minimum visible
  // window (BOOTSTRAP_MIN_MS) so the loading state is perceivable on fast
  // localhost responses.
  useEffect(() => {
    let cancelled = false;
    const log = (level, msg) => dispatch({
      type: 'LOG',
      entry: { ts: new Date().toISOString(), level, source: 'bootstrap', msg },
    });
    log('info', 'Verificando estado persistido no servidor…');
    const t1 = setTimeout(() => {
      if (cancelled) return;
      dispatch({ type: 'BOOTSTRAP_STEP', step: 'config' });
      log('info', 'Verificando bases persistidas (config)…');
    }, 450);
    const t2 = setTimeout(() => {
      if (cancelled) return;
      dispatch({ type: 'BOOTSTRAP_STEP', step: 'modules' });
      log('info', 'Verificando módulos disponíveis…');
    }, 850);

    const minDelay = new Promise(r => setTimeout(r, BOOTSTRAP_MIN_MS));
    Promise.all([API.initialData(), minDelay])
      .then(([res]) => {
        if (cancelled) return;
        const session = res.measurement_status === 'MEASUREMENT_READY'
          ? { active: true, mes_referencia: res.mes_referencia, medicao: { name: 'medição registrada', size: 0 }, loadedAt: new Date().toISOString() }
          : initialState.session;
        const cfg = {};
        Object.entries(res.config || {}).forEach(([k, v]) => {
          if (v.ready) cfg[k] = { name: v.name, savedAt: v.saved_at };
        });
        Object.entries(res.tables || {}).forEach(([t, present]) => {
          log(present ? 'ok' : 'warn', `tabela ${t}: ${present ? 'presente' : 'ausente'}`);
        });
        dispatch({ type: 'BOOTSTRAP_DONE', session, modulesMeta: res.modules || {}, config: cfg });
        log('ok', 'Estado restaurado do servidor');
      })
      .catch(async err => {
        await minDelay;
        if (cancelled) return;
        log('error', `Falha no bootstrap: ${err.message || err.code || 'erro'}`);
        dispatch({ type: 'BOOTSTRAP_DONE' });
      });
    return () => { cancelled = true; clearTimeout(t1); clearTimeout(t2); };
  }, []);

  const blocked = state.run.lock || state.bootstrapping;
  const fileRefs = { medicao: medicaoFileRef, relatorios: relatorioFilesRef };

  return (
    <div data-screen-label="Automação de Medição" style={{
      display: 'grid',
      gridTemplateColumns: '232px 1fr',
      gridTemplateRows: '1fr',
      height: '100vh', background: 'var(--bg-subtle)',
      fontFamily: 'var(--font-sans)', color: 'var(--fg)',
    }}>
      <Sidebar view={view} setView={setView} session={state.session} blocked={blocked} bootstrapping={state.bootstrapping} />
      <Main view={view} setView={setView} state={state} dispatch={dispatch} blocked={blocked} fileRefs={fileRefs} />
    </div>
  );
}


function Main({ view, setView, state, dispatch, blocked, fileRefs }) {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '1fr 380px',
      gridTemplateRows: '1fr',
      minWidth: 0, minHeight: 0,
    }}>
      <div style={{ overflow: 'auto', minWidth: 0 }}>
        {view === 'execucao'
          ? <ExecucaoView state={state} dispatch={dispatch} blocked={blocked} fileRefs={fileRefs} setView={setView} />
          : <ConfigView   state={state} dispatch={dispatch} blocked={blocked} fileRefs={fileRefs} configKeys={CONFIG_KEYS} />}
      </div>
      <LogPanel logs={state.logs} run={state.run} dispatch={dispatch} />
    </div>
  );
}




