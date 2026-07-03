# Vue Dashboard

Dieses Verzeichnis enthält das Vue-Frontend für das Shopping-Analyzer-Dashboard.

## Start

```bash
npm install
npm run dev
```

Wenn das FastAPI-Backend nicht auf `http://localhost:8000` läuft, setze:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

## Tests

```bash
npm test
```

## Build

```bash
npm run build
```

## API

Das Frontend liest das Dashboard über `GET /ui/dashboard`.
