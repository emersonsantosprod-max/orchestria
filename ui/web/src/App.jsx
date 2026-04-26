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

// ─────────────────────────────────────────────────────────────
// STATE MODEL
// ─────────────────────────────────────────────────────────────
const initialState = {
  session: { active: false, mes_referencia: null, medicao: null, loadedAt: null },
  run: { lock: false, action: null, startedAt: null },
  modules: {
    treinamentos:  {},
    ferias:        {},
    atestados:     {},
    'validar-hr':  {},
    'validar-dist':{},
  },
  config: {},
  logs: [],
  apiError: null,
};

function reducer(state, ev) {
  switch (ev.type) {
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
          ? { ...state.modules, [ev.module]: { ...state.modules[ev.module], lastRun: { ok: true, at: new Date().toISOString(), summary: ev.summary } } }
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
// FAKE API — replace each call with a real fetch when the backend lands.
// ─────────────────────────────────────────────────────────────
const API = {
  loadMedicao(file) {
    return new Promise((resolve) => {
      setTimeout(() => {
        const mes = '2026-04';
        resolve({ mes_referencia: mes, medicao: { name: file.name, size: file.size } });
      }, 900);
    });
  },
  run(action) {
    return new Promise((resolve) => {
      setTimeout(() => {
        const map = {
          treinamentos:  { summary: '236 linhas processadas · 3 inconsistências' },
          ferias:        { summary: '184 colaboradores · 12 períodos aplicados' },
          atestados:     { summary: '47 atestados aplicados · 1 fora do período' },
          'validar-hr':  { summary: 'HR íntegro · 0 divergências encontradas' },
          'validar-dist':{ summary: 'Distribuição validada · 2 contratos sem rateio' },
        };
        resolve(map[action] || { summary: 'OK' });
      }, 1700);
    });
  },
  saveConfig(key, file) {
    return new Promise((resolve) => setTimeout(() => resolve({ key, file: { name: file.name } }), 600));
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
  useLogStream(dispatch, state.run);

  const blocked = state.run.lock;

  return (
    <div data-screen-label="Automação de Medição" style={{
      display: 'grid',
      gridTemplateColumns: '232px 1fr',
      gridTemplateRows: '1fr',
      height: '100vh', background: 'var(--bg-subtle)',
      fontFamily: 'var(--font-sans)', color: 'var(--fg)',
    }}>
      <Sidebar view={view} setView={setView} session={state.session} blocked={blocked} />
      <Main view={view} state={state} dispatch={dispatch} blocked={blocked} />
    </div>
  );
}

function Sidebar({ view, setView, session, blocked }) {
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
        {session.active ? (
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

function Main({ view, state, dispatch, blocked }) {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '1fr 380px',
      gridTemplateRows: '1fr',
      minWidth: 0, minHeight: 0,
    }}>
      <div style={{ overflow: 'auto', minWidth: 0 }}>
        {view === 'execucao'
          ? <ExecucaoView state={state} dispatch={dispatch} blocked={blocked} />
          : <ConfigView   state={state} dispatch={dispatch} blocked={blocked} />}
      </div>
      <LogPanel logs={state.logs} run={state.run} dispatch={dispatch} />
    </div>
  );
}

function ExecucaoView({ state, dispatch, blocked }) {
  return (
    <div style={{ padding: '28px 32px 48px', maxWidth: 920 }}>
      <Header title="Execução" subtitle="Carregue a medição do mês e execute os módulos de lançamento." />
      {state.apiError && (
        <ApiErrorBanner err={state.apiError} onDismiss={() => dispatch({ type: 'API_ERROR', error: null })} />
      )}
      <SessionBlock state={state} dispatch={dispatch} blocked={blocked} />
      <SectionTitle>Módulos</SectionTitle>
      <div style={{ display: 'grid', gap: 10 }}>
        {MODULES.map(m => (
          <ModuleRow key={m.id} module={m} state={state} dispatch={dispatch} blocked={blocked} />
        ))}
      </div>
    </div>
  );
}

function SessionBlock({ state, dispatch, blocked }) {
  const fileRef = useRef(null);
  const { session, run } = state;
  const isLoadingSession = run.action === 'session/medicao';

  function pick() { if (!blocked) fileRef.current?.click(); }
  function onPick(e) {
    const f = e.target.files?.[0]; if (!f) return;
    e.target.value = '';
    dispatch({ type: 'RUN_START', action: 'session/medicao' });
    API.loadMedicao(f).then(res => {
      dispatch({ type: 'SESSION_LOADED', mes: res.mes_referencia, medicao: res.medicao });
      dispatch({ type: 'RUN_END_OK', summary: 'Sessão ativada' });
    }).catch(err => {
      dispatch({ type: 'RUN_END_ERR', error: { code: err.code || 'SESSION_NOT_INITIALIZED', message: err.message || 'Falha ao ler medição' } });
    });
  }

  function clear() {
    if (blocked) return;
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

function ModuleRow({ module, state, dispatch, blocked }) {
  const m = state.modules[module.id] || {};
  const session = state.session;
  const sessionOff = !session.active;
  const needsRel = module.deps.includes('relatorio');
  const needsSqlite = module.deps.includes('sqlite');
  const sqliteReady = !needsSqlite || !!state.config.bd_distribuicao;
  const relReady = !needsRel || !!m.relatorio;
  const canRun = !blocked && !sessionOff && relReady && sqliteReady;
  const running = state.run.action === module.id;

  let reason = null;
  if (sessionOff) reason = 'Carregue a medição para liberar este módulo.';
  else if (!relReady) reason = 'Selecione o relatório do módulo.';
  else if (!sqliteReady) reason = 'Configure bd_distribuicao em Configuração.';

  const fileRef = useRef(null);
  function pickRel() { if (!sessionOff && !blocked) fileRef.current?.click(); }
  function onRel(e) {
    const f = e.target.files?.[0]; if (!f) return;
    e.target.value = '';
    dispatch({ type: 'MODULE_RELATORIO', module: module.id, file: { name: f.name, size: f.size } });
    dispatch({ type: 'LOG', entry: { ts: new Date().toISOString(), level: 'info', source: module.id, msg: `Relatório anexado: ${f.name}` } });
  }
  function run() {
    if (!canRun) return;
    dispatch({ type: 'RUN_START', action: module.id });
    API.run(module.id).then(res => {
      dispatch({ type: 'RUN_END_OK', module: module.id, summary: res.summary });
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
  return (
    <div style={{ padding: '28px 32px 48px', maxWidth: 920 }}>
      <Header title="Configuração" subtitle="Bases persistidas pelo backend. Independem da sessão de medição." />
      {state.apiError && (
        <ApiErrorBanner err={state.apiError} onDismiss={() => dispatch({ type: 'API_ERROR', error: null })} />
      )}
      <div style={{ display: 'grid', gap: 10 }}>
        {CONFIG_KEYS.map(c => (
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

function LogPanel({ logs, run, dispatch }) {
  const ref = useRef(null);
  const [follow, setFollow] = useState(true);

  useEffect(() => {
    if (!follow || !ref.current) return;
    ref.current.scrollTop = ref.current.scrollHeight;
  }, [logs, follow]);

  function onScroll() {
    const el = ref.current;
    if (!el) return;
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 12;
    setFollow(atBottom);
  }

  return (
    <aside className="log-panel" style={{
      background: 'var(--msv-subtom-chumbo)',
      color: '#e8e8e8', display: 'flex', flexDirection: 'column',
      borderLeft: '1px solid #000',
      minHeight: 0,
    }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 10,
        padding: '14px 18px', borderBottom: '1px solid #2a2a2a',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1 }}>
          <RunDot running={run.lock} />
          <div style={{ fontSize: 12, fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: '#e8e8e8' }}>
            {run.lock ? 'Executando' : 'Log de execução'}
          </div>
          {run.lock && (
            <span style={{ fontSize: 11, color: '#9a9a9a', fontFamily: 'var(--font-mono)' }}>
              {run.action}
            </span>
          )}
        </div>
        <button
          onClick={() => dispatch({ type: 'LOGS_CLEAR' })}
          style={{
            background: 'transparent', border: '1px solid #3a3a3a', color: '#bababa',
            padding: '4px 10px', borderRadius: 4, cursor: 'pointer', fontFamily: 'inherit',
            fontSize: 11,
          }}
        >Limpar</button>
      </div>

      <div ref={ref} onScroll={onScroll} style={{
        flex: 1, minHeight: 0, overflow: 'auto',
        fontFamily: 'var(--font-mono)', fontSize: 12, lineHeight: 1.55,
        padding: '12px 14px',
      }}>
        {logs.length === 0 && (
          <div style={{ color: '#5a5a5a', fontStyle: 'italic' }}>
            Aguardando execução…
          </div>
        )}
        {logs.map((l, i) => <LogLine key={i} entry={l} />)}
      </div>

      <div style={{
        padding: '8px 14px', borderTop: '1px solid #2a2a2a',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        fontSize: 11, color: '#6a6a6a',
      }}>
        <span>WS · /ws/log</span>
        <span>{follow ? 'auto-scroll' : 'pausado (role até o fim)'}</span>
      </div>
    </aside>
  );
}

function LogLine({ entry }) {
  const colors = { info: '#bdbdbd', warn: '#e7b85b', error: '#ff6b4a', ok: '#5fd28a' };
  const color = colors[entry.level] || '#bdbdbd';
  const time = entry.ts ? entry.ts.slice(11, 19) : '';
  return (
    <div style={{ display: 'flex', gap: 10, whiteSpace: 'pre-wrap' }}>
      <span style={{ color: '#5a5a5a' }}>{time}</span>
      <span style={{ color, width: 44, flexShrink: 0, textTransform: 'uppercase', fontWeight: 600, fontSize: 10, paddingTop: 1 }}>
        {entry.level}
      </span>
      <span style={{ color: '#7a7a7a', minWidth: 90 }}>{entry.source}</span>
      <span style={{ color: '#e8e8e8', flex: 1 }}>{entry.msg}</span>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// PRIMITIVES
// ─────────────────────────────────────────────────────────────
function Header({ title, subtitle }) {
  return (
    <div style={{ marginBottom: 22 }}>
      <h1 style={{ fontWeight: 600, fontSize: 26, margin: 0, letterSpacing: '-0.02em' }}>{title}</h1>
      <div style={{ fontSize: 13, color: 'var(--fg-muted)', marginTop: 4 }}>{subtitle}</div>
    </div>
  );
}

function SectionTitle({ children }) {
  return (
    <div style={{
      fontSize: 11, fontWeight: 600, textTransform: 'uppercase',
      letterSpacing: '0.12em', color: 'var(--fg-muted)',
      margin: '4px 0 10px',
    }}>{children}</div>
  );
}

function Card({ children, style }) {
  return (
    <div style={{
      background: '#fff', border: '1px solid var(--border)',
      borderRadius: 8, ...(style || {}),
    }}>{children}</div>
  );
}

function Button({ kind = 'primary', children, disabled, running, onClick }) {
  const base = {
    padding: '9px 16px', borderRadius: 4, fontFamily: 'inherit',
    fontSize: 14, fontWeight: 600,
    cursor: disabled ? 'not-allowed' : 'pointer',
    display: 'inline-flex', alignItems: 'center', gap: 8, whiteSpace: 'nowrap',
    transition: 'background 120ms, color 120ms, border-color 120ms',
    border: '1px solid transparent',
  };
  const styles = {
    primary: {
      background: disabled ? '#f3a886' : 'var(--accent)',
      color: '#fff', borderColor: 'transparent',
      opacity: disabled && !running ? 0.85 : 1,
    },
    secondary: {
      background: '#fff',
      color: disabled ? 'var(--fg-disabled)' : 'var(--fg)',
      borderColor: disabled ? 'var(--border)' : 'var(--msv-chumbo)',
    },
    ghost: {
      background: 'transparent',
      color: disabled ? 'var(--fg-disabled)' : 'var(--fg-muted)',
      borderColor: 'transparent',
    },
  };
  return (
    <button
      onClick={disabled ? undefined : onClick}
      disabled={disabled}
      style={{ ...base, ...styles[kind] }}
      onMouseEnter={e => { if (!disabled && kind === 'primary') e.currentTarget.style.background = 'var(--accent-pressed)'; if (!disabled && kind === 'secondary') e.currentTarget.style.background = 'var(--bg-subtle)'; if (!disabled && kind === 'ghost') e.currentTarget.style.background = 'var(--bg-subtle)'; }}
      onMouseLeave={e => { if (!disabled && kind === 'primary') e.currentTarget.style.background = 'var(--accent)'; if (!disabled && kind === 'secondary') e.currentTarget.style.background = '#fff'; if (!disabled && kind === 'ghost') e.currentTarget.style.background = 'transparent'; }}
    >
      {running && <Spinner color={kind === 'primary' ? '#fff' : 'var(--fg)'} />}
      {running ? 'Executando…' : children}
    </button>
  );
}

function Spinner({ color = '#fff' }) {
  return (
    <span style={{
      width: 14, height: 14, borderRadius: '50%',
      border: `2px solid ${color === '#fff' ? 'rgba(255,255,255,0.4)' : 'rgba(0,0,0,0.18)'}`,
      borderTopColor: color,
      animation: 'msvspin 700ms linear infinite', display: 'inline-block',
    }} />
  );
}

function StatusOrb({ ok, err, loading, step }) {
  let bg = 'var(--bg-subtle)', color = 'var(--fg-muted)';
  if (loading) { bg = 'var(--accent)'; color = '#fff'; }
  else if (err) { bg = '#c1271a'; color = '#fff'; }
  else if (ok) { bg = '#1b6e3f'; color = '#fff'; }
  return (
    <div style={{
      width: 32, height: 32, borderRadius: '50%',
      background: bg, color,
      display: 'grid', placeItems: 'center',
      fontSize: 13, fontWeight: 700,
      flexShrink: 0,
    }}>
      {loading
        ? <Spinner color="#fff" />
        : ok
          ? <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="4 12 10 18 20 6"/></svg>
          : err
            ? <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            : step}
    </div>
  );
}

function Chip({ kind = 'muted', children }) {
  const palette = {
    ok:     { bg: '#e6f4ec', fg: '#1b6e3f' },
    err:    { bg: '#fde7e3', fg: '#a01d10' },
    muted:  { bg: 'var(--bg-subtle)', fg: 'var(--fg-muted)' },
    accent: { bg: 'var(--accent-soft)', fg: 'var(--accent-pressed)' },
  };
  const c = palette[kind] || palette.muted;
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 6,
      background: c.bg, color: c.fg,
      fontSize: 11, fontWeight: 600,
      padding: '3px 8px', borderRadius: 999,
      letterSpacing: '0.02em', whiteSpace: 'nowrap',
    }}>{children}</span>
  );
}

function FileChip({ name, size, onChange, disabled }) {
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 8,
      background: 'var(--bg-subtle)',
      padding: '4px 10px', borderRadius: 4,
      fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--fg)',
      maxWidth: '100%',
    }}>
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
      </svg>
      <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{name}</span>
      {size != null && <span style={{ color: 'var(--fg-muted)' }}>· {(size / 1024).toFixed(1)} KB</span>}
      {onChange && (
        <button onClick={onChange} disabled={disabled} style={{
          background: 'transparent', border: 'none',
          cursor: disabled ? 'not-allowed' : 'pointer',
          color: disabled ? 'var(--fg-disabled)' : 'var(--accent)',
          fontSize: 11, fontFamily: 'inherit', padding: 0, marginLeft: 2,
        }}>trocar</button>
      )}
    </span>
  );
}

function RunDot({ running }) {
  return (
    <span style={{
      width: 9, height: 9, borderRadius: '50%',
      background: running ? 'var(--accent)' : '#3a3a3a',
      boxShadow: running ? '0 0 0 4px rgba(255,70,10,0.18)' : 'none',
      animation: running ? 'msvpulse 1.4s ease-in-out infinite' : 'none',
      flexShrink: 0,
    }} />
  );
}

function ApiErrorBanner({ err, onDismiss }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'flex-start', gap: 12,
      background: '#fde7e3', border: '1px solid #f5b8ad',
      color: '#7a1c10', padding: '12px 14px', borderRadius: 6,
      fontSize: 13, marginBottom: 18,
    }}>
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0, marginTop: 1 }}>
        <circle cx="12" cy="12" r="10"/>
        <line x1="12" y1="8" x2="12" y2="12"/>
        <line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
      <div style={{ flex: 1 }}>
        <div style={{ fontWeight: 600, fontFamily: 'var(--font-mono)', fontSize: 12 }}>{err.code}</div>
        <div style={{ marginTop: 2 }}>{err.message}</div>
      </div>
      <button onClick={onDismiss} style={{
        background: 'transparent', border: 'none', cursor: 'pointer',
        color: '#7a1c10', fontSize: 18, lineHeight: 1, padding: 0,
      }}>×</button>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// HELPERS
// ─────────────────────────────────────────────────────────────
function fmtMes(yyyymm) {
  if (!yyyymm) return '';
  const [y, m] = yyyymm.split('-');
  const meses = ['jan','fev','mar','abr','mai','jun','jul','ago','set','out','nov','dez'];
  return `${meses[parseInt(m, 10) - 1]} · ${y}`;
}
function fmtRelative(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  const diff = (Date.now() - d.getTime()) / 1000;
  if (diff < 60) return 'agora';
  if (diff < 3600) return `há ${Math.floor(diff / 60)} min`;
  if (diff < 86400) return `há ${Math.floor(diff / 3600)} h`;
  return d.toLocaleDateString('pt-BR');
}
