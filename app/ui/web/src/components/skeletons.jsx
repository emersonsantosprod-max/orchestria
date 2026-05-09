// Bootstrap skeletons — phased reveal: session → config → modules.
// Each row passes pending → checking → done as bootstrapStep advances.

import { Card, Spinner } from './primitives.jsx';

export function bootPhase(targetStep, currentStep) {
  const order = ['session', 'config', 'modules', 'done'];
  const a = order.indexOf(targetStep);
  const b = order.indexOf(currentStep);
  if (b < a) return 'pending';
  if (b === a) return 'checking';
  return 'done';
}

export function SkelBar({ w = '100%', h = 10, mt = 0, intense = false }) {
  return (
    <span style={{
      display: 'inline-block',
      width: w, height: h, marginTop: mt,
      borderRadius: 3,
      background: intense
        ? 'linear-gradient(90deg, #d9d9d9 0%, #ebebeb 50%, #d9d9d9 100%)'
        : 'linear-gradient(90deg, #e6e6e6 0%, #f1f1f1 50%, #e6e6e6 100%)',
      backgroundSize: '200% 100%',
      animation: 'msvshimmer 1.4s linear infinite',
      verticalAlign: 'middle',
    }} />
  );
}

export function SkelOrb({ checking }) {
  return (
    <div style={{
      width: 32, height: 32, borderRadius: '50%',
      background: checking ? 'rgba(255,70,10,0.10)' : '#e6e6e6',
      border: checking ? '1.5px dashed var(--accent)' : '1.5px solid #d9d9d9',
      display: 'grid', placeItems: 'center',
      flexShrink: 0,
      animation: checking ? 'msvpulse 1.4s ease-in-out infinite' : 'none',
    }}>
      {checking && <Spinner color="var(--accent)" />}
    </div>
  );
}

export function BootDot({ active, done }) {
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 6,
      marginLeft: 10, fontSize: 10,
      color: active ? 'var(--accent)' : (done ? 'var(--fg-muted)' : 'var(--fg-subtle)'),
      letterSpacing: '0.06em',
    }}>
      <span style={{
        width: 6, height: 6, borderRadius: '50%',
        background: active ? 'var(--accent)' : (done ? '#1b6e3f' : '#c2c2c2'),
        animation: active ? 'msvpulse 1.4s ease-in-out infinite' : 'none',
      }} />
      {active ? 'verificando…' : done ? 'pronto' : 'aguardando'}
    </span>
  );
}

export function SessionBlockSkeleton({ step }) {
  const phase = bootPhase('session', step);
  return (
    <Card style={{ padding: 0, marginBottom: 24 }} aria-busy="true">
      <div style={{
        display: 'grid', gridTemplateColumns: 'auto 1fr auto',
        alignItems: 'center', gap: 18, padding: '18px 22px',
      }}>
        <SkelOrb checking={phase === 'checking'} />
        <div style={{ minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <SkelBar w={150} h={14} intense />
            <SkelBar w={120} h={18} />
          </div>
          <div style={{ marginTop: 10 }}>
            <SkelBar w="62%" h={10} />
          </div>
        </div>
        <SkelBar w={138} h={36} />
      </div>
    </Card>
  );
}

export function ModuleRowSkeleton({ index, step }) {
  const phase = bootPhase('modules', step);
  return (
    <Card style={{ padding: 0, opacity: phase === 'pending' ? 0.55 : 1, transition: 'opacity 200ms' }} aria-busy="true">
      <div style={{
        display: 'grid', gridTemplateColumns: 'auto 1fr auto',
        gap: 16, alignItems: 'center', padding: '16px 20px',
      }}>
        <SkelOrb checking={phase === 'checking'} />
        <div style={{ minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <SkelBar w={120 + (index % 3) * 24} h={14} intense />
            {phase === 'checking' && <SkelBar w={92} h={16} />}
          </div>
          <div style={{ marginTop: 8 }}>
            <SkelBar w="74%" h={9} />
          </div>
          {phase === 'checking' && (
            <div style={{ marginTop: 10, display: 'flex', alignItems: 'center', gap: 8, fontSize: 11, color: 'var(--fg-subtle)', fontFamily: 'var(--font-mono)' }}>
              <Spinner color="var(--accent)" />
              <span>verificando módulo no banco…</span>
            </div>
          )}
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <SkelBar w={120} h={36} />
          <SkelBar w={92} h={36} />
        </div>
      </div>
    </Card>
  );
}

export function ConfigRowSkeleton({ index, step }) {
  const phase = bootPhase('config', step);
  return (
    <Card style={{ padding: 0, opacity: phase === 'pending' ? 0.55 : 1, transition: 'opacity 200ms' }} aria-busy="true">
      <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr auto', gap: 16, alignItems: 'center', padding: '16px 20px' }}>
        <SkelOrb checking={phase === 'checking'} />
        <div style={{ minWidth: 0 }}>
          <SkelBar w={140 + (index % 2) * 30} h={14} intense />
          <div style={{ marginTop: 8 }}><SkelBar w="68%" h={9} /></div>
          {phase === 'checking' && (
            <div style={{ marginTop: 10, display: 'flex', alignItems: 'center', gap: 8, fontSize: 11, color: 'var(--fg-subtle)', fontFamily: 'var(--font-mono)' }}>
              <Spinner color="var(--accent)" />
              <span>verificando arquivo persistido…</span>
            </div>
          )}
        </div>
        <SkelBar w={120} h={36} />
      </div>
    </Card>
  );
}
