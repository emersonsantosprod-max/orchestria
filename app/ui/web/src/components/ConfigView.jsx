import { Header, ApiErrorBanner } from './primitives.jsx';
import { ConfigRowSkeleton, SessionBlockSkeleton } from './skeletons.jsx';
import SessionBlock from './SessionBlock.jsx';
import ConfigCard from './ConfigCard.jsx';

export default function ConfigView({ state, dispatch, blocked, configKeys }) {
  const boot = state.bootstrapping;
  const sessionActive = state.session.active;
  const disabledReason = sessionActive ? null : 'anexe a medição primeiro';
  return (
    <div style={{ padding: '28px 32px 48px', maxWidth: 920 }}>
      <Header
        title="Configurações"
        subtitle="Bases persistidas pelo backend. A medição é o ponto de partida."
      />
      {state.apiError && (
        <ApiErrorBanner err={state.apiError} onDismiss={() => dispatch({ type: 'API_ERROR', error: null })} />
      )}
      {boot
        ? <SessionBlockSkeleton step={state.bootstrapStep} />
        : <SessionBlock state={state} dispatch={dispatch} blocked={blocked} />}
      <div style={{ display: 'grid', gap: 10 }}>
        {boot
          ? configKeys.map((c, i) => <ConfigRowSkeleton key={c.key} index={i} step={state.bootstrapStep} />)
          : configKeys.map(c => (
              <ConfigCard
                key={c.key}
                cfg={c}
                value={state.config[c.key]}
                dispatch={dispatch}
                disabled={blocked || !sessionActive}
                disabledReason={disabledReason}
              />
            ))}
      </div>
      <div style={{ marginTop: 24, fontSize: 12, color: 'var(--fg-muted)' }}>
        Os arquivos enviados aqui são gravados no servidor e ficam disponíveis para os módulos de execução.
      </div>
    </div>
  );
}
