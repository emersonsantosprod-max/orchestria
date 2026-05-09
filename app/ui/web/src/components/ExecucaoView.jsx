import { Header, SectionTitle, Card, ApiErrorBanner } from './primitives.jsx';
import { BootDot, ModuleRowSkeleton } from './skeletons.jsx';
import ModuleRow from './ModuleRow.jsx';
import { MODULES } from '../App.jsx';

export default function ExecucaoView({ state, dispatch, blocked, fileRefs, setView }) {
  const boot = state.bootstrapping;
  const sessionActive = state.session.active;
  return (
    <div style={{ padding: '28px 32px 48px', maxWidth: 920 }}>
      <Header title="Execução" subtitle="Execute os módulos de lançamento da medição ativa." />
      {state.apiError && (
        <ApiErrorBanner err={state.apiError} onDismiss={() => dispatch({ type: 'API_ERROR', error: null })} />
      )}
      {!boot && !sessionActive ? (
        <Card style={{ padding: 0, marginBottom: 24 }}>
          <div style={{ padding: '20px 22px', fontSize: 14, color: 'var(--fg-muted)' }}>
            Anexe a medição em{' '}
            <button
              type="button"
              onClick={() => setView && setView('config')}
              style={{
                background: 'transparent', border: 'none', padding: 0,
                color: 'var(--accent)', fontWeight: 600, cursor: 'pointer',
                fontFamily: 'inherit', fontSize: 'inherit',
              }}
            >Configurações</button> para liberar os módulos.
          </div>
        </Card>
      ) : null}
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
