import { useRef } from 'react';
import { Card, Button, StatusOrb, Chip, FileChip } from './primitives.jsx';
import { API, MODULES, getRunBlockReason } from '../App.jsx';

export default function ModuleRow({ module, state, dispatch, blocked, fileRefs }) {
  const m = state.modules[module.id] || {};
  const session = state.session;
  const sessionOff = !session.active;
  const needsRel = module.deps.includes('relatorio');
  const needsSqlite = module.deps.includes('sqlite');
  const sqliteReady = !needsSqlite || !!state.config.bd_distribuicao;
  const block = getRunBlockReason(module.id, state);
  const canRun = !blocked && !block.blocked;
  const reason = block.reason;
  const running = state.run.action === module.id;

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
          <Button kind="primary" disabled={!canRun} running={running} onClick={run} title={!canRun ? reason : undefined}>
            Executar
          </Button>
        </div>
      </div>
    </Card>
  );
}
