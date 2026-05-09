// UI primitives — presentational, stateless. No domain logic.

export function Spinner({ color = '#fff' }) {
  return (
    <span style={{
      width: 14, height: 14, borderRadius: '50%',
      border: `2px solid ${color === '#fff' ? 'rgba(255,255,255,0.4)' : 'rgba(0,0,0,0.18)'}`,
      borderTopColor: color,
      animation: 'msvspin 700ms linear infinite', display: 'inline-block',
    }} />
  );
}

export function Header({ title, subtitle }) {
  return (
    <div style={{ marginBottom: 22 }}>
      <h1 style={{ fontWeight: 600, fontSize: 26, margin: 0, letterSpacing: '-0.02em' }}>{title}</h1>
      <div style={{ fontSize: 13, color: 'var(--fg-muted)', marginTop: 4 }}>{subtitle}</div>
    </div>
  );
}

export function SectionTitle({ children }) {
  return (
    <div style={{
      fontSize: 11, fontWeight: 600, textTransform: 'uppercase',
      letterSpacing: '0.12em', color: 'var(--fg-muted)',
      margin: '4px 0 10px',
    }}>{children}</div>
  );
}

export function Card({ children, style }) {
  return (
    <div style={{
      background: '#fff', border: '1px solid var(--border)',
      borderRadius: 8, ...(style || {}),
    }}>{children}</div>
  );
}

export function Button({ kind = 'primary', children, disabled, running, onClick, title }) {
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
      type="button"
      onClick={disabled ? undefined : onClick}
      disabled={disabled}
      title={title}
      style={{ ...base, ...styles[kind] }}
      onMouseEnter={e => { if (!disabled && kind === 'primary') e.currentTarget.style.background = 'var(--accent-pressed)'; if (!disabled && kind === 'secondary') e.currentTarget.style.background = 'var(--bg-subtle)'; if (!disabled && kind === 'ghost') e.currentTarget.style.background = 'var(--bg-subtle)'; }}
      onMouseLeave={e => { if (!disabled && kind === 'primary') e.currentTarget.style.background = 'var(--accent)'; if (!disabled && kind === 'secondary') e.currentTarget.style.background = '#fff'; if (!disabled && kind === 'ghost') e.currentTarget.style.background = 'transparent'; }}
    >
      {running && <Spinner color={kind === 'primary' ? '#fff' : 'var(--fg)'} />}
      {running ? 'Executando…' : children}
    </button>
  );
}

export function StatusOrb({ ok, err, loading, step }) {
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

export function Chip({ kind = 'muted', children }) {
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

export function FileChip({ name, size, onChange, disabled }) {
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
        <button type="button" onClick={onChange} disabled={disabled} style={{
          background: 'transparent', border: 'none',
          cursor: disabled ? 'not-allowed' : 'pointer',
          color: disabled ? 'var(--fg-disabled)' : 'var(--accent)',
          fontSize: 11, fontFamily: 'inherit', padding: 0, marginLeft: 2,
        }}>trocar</button>
      )}
    </span>
  );
}

export function RunDot({ running }) {
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

export function ApiErrorBanner({ err, onDismiss }) {
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
      <button type="button" onClick={onDismiss} style={{
        background: 'transparent', border: 'none', cursor: 'pointer',
        color: '#7a1c10', fontSize: 18, lineHeight: 1, padding: 0,
      }}>×</button>
    </div>
  );
}
