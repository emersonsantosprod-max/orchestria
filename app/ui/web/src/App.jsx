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
import LogPanel from './components/LogPanel.jsx';
import Sidebar from './components/Sidebar.jsx';
import ConfigView from './components/ConfigView.jsx';
import ExecucaoView from './components/ExecucaoView.jsx';
import { reducer, initialState } from './modules/lifecycle/reducer.js';
import { getRunBlockReason as _gatingGetRunBlockReason } from './modules/gating/index.js';

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
// API — real backend (FastAPI in app/api/). Path-based registry após
// Entrega 4a; medição e bases vêm de /api/registry/<tipo>. Execute
// envia apenas o relatório do módulo (multipart) — backend lê medição
// do registry pelo Conn.
// ─────────────────────────────────────────────────────────────
export const API = {
  initialData() { return fetchJSON('/api/initial-data'); },

  run(action, { relatorio } = {}) {
    const cfg = ENDPOINTS[action];
    if (!cfg) {
      const err = new Error(`Endpoint /api/run/${action} ainda não implementado no backend.`);
      err.code = 'RUN_NOT_IMPLEMENTED';
      return Promise.reject(err);
    }
    const fd = new FormData();
    if (cfg.relatorioField && relatorio) fd.append(cfg.relatorioField, relatorio);
    return fetchJSON(cfg.url, { method: 'POST', body: fd });
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
    ['info', 'Cruzando matrículas com Base de Férias'],
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
    ['info', 'Comparando HR com Base de Férias'],
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
  { id: 'validar-hr',    label: 'Validar HR',    deps: [],            blurb: 'Verifica consistência entre HR e Base de Férias. Não requer arquivo.' },
  { id: 'validar-dist',  label: 'Validar Dist.', deps: ['sqlite'],    blurb: 'Cruza distribuição com bd_distribuicao.sqlite (Config).' },
];

const CONFIG_KEYS = [
  { key: 'base_treinamentos', label: 'Base de Treinamentos', hint: 'Catálogo de cursos e cargas horárias.',   accept: '.xlsx,.xls' },
  { key: 'base_cobranca',     label: 'Base de Férias',       hint: 'Persistida. Usada por todos os módulos.', accept: '.xlsx,.xls' },
  { key: 'bd_distribuicao',   label: 'BD Distribuição',      hint: 'SQLite. Requerido para Validar Dist.',     accept: '.sqlite,.db' },
];

// Re-export do helper canônico (single source of truth em modules/gating).
export const getRunBlockReason = _gatingGetRunBlockReason;

// ─────────────────────────────────────────────────────────────
// APP SHELL
// ─────────────────────────────────────────────────────────────
export default function App() {
  const [state, dispatch] = useReducer(reducer, initialState);
  const [view, setView] = useState('config');
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
  const collapsed = !!state.logsCollapsed;
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: collapsed ? '1fr 0px' : '1fr 380px',
      gridTemplateRows: '1fr',
      minWidth: 0, minHeight: 0,
      position: 'relative',
    }}>
      <div style={{ overflow: 'auto', minWidth: 0 }}>
        {view === 'execucao'
          ? <ExecucaoView state={state} dispatch={dispatch} blocked={blocked} fileRefs={fileRefs} setView={setView} />
          : <ConfigView   state={state} dispatch={dispatch} blocked={blocked} configKeys={CONFIG_KEYS} />}
      </div>
      <LogPanel logs={state.logs} run={state.run} dispatch={dispatch} collapsed={collapsed} />
      {collapsed && (
        <button
          type="button"
          onClick={() => dispatch({ type: 'LOGS_TOGGLE' })}
          aria-label="Mostrar log"
          title="Mostrar log"
          style={{
            position: 'absolute', right: 18, bottom: 18,
            background: 'var(--msv-chumbo)', color: '#fff',
            border: 'none', borderRadius: 999,
            padding: '10px 16px', fontSize: 12, fontWeight: 600,
            letterSpacing: '0.04em', textTransform: 'uppercase',
            cursor: 'pointer', boxShadow: '0 4px 12px rgba(0,0,0,0.25)',
            zIndex: 10,
          }}
        >Mostrar log</button>
      )}
    </div>
  );
}




