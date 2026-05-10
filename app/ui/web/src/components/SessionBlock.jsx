import { Card, Button, StatusOrb, Chip, FileChip } from './primitives.jsx';
import { fmtMes, fmtRelative } from './format.js';
import { registrar, escolherArquivoNativo } from '../modules/registry/index.js';

export default function SessionBlock({ state, dispatch, blocked }) {
  const { session, run } = state;
  const isLoadingSession = run.action === 'session/medicao';

  async function selecionar() {
    if (blocked) return;
    const caminho = await escolherArquivoNativo('Selecionar medição');
    if (!caminho) {
      if (!window.pywebview?.api?.escolher_arquivo) {
        dispatch({
          type: 'API_ERROR',
          error: {
            code: 'NATIVE_DIALOG_UNAVAILABLE',
            message: 'Dialog nativo disponível apenas no build empacotado (pywebview).',
          },
        });
      }
      return;
    }
    dispatch({ type: 'RUN_START', action: 'session/medicao' });
    try {
      const res = await registrar('medicao', caminho);
      dispatch({
        type: 'SESSION_LOADED',
        mes: res.mes_referencia,
        medicao: { name: caminho.split(/[\\/]/).pop(), caminho, size: 0 },
      });
      dispatch({ type: 'RUN_END_OK', summary: 'Sessão ativada' });
    } catch (err) {
      dispatch({
        type: 'RUN_END_ERR',
        error: {
          code: err.code || 'SESSION_NOT_INITIALIZED',
          message: err.message || 'Falha ao registrar medição',
        },
      });
    }
  }

  function clear() {
    if (blocked) return;
    dispatch({ type: 'SESSION_CLEARED' });
    dispatch({
      type: 'LOG',
      entry: { ts: new Date().toISOString(), level: 'info', source: 'session', msg: 'Sessão encerrada' },
    });
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
              ? <>Arquivo registrado: <FileChip name={session.medicao?.name || 'medição registrada'} /> · ativada {fmtRelative(session.loadedAt)}.</>
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
            onClick={selecionar}
          >
            {session.active ? 'Trocar medição' : 'Selecionar medição'}
          </Button>
        </div>
      </div>
    </Card>
  );
}
