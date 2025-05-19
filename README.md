# CarbonPilot

![Versione](https://img.shields.io/badge/versione-0.1.0-green)

CarbonPilot è una piattaforma completa per l'ottimizzazione di processi industriali con l'obiettivo di ridurre l'impatto ambientale. Utilizza algoritmi avanzati di nesting e ottimizzazione per minimizzare gli sprechi e massimizzare l'efficienza.

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
docker-compose exec backend pytest
```

### Frontend

```bash
docker-compose exec frontend npm test
```

## 📚 Documentazione API

La documentazione interattiva dell'API è disponibile all'indirizzo:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

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