import { useRef, useState } from 'react';
import { Card, Button, StatusOrb, FileChip } from './primitives.jsx';
import { fmtRelative } from './format.js';
import { API } from '../App.jsx';

export default function ConfigCard({ cfg, value, dispatch, disabled, disabledReason }) {
  const ref = useRef(null);
  const [saving, setSaving] = useState(false);
  function pick() { if (!disabled) ref.current?.click(); }
  function onFile(e) {
    const f = e.target.files?.[0]; if (!f) return;
    e.target.value = '';
    setSaving(true);
    API.saveConfig(cfg.key, f).then(() => {
      dispatch({ type: 'CONFIG_SAVED', key: cfg.key, file: { name: f.name } });
      dispatch({ type: 'LOG', entry: { ts: new Date().toISOString(), level: 'ok', source: `config/${cfg.key}`, msg: `Salvo: ${f.name}` } });
    }).catch(err => {
      dispatch({ type: 'API_ERROR', error: { code: err.code || 'CONFIG_FAILED', message: err.message || 'Falha ao salvar configuração' } });
      dispatch({ type: 'LOG', entry: { ts: new Date().toISOString(), level: 'err', source: `config/${cfg.key}`, msg: err.message || 'Falha ao salvar configuração' } });
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
          {disabled && disabledReason && (
            <div style={{ fontSize: 12, color: 'var(--fg-subtle)', marginTop: 6, fontStyle: 'italic' }}>
              {disabledReason}
            </div>
          )}
        </div>
        <Button
          kind={value ? 'secondary' : 'primary'}
          disabled={disabled}
          running={saving}
          onClick={pick}
          title={disabled ? disabledReason : undefined}
        >
          {value ? 'Substituir' : 'Enviar arquivo'}
        </Button>
        <input ref={ref} type="file" accept={cfg.accept} hidden onChange={onFile} />
      </div>
    </Card>
  );
}
