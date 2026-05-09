import { Spinner } from './primitives.jsx';
import { fmtMes } from './format.js';

export default function Sidebar({ view, setView, session, blocked, bootstrapping }) {
  const items = [
    { id: 'config',   label: 'Configurações', desc: 'Bases persistidas' },
    { id: 'execucao', label: 'Execução',      desc: 'Sessão e módulos' },
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
              type="button"
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
