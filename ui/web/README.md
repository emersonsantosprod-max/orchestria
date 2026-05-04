# Automação de Medição — Web UI

React frontend (Vite) for the Automação de Medição tool. Sole UI surface;
the legacy Tkinter GUI was removed.

## Backend integration

The UI calls the FastAPI backend at `app/api/main.py`. Endpoints currently
wired by the UI:

| UI surface                 | Endpoint                       | Status                      |
|----------------------------|--------------------------------|-----------------------------|
| Carregar medição           | client-side only (File held in `useRef`) | mes_referencia stays null until a backend route exposes it |
| Executar Treinamentos      | `POST /api/run/treinamentos` (multipart: `medicao`, `catalogo`) | wired |
| Executar Férias / Atestados / Validar HR / Validar Dist. | `POST /api/run/<id>` | UI surfaces `RUN_NOT_IMPLEMENTED` until the route exists |
| Configuração (base_*, bd_*) | `POST /api/config/<key>` | UI surfaces `CONFIG_NOT_IMPLEMENTED` until the route exists |
| Status inicial             | `GET /api/initial-data`        | available via `API.initialData()` (not yet rendered) |

The list of endpoints actually called per module lives in `ENDPOINTS`
inside [src/App.jsx](src/App.jsx). Add a new entry there as each FastAPI
route lands — no other UI change needed.

## Source of truth

- **Visual design:** Manserv brand book → `src/styles/colors_and_type.css`,
  `public/fonts/IBMPlexSans-*.ttf`, `public/assets/favicon.{png,ico}`
- **Component code:** `src/App.jsx` — single file, ported from
  `data/entrada/ui_kits/automacao_medicao/App.jsx`
- **C5 (File-blob capture):** `medicaoFileRef` + `relatorioFilesRef` at the
  `App` root. The reducer holds only `{name, size}` metadata; the actual
  `File` blobs travel through refs and are sent at run time via multipart.

## Develop

Two processes side-by-side:

```bash
# Terminal 1 — FastAPI backend
source venv/bin/activate
uvicorn app.api.main:app --reload --port 8000

# Terminal 2 — Vite dev server (proxies /api and /ws to :8000)
cd ui/web
npm install
npm run dev
```

Open <http://localhost:5173>. The Vite proxy in `vite.config.js` forwards
`/api/*`, `/ws/*`, and `/health` to `127.0.0.1:8000` so HMR works without
CORS. In production, `app/api/main.py` mounts `ui/web/dist/` as
StaticFiles under `/`, so a single uvicorn process serves both.

## Build

```bash
cd ui/web
npm run build      # → ui/web/dist/
```

After building, restart uvicorn — the lifespan picks up `dist/` and
serves the SPA at the same origin as the API.
