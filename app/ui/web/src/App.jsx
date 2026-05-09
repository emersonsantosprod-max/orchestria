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

const API = {
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
const MODULES = [
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
      <Main view={view} state={state} dispatch={dispatch} blocked={blocked} fileRefs={fileRefs} />
    </div>
  );
}

function Sidebar({ view, setView, session, blocked, bootstrapping }) {
  const items = [
    { id: 'execucao', label: 'Execução',     desc: 'Sessão e módulos' },
    { id: 'config',   label: 'Configuração', desc: 'Bases persistidas' },
  ];
  return (
    <aside style={{
      background: 'var(--msv-chumbo)', color: '#fff',
      display: 'flex', flexDirection: 'column',
      borderRight: '1px solid #000',
    }}>
      <div style={{ padding: '20px 20px 18px', borderBottom: '1px solid #3a3a3a' }}>
        <div style={{ fontSize: 11, fontWeight: 600, letterSpacing: '0.14em', color: 'var(--accent)', textTransform: 'uppercase' }}>
          Manserv
        </div>
        <div style={{ fontSize: 17, fontWeight: 600, lineHeight: 1.15, letterSpacing: '-0.01em', marginTop: 4 }}>
          Automação de<br/>Medição
        </div>
      </div>

      <div style={{ padding: '14px 12px 6px' }}>
        {items.map(it => {
          const active = view === it.id;
          return (
            <button key={it.id}
              onClick={() => !blocked && setView(it.id)}
              disabled={blocked}
              style={{
                width: '100%', textAlign: 'left', padding: '10px 12px',
                borderRadius: 4, border: 'none', cursor: blocked ? 'not-allowed' : 'pointer',
                fontFamily: 'inherit',
                background: active ? 'var(--accent)' : 'transparent',
                color: active ? '#fff' : (blocked ? '#5a5a5a' : '#d4d4d4'),
                fontSize: 14, fontWeight: active ? 600 : 500, marginBottom: 2,
                transition: 'background 120ms',
                display: 'flex', flexDirection: 'column', gap: 2,
              }}
              onMouseEnter={e => { if (!active && !blocked) e.currentTarget.style.background = '#2e2e2e'; }}
              onMouseLeave={e => { if (!active && !blocked) e.currentTarget.style.background = 'transparent'; }}
            >
              <span>{it.label}</span>
              <span style={{ fontSize: 11, fontWeight: 400, color: active ? 'rgba(255,255,255,0.85)' : '#7a7a7a' }}>{it.desc}</span>
            </button>
          );
        })}
      </div>

      <div style={{ marginTop: 'auto', padding: '14px 18px 18px', borderTop: '1px solid #3a3a3a' }}>
        <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: '0.14em', color: '#7a7a7a', textTransform: 'uppercase', marginBottom: 6 }}>
          Sessão
        </div>
        {bootstrapping ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#9a9a9a' }}>
            <Spinner color="#bdbdbd" />
            Verificando…
          </div>
        ) : session.active ? (
          <>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#9be1b3' }}>
              <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#22c55e' }} />
              Ativa
            </div>
            <div style={{ fontSize: 13, fontFamily: 'var(--font-mono)', marginTop: 4, color: '#fff' }}>
              {fmtMes(session.mes_referencia)}
            </div>
          </>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#9a9a9a' }}>
            <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#5a5a5a' }} />
            Inativa
          </div>
        )}
      </div>
    </aside>
  );
}

function Main({ view, state, dispatch, blocked, fileRefs }) {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '1fr 380px',
      gridTemplateRows: '1fr',
      minWidth: 0, minHeight: 0,
    }}>
      <div style={{ overflow: 'auto', minWidth: 0 }}>
        {view === 'execucao'
          ? <ExecucaoView state={state} dispatch={dispatch} blocked={blocked} fileRefs={fileRefs} />
          : <ConfigView   state={state} dispatch={dispatch} blocked={blocked} />}
      </div>
      <LogPanel logs={state.logs} run={state.run} dispatch={dispatch} />
    </div>
  );
}

function ExecucaoView({ state, dispatch, blocked, fileRefs }) {
  const boot = state.bootstrapping;
  return (
    <div style={{ padding: '28px 32px 48px', maxWidth: 920 }}>
      <Header title="Execução" subtitle="Carregue a medição do mês e execute os módulos de lançamento." />
      {state.apiError && (
        <ApiErrorBanner err={state.apiError} onDismiss={() => dispatch({ type: 'API_ERROR', error: null })} />
      )}
      {boot
        ? <SessionBlockSkeleton step={state.bootstrapStep} />
        : <SessionBlock state={state} dispatch={dispatch} blocked={blocked} fileRefs={fileRefs} />}
      <SectionTitle>
        Módulos
        {boot && <BootDot active={state.bootstrapStep === 'modules'} done={false} />}
      </SectionTitle>
      <div style={{ display: 'grid', gap: 10 }}>
        {boot
          ? MODULES.map((m, i) => <ModuleRowSkeleton key={m.id} index={i} step={state.bootstrapStep} />)
          : MODULES.map(m => (
              <ModuleRow key={m.id} module={m} state={state} dispatch={dispatch} blocked={blocked} fileRefs={fileRefs} />
            ))}
      </div>
    </div>
  );
}

function SessionBlock({ state, dispatch, blocked, fileRefs }) {
  const fileRef = useRef(null);
  const { session, run } = state;
  const isLoadingSession = run.action === 'session/medicao';

  function pick() { if (!blocked) fileRef.current?.click(); }
  function onPick(e) {
    const f = e.target.files?.[0]; if (!f) return;
    e.target.value = '';
    dispatch({ type: 'RUN_START', action: 'session/medicao' });
    fileRefs.medicao.current = f;  // C5: hold the actual File for run-time multipart
    API.loadMedicao(f).then(res => {
      dispatch({ type: 'SESSION_LOADED', mes: res.mes_referencia, medicao: res.medicao });
      dispatch({ type: 'RUN_END_OK', summary: 'Sessão ativada' });
    }).catch(err => {
      fileRefs.medicao.current = null;
      dispatch({ type: 'RUN_END_ERR', error: { code: err.code || 'SESSION_NOT_INITIALIZED', message: err.message || 'Falha ao ler medição' } });
    });
  }

  function clear() {
    if (blocked) return;
    fileRefs.medicao.current = null;
    fileRefs.relatorios.current = {};
    dispatch({ type: 'SESSION_CLEARED' });
    dispatch({ type: 'LOG', entry: { ts: new Date().toISOString(), level: 'info', source: 'session', msg: 'Sessão encerrada' } });
  }

  return (
    <Card style={{ padding: 0, marginBottom: 24 }}>
      <div style={{
        display: 'grid', gridTemplateColumns: 'auto 1fr auto',
        alignItems: 'center', gap: 18, padding: '18px 22px',
      }}>
        <StatusOrb ok={session.active} loading={isLoadingSession} step="M" />
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ fontSize: 16, fontWeight: 600 }}>Medição do mês</div>
            {session.active
              ? <Chip kind="ok">Sessão ativa · {fmtMes(session.mes_referencia)}</Chip>
              : <Chip kind="muted">Obrigatória — bloqueia os módulos</Chip>}
          </div>
          <div style={{ fontSize: 13, color: 'var(--fg-muted)', marginTop: 4 }}>
            {session.active
              ? <>Arquivo carregado: <FileChip name={session.medicao.name} size={session.medicao.size} /> · ativada {fmtRelative(session.loadedAt)}.</>
              : 'Selecione a planilha de medição para extrair mes_referencia e ativar a sessão.'}
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          {session.active && (
            <Button kind="ghost" disabled={blocked} onClick={clear}>Encerrar sessão</Button>
          )}
          <Button
            kind={session.active ? 'secondary' : 'primary'}
            disabled={blocked}
            running={isLoadingSession}
            onClick={pick}
          >
            {session.active ? 'Trocar medição' : 'Carregar medição'}
          </Button>
          <input ref={fileRef} type="file" accept=".xlsx,.xls" hidden onChange={onPick} />
        </div>
      </div>
    </Card>
  );
}

function ModuleRow({ module, state, dispatch, blocked, fileRefs }) {
  const m = state.modules[module.id] || {};
  const session = state.session;
  const sessionOff = !session.active;
  const needsRel = module.deps.includes('relatorio');
  const needsSqlite = module.deps.includes('sqlite');
  const sqliteReady = !needsSqlite || !!state.config.bd_distribuicao;
  const relReady = !needsRel || !!m.relatorio;
  const canRun = !blocked && !sessionOff && relReady && sqliteReady;
  const running = state.run.action === module.id;

  const meta = state.modulesMeta?.[module.id];
  let reason = null;
  if (sessionOff) reason = 'Carregue a medição para liberar este módulo.';
  else if (!relReady) reason = 'Selecione o relatório do módulo.';
  else if (!sqliteReady) reason = 'Configure bd_distribuicao em Configuração.';
  else if (meta && !meta.enabled && meta.reason) reason = meta.reason;

  const fileRef = useRef(null);
  function pickRel() { if (!sessionOff && !blocked) fileRef.current?.click(); }
  function onRel(e) {
    const f = e.target.files?.[0]; if (!f) return;
    e.target.value = '';
    fileRefs.relatorios.current[module.id] = f;  // C5: keep blob for multipart
    dispatch({ type: 'MODULE_RELATORIO', module: module.id, file: { name: f.name, size: f.size } });
    dispatch({ type: 'LOG', entry: { ts: new Date().toISOString(), level: 'info', source: module.id, msg: `Relatório anexado: ${f.name}` } });
  }
  function run() {
    if (!canRun) return;
    dispatch({ type: 'RUN_START', action: module.id });
    const payload = {
      medicao: fileRefs.medicao.current,
      relatorio: fileRefs.relatorios.current[module.id] || null,
    };
    API.run(module.id, payload).then(res => {
      const summary = res.summary
        || `${res.processados ?? 0} processado(s) · ${res.atualizados ?? 0} atualizado(s) · ${(res.inconsistencias?.length ?? 0)} inconsistência(s)`;
      dispatch({ type: 'RUN_END_OK', module: module.id, summary, output: res.arquivo_saida || null });
    }).catch(err => {
      dispatch({ type: 'RUN_END_ERR', module: module.id, error: { code: err.code || 'RUN_FAILED', message: err.message || 'Falha de execução' } });
    });
  }

  return (
    <Card style={{
      padding: 0,
      borderColor: sessionOff ? 'var(--border)' : 'var(--border)',
      opacity: sessionOff ? 0.7 : 1,
    }}>
      <div style={{
        display: 'grid', gridTemplateColumns: 'auto 1fr auto',
        gap: 16, alignItems: 'center', padding: '16px 20px',
      }}>
        <StatusOrb
          ok={m.lastRun?.ok}
          err={m.lastRun && !m.lastRun.ok}
          loading={running}
          step={MODULES.findIndex(x => x.id === module.id) + 1}
        />
        <div style={{ minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            <div style={{ fontSize: 15, fontWeight: 600 }}>{module.label}</div>
            {m.lastRun?.ok && <Chip kind="ok">Concluído</Chip>}
            {m.lastRun && !m.lastRun.ok && <Chip kind="err">{m.lastRun.error}</Chip>}
            {needsRel && !m.relatorio && <Chip kind="muted">Relatório necessário</Chip>}
            {needsSqlite && !sqliteReady && <Chip kind="muted">SQLite necessário</Chip>}
          </div>
          <div style={{ fontSize: 13, color: 'var(--fg-muted)', marginTop: 3 }}>
            {module.blurb}
          </div>
          {m.relatorio && (
            <div style={{ marginTop: 8 }}>
              <FileChip name={m.relatorio.name} size={m.relatorio.size}
                onChange={pickRel} disabled={blocked || sessionOff} />
            </div>
          )}
          {m.lastRun?.ok && m.lastRun.summary && (
            <div style={{ fontSize: 12.5, color: '#1b6e3f', marginTop: 8, fontWeight: 500 }}>
              ✓ {m.lastRun.summary}
            </div>
          )}
          {reason && (
            <div style={{ fontSize: 12, color: 'var(--fg-subtle)', marginTop: 6, fontStyle: 'italic' }}>
              {reason}
            </div>
          )}
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {needsRel && (
            <>
              <Button kind="secondary" disabled={blocked || sessionOff} onClick={pickRel}>
                {m.relatorio ? 'Trocar relatório' : 'Anexar relatório'}
              </Button>
              <input ref={fileRef} type="file" accept=".xlsx,.xls,.csv" hidden onChange={onRel} />
            </>
          )}
          <Button kind="primary" disabled={!canRun} running={running} onClick={run}>
            Executar
          </Button>
        </div>
      </div>
    </Card>
  );
}

function ConfigView({ state, dispatch, blocked }) {
  const boot = state.bootstrapping;
  return (
    <div style={{ padding: '28px 32px 48px', maxWidth: 920 }}>
      <Header title="Configuração" subtitle="Bases persistidas pelo backend. Independem da sessão de medição." />
      {state.apiError && (
        <ApiErrorBanner err={state.apiError} onDismiss={() => dispatch({ type: 'API_ERROR', error: null })} />
      )}
      <div style={{ display: 'grid', gap: 10 }}>
        {boot
          ? CONFIG_KEYS.map((c, i) => <ConfigRowSkeleton key={c.key} index={i} step={state.bootstrapStep} />)
          : CONFIG_KEYS.map(c => (
              <ConfigRow key={c.key} cfg={c} value={state.config[c.key]} dispatch={dispatch} blocked={blocked} />
            ))}
      </div>
      <div style={{ marginTop: 24, fontSize: 12, color: 'var(--fg-muted)' }}>
        Os arquivos enviados aqui são gravados no servidor e ficam disponíveis para os módulos de execução. Não dependem da medição ativa.
      </div>
    </div>
  );
}

function ConfigRow({ cfg, value, dispatch, blocked }) {
  const ref = useRef(null);
  const [saving, setSaving] = useState(false);
  function pick() { if (!blocked) ref.current?.click(); }
  function onFile(e) {
    const f = e.target.files?.[0]; if (!f) return;
    e.target.value = '';
    setSaving(true);
    API.saveConfig(cfg.key, f).then(() => {
      dispatch({ type: 'CONFIG_SAVED', key: cfg.key, file: { name: f.name } });
      dispatch({ type: 'LOG', entry: { ts: new Date().toISOString(), level: 'ok', source: `config/${cfg.key}`, msg: `Salvo: ${f.name}` } });
    }).catch(err => {
      dispatch({ type: 'API_ERROR', error: { code: err.code || 'CONFIG_FAILED', message: err.message || 'Falha ao salvar configuração' } });
      dispatch({ type: 'LOG', entry: { ts: new Date().toISOString(), level: 'err', source: `config/${cfg.key}`, msg: err.message || 'Falha ao salvar configuração' } });
    }).finally(() => setSaving(false));
  }
  return (
    <Card style={{ padding: 0 }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr auto', gap: 16, alignItems: 'center', padding: '16px 20px' }}>
        <StatusOrb ok={!!value} loading={saving} step={
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
          </svg>
        } />
        <div>
          <div style={{ fontSize: 15, fontWeight: 600 }}>{cfg.label}</div>
          <div style={{ fontSize: 13, color: 'var(--fg-muted)', marginTop: 3 }}>{cfg.hint}</div>
          {value
            ? <div style={{ marginTop: 8 }}><FileChip name={value.name} /> <span style={{ fontSize: 11, color: 'var(--fg-muted)', marginLeft: 8 }}>salvo {fmtRelative(value.savedAt)}</span></div>
            : <div style={{ fontSize: 12, color: 'var(--fg-subtle)', marginTop: 6, fontStyle: 'italic' }}>Nenhum arquivo carregado.</div>}
        </div>
        <Button kind={value ? 'secondary' : 'primary'} disabled={blocked} running={saving} onClick={pick}>
          {value ? 'Substituir' : 'Enviar arquivo'}
        </Button>
        <input ref={ref} type="file" accept={cfg.accept} hidden onChange={onFile} />
      </div>
    </Card>
  );
}


