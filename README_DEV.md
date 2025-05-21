# 🚀 Guida Sviluppatore CarbonPilot

## 📁 Struttura del Progetto

### Backend (`/backend`)
- `api/`: Endpoint FastAPI e logica di business
- `models/`: Modelli SQLAlchemy per il database
- `schemas/`: Pydantic schemas per validazione dati
- `services/`: Logica di business e servizi
- `nesting_optimizer/`: Algoritmi di ottimizzazione nesting
- `tests/`: Test unitari e di integrazione

### Frontend (`/frontend`)
- `components/`: Componenti React riutilizzabili
- `pages/`: Pagine Next.js e routing
- `lib/`: Utility e configurazioni
- `utils/`: Funzioni helper

### Documentazione (`/doc`)
- Guide tecniche e documentazione
- Changelog e note di rilascio
- Guide di migrazione

## 🛠️ Comandi Utili

### Avvio Ambiente di Sviluppo
```bash
# Avvia tutti i servizi
docker compose up -d

# Avvia solo il backend
docker compose -f docker-compose-backend.yml up -d

# Avvia con override per sviluppo
docker compose -f docker-compose.yml -f docker-compose.override.yml up -d
```

### Database
```bash
# Seed del database
docker compose exec backend python -m scripts.seed_db

# Reset database
docker compose exec backend python -m scripts.reset_db
```

### Build
```bash
# Build frontend
cd frontend && npm run build

# Build backend
cd backend && python -m build
```

## 📚 Documentazione Aggiuntiva
Per una guida dettagliata alla navigazione del codice, consulta [Guida alla Navigazione](doc/navigation_guide.md)

## 🔧 Configurazione IDE
Il progetto include un file workspace VS Code (`carbonpilot.code-workspace`) con configurazioni ottimizzate per lo sviluppo. 