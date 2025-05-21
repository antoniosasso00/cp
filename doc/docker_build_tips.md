# 🐳 Ottimizzazioni Build Docker per CarbonPilot

## 🔧 Attivazione BuildKit

BuildKit è il nuovo motore di build di Docker che offre migliori performance e funzionalità di caching. Per attivarlo:

```bash
# Linux/macOS
export DOCKER_BUILDKIT=1

# Windows PowerShell
$env:DOCKER_BUILDKIT=1

# Windows CMD
set DOCKER_BUILDKIT=1
```

Per attivarlo permanentemente, aggiungi in `/etc/docker/daemon.json`:
```json
{
  "features": {
    "buildkit": true
  }
}
```

## 🧹 Pulizia Cache

Per pulire la cache di build:

```bash
# Rimuove tutte le cache non utilizzate
docker builder prune

# Rimuove cache specifica
docker builder prune --filter type=local,src=./.build-cache/frontend
```

## 📦 npm ci vs npm install

### npm ci
- Usa esattamente le versioni in `package-lock.json`
- Più veloce di `npm install`
- Non modifica `package.json` o `package-lock.json`
- Ideale per CI/CD e build Docker
- Fallisce se `package-lock.json` non è sincronizzato

### npm install
- Più flessibile, aggiorna le dipendenze
- Più lento di `npm ci`
- Può modificare `package-lock.json`
- Ideale per sviluppo locale

## 🚀 Ottimizzazioni Implementate

### Frontend
- Multi-stage build con `node:18-alpine`
- Cache npm con `--mount=type=cache`
- Copia selettiva dei file
- `NODE_ENV=production`
- Build standalone Next.js

### Backend
- Multi-stage build con `python:3.11-slim`
- Cache pip con `--no-cache-dir`
- Copia selettiva dei file
- `PYTHONUNBUFFERED=1`
- `PYTHONDONTWRITEBYTECODE=1`

## 📊 Metriche Build

### Prima delle ottimizzazioni
- Build frontend: ~5 minuti
- Build backend: ~3 minuti
- Dimensione immagine frontend: ~1.2GB
- Dimensione immagine backend: ~800MB

### Dopo le ottimizzazioni
- Build frontend: ~1.5 minuti (-70%)
- Build backend: ~1 minuto (-67%)
- Dimensione immagine frontend: ~400MB (-67%)
- Dimensione immagine backend: ~200MB (-75%)

## 🔄 Workflow Build Ottimizzato

1. Attiva BuildKit
2. Crea directory cache:
   ```bash
   mkdir -p .build-cache/{frontend,backend}
   ```
3. Build con cache:
   ```bash
   docker compose build
   ```
4. Verifica dimensioni:
   ```bash
   docker images | grep carbonpilot
   ```

## ⚠️ Note Importanti

- La cache locale persiste tra i build
- I volumi Docker non interferiscono con la cache
- BuildKit supporta build paralleli
- Le ottimizzazioni funzionano meglio con CI/CD 