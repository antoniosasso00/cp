# 🧭 Guida alla Navigazione del Codice CarbonPilot

## 📊 Schemi e Modelli

### Backend
- **Schemi Pydantic**: `/backend/schemas/`
  - `models.py`: Definizioni principali
  - `requests.py`: Schemi per richieste API
  - `responses.py`: Schemi per risposte API

- **Modelli Database**: `/backend/models/`
  - `base.py`: Classe base per tutti i modelli
  - `user.py`: Gestione utenti
  - `project.py`: Gestione progetti
  - `nesting.py`: Modelli per ottimizzazione nesting

## 🔄 Cicli e Report

### Frontend
- **Cicli di Lavoro**: `/frontend/pages/workflows/`
  - `[id].tsx`: Visualizzazione singolo ciclo
  - `create.tsx`: Creazione nuovo ciclo
  - `edit.tsx`: Modifica ciclo esistente

- **Report**: `/frontend/pages/reports/`
  - `dashboard.tsx`: Dashboard principale
  - `analytics.tsx`: Analisi dettagliate
  - `export.tsx`: Esportazione dati

## 🏭 Gestione Autoclavi e Nesting

### Backend
- **Autoclavi**: `/backend/services/autoclave/`
  - `manager.py`: Gestione ciclo di vita
  - `optimizer.py`: Ottimizzazione parametri
  - `validator.py`: Validazione operazioni

- **Nesting**: `/backend/nesting_optimizer/`
  - `algorithm.py`: Algoritmi di ottimizzazione
  - `visualizer.py`: Visualizzazione risultati
  - `validator.py`: Validazione layout

### Frontend
- **Interfaccia Autoclavi**: `/frontend/pages/autoclaves/`
  - `[id].tsx`: Dettaglio autoclave
  - `monitor.tsx`: Monitoraggio in tempo reale
  - `settings.tsx`: Configurazione

## 🏗️ Struttura Tipica di una Feature

1. **Frontend** (`/frontend/`)
   ```
   pages/
   └── feature/
       ├── index.tsx        # Lista elementi
       ├── [id].tsx         # Dettaglio
       ├── create.tsx       # Creazione
       └── edit.tsx         # Modifica
   components/
   └── feature/
       ├── List.tsx         # Componente lista
       ├── Form.tsx         # Form condiviso
       └── Detail.tsx       # Vista dettaglio
   ```

2. **Backend** (`/backend/`)
   ```
   api/
   └── feature/
       ├── router.py        # Definizione endpoint
       └── handlers.py      # Logica endpoint
   models/
   └── feature.py           # Modello database
   schemas/
   └── feature.py           # Schemi Pydantic
   services/
   └── feature/
       ├── manager.py       # Logica business
       └── validator.py     # Validazione
   ```

## 🔍 Flusso dei Dati

1. **Richiesta Frontend** → `pages/feature/[id].tsx`
2. **Chiamata API** → `lib/api.ts`
3. **Endpoint Backend** → `api/feature/router.py`
4. **Validazione** → `schemas/feature.py`
5. **Logica Business** → `services/feature/manager.py`
6. **Database** → `models/feature.py`
7. **Risposta** → Frontend

## 🛠️ Utility e Helper

- **Frontend**: `/frontend/utils/`
  - `api.ts`: Client API
  - `validation.ts`: Validazione form
  - `formatting.ts`: Formattazione dati

- **Backend**: `/backend/utils/`
  - `security.py`: Funzioni di sicurezza
  - `validation.py`: Validazione dati
  - `logging.py`: Gestione log 