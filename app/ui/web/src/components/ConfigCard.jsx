import { useState } from 'react';
import { Card, Button, StatusOrb, FileChip } from './primitives.jsx';
import { fmtRelative } from './format.js';
import { registrar, escolherArquivoNativo } from '../modules/registry/index.js';

// Mapping cfg.key → tipo do registry endpoint.
const TIPO_POR_KEY = {
  base_treinamentos: 'treinamentos',
  base_cobranca:     'cobranca',
  base_tags:         'tags',
  bd_distribuicao:   'distribuicao',
};

export default function ConfigCard({ cfg, value, dispatch, disabled, disabledReason }) {
  const [saving, setSaving] = useState(false);

  async function selecionar() {
    if (disabled) return;
    const tipo = TIPO_POR_KEY[cfg.key];
    if (!tipo) {
      dispatch({
        type: 'API_ERROR',
        error: { code: 'CONFIG_KEY_DESCONHECIDA', message: `Sem tipo registry para ${cfg.key}` },
      });
      return;
    }
    const caminho = await escolherArquivoNativo(`Selecionar ${cfg.label}`);
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
    setSaving(true);
    try {
      await registrar(tipo, caminho);
      const nome = caminho.split(/[\\/]/).pop();
      dispatch({ type: 'CONFIG_SAVED', key: cfg.key, file: { name: nome, caminho } });
      dispatch({
        type: 'LOG',
        entry: { ts: new Date().toISOString(), level: 'ok', source: `config/${cfg.key}`, msg: `Registrado: ${nome}` },
      });
    } catch (err) {
      dispatch({
        type: 'API_ERROR',
        error: { code: err.code || 'CONFIG_FAILED', message: err.message || 'Falha ao registrar arquivo' },
      });
      dispatch({
        type: 'LOG',
        entry: { ts: new Date().toISOString(), level: 'err', source: `config/${cfg.key}`, msg: err.message || 'Falha ao registrar arquivo' },
      });
    } finally {
      setSaving(false);
    }
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
            ? <div style={{ marginTop: 8 }}><FileChip name={value.name} /> <span style={{ fontSize: 11, color: 'var(--fg-muted)', marginLeft: 8 }}>registrado {fmtRelative(value.savedAt)}</span></div>
            : <div style={{ fontSize: 12, color: 'var(--fg-subtle)', marginTop: 6, fontStyle: 'italic' }}>Nenhum arquivo registrado.</div>}
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
          onClick={selecionar}
          title={disabled ? disabledReason : undefined}
        >
          {value ? 'Trocar arquivo' : 'Selecionar arquivo'}
        </Button>
      </div>
    </Card>
  );
}
