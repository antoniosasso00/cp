# Changelog CarbonPilot

Questo file contiene il registro dei cambiamenti più significativi del progetto.

## [v0.9.0] - Fase 9: Report PDF Automatici

### [2024-01-16 - Generazione Report PDF]

- **Implementata generazione completa di report PDF** con contenuti dettagliati:
  - Riepilogo nesting con tabelle autoclavi, ODL assegnati, area e valvole utilizzate
  - Layout grafico visivo delle autoclavi con codifica colori per utilizzo
  - Sezioni opzionali: dettaglio ODL e tempi fase
  - Report per periodi: giornaliero, settimanale, mensile
- **Nuove API backend per report**:
  - `GET /api/v1/reports/generate` - Genera e scarica report PDF
  - `GET /api/v1/reports/list` - Lista report esistenti
  - `GET /api/v1/reports/download/{filename}` - Scarica report specifico
- **Servizio ReportService** con generazione PDF tramite reportlab:
  - Calcolo automatico intervalli di date (giorno/settimana/mese)
  - Query ottimizzate per recupero dati nesting, ODL e tempi fase
  - Layout grafico SVG per visualizzazione autoclavi
  - Tabelle formattate con stili professionali
- **Nuova pagina frontend `/dashboard/reports`**:
  - UI moderna con card per generazione e gestione report
  - Checkbox per selezione sezioni opzionali (ODL, tempi)
  - Pulsanti dedicati per report giornaliero, settimanale, mensile
  - Tabella report esistenti con download diretto
  - Gestione completa errori e feedback utente
- **Miglioramenti infrastruttura**:
  - Aggiunta dipendenza reportlab==4.2.5
  - Creazione directory `/app/reports` in Docker
  - Componente Checkbox per shadcn/ui
  - API client con gestione blob per download PDF

### Funzionalità Tecniche
- Generazione PDF con reportlab: tabelle, grafici, layout responsive
- Salvataggio automatico file su disco con naming convention
- Download diretto browser con gestione blob
- Filtri temporali automatici per recupero dati
- Gestione errori completa con toast notifications

### Correzioni
- Aggiunto router reports alle route principali
- Installata dipendenza @radix-ui/react-checkbox
- Corretta gestione tipi TypeScript per componenti checkbox

## [v0.6.0] - Fase 8: Schedulazione Manuale Stabile

### [2024-01-15 - Schedulazione ODL per Autoclavi]

- **Risolto crash "startOf is not a function"** nel componente CalendarSchedule.tsx
- **Sostituito localizer manuale con dateFnsLocalizer ufficiale** di react-big-calendar
  - Implementato localizer italiano con date-fns e locale 'it'
  - Rimosso import errato di momentLocalizer
  - Corretta implementazione con `dateFnsLocalizer({ format, parse, startOfWeek, getDay, locales: { it } })`
- **Stabilizzata pagina `/dashboard/schedule`** senza errori runtime
- **Funzionalità complete di schedulazione manuale**:
  - Creazione manuale di schedule (ODL in "Attesa Cura" + Autoclave + orario)
  - Editing con caricamento automatico dei dati nel form
  - Eliminazione di schedulazioni esistenti
  - Visualizzazione su react-big-calendar con risorse (autoclavi)
  - Auto-generazione di schedulazioni tramite algoritmo backend
- **Miglioramenti tecnici**:
  - Aggiunto useCallback per fetchSchedules per evitare loop infiniti
  - Corrette dipendenze nei useEffect
  - Rimosso cast "as any" dal localizer
  - Integrazione completa con API backend per schedules, autoclavi e ODL

### Correzioni
- Risolto problema di compatibilità tra react-big-calendar e date-fns
- Sistemata gestione delle date italiane nel calendario
- Corretta visualizzazione degli eventi con colori differenziati (manuali vs automatici)

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

### [2023-05-23 - Modulo di Nesting Automatico]

- Implementata pagina `/nesting` con visualizzazione tabellare dei nesting generati
- Aggiunta funzionalità per la generazione automatica di nesting tramite `POST /api/v1/nesting/auto`
- Visualizzazione dettagliata dei nesting con ODL inclusi
- Ottimizzazione automatica degli ODL in stato "in_attesa_di_cura"
- Interfaccia utente con feedback visivo durante la generazione (toast e spinner)
- Aggiornamento automatico della tabella dopo la generazione di nuovi nesting
- Integrazione completa con il modulo backend di ottimizzazione

---

_Il formato di questo changelog è basato su [Keep a Changelog](https://keepachangelog.com/it/1.0.0/)._ 