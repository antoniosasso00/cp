# CarbonPilot

Sistema modulare per la gestione avanzata della produzione in fibra di carbonio, con dashboard interattiva, gestione catalogo, parti, tools, autoclavi e cicli di cura.

![versione](https://img.shields.io/badge/version-0.9.0-brightgreen)

## Tecnologie principali

- 📦 Backend: FastAPI + PostgreSQL + SQLAlchemy + Alembic
- 💻 Frontend: Next.js + TypeScript + TailwindCSS + shadcn/ui
- 🐳 Containerizzazione: Docker + Docker Compose
- 📈 Dashboard amministrativa con filtri, CRUD e interfaccia minimal
- 🧠 Algoritmi di ottimizzazione per nesting
- 📄 Generazione report PDF automatici

## Funzionalità implementate nella v0.9.0

✅ CRUD completo:
- Catalogo (Part Number)
- Parti associate a PN
- Tools
- Autoclavi
- Cicli di Cura
- ODL (Ordini di Lavoro)

✅ Nesting Automatico:
- Ottimizzazione degli ODL nelle autoclavi
- Gestione automatica del processo di cura
- Visualizzazione dei nesting generati
- Dettagli completi dei nesting e ODL inclusi

✅ Schedulazione Manuale:
- Creazione manuale di schedule (ODL + Autoclave + orario)
- Visualizzazione calendario con react-big-calendar
- Auto-generazione schedulazioni tramite algoritmo backend
- Editing e eliminazione schedulazioni esistenti

✅ **Report PDF Automatici** (NUOVO v0.9.0):
- Generazione report giornalieri, settimanali, mensili
- Riepilogo nesting con tabelle dettagliate
- Layout grafico visivo delle autoclavi
- Sezioni opzionali: dettaglio ODL e tempi fase
- Download diretto e gestione report esistenti
- Salvataggio automatico su disco

✅ Frontend con:
- Sidebar navigabile
- Tabelle responsive filtrabili
- Moduli dinamici per creazione e modifica
- Gestione stati ODL e priorità
- Interfaccia uniforme per le azioni (Modifica/Elimina)
- Feedback visivo con toast notifications
- **Pagina Reports con UI moderna per generazione PDF**

## 🚀 Stato del Progetto – v0.9.0
- Completata la Fase 9: Report PDF Automatici
- Sistema completo di generazione report con reportlab
- Dashboard CRUD stabile per tutti i moduli
- Nesting automatico e schedulazione manuale funzionanti
- **Nuova sezione Reports con download PDF**
- Backend FastAPI e frontend Next.js sincronizzati
- Build stabile in locale e Docker

## Come avviare il progetto

```bash
docker-compose up -d --build
```

Accedi a:
- Frontend: http://localhost:3000
- API Swagger: http://localhost:8000/docs

## Prossima fase

🚧 v0.6.x – Introduzione del modulo di gestione delle risorse

## 📋 Caratteristiche

- **Frontend moderno**: Interfaccia utente reattiva costruita con Next.js, TypeScript e TailwindCSS
- **Backend robusto**: API RESTful sviluppata con FastAPI e SQLAlchemy
- **Database relazionale**: PostgreSQL per l'archiviazione persistente dei dati
- **Containerizzazione**: Configurazione Docker per facilitare lo sviluppo e il deployment
- **Pronto per l'autenticazione**: Struttura predisposta per l'implementazione di funzionalità di autenticazione

## 🚀 Installazione e Avvio

### Prerequisiti

- Docker e Docker Compose
- Git

### Passi per l'avvio

1. Clona il repository:
   ```bash
   git clone https://github.com/tuonome/carbonpilot.git
   cd carbonpilot
   ```

2. Avvia i container con Docker Compose:
   ```bash
   docker-compose up -d
   ```

3. Accedi all'applicazione:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000

## 🏗️ Struttura del Progetto

```
progetto-root/
├── backend/              # Servizio API FastAPI
│ ├── api/                # Implementazione API
│ │ ├── routers/          # Router per le operazioni CRUD
│ │ │   ├── v1/           # Router per le operazioni CRUD v1
│ │ │   └── nesting_optimizer/  # Algoritmi di ottimizzazione
│ │ ├── models/             # Modelli SQLAlchemy
│ │ ├── schemas/            # Schemi Pydantic
│ │ ├── services/           # Logica di business
│ │ ├── migrations/         # Migrazioni Alembic
│ │ └── tests/              # Test unitari e di integrazione
│ ├── frontend/             # Applicazione Next.js
│ │ ├── src/
│ │ │   ├── app/              # Routes e layout
│ │ │   │   ├── dashboard/    # Pagine della dashboard
│ │ │   │   │   ├── tools/    # Gestione tools
│ │ │   │   │   ├── catalog/  # Gestione catalogo
│ │ │   │   │   ├── parts/    # Gestione parti
│ │ │   │   │   ├── cicli-cura/ # Gestione cicli
│ │ │   │   │   └── autoclavi/  # Gestione autoclavi
│ │ │   │   ├── components/       # Componenti riutilizzabili
│ │ │   │   │   ├── ui/          # Componenti UI base
│ │ │   │   │   └── shared/      # Componenti condivisi
│ │ │   │   ├── lib/             # Utilities e hooks
│ │ │   │   │   ├── api/         # Client API
│ │ │   │   │   └── utils/       # Funzioni di utilità
│ │ │   │   └── styles/          # CSS e stili
│ │ ├── components/       # Componenti riutilizzabili
│ │ └── styles/          # CSS e stili
├── docs/                 # Documentazione
│ └── changelog.md        # Registro dei cambiamenti
├── docker-compose.yml    # Configurazione Docker Compose
└── README.md             # Documentazione principale
```

## 🧪 Testing

### Backend

```bash
# All'interno del container:
cd backend
./start.sh test

# Dall'esterno del container:
docker-compose exec backend ./start.sh test
```

### Frontend

```bash
docker-compose exec frontend npm test
```

## 📚 Documentazione API

La documentazione interattiva dell'API è disponibile all'indirizzo:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Endpoint principali

CarbonPilot espone API CRUD complete per tutti i modelli principali:

| Risorsa | Endpoint Base | Operazioni |
|---------|--------------|------------|
| Catalogo | `/api/v1/catalogo` | GET, POST, PUT, DELETE |
| Parti | `/api/v1/parti` | GET, POST, PUT, DELETE |
| Tools | `/api/v1/tools` | GET, POST, PUT, DELETE |
| Autoclavi | `/api/v1/autoclavi` | GET, POST, PUT, DELETE |
| Cicli di Cura | `/api/v1/cicli-cura` | GET, POST, PUT, DELETE |
| ODL | `/api/v1/odl` | GET, POST, PUT, DELETE |
| Nesting | `/api/v1/nesting` | GET, POST (auto) |
| Schedules | `/api/v1/schedules` | GET, POST, PUT, DELETE |
| **Reports** | `/api/v1/reports` | **GET (generate, list, download)** |

#### Endpoint Reports (NUOVO v0.9.0)

| Endpoint | Metodo | Descrizione |
|----------|--------|-------------|
| `/api/v1/reports/generate` | GET | Genera e scarica report PDF |
| `/api/v1/reports/list` | GET | Lista report esistenti |
| `/api/v1/reports/download/{filename}` | GET | Scarica report specifico |

**Parametri per generazione report:**
- `range_type`: `giorno`, `settimana`, `mese`
- `include`: `odl,tempi` (sezioni opzionali)
- `download`: `true/false` (download diretto o info file)

Ogni endpoint supporta operazioni di filtraggio e paginazione:

```
GET /api/v1/parti?part_number=ABC123&skip=0&limit=10
GET /api/v1/reports/generate?range_type=settimana&include=odl,tempi
```

### Autenticazione

L'autenticazione non è ancora implementata. Tutte le API sono attualmente accessibili senza credenziali.

## 🤝 Contribuire

Per contribuire al progetto, segui questi passi:

1. Forka il repository
2. Crea un branch per la tua feature (`git checkout -b feature/nome-feature`)
3. Effettua i tuoi cambiamenti
4. Pusha al branch (`git push origin feature/nome-feature`)
5. Apri una Pull Request

## 📄 Licenza

[MIT](LICENSE)

## 📧 Contatti

Per domande o supporto, contattaci a [email@example.com](mailto:email@example.com).

---