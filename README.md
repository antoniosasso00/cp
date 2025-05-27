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

### 🔧 **NUOVO: Parametri di Nesting Regolabili** ⭐
- **Controlli in tempo reale**: Modifica distanza perimetrale, spaziatura tool, rotazione automatica
- **Preview dinamica**: Visualizzazione immediata dei risultati senza salvare
- **Ottimizzazione personalizzata**: Priorità configurabile (peso/area/equilibrato)
- **Interfaccia intuitiva**: Pannello dedicato con slider, toggle e dropdown

### 🎯 Sistema di Nesting Avanzato
- Ottimizzazione automatica del posizionamento ODL nelle autoclavi
- Nesting su due piani con gestione peso e area
- Preview interattiva con drag & drop
- Generazione automatica multipla per tutte le autoclavi disponibili

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

3. **Setup Frontend**
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

## 🎮 Come Utilizzare i Parametri di Nesting

### 1. Accesso alla Funzionalità
1. Vai su **Dashboard → Autoclavista → Nesting**
2. Clicca su **"Anteprima Nesting"**
3. Il pannello **⚙️ Parametri Nesting** appare sopra la preview

### 2. Controlli Disponibili
- **Distanza Perimetrale** (0-10 cm): Spazio dal bordo dell'autoclave
- **Spaziatura Tool** (0-5 cm): Spazio minimo tra i componenti
- **Rotazione Automatica**: Abilita/disabilita rotazione tool per ottimizzare spazio
- **Priorità Ottimizzazione**: PESO/AREA/EQUILIBRATO

### 3. Utilizzo
1. Modifica i parametri con i controlli intuitivi
2. Clicca **"Applica Modifiche"** per rigenerare la preview
3. Visualizza immediatamente i risultati
4. Usa **"Reset Default"** per tornare ai valori predefiniti
5. Salva o approva quando soddisfatto

## 📁 Struttura Progetto

```
carbonpilot/
├── backend/                 # API FastAPI
│   ├── api/                # Router e endpoint
│   ├── models/             # Modelli SQLAlchemy
│   ├── schemas/            # Schemi Pydantic
│   ├── services/           # Logica business
│   ├── nesting_optimizer/  # Algoritmi ottimizzazione
│   └── tests/              # Test backend
├── frontend/               # App React/Next.js
│   ├── src/
│   │   ├── app/           # Pages e layout
│   │   ├── components/    # Componenti riutilizzabili
│   │   ├── lib/          # Utilities e API client
│   │   └── utils/        # Helper functions
│   └── public/           # Asset statici
├── docs/                 # Documentazione
│   ├── changelog.md      # Log delle modifiche
│   └── *.md             # Guide specifiche
└── README.md            # Questo file
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

- [Parametri Nesting Regolabili](docs/nesting-parametri-regolabili.md) - Guida completa alla nuova funzionalità
- [Changelog](docs/changelog.md) - Cronologia delle modifiche
- [API Documentation](http://localhost:8000/docs) - Swagger UI (quando il backend è attivo)

## 🧪 Testing

### Backend
```bash
cd backend
pytest
```

### Frontend
```bash
cd frontend
npm test
npm run build  # Test build produzione
```

### Test Endpoint Parametri
```bash
# Test senza parametri
curl "http://localhost:8000/api/v1/nesting/preview"

# Test con parametri personalizzati
curl "http://localhost:8000/api/v1/nesting/preview?distanza_perimetrale_cm=2.0&spaziatura_tra_tool_cm=1.0&rotazione_tool_abilitata=true&priorita_ottimizzazione=PESO"
```

## 🤝 Contribuire

1. Fork del progetto
2. Crea un branch per la feature (`git checkout -b feature/AmazingFeature`)
3. Commit delle modifiche (`git commit -m 'Add some AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Apri una Pull Request

## 📄 Licenza

Questo progetto è sotto licenza MIT. Vedi il file `LICENSE` per i dettagli.

## 🆘 Supporto

Per problemi o domande:
- Apri un issue su GitHub
- Consulta la documentazione in `docs/`
- Controlla il changelog per modifiche recenti

---

**Sviluppato con ❤️ per l'ottimizzazione della produzione industriale**