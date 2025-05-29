# 🚀 CarbonPilot - Sistema di Gestione Produzione Compositi

## 📋 Panoramica del Progetto

CarbonPilot è un sistema completo per la gestione della produzione di componenti in fibra di carbonio, con focus sull'ottimizzazione del processo di cura in autoclave attraverso algoritmi di nesting avanzati.

## ✅ Step 8 - Caricamento Nesting COMPLETATO

### 🎯 Funzionalità Implementate

#### Backend (FastAPI + Python)
- ✅ **Endpoint Caricamento**: `POST /nesting/{id}/load` per caricare nesting in autoclave
- ✅ **Endpoint Nesting Attivi**: `GET /nesting/active` per monitorare nesting caricati
- ✅ **Aggiornamenti Automatici**: Stati ODL, Autoclave e Nesting sincronizzati
- ✅ **Sistema Logging**: Audit trail completo con StateTracking e SystemLog
- ✅ **Gestione Fasi**: Tracking temporale automatico delle fasi di produzione

#### Frontend (React + TypeScript)
- ✅ **Tabella Nesting Attivi**: Componente `ActiveNestingTable` per monitoraggio real-time
- ✅ **Caricamento Nesting**: Pulsanti e dialog per caricamento con note
- ✅ **Badge di Stato**: Componente `NestingStatusBadge` con colori e icone
- ✅ **Dashboard Integrato**: Pagina con tab per nesting attivi e gestione completa
- ✅ **Statistiche Live**: Contatori e metriche aggiornate automaticamente

## 🏗️ Architettura del Sistema

### Backend Structure
```
backend/
├── api/routers/nesting.py      # Endpoint nesting con caricamento
├── models/                     # Modelli SQLAlchemy
├── schemas/                    # Schema Pydantic per validazione
├── services/                   # Servizi business logic
└── nesting_optimizer/          # Algoritmi di ottimizzazione
```

### Frontend Structure
```
frontend/src/
├── app/dashboard/curing/nesting/    # Pagine nesting
├── components/nesting/              # Componenti modulari
├── lib/api.ts                      # Client API TypeScript
└── components/ui/                  # Componenti UI base
```

## 🚀 Avvio del Sistema

### Prerequisiti
- Python 3.8+
- Node.js 18+
- PostgreSQL
- Docker (opzionale)

### Backend
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Accesso
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Documentazione API**: http://localhost:8000/docs

## 📊 Flusso Operativo Step 8

### 1. Generazione Nesting
```
Dashboard → Curing → Nesting → "Genera Nesting Automatico"
```

### 2. Conferma Nesting
```
Tabella Nesting → Pulsante "Conferma" → Stato: "In sospeso"
```

### 3. Caricamento in Autoclave
```
Tabella Nesting → Pulsante "Carica" → Dialog con note → Conferma
```

### 4. Aggiornamenti Automatici
- **Nesting**: Stato → "Caricato"
- **Autoclave**: Stato → "IN_USO"  
- **ODL**: Stato → "Cura"
- **Fasi**: Chiusura "attesa_cura" + Apertura "cura"

### 5. Monitoraggio
```
Tab "Nesting Attivi" → Visualizzazione real-time → Dettagli espandibili
```

## 🔧 API Endpoints Principali

### Nesting Management
- `GET /api/v1/nesting/` - Lista tutti i nesting
- `GET /api/v1/nesting/active` - Nesting attivi (caricati)
- `POST /api/v1/nesting/{id}/load` - Carica nesting in autoclave
- `POST /api/v1/nesting/{id}/confirm` - Conferma nesting
- `GET /api/v1/nesting/{id}` - Dettagli nesting specifico

### Automatic Nesting
- `POST /api/v1/nesting/automatic` - Genera nesting automatico
- `GET /api/v1/nesting/preview` - Anteprima nesting
- `GET /api/v1/nesting/parameters` - Parametri ottimizzazione

## 📈 Componenti Frontend

### Componenti Nesting
- **`ActiveNestingTable`**: Tabella nesting attivi con statistiche
- **`NestingTable`**: Gestione completa nesting con azioni
- **`NestingStatusBadge`**: Badge colorati per stati
- **`NestingVisualization`**: Visualizzazione grafica layout

### Pagine Principali
- **`/dashboard/curing/nesting`**: Dashboard principale con tab
- **`/dashboard/curing/nesting/[id]`**: Dettaglio nesting specifico
- **`/dashboard/curing/nesting/[id]/visualizza`**: Visualizzazione grafica

## 🧪 Testing

### Backend Tests
```bash
python test_nesting_endpoints.py
```

### Test Coverage
- ✅ Endpoint caricamento nesting
- ✅ Endpoint nesting attivi
- ✅ Validazione stati e prerequisiti
- ✅ Sistema logging e audit trail

## 📋 Database Schema

### Tabelle Principali
- **`nesting_results`**: Risultati nesting con stati
- **`odl`**: Ordini di lavoro con tracking stati
- **`autoclavi`**: Autoclavi con stati operativi
- **`tempo_fase`**: Tracking temporale fasi produzione
- **`system_logs`**: Log sistema per audit trail

### Stati Gestiti
- **Nesting**: "In sospeso", "Confermato", "Caricato", "Completato"
- **ODL**: "Preparazione", "Laminazione", "In Coda", "Attesa Cura", "Cura", "Finito"
- **Autoclave**: "DISPONIBILE", "IN_USO", "GUASTO", "MANUTENZIONE", "SPENTA"

## 🔄 Logging e Audit Trail

### Sistema di Logging
- **`StateTrackingService`**: Cambio stati ODL
- **`SystemLogService`**: Operazioni sistema
- **`ODLLog`**: Log specifici ODL
- **`TempoFase`**: Tracking temporale fasi

### Informazioni Tracciate
- Timestamp precisi di ogni operazione
- Utente/ruolo responsabile dell'azione
- Dettagli delle modifiche (old_value → new_value)
- Note personalizzabili per ogni operazione

## 🚀 Prossimi Sviluppi

### Step 9 - Completamento Ciclo Cura
- Scarico autoclave automatico
- Finalizzazione ODL
- Generazione report produzione

### Ottimizzazioni Future
- Cache Redis per performance
- Notifiche real-time
- Dashboard analytics avanzato
- Export dati produzione

## 📞 Supporto

Per domande o problemi:
1. Consulta la documentazione API: http://localhost:8000/docs
2. Verifica i log di sistema nel database
3. Controlla il changelog in `docs/changelog.md`

## 📄 Licenza

Progetto interno - Tutti i diritti riservati.

## 📋 Funzionalità Principali

### 🎯 Gestione ODL (Ordini di Lavoro)
- Creazione e gestione ordini di lavoro
- Tracking stato produzione
- Prioritizzazione automatica
- Monitoraggio tempi e fasi

### 🏭 Gestione Autoclavi
- Configurazione autoclavi multiple
- Monitoraggio stato e disponibilità
- Gestione capacità peso e dimensioni
- Ottimizzazione utilizzo risorse

### 🧩 Sistema Nesting Avanzato
- **Nesting Singolo**: Ottimizzazione per singola autoclave
- **Nesting Multiplo (Step 11)**: Gestione batch con assegnazione automatica multi-autoclave

#### 🔥 Nesting Multiplo - Funzionalità Avanzate

Il sistema di nesting multiplo implementato nello Step 11 offre:

##### 📊 Gestione Batch Intelligente
- **Raggruppamento Automatico**: ODL raggruppati per compatibilità ciclo di cura
- **Assegnazione Ottimale**: Algoritmi di ottimizzazione per assegnazione autoclavi
- **Preview System**: Anteprima completa prima del salvataggio
- **Workflow Stati**: Pianificazione → Pronto → In Esecuzione → Completato

##### ⚙️ Parametri Configurabili
- **Distanza Minima Tool**: 0.5-10.0 cm (default: 2.0 cm)
- **Padding Bordo Autoclave**: 0.5-5.0 cm (default: 1.5 cm)
- **Margine Sicurezza Peso**: 0-50% (default: 10%)
- **Priorità Minima ODL**: 1-10 (default: 1)
- **Efficienza Minima**: 30-95% (default: 60%)

##### 📈 Statistiche e Monitoraggio
- **Dashboard Batch**: Panoramica completa batch attivi
- **Metriche Real-time**: Efficienza, utilizzo, peso totale
- **Progress Tracking**: Visualizzazione progresso assegnazione ODL
- **Audit Trail**: Tracciabilità completa operazioni

##### 🎛️ Interfaccia Utente
- **Form Parametri**: Configurazione intuitiva con slider e validazione
- **Preview Dettagliato**: Visualizzazione completa assegnazioni prima del salvataggio
- **Tabella Batch**: Gestione batch salvati con azioni contestuali
- **Modal Dettagli**: Visualizzazione approfondita statistiche e parametri

#### 🚀 Come Utilizzare il Nesting Multiplo

1. **Accesso**: Naviga su `/dashboard/curing/nesting`
2. **Configurazione**: Imposta i parametri di ottimizzazione nella tab "Parametri"
3. **Preview**: Clicca "Crea Preview" per visualizzare l'assegnazione ottimale
4. **Verifica**: Controlla statistiche, efficienza e ODL assegnati nella tab "Preview Batch"
5. **Salvataggio**: Conferma il batch cliccando "Salva Batch"
6. **Gestione**: Monitora e gestisci i batch nella tab "Batch Salvati"

#### 🔧 API Endpoints

Il sistema espone i seguenti endpoint REST:

```
GET    /api/v1/multi-nesting/gruppi-odl           # Raggruppa ODL per ciclo cura
GET    /api/v1/multi-nesting/autoclavi-disponibili # Lista autoclavi disponibili
POST   /api/v1/multi-nesting/preview-batch        # Crea preview batch
POST   /api/v1/multi-nesting/salva-batch          # Salva batch nel database
GET    /api/v1/multi-nesting/batch                # Lista batch salvati
GET    /api/v1/multi-nesting/batch/{id}           # Dettagli batch specifico
PUT    /api/v1/multi-nesting/batch/{id}/stato     # Aggiorna stato batch
DELETE /api/v1/multi-nesting/batch/{id}           # Elimina batch
```

### 📊 Dashboard e Reporting
- Dashboard operativo in tempo reale
- Report PDF automatici
- Statistiche produzione
- Analisi performance

### 🔐 Sistema di Logging
- Audit trail completo
- Monitoraggio operazioni
- Gestione errori
- Tracciabilità modifiche

## 🛠️ Tecnologie Utilizzate

### Backend
- **FastAPI**: Framework web moderno e performante
- **SQLAlchemy**: ORM per gestione database
- **PostgreSQL**: Database relazionale robusto
- **Pydantic**: Validazione dati e serializzazione
- **Alembic**: Gestione migrazioni database

### Frontend
- **Next.js 14**: Framework React con App Router
- **TypeScript**: Tipizzazione statica per maggiore robustezza
- **Tailwind CSS**: Framework CSS utility-first
- **shadcn/ui**: Componenti UI moderni e accessibili
- **React Hook Form**: Gestione form avanzata
- **Sonner**: Sistema toast per feedback utente

### Algoritmi di Ottimizzazione
- **Nesting Optimizer**: Algoritmi proprietari per ottimizzazione spazio
- **Multi-Autoclave Assignment**: Assegnazione intelligente risorse
- **Bin Packing**: Ottimizzazione utilizzo spazio 2D
- **Priority Scheduling**: Gestione priorità ODL

## 🚀 Installazione e Setup

### Prerequisiti
- Python 3.9+
- Node.js 18+
- PostgreSQL 13+
- Git

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Database Setup
```bash
# Crea database PostgreSQL
createdb carbonpilot

# Configura variabili ambiente
cp .env.example .env
# Modifica .env con le tue configurazioni

# Esegui migrazioni
cd backend
alembic upgrade head
```

## 📁 Struttura Progetto

```
CarbonPilot/
├── backend/                 # API Backend FastAPI
│   ├── api/                # Endpoints REST
│   ├── models/             # Modelli database SQLAlchemy
│   ├── services/           # Logica business
│   ├── nesting_optimizer/  # Algoritmi ottimizzazione
│   └── tests/              # Test automatizzati
├── frontend/               # Frontend Next.js
│   ├── src/
│   │   ├── app/           # App Router Next.js 14
│   │   ├── components/    # Componenti React riutilizzabili
│   │   └── lib/           # Utilities e configurazioni
├── docs/                   # Documentazione
│   └── changelog.md       # Log modifiche dettagliato
└── docker-compose.yml     # Setup Docker per sviluppo
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v
```

### Frontend Tests
```bash
cd frontend
npm run test
```

## 📚 Documentazione

- **API Documentation**: Disponibile su `http://localhost:8000/docs` (Swagger UI)
- **Changelog**: Documentazione dettagliata modifiche in `docs/changelog.md`
- **Database Schema**: Diagrammi ER in `docs/database/`
- **User Guide**: Guide utente in `docs/user-guide/`

## 🤝 Contribuire

1. Fork del repository
2. Crea branch feature (`git checkout -b feature/nome-feature`)
3. Commit modifiche (`git commit -am 'Aggiunge nuova feature'`)
4. Push branch (`git push origin feature/nome-feature`)
5. Crea Pull Request

## 📄 Licenza

Questo progetto è proprietario e riservato.

## 📞 Supporto

Per supporto tecnico o domande:
- Email: support@carbonpilot.com
- Documentazione: [docs.carbonpilot.com](https://docs.carbonpilot.com)
- Issues: GitHub Issues per bug report e feature request

---

**CarbonPilot** - Ottimizzazione intelligente per la produzione in fibra di carbonio 🚀