import { useEffect, useRef, useState } from 'react';
import { RunDot } from './primitives.jsx';

export default function LogPanel({ logs, run, dispatch }) {
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
          type="button"
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
