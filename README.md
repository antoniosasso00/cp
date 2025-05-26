# 🚀 CarbonPilot - Sistema di Gestione Produzione Manta Group

Sistema completo per la gestione della produzione di componenti aeronautici in fibra di carbonio, con focus su ottimizzazione nesting, gestione autoclavi e tracciabilità completa del processo produttivo.

## ✨ Funzionalità Principali

### 🎯 Dashboard Operative per Ruolo
- **Admin**: KPI sistema, gestione utenti, configurazioni globali, monitoraggio completo
- **Responsabile**: KPI produzione, storico ODL filtrabile, gestione nesting, reports
- **Laminatore**: ODL in Preparazione/Laminazione con cambio stato funzionale, metriche turno
- **Autoclavista**: ODL in Attesa Cura/Cura, nesting confermati caricabili, controllo autoclavi

### 📊 Sistema KPI Real-time
- **Metriche Operative**: ODL per stato, efficienza produzione, utilizzo autoclavi
- **Aggiornamento Automatico**: Refresh ogni 5 minuti con possibilità di aggiornamento manuale
- **Storico Filtrabile**: Cronologia ODL con filtri per stato, ricerca e range date
- **Indicatori Colorati**: Stati visivi per performance e trend

### 🔧 Gestione ODL (Ordini Di Lavorazione)
- **Flusso Completo**: Preparazione → Laminazione → Attesa Cura → Cura → Finito
- **Cambio Stato per Ruolo**: Pulsanti funzionali specifici per laminatore e autoclavista
- **Priorità Dinamiche**: Sistema di priorità con ordinamento automatico
- **Tracciabilità**: Storico completo con dettagli parte, tool e tempi

### 🧩 Ottimizzazione Nesting Avanzata
- **Algoritmo Genetico**: Ottimizzazione automatica del carico autoclavi
- **Nesting su Due Piani**: Supporto per autoclavi multi-livello con controllo peso
- **Visualizzazione 3D**: Rappresentazione grafica del posizionamento tools
- **Conferma per Ruolo**: Workflow di approvazione nesting prima del caricamento

### 🏭 Gestione Autoclavi
- **Monitoraggio Stato**: Controllo real-time temperatura, pressione, cicli
- **Cicli di Cura**: Gestione parametri termici con stasi multiple
- **Scheduling**: Pianificazione automatica cicli basata su priorità ODL
- **Utilizzo Ottimale**: Calcolo efficienza e statistiche utilizzo

### 📈 Sistema di Logging e Audit
- **Tracciabilità Completa**: Log di tutte le operazioni critiche
- **Audit Trail**: Storico modifiche con utente, timestamp e dettagli
- **Dashboard Analytics**: Visualizzazione logs con filtri avanzati
- **Export Dati**: Esportazione in CSV per analisi esterne

### 🔐 Gestione Ruoli e Sicurezza
- **4 Ruoli Operativi**: Admin, Responsabile, Laminatore, Autoclavista
- **Permessi Granulari**: Accesso controllato per ogni funzionalità
- **Workflow Approvazioni**: Sistema di conferme per operazioni critiche
- **Tracciamento Accessi**: Log completo delle attività utente

## 🛠️ Tecnologie Utilizzate

### Backend
- **FastAPI**: Framework Python ad alte performance per API REST
- **SQLAlchemy**: ORM per gestione database con modelli tipizzati
- **PostgreSQL**: Database relazionale per persistenza dati
- **Pydantic**: Validazione dati e serializzazione automatica

### Frontend
- **Next.js 14**: Framework React con App Router e SSR
- **TypeScript**: Tipizzazione statica per maggiore robustezza
- **Tailwind CSS**: Styling utility-first per UI responsive
- **Shadcn/ui**: Componenti UI moderni e accessibili

### Algoritmi e Ottimizzazione
- **DEAP**: Libreria Python per algoritmi genetici
- **Ottimizzazione Multi-obiettivo**: Bilanciamento area, valvole e priorità
- **Bin Packing 2D**: Algoritmi per posizionamento ottimale tools
- **Constraint Solving**: Gestione vincoli fisici e operativi

## 🚀 Quick Start

### Prerequisiti
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Git

### Installazione Backend
```bash
# Clone repository
git clone <repository-url>
cd CarbonPilot

# Setup ambiente virtuale
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# oppure
.venv\Scripts\activate     # Windows

# Installa dipendenze
pip install -r requirements.txt

# Configura database
# Crea database PostgreSQL 'carbonpilot'
# Configura variabili ambiente in .env

# Avvia backend
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Installazione Frontend
```bash
# In una nuova shell
cd frontend

# Installa dipendenze
npm install

# Configura variabili ambiente
# Crea .env.local con NEXT_PUBLIC_API_URL

# Avvia frontend
npm run dev
```

### Accesso Sistema
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Documentazione API**: http://localhost:8000/docs

## 📁 Struttura Progetto

```
CarbonPilot/
├── backend/                 # API FastAPI
│   ├── api/                # Endpoints REST
│   ├── models/             # Modelli SQLAlchemy
│   ├── schemas/            # Schemi Pydantic
│   ├── services/           # Logica business
│   └── nesting_optimizer/  # Algoritmi ottimizzazione
├── frontend/               # App Next.js
│   ├── src/
│   │   ├── app/           # App Router pages
│   │   ├── components/    # Componenti React
│   │   ├── hooks/         # Custom hooks
│   │   └── lib/          # Utilities e API client
├── docs/                  # Documentazione
├── tools/                 # Script utilità
└── requirements.txt       # Dipendenze Python
```

## 🎯 Roadmap

### ✅ Completato (v2.3.1)
- **Fix Definitivo Select Components**: Risoluzione completa errore Radix UI "empty string value"
- **Componente SafeSelect**: Wrapper sicuro per prevenire errori futuri
- **Best Practices Documentation**: Guida per sviluppatori su gestione Select
- **Stabilità Dashboard**: Eliminazione crash nelle dashboard admin e responsabile

### ✅ Completato (v2.3.0)
- Dashboard operative per tutti i ruoli con dati reali
- Fix crash Select component
- Hook specializzato per ODL filtrati per ruolo
- Cambio stato ODL funzionale per laminatore e autoclavista
- Integrazione nesting confermati per autoclavista

### 🔄 In Sviluppo
- Sistema notifiche real-time
- Mobile app per operatori
- Integrazione sensori IoT autoclavi
- Machine learning per previsioni tempi

### 📋 Pianificato
- Integrazione ERP aziendale
- Modulo manutenzione predittiva
- Dashboard executive con BI
- API pubbliche per integrazioni

## 🤝 Contributi

Il progetto è sviluppato internamente per Manta Group. Per contributi o segnalazioni:

1. Crea un branch feature
2. Implementa modifiche con test
3. Aggiorna documentazione
4. Crea pull request con descrizione dettagliata

## 📄 Licenza

Proprietario - Manta Group. Tutti i diritti riservati.

## 📞 Supporto

Per supporto tecnico o domande:
- **Documentazione**: `/docs/` directory
- **API Docs**: http://localhost:8000/docs
- **Changelog**: `/docs/changelog.md`
- **Issues**: Sistema interno di ticketing

---

**CarbonPilot v2.3.1** - Sistema di gestione produzione per l'eccellenza aeronautica 🛩️