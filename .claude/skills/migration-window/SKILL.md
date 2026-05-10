---
name: migration-window
description: Migration window state — which legacy paths remain, what has moved, and import conventions during the transition.
---

# Migration Window

Estado: **encerrada**. A migração flat→layered (de `app/*.py` plano para
`app/domain/` + `app/application/` + `app/infrastructure/`) foi
consolidada em Entregas 4a/4b.

## Status atual

- Todos os módulos legados sob `app/*.py` foram movidos para a estrutura
  layered. Conferir com `ls app/*.py`.
- Único módulo flat remanescente: `app/validar_horas.py` (sem target path
  definido; permanece como-é).
- Shim posicional de `gerar_updates_ferias` removido na Entrega 5;
  todos os callers usam `FeriasContext`.

## Convenção de imports

- Sempre via paths layered: `from app.domain.X import ...`,
  `from app.application.X import ...`, `from app.infrastructure.X import ...`.
- Nenhum re-export shim em `app/__init__.py`.
- `from app.X import ...` (flat) só vale para `app.main`, `app.desktop_entry`,
  `app.validar_horas`.

## Quando reabrir esta skill

Quando uma nova janela de migração começar (ex.: extrair API HTTP para
serviço separado, separar `app/ui/web/` em repo próprio, refatorar
`validar_horas` para `domain/horas_trabalhadas.py`). Até lá, esta skill
é informativa apenas.
