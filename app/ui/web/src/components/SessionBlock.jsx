import { useRef } from 'react';
import { Card, Button, StatusOrb, Chip, FileChip } from './primitives.jsx';
import { fmtMes, fmtRelative } from './format.js';
import { API } from '../App.jsx';

export default function SessionBlock({ state, dispatch, blocked, fileRefs }) {
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
