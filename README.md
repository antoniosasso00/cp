# CarbonPilot

Sistema modulare per la gestione avanzata della produzione in fibra di carbonio, con dashboard interattiva, gestione catalogo, parti, tools, autoclavi e cicli di cura.

Versione attuale: `v0.4.0`

## Tecnologie principali

- 📦 Backend: FastAPI + PostgreSQL + SQLAlchemy + Alembic
- 💻 Frontend: Next.js + TypeScript + TailwindCSS + shadcn/ui
- 🐳 Containerizzazione: Docker + Docker Compose
- 📈 Dashboard amministrativa con filtri, CRUD e interfaccia minimal

## Funzionalità implementate nella v0.4.0

✅ CRUD completo:
- Catalogo (Part Number)
- Parti associate a PN
- Tools
- Autoclavi
- Cicli di Cura

✅ Frontend con:
- Sidebar navigabile
- Tabelle responsive filtrabili
- Moduli dinamici per creazione e modifica

## Come avviare il progetto

```bash
docker-compose up -d --build
```

Accedi a:
- Frontend: http://localhost:3000
- API Swagger: http://localhost:8000/docs

## Prossima fase

🚧 v0.5.x – Introduzione del modulo ODL con gestione stato e priorità

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
│ ├── models/             # Modelli SQLAlchemy
│ ├── schemas/            # Schemi Pydantic
│ ├── services/           # Logica di business
│ ├── migrations/         # Migrazioni Alembic
│ ├── nesting_optimizer/  # Algoritmi di ottimizzazione
│ └── tests/              # Test unitari e di integrazione
├── frontend/             # Applicazione Next.js
│ ├── src/
│ │ ├── app/              # Routes e layout
│ │ ├── components/       # Componenti riutilizzabili
│ │ ├── lib/              # Utilities e hooks
│ │ └── styles/           # CSS e stili
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
| Catalogo | `/api/catalogo` | GET, POST, PUT, DELETE |
| Parti | `/api/parti` | GET, POST, PUT, DELETE |
| Tools | `/api/tools` | GET, POST, PUT, DELETE |
| Autoclavi | `/api/autoclavi` | GET, POST, PUT, DELETE |
| Cicli di Cura | `/api/cicli-cura` | GET, POST, PUT, DELETE |

Ogni endpoint supporta operazioni di filtraggio e paginazione:

```
GET /api/parti?part_number=ABC123&cliente=Cliente1&skip=0&limit=10
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

Sviluppato con ❤️ dal team CarbonPilot