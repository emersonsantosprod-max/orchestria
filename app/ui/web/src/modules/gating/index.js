// Gating helpers — single source of truth para razões de bloqueio.
// Espelha a lógica equivalente que pode existir no backend (futuro);
// frontend usa apenas para UX (disabled/tooltip/mensagem).
//
// IMPORTANTE: alterações aqui devem manter a ordem determinística de
// prioridade documentada no plano de Entrega 4.

const MODULES_DEFS = {
  treinamentos: { needsRel: true,  needsSqlite: false, needsBaseFerias: false, needsBaseTreinamentos: true,  needsBaseTags: false },
  ferias:       { needsRel: true,  needsSqlite: false, needsBaseFerias: true,  needsBaseTreinamentos: false, needsBaseTags: false },
  atestados:    { needsRel: true,  needsSqlite: false, needsBaseFerias: false, needsBaseTreinamentos: false, needsBaseTags: false },
  'validar-hr': { needsRel: false, needsSqlite: false, needsBaseFerias: false, needsBaseTreinamentos: false, needsBaseTags: false },
  'validar-dist': { needsRel: false, needsSqlite: true,  needsBaseFerias: false, needsBaseTreinamentos: false, needsBaseTags: false },
};

export function getRunBlockReason(moduleId, state) {
  const def = MODULES_DEFS[moduleId];
  if (!def) return { blocked: true, reason: 'Módulo desconhecido.' };
  const m = state.modules[moduleId] || {};
  const sessionOff = !state.session.active;
  const relReady = !def.needsRel || !!m.relatorio;
  const sqliteReady = !def.needsSqlite || !!state.config.bd_distribuicao;
  const baseTrReady = !def.needsBaseTreinamentos || !!state.config.base_treinamentos;
  const baseFeReady = !def.needsBaseFerias || !!state.config.base_cobranca;
  const baseTagsReady = !def.needsBaseTags || !!state.config.base_tags;
  const meta = state.modulesMeta?.[moduleId];

  if (state.run.lock || state.bootstrapping)
    return { blocked: true, reason: 'Execução em andamento.' };
  if (sessionOff)
    return { blocked: true, reason: 'Carregue a medição para liberar este módulo.' };
  if (!relReady)
    return { blocked: true, reason: 'Selecione o relatório do módulo.' };
  if (!sqliteReady)
    return { blocked: true, reason: 'Configure bd_distribuicao em Configurações.' };
  if (!baseTrReady)
    return { blocked: true, reason: 'Configure Base de Treinamentos em Configurações.' };
  if (!baseFeReady)
    return { blocked: true, reason: 'Configure Base de Férias em Configurações.' };
  if (!baseTagsReady)
    return { blocked: true, reason: 'Configure Base de Tags em Configurações.' };
  if (meta && !meta.enabled)
    return { blocked: true, reason: meta.reason || 'Indisponível.' };
  return { blocked: false, reason: null };
}
