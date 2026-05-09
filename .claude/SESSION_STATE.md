Plan: /home/emersonagi/.claude/plans/problemas-indentificados-mudan-as-feitas-zesty-parnas.md
Active session: .claude/sessions/2026-05-09-entrega-3-ui-nav-gating-modular.tmp (closed)

## Last Completed Step
Entrega 3 (V3) concluída — UI: extração de 9 componentes em `app/ui/web/src/components/` (primitives, format, skeletons, LogPanel, Sidebar, SessionBlock, ConfigCard, ConfigView, ModuleRow, ExecucaoView). Sidebar reordenada (Configurações → Execução), label "Configuração" → "Configurações". SessionBlock movido para topo de ConfigView. Rename visual "Base de cobrança" → "Base de Férias" (label only; backend keys/endpoint preservados). Gating visual de uploads de bases por medição ativa via `ConfigCard.disabled`. Helper puro `getRunBlockReason(moduleId, state)` em App.jsx centraliza prioridade de motivos de bloqueio (sessionOff → relReady → sqliteReady → baseReady → meta). ExecucaoView mostra hint clicável "anexe a medição em Configurações" quando session inativa. App.jsx enxugada de 1110 → 367 linhas. `processed_output_path` agora assume mkdir explícito. CLI `normalizar` defere `exports_dir()` resolution.
Test count: 265 passed, 0 failed | npm build: clean (174.84 KB JS) | Lint: 2 erros pré-existentes (não introduzidos).

## Next Step
Entrega 4 (V3) — Cleanup documental: auditar `.claude/rules/`, `.claude/skills/`, `CLAUDE.md`, docstrings/schemas em busca de referências a `saida_dir`, `data/saida`, `obter_mes_referencia_excel`. Quality gate final.
Blocker: none.

## Invariants Exercised This Session
- App.jsx coordena estado/views; sem layout/gating inline (`useReducer` central, sem Context, sem store): ✓
- Componentes em `app/ui/web/src/components/`, props rasas (≤ 2 níveis): ✓
- Backend valida mesmo após gating UI (UI bloqueio é UX): ✓
- `getRunBlockReason` puro com prioridade determinística (compartilhável, testável): ✓
- Imports unidirecionais (primitives ← skeletons; sem ciclo): ✓
- Backend contract preservation: `base_cobranca`, `/api/config/cobranca`, `state.config.base_cobranca` intactos: ✓

## Files Modified
- app/ui/web/src/App.jsx (1110 → 367 linhas)
- app/ui/web/src/components/primitives.jsx (NEW)
- app/ui/web/src/components/format.js (NEW)
- app/ui/web/src/components/skeletons.jsx (NEW)
- app/ui/web/src/components/LogPanel.jsx (NEW)
- app/ui/web/src/components/Sidebar.jsx (NEW: rename + reorder)
- app/ui/web/src/components/SessionBlock.jsx (NEW)
- app/ui/web/src/components/ConfigCard.jsx (NEW: dumb component, disabled prop)
- app/ui/web/src/components/ConfigView.jsx (NEW: SessionBlock no topo + gating)
- app/ui/web/src/components/ModuleRow.jsx (NEW: usa getRunBlockReason)
- app/ui/web/src/components/ExecucaoView.jsx (NEW: EmptyHint clicável)

## TODO
- [x] Entrega 1 (V3) — backend: paths, validação, domínio
- [x] Entrega 2 (V3) — testes: isolamento explícito
- [x] Entrega 3 (V3) — UI: navegação, rename, gating, modularização
- [ ] Entrega 4 — Cleanup documental