# Automação de Medição — Web UI

React frontend (Vite) for the Automação de Medição tool. Replaces the
Tkinter GUI in `ui/gui.py` with a browser-served SPA. Coexists with Tkinter
during the migration window.

## Source of truth

- **Visual design:** Manserv brand book → `src/styles/colors_and_type.css`,
  `public/fonts/IBMPlexSans-*.ttf`, `public/assets/favicon.{png,ico}`
- **Component code:** `src/App.jsx` — ported from
  `data/entrada/ui_kits/automacao_medicao/App.jsx` (Babel-standalone prototype)
  to Vite ES modules. Logic and visual structure are unchanged from the prototype.
- **Backend contract (mocked in `App.jsx > API`):** `POST /api/session/medicao`,
  `POST /api/run/<id>`, `POST /api/config/<key>`, `WS /ws/log`. The backend
  side is not yet implemented — see the integration evaluation in
  `~/.claude/plans/prompt-model-claude-opus-4-7-role-senio-compressed-thunder.md`.

## Develop

```bash
cd ui/web
npm install
npm run dev
```

Vite serves at <http://localhost:5173>. The mocked `API` object simulates
the backend so the UI is fully clickable without a server.

## Build

```bash
npm run build      # → ui/web/dist/
npm run preview    # serve dist/ locally
```
