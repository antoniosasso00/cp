# Changelog CarbonPilot

Questo file contiene il registro dei cambiamenti più significativi del progetto.

## [v0.7.1] - Fix Nesting Docker

### Correzioni
- Risolto problema di avvio in Docker dopo l'aggiunta del modulo di nesting
- Aggiunta migrazione manuale per i modelli `NestingParams` e `NestingResult`
- Implementata soluzione per garantire l'installazione di OR-Tools
- Creato script di riparazione `fix_nesting_docker.sh` per applicare patch in modo automatico
- Migliorati timeout di avvio e healthcheck nei container Docker

### Miglioramenti
- Documentata procedura di debugging Docker in `docker_debug_log.md`
- Aggiunto script SQL diretto per la creazione delle tabelle di nesting
- Ottimizzati parametri di connessione al database

## [v0.7.0] - Nesting Automatico OR-Tools

### Aggiunte
- Implementato sistema completo di nesting automatico con OR-Tools
  - Algoritmo di ottimizzazione per disposizione ODL nelle autoclavi
  - Interfaccia utente per nesting automatico e manuale
  - Visualizzazione grafica dei layout con canvas
  - Parametri configurabili per l'ottimizzazione
  - API backend complete per supporto nesting

### Funzionalità
- Nesting automatico multi-autoclave con ottimizzazione OR-Tools
  - Rispetto di area utile e linee vuoto per ogni autoclave
  - Accorpamento ODL con cicli di cura compatibili
  - Ottimizzazione basata su priorità, area e valvole
- Nesting manuale con selezione ODL
  - Filtri per ciclo di cura, priorità e ricerca
  - Visualizzazione dettagliata degli ODL selezionati
- Gestione risultati nesting
  - Conferma/rifiuto del layout proposto
  - Aggiornamento stato ODL a "in cura" alla conferma
  - Storia dei nesting eseguiti e statistiche

### Backend
- Modelli per parametri di nesting e risultati
- API RESTful per tutte le operazioni
- Algoritmo bin packing 2D con OR-Tools
- Fallback greedy per casi non risolvibili

### Frontend
- Interfaccia suddivisa in tab (Automatico/Manuale/Risultati)
- Visualizzatore del layout con canvas
- Form per parametri di ottimizzazione
- Statistiche di efficienza area e valvole

## [v0.5.0] 

### Aggiunte
- Implementato seed completo degli ODL (Ordini di Lavoro)
  - Creazione automatica di 5 ODL di test con stati diversi
  - Associazione corretta con parti e strumenti esistenti
  - Gestione delle priorità e note per ogni ODL
  - Verifica automatica del corretto seeding

### Miglioramenti
- Ottimizzato script `seed_test_data.py` con modalità debug
- Migliorata gestione delle dipendenze tra modelli nel seeding
- Aggiunta verifica automatica degli endpoint dopo il seeding

### Correzioni
- Risolti problemi di TypeScript nel componente ODLModal
- Corretta implementazione del componente Textarea
- Sistemata gestione degli eventi onChange nei form
- Migliorata gestione degli errori durante il seeding

## [v0.4.2] 

### Aggiunte
- Implementata sezione Strumenti nella dashboard
  - Tabella con lista degli strumenti
  - Modal per creazione/modifica strumenti
  - Funzionalità di ricerca e filtro
  - Gestione stati (DISPONIBILE, IN_USO, GUASTO, MANUTENZIONE)
  - Integrazione con API backend

- Implementata sezione Cicli di Cura nella dashboard
  - Tabella con lista dei cicli di cura
  - Modal per creazione/modifica cicli
  - Funzionalità di ricerca e filtro
  - Gestione stati (ATTIVO, INATTIVO)
  - Integrazione con API backend

- Implementata sezione Autoclavi nella dashboard
  - Tabella con lista delle autoclavi
  - Modal per creazione/modifica autoclavi
  - Funzionalità di ricerca e filtro
  - Gestione stati (DISPONIBILE, IN_USO, GUASTO, MANUTENZIONE)
  - Integrazione con API backend

### Miglioramenti
- Aggiunta validazione dei form con Zod
- Implementata gestione degli errori con toast notifications
- Migliorata UX con feedback visivi per le azioni
- Ottimizzata gestione dello stato delle applicazioni

### Correzioni
- Risolti problemi di TypeScript nei componenti
- Corretta gestione delle date nei form
- Sistemata visualizzazione dei badge di stato

## [v0.4.1] - Fix Routing e Test CRUD 

### Correzioni
- Risolto problema di routing per l'endpoint `/api/v1/parte/`
- Uniformato il routing di tutti gli endpoint sotto `/api/v1/`
- Migliorata la struttura dei router FastAPI per maggiore coerenza
- Corretti i test CRUD per la gestione delle parti

### Miglioramenti
- Aggiunto script `clean_pycache.py` per la pulizia dei file `.pyc`
- Migliorato lo script di seed dei dati di test
- Ottimizzata la gestione delle dipendenze tra modelli

## [v0.3.0] - API CRUD Backend 

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

## [v0.2.0] - Modelli SQLAlchemy e Schemi 

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

## [v0.1.0] - Setup Iniziale 

### Aggiunte
- Struttura base del progetto con Next.js per il frontend
- Backend FastAPI con PostgreSQL
- Configurazione Docker Compose
- Setup di base per autenticazione
- CI/CD iniziale

## [v0.5.2] 

### Miglioramenti
- Uniformata l'interfaccia utente delle azioni (Modifica/Elimina) in tutte le tabelle dell'applicazione
  - Implementato DropdownMenu per le azioni in Tools, Catalogo, Parti, Cicli Cura e Autoclavi
  - Aggiunto feedback visivo con toast notifications per tutte le azioni
  - Migliorata la coerenza UX/UI tra le diverse sezioni
  - Ottimizzata la gestione degli stati di caricamento

### Correzioni
- Risolti problemi di allineamento nelle tabelle
- Sistemata la gestione degli errori nelle operazioni CRUD
- Migliorata la reattività dell'interfaccia durante le operazioni

---

_Il formato di questo changelog è basato su [Keep a Changelog](https://keepachangelog.com/it/1.0.0/)._ 