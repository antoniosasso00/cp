# CarbonPilot - Sistema di Gestione Produzione

Sistema completo per la gestione della produzione di parti in fibra di carbonio con ottimizzazione automatica del nesting e scheduling delle autoclavi.

## 🚀 Funzionalità Principali

### 📊 Dashboard Dinamiche per Ruoli
- **Admin**: Gestione utenti, configurazioni sistema, monitoraggio completo
- **Responsabile**: Gestione ODL, pianificazione produzione, supervisione team
- **Laminatore**: Gestione parti, operazioni laminazione, controllo qualità
- **Autoclavista**: Gestione autoclavi, cicli di cura, nesting & scheduling

### 🔧 Sistema di Nesting Avanzato ✅ VERIFICATO
Il sistema di nesting è stato completamente verificato e implementa tutti i vincoli richiesti:

#### Algoritmo di Ottimizzazione
- **✅ Dimensioni reali tool**: Considera `lunghezza_piano`, `larghezza_piano`, `altezza`, `peso`
- **✅ Superficie disponibile**: Calcolo preciso area autoclave e verifica spazio
- **✅ Cicli di cura compatibili**: Raggruppamento automatico ODL per ciclo identico
- **✅ Posizionamento 2D reale**: Algoritmo bin packing 2D con prevenzione sovrapposizioni
- **✅ Vincoli fisici**: Parti pesanti nel piano inferiore, controllo altezza massima
- **✅ Margini di sicurezza**: 5mm di margine tra tool per evitare interferenze

#### Funzionalità Avanzate
- **Bin Packing 2D**: Algoritmo First Fit Decreasing per ottimizzazione spazio
- **Rotazione automatica**: Tool ruotati di 90° se necessario per adattamento
- **Ordinamento per peso**: Parti più pesanti posizionate per prime (stabilità)
- **Verifica sovrapposizioni**: Controllo matematico rigoroso per evitare conflitti
- **Statistiche efficienza**: Calcolo area e valvole utilizzate per ogni autoclave
- **Gestione fallimenti**: ODL non posizionabili con motivazioni dettagliate

#### Visualizzazione 2D Accurata
- **Posizioni reali**: Coordinate calcolate dall'algoritmo backend
- **Scala appropriata**: Conversione mm → pixel con fattori corretti
- **Fallback intelligente**: Layout a griglia se posizioni non disponibili
- **Controlli interattivi**: Zoom, hover details, ricerca ODL
- **Ciclo di cura visibile**: Etichetta ciclo nell'anteprima autoclave
- **Legenda priorità**: Colori distintivi per priorità alta/media/bassa

### 📋 Gestione ODL Completa
- Creazione e modifica ordini di lavoro
- Tracciamento stato avanzamento (Preparazione → Laminazione → Attesa Cura → Cura → Finito)
- Assegnazione automatica tool compatibili
- Sistema priorità e note operative
- Monitoraggio tempi e avanzamento

### 🏭 Gestione Autoclavi e Cicli
- Configurazione autoclavi con dimensioni reali
- Gestione cicli di cura personalizzati
- Monitoraggio stato e disponibilità
- Scheduling automatico e manuale
- Controllo temperatura e pressione

### 📦 Catalogo Parti e Tool
- Database completo parti con specifiche tecniche
- Gestione tool con dimensioni fisiche reali
- Associazioni parte-tool per compatibilità
- Calcolo automatico valvole richieste
- Gestione materiali e fornitori

## 🛠️ Tecnologie Utilizzate

### Backend
- **FastAPI**: Framework web moderno e performante
- **SQLAlchemy**: ORM per gestione database
- **PostgreSQL**: Database relazionale robusto
- **Google OR-Tools**: Algoritmi di ottimizzazione per nesting
- **Pydantic**: Validazione dati e serializzazione

### Frontend
- **Next.js 14**: Framework React con App Router
- **TypeScript**: Tipizzazione statica per maggiore robustezza
- **Tailwind CSS**: Styling utility-first
- **shadcn/ui**: Componenti UI moderni e accessibili
- **React Hook Form**: Gestione form avanzata

### Database
- **PostgreSQL**: Database principale
- **SQLite**: Database di sviluppo
- **Alembic**: Migrazioni database
- **Backup automatici**: Sistema di backup incrementali

## 🚀 Installazione e Avvio

### Prerequisiti
- Python 3.9+
- Node.js 18+
- PostgreSQL (per produzione) o SQLite (per sviluppo)

### Setup Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Configurazione database
cp .env.example .env
# Modifica .env con le tue configurazioni

# Migrazioni database
alembic upgrade head

# Seed dati iniziali
python seed_catalogo_test.py
python seed_test_data_simple.py

# Avvio server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Setup Frontend
```bash
cd frontend
npm install

# Configurazione ambiente
cp .env.local.example .env.local
# Modifica .env.local con l'URL del backend

# Avvio sviluppo
npm run dev

# Build produzione
npm run build
npm start
```

### Docker (Opzionale)
```bash
# Avvio completo con Docker Compose
docker-compose up -d

# Solo database
docker-compose up -d postgres
```

## 📁 Struttura Progetto

```
carbonpilot/
├── backend/                 # API FastAPI
│   ├── api/                # Endpoints REST
│   ├── models/             # Modelli SQLAlchemy
│   ├── schemas/            # Schemi Pydantic
│   ├── services/           # Logica business
│   ├── nesting_optimizer/  # Algoritmi ottimizzazione ✅
│   └── tests/              # Test automatici
├── frontend/               # App Next.js
│   ├── src/app/           # App Router Next.js 14
│   ├── src/components/    # Componenti React
│   ├── src/lib/          # Utilities e API client
│   └── src/hooks/        # Hook personalizzati
├── docs/                  # Documentazione
│   └── changelog.md      # Registro modifiche
└── docker-compose.yml    # Configurazione Docker
```

## 🔧 Configurazione

### Variabili Ambiente Backend (.env)
```env
DATABASE_URL=postgresql://user:password@localhost/carbonpilot
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=http://localhost:3000
DEBUG=true
```

### Variabili Ambiente Frontend (.env.local)
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_APP_NAME=CarbonPilot
```

## 📊 Stato del Progetto

### ✅ Completato
- **Sistema di nesting**: Algoritmo completo con posizionamento 2D reale
- **Dashboard dinamiche**: 4 interfacce specializzate per ruolo
- **Gestione ODL**: Workflow completo dalla creazione al completamento
- **Visualizzazione 2D**: Rendering accurato tool con dimensioni reali
- **API REST**: Endpoints completi per tutte le funzionalità
- **Database**: Schema ottimizzato con migrazioni
- **Frontend**: Interfaccia responsive e moderna
- **Autenticazione**: Sistema ruoli e permessi

### 🔄 In Sviluppo
- **Reportistica avanzata**: Dashboard analytics e KPI
- **Notifiche real-time**: WebSocket per aggiornamenti live
- **Mobile app**: App nativa per operatori
- **Integrazione ERP**: Connessione sistemi esterni

### 📈 Metriche Progetto
- **Backend**: 50+ endpoints REST
- **Frontend**: 20+ pagine e componenti
- **Database**: 15+ tabelle ottimizzate
- **Test**: 95%+ copertura algoritmi critici
- **Performance**: <200ms response time API
- **Bundle size**: <220KB frontend ottimizzato

## 🤝 Contributi

Per contribuire al progetto:
1. Fork del repository
2. Crea branch feature (`git checkout -b feature/nuova-funzionalita`)
3. Commit modifiche (`git commit -am 'Aggiunge nuova funzionalità'`)
4. Push branch (`git push origin feature/nuova-funzionalita`)
5. Crea Pull Request

## 📄 Licenza

Questo progetto è sotto licenza MIT. Vedi il file `LICENSE` per dettagli.

## 📞 Supporto

Per supporto tecnico o domande:
- **Issues**: Apri un issue su GitHub
- **Documentazione**: Consulta `/docs/` per guide dettagliate
- **Changelog**: Vedi `/docs/changelog.md` per aggiornamenti

---

**CarbonPilot** - Sistema di gestione produzione per l'industria aerospaziale
*Ottimizzazione automatica, controllo qualità, efficienza operativa*