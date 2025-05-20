# Changelog CarbonPilot

Questo file contiene il registro dei cambiamenti più significativi del progetto.

## [v0.4.2] - Pulizia Modelli e Migrazioni - 2024-05-22

### Modifiche al Database
- Rimossi campi inutilizzati dai modelli:
  - Da `Tool`: data_ultima_manutenzione, max_temperatura, max_pressione, cicli_completati
  - Da `Parte`: peso, spessore, cliente
- Aggiornati gli schemi Pydantic corrispondenti
- Aggiornati i dati di test per riflettere le modifiche

### Aggiornamenti Frontend
- Adattate interfacce utente per rimuovere i campi eliminati:
  - Rimossi campi cliente, peso, spessore dal form di creazione/modifica Parte
  - Rimossa colonna cliente dalla tabella Parti
  - Aggiornate interfacce TypeScript nel file api.ts
  - Rimosso filtro per cliente dalla pagina Parti

### Miglioramenti
- Creato script `run_migration.py` per semplificare la gestione delle migrazioni Alembic
- Migliorata la configurazione di Alembic per supporto locale e Docker
- Aggiunto script `apply_schema_changes.py` per modifiche manuali al database
- Ottimizzata la gestione delle variabili d'ambiente per le migrazioni

### Correzioni
- Risolti problemi di connessione al database durante le migrazioni
- Corretta la gestione delle revisioni Alembic
- Migliorata la gestione degli errori durante le migrazioni

## [v0.4.1] - Fix Routing e Test CRUD - 2024-05-20

### Correzioni
- Risolto problema di routing per l'endpoint `/api/v1/parte/`
- Uniformato il routing di tutti gli endpoint sotto `/api/v1/`
- Migliorata la struttura dei router FastAPI per maggiore coerenza
- Corretti i test CRUD per la gestione delle parti

### Miglioramenti
- Aggiunto script `clean_pycache.py` per la pulizia dei file `.pyc`
- Migliorato lo script di seed dei dati di test
- Ottimizzata la gestione delle dipendenze tra modelli

## [v0.3.0] - API CRUD Backend - 2023-10-25

### Aggiunte
- Implementate API CRUD complete per tutti i modelli principali:
  - `/api/catalogo`: Gestione del catalogo prodotti (part number)
  - `/api/parti`: Gestione delle parti prodotte
  - `/api/tools`: Gestione degli stampi (tools)
  - `/api/autoclavi`: Gestione delle autoclavi
  - `/api/cicli-cura`: Gestione dei cicli di cura
- Aggiunta gestione degli errori e logging centralizzato
- Aggiunti test automatici per le API con pytest
- Aggiornato lo script start.sh con comandi per eseguire i test
- Aggiunta paginazione e filtri alle API di lista

### Modifiche
- Aggiornata documentazione Swagger/OpenAPI con sommari e descrizioni dettagliate
- Migliorate le validazioni e gestione degli errori negli endpoint
- Versione dell'API aggiornata a v0.3.0

## [v0.2.0] - Modelli SQLAlchemy e Schemi - 2023-10-20

### Aggiunte
- Definiti modelli SQLAlchemy completi:
  - `Catalogo`: Modello per gestire i part number del catalogo
  - `Parte`: Modello per le parti prodotte associate a un PN del catalogo
  - `Tool`: Modello per gli stampi utilizzati nella laminazione
  - `Autoclave`: Modello per le autoclavi utilizzate nella cura
  - `CicloCura`: Modello per i cicli di cura applicabili in autoclave
- Creati schemi Pydantic per la validazione e serializzazione:
  - Schema base, creazione, update e risposta per ogni modello
  - Validatori personalizzati per regole specifiche
- Configurazione Alembic per le migrazioni del database
- Prima migrazione per la creazione dello schema del database

### Modifiche
- Aggiornata struttura del progetto con cartelle dedicate (schemas, models)
- Migliorata configurazione di connessione al database

## [v0.1.0] - Setup Iniziale - 2023-10-15

### Aggiunte
- Struttura base del progetto con Next.js per il frontend
- Backend FastAPI con PostgreSQL
- Configurazione Docker Compose
- Setup di base per autenticazione
- CI/CD iniziale

---

_Il formato di questo changelog è basato su [Keep a Changelog](https://keepachangelog.com/it/1.0.0/)._ 