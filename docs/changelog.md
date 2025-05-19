# Changelog CarbonPilot

Questo file mantiene un registro di tutti i cambiamenti significativi apportati al progetto CarbonPilot.

## [0.1.0] - 2023-12-01

### Aggiunte
- Setup iniziale del progetto con struttura modulare
- Configurazione del backend FastAPI con SQLAlchemy e PostgreSQL
- Configurazione del frontend Next.js 14 con TypeScript e TailwindCSS
- Aggiunta dei componenti UI di base utilizzando shadcn/ui
- Configurazione di Docker e Docker Compose per orchestrare i servizi
- Predisposizione per l'autenticazione e la gestione utenti
- Configurazione di Alembic per le migrazioni del database
- Pagina Home con layout di base e tema responsivo

### Infrastruttura
- Struttura del database PostgreSQL con tabelle base
- Implementazione base del sistema di API RESTful
- Configurazione ambiente di sviluppo Docker-based

### Modifiche al database
- Setup iniziale schema database
- Creata tabella `users` (predisposta per autenticazione futura)

---

_Il formato di questo changelog è basato su [Keep a Changelog](https://keepachangelog.com/it/1.0.0/)._ 