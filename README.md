# 🚀 CarbonPilot - Sistema di Gestione Produzione Autoclavi

Sistema completo per la gestione della produzione con autoclavi, ottimizzazione del nesting e monitoraggio in tempo reale.

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

### 🔧 **NUOVO: Sistema Nesting Rifattorizzato** ⭐
- **Gestione Stati Strutturata**: Bozza → In Sospeso → Confermato → Completato/Annullato
- **Blocco Autoclavi Solo alla Conferma**: Le autoclavi rimangono disponibili durante la generazione
- **Algoritmo Batch Multi-Autoclave**: Ottimizzazione intelligente su tutte le autoclavi disponibili
- **Parametri Personalizzabili**: Controllo completo di padding, bordi, valvole e rotazione
- **Workflow Approvazioni**: Sistema di conferme per operazioni critiche

### 🎯 Sistema di Nesting Avanzato
- **Ottimizzazione Multi-Autoclave**: Distribuzione intelligente degli ODL su più autoclavi
- **Nesting su Due Piani**: Gestione peso e area con configurazione superficie secondaria
- **Preview Interattiva**: Visualizzazione in tempo reale con drag & drop
- **Parametri Configurabili**: Spaziatura, bordi, limite valvole, rotazione automatica
- **Scoring Intelligente**: Algoritmo di compatibilità autoclave-ODL per ottimizzazione

### 📊 Gestione Produzione
- Monitoraggio ODL in tempo reale
- Tracking fasi produttive (Laminazione → Attesa Cura → Cura → Finito)
- Statistiche e metriche di performance
- Sistema di priorità e gestione code

### 🏭 Gestione Autoclavi
- Monitoraggio stato autoclavi (Disponibile/In Uso/Guasto/Manutenzione)
- Configurazione cicli di cura personalizzati
- Assegnazione automatica e manuale
- Controllo carico massimo e capacità

### 📈 Sistema di Logging e Audit ✅ COMPLETATO
- **Tracciabilità Completa**: Log di tutte le operazioni critiche con timestamp precisi
- **Timeline ODL**: Cronologia completa di ogni ODL dalla creazione al completamento
- **Statistiche Temporali**: Durata in ogni stato, tempo totale produzione, efficienza
- **Monitoraggio Real-time**: Endpoint per progresso e timeline con dati live
- **Generazione Log Automatica**: Sistema per inizializzare log ODL esistenti
- **API Monitoring**: Endpoint completi per stats, timeline e progresso ODL

### 🔐 Gestione Ruoli e Sicurezza
- **4 Ruoli Operativi**: Admin, Responsabile, Laminatore, Autoclavista
- **Permessi Granulari**: Accesso controllato per ogni funzionalità
- **Workflow Approvazioni**: Sistema di conferme per operazioni critiche
- **Tracciamento Accessi**: Log completo delle attività utente

## 🛠️ Tecnologie Utilizzate

### Backend
- **FastAPI**: Framework Python ad alte performance per API REST
- **SQLAlchemy**: ORM per gestione database con modelli tipizzati
- **PostgreSQL/SQLite**: Database relazionale per persistenza dati
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
- **Batch Processing**: Algoritmi per ottimizzazione multi-autoclave

## 🚀 Quick Start

### Prerequisiti
- Python 3.8+
- Node.js 18+
- npm o yarn

### Installazione

1. **Clone del repository**
```bash
git clone https://github.com/your-repo/carbonpilot.git
cd carbonpilot
```

2. **Setup Backend**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

3. **Configurazione Database**
```bash
# Esegui le migrazioni per aggiornare il database
python migrations/add_nesting_enum_and_parameters.py

# Valida la coerenza dei dati
python ../tools/validate_nesting_states.py --verbose
```

4. **Setup Frontend**
```bash
cd frontend
npm install
```

### Avvio Applicazione

1. **Avvia Backend**
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

2. **Avvia Frontend**
```bash
cd frontend
npm run dev
```

3. **Accedi all'applicazione**
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

## 🎮 Come Utilizzare il Nuovo Sistema Nesting

### 1. Workflow Stati Nesting
1. **Generazione Bozza**: Crea nesting in stato "bozza" senza bloccare autoclavi
2. **Promozione a In Sospeso**: Conferma il nesting e blocca l'autoclave
3. **Conferma Finale**: Sposta ODL in "Cura" e mantiene autoclave occupata
4. **Completamento**: Libera autoclave e completa il ciclo

### 2. Algoritmo Batch Multi-Autoclave
1. Vai su **Dashboard → Responsabile → Nesting Batch**
2. Seleziona gli ODL in "Attesa Cura"
3. Il sistema valuta tutte le autoclavi disponibili
4. Genera automaticamente nesting ottimizzati per ogni autoclave
5. Distribuisce gli ODL in modo bilanciato

### 3. Parametri Personalizzabili
- **Padding (mm)**: Spaziatura tra tool (default: 10mm)
- **Borda (mm)**: Bordo minimo dall'autoclave (default: 20mm)
- **Max Valvole**: Limite massimo valvole per autoclave (opzionale)
- **Rotazione**: Abilita/disabilita rotazione automatica tool

### 4. Controlli Disponibili
1. Modifica i parametri nell'interfaccia dedicata
2. Visualizza preview in tempo reale
3. Salva configurazioni personalizzate
4. Applica a singola autoclave o batch completo

## 📁 Struttura Progetto

```
carbonpilot/
├── backend/                 # API FastAPI
│   ├── api/                # Router e endpoint
│   ├── models/             # Modelli SQLAlchemy
│   ├── schemas/            # Schemi Pydantic
│   ├── services/           # Logica business
│   ├── nesting_optimizer/  # Algoritmi ottimizzazione
│   ├── migrations/         # Script migrazione database
│   └── tests/              # Test backend
├── frontend/               # App React/Next.js
│   ├── src/
│   │   ├── app/           # Pages e layout
│   │   ├── components/    # Componenti riutilizzabili
│   │   ├── lib/          # Utilities e API client
│   │   └── utils/        # Helper functions
│   └── public/           # Asset statici
├── tools/                  # Script utilità
│   ├── validate_nesting_states.py  # Validazione coerenza dati
│   └── print_schema_summary.py     # Analisi schema database
├── docs/                   # Documentazione
│   ├── changelog.md        # Log delle modifiche dettagliato
│   └── *.md               # Guide specifiche
└── README.md              # Questo file
```

## 🔧 Configurazione

### Variabili d'Ambiente

**Backend (.env)**
```env
DATABASE_URL=sqlite:///./carbonpilot.db
SECRET_KEY=your-secret-key
DEBUG=True
```

**Frontend (.env.local)**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## 📚 Documentazione

- [Changelog Completo](docs/changelog.md) - Cronologia dettagliata delle modifiche
- [API Documentation](http://localhost:8000/docs) - Swagger UI (quando il backend è attivo)
- [Validazione Stati Nesting](tools/validate_nesting_states.py) - Script per controllo coerenza

## 🧪 Testing e Validazione

### Backend
```bash
cd backend
pytest
```

### Validazione Database
```bash
cd backend
# Controllo coerenza stati nesting
python ../tools/validate_nesting_states.py --verbose

# Correzione automatica inconsistenze
python ../tools/validate_nesting_states.py --fix --verbose
```

### Frontend
```bash
cd frontend
npm run test
```

## 🔄 Migrazioni Database

### Applicazione Migrazioni
```bash
cd backend
# Migrazione parametri nesting e enum stati
python migrations/add_nesting_enum_and_parameters.py
```

### Verifica Post-Migrazione
```bash
# Controllo struttura database
python test_db_data.py

# Validazione coerenza dati
python ../tools/validate_nesting_states.py --verbose
```

## 🚨 Troubleshooting

### Problemi Comuni

1. **Errori Enum Stati**: Esegui la migrazione e validazione
2. **Autoclavi Bloccate**: Usa lo script di validazione con `--fix`
3. **ODL Inconsistenti**: Controlla log e applica correzioni automatiche
4. **Parametri Mancanti**: La migrazione imposta valori di default

### Log e Debug
- Backend logs: Controllare console FastAPI
- Database: Usare script `test_db_data.py` per diagnostica
- Validazione: Script `validate_nesting_states.py` per controlli completi

## 📈 Roadmap

- [ ] Interfaccia frontend per nuovo sistema nesting
- [ ] Dashboard real-time per monitoraggio batch
- [ ] Ottimizzazioni algoritmo multi-autoclave
- [ ] Sistema notifiche per stati nesting
- [ ] Export/import configurazioni parametri

## 🤝 Contributi

Per contribuire al progetto:
1. Fork del repository
2. Crea branch feature (`git checkout -b feature/nome-feature`)
3. Commit modifiche (`git commit -am 'Aggiunge nuova feature'`)
4. Push al branch (`git push origin feature/nome-feature`)
5. Crea Pull Request

## 📄 Licenza

Questo progetto è sotto licenza MIT. Vedi il file `LICENSE` per dettagli.