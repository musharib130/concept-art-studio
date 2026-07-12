# frontend

React (Vite) frontend for the Concept Art Studio desktop app. Talks to the Python image-generation
backend via pywebview's `js_api` bridge (`window.pywebview.api`) — no HTTP server involved.

## Development

```bash
npm install
npm run dev
```

This starts the Vite dev server on `http://localhost:5173`. It needs to be running before launching
the desktop shell in dev mode (see `backend/README` / `poetry run python -m app.main --dev`).

## Production build

```bash
npm run build
```

Emits `dist/`, which the desktop shell loads directly as a local file (no dev server needed).
