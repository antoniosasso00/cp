# Changelog CarbonPilot

Questo file contiene il registro dei cambiamenti più significativi del progetto.

## [v1.0.2] - Risoluzione Errori di Fetch e Connessione API

### [2024-01-19 - Fix Critico Connessione Frontend-Backend]

- **Risolto problema configurazione hostname per sviluppo locale**:
  - Corretto `next.config.js` da `carbonpilot-backend:8000` (Docker) a `localhost:8000` (locale)
  - Eliminati errori "Failed to fetch" con status 0
  - Ripristinata comunicazione corretta tra frontend e backend

- **Inizializzazione database completa**:
  - Eseguito `create_tables.py` per creare tutte le tabelle SQLAlchemy
  - Risolti errori 500 causati da database vuoto
  - Verificata presenza di tutte le tabelle necessarie

- **Migliorata gestione errori API**:
  - Aggiunto timeout di 10 secondi per le richieste Axios
  - Implementato interceptors per logging dettagliato delle richieste/risposte
  - Gestione errori specifica per ECONNREFUSED, 404, 500+
  - Rimossa dichiarazione duplicata della variabile `api`

- **Nuovo script di avvio intelligente**:
  - Creato `start_dev_fixed.bat` con controlli automatici
  - Verifica se backend/frontend sono già attivi prima dell'avvio
  - Avvio sequenziale con attesa e verifiche di stato
  - Apertura automatica del browser all'avvio completo

### Funzionalità Tecniche
- **Logging migliorato**: Console dettagliata per debug API con emoji e colori
- **Auto-refresh**: Aggiornamento automatico ogni 5 secondi per dati tools
- **Gestione focus**: Refresh automatico quando si torna alla finestra
- **Error handling**: Toast notifications per errori di rete e API

### Correzioni UX
- Eliminati errori React "Objects are not valid as a React child"
- Ripristinato caricamento corretto dei dati in tutte le sezioni
- Indicatori visivi per stato di caricamento e aggiornamento
- Messaggi di errore più chiari e informativi

### Documentazione
- Creato `docs/RISOLUZIONE_ERRORI_FETCH.md` con guida completa
- Istruzioni per troubleshooting e verifica funzionamento
- Note per configurazione Docker vs sviluppo locale

## [v1.0.1] - Fix Connessione Database e Cicli di Cura

### [2024-01-18 - Correzioni Critiche]

- **Fix Connessione Database in ambiente locale**:
  - Corretto il default hardcoded `@db:5432` in `@localhost:5432` nel file `backend/models/db.py`
  - Aggiunto caricamento automatico del file `.env` con `load_dotenv()`
  - Implementato logging della configurazione database per debug
  - Creato file `.env` con configurazione locale: `DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/carbonpilot`
  - Verificata dipendenza `python-dotenv==1.1.0` già presente nei requirements

- **Fix Bug Modifica Cicli di Cura**:
  - Corretto problema nel form di modifica dove i campi delle stasi andavano a `0`
  - Aggiunto `useEffect` per precompilare correttamente il form quando `editingItem` cambia
  - Migliorata gestione dei valori `undefined`/`null` per i campi della stasi 2
  - Corretta logica backend per gestire disattivazione della stasi 2
  - Aggiunta validazione migliorata per l'aggiornamento delle stasi

### Correzioni Tecniche
- **Backend**: Migliorata logica di update in `update_ciclo_cura()` per gestire correttamente l'attivazione/disattivazione della stasi 2
- **Frontend**: Implementato reset automatico del form con valori corretti in modalità edit
- **Database**: Configurazione locale ora caricata correttamente dal file `.env`
- **Logging**: Aggiunto logging per debug della configurazione database

### Test e Verifica
- Creato script `test_fixes.py` per verificare le correzioni
- Testata connessione database locale
- Verificato funzionamento modifica cicli di cura
- Confermato caricamento corretto variabili d'ambiente

## [v1.0.0] - Miglioramenti Form Parti e Ricerca Smart

### [2024-01-17 - Potenziamento Sezione Parti]

- **Implementata ricerca smart nei campi form parti**:
  - Debounce e filtro real-time per cicli di cura e tools
  - Evidenziazione dei match nella ricerca
  - Fallback intelligente se nessun risultato
  - Miglioramento UX con feedback visivo
- **Aggiunto sistema shortcut per creazione rapida**:
  - Shortcut "+ Nuovo Tool" direttamente dal form parte
  - Shortcut "+ Nuovo Ciclo" direttamente dal form parte  
  - Modal in-place senza perdere dati del form principale
  - Auto-selezione dell'item appena creato nel form parte
- **Rinominato campo "codice" in "Part Number Tool"**:
  - Aggiornati modelli SQLAlchemy e schemi Pydantic
  - Aggiornati form frontend e interfacce UI
  - Migrazione database per retrocompatibilità
  - Aggiornate tabelle e label in tutta l'applicazione
- **Rimosso completamente campo "in manutenzione" dai Tools**:
  - Puliti modelli e schemi backend
  - Aggiornate interfacce frontend
  - Migrazione database per rimozione campo
  - Verificata retrocompatibilità con dati esistenti

### Funzionalità Tecniche
- Implementazione debounce con hook personalizzato
- Componenti modal riutilizzabili per shortcut
- Gestione stato form complessa con context
- Migrazioni SQLAlchemy per modifiche schema
- Ricerca semantica con highlighting

### Miglioramenti UX
- Form più fluido e intuitivo per creazione parti
- Riduzione dei click necessari per creare elementi collegati
- Feedback visivo migliorato per ricerche e selezioni
- Naming più chiaro e consistente in tutta l'app

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

## [24 Maggio 2025 - Miglioramenti Sezione ODL]

### 🚀 Nuove Funzionalità

#### Pagina ODL Principale (`/dashboard/odl`)
- **Barra di Avanzamento Migliorata**: Implementata barra di progresso visuale che mostra le fasi di produzione con:
  - Icone rappresentative per ogni fase (⚙️ Preparazione, 🔨 Laminazione, ⏱️ Attesa Cura, 🔥 Cura, ✅ Finito)
  - Colori progressivi che indicano lo stato di completamento
  - Durata proporzionale di ogni segmento basata sui tempi medi di produzione
  - Indicatore di fase corrente con animazioni fluide

- **Sistema di Priorità Migliorato**: Visualizzazione priorità ODL con:
  - Indicatori grafici colorati (🔴 Alta, 🟠 Media-Alta, 🟡 Media, 🟢 Bassa)
  - Badge numerici con colori corrispondenti alla priorità
  - Logica di priorità: ≥8 (Critica), ≥5 (Alta), ≥3 (Media), <3 (Bassa)

- **Interfaccia Semplificata**: 
  - Rimosso storico ODL completati dalla pagina principale
  - Rimosso bottone di avanzamento stato (spostato in Monitoraggio)
  - Focus esclusivo su ODL attivi in produzione
  - Link diretto alla nuova pagina di Monitoraggio ODL

#### Nuova Pagina Monitoraggio ODL (`/dashboard/odl/monitoraggio`)
- **Monitoraggio in Tempo Reale**: 
  - Visualizzazione stato corrente di tutti gli ODL in produzione
  - Informazioni dettagliate sulla fase attuale con durata in tempo reale
  - Bottone "Avanza" per gestire il passaggio tra le fasi

- **Storico Completo delle Fasi**:
  - Accordion espandibile con tutti gli ODL completati
  - Timeline dettagliata di ogni fase con tempi di inizio/fine
  - Calcolo automatico della durata di ogni fase
  - Visualizzazione dello storico delle fasi per ogni ODL

- **Gestione Avanzamento Fasi**:
  - Dialog di conferma per l'avanzamento di stato
  - Integrazione automatica con il sistema `tempi_produzione`
  - Chiusura automatica della fase corrente e apertura della successiva

#### Form Modifica ODL Migliorato
- **Titolo Descrittivo**: Il titolo del modal ora mostra il nome della parte invece dell'ID ODL
- **Descrizione Dettagliata**: Sottotitolo con descrizione breve della parte
- **Precompilazione Corretta**: Tutti i campi vengono precompilati correttamente durante la modifica
- **Validazione Migliorata**: Controlli di validazione più robusti per parte e tool

### 🔧 Miglioramenti Tecnici

#### Componenti UI
- **BarraAvanzamento**: Nuovo componente React per visualizzare il progresso delle fasi
- **Gestione Stati**: Logica migliorata per la gestione degli stati ODL
- **Responsive Design**: Interfaccia ottimizzata per dispositivi mobili e desktop

#### Integrazione Backend
- **API tempoFasiApi**: Integrazione completa con il sistema di tracciamento tempi
- **Gestione Errori**: Handling robusto degli errori con messaggi informativi
- **Performance**: Caricamento ottimizzato dei dati con loading states

#### Struttura Dati
- **Configurazione Fasi**: Array strutturato con durate, colori e icone per ogni fase
- **Mapping Stati**: Mappatura corretta tra stati ODL e fasi di produzione
- **Calcolo Durate**: Funzioni utility per calcolo e formattazione durate

### 📊 Flusso di Lavoro Migliorato

1. **Visualizzazione ODL**: Pagina principale mostra solo ODL attivi con barra di avanzamento
2. **Monitoraggio Dettagliato**: Pagina dedicata per monitoraggio in tempo reale e storico
3. **Gestione Fasi**: Avanzamento controllato delle fasi con tracciamento automatico
4. **Modifica ODL**: Form migliorato con titoli descrittivi e validazione

### 🎨 Miglioramenti UX/UI

- **Colori Semantici**: Schema colori coerente per stati e priorità
- **Icone Intuitive**: Icone emoji per identificazione rapida delle fasi
- **Feedback Visivo**: Animazioni e transizioni fluide per migliorare l'esperienza
- **Navigazione Chiara**: Link e breadcrumb per navigazione intuitiva

### 🧪 Testing e Validazione

- **Dati di Test**: Popolamento automatico con dati realistici tramite `seed_test_data.py`
- **Flusso Completo**: Test di creazione, modifica, visualizzazione e avanzamento ODL
- **Integrazione**: Verifica dell'integrazione con sistema tempi di produzione

### 📝 Documentazione

- **Commenti Codice**: Documentazione inline per tutti i nuovi componenti
- **Struttura Chiara**: Organizzazione logica dei file e componenti
- **Esempi d'Uso**: Implementazione di esempi pratici per ogni funzionalità

---

## Versioni Precedenti

### [Versione Base - Sistema ODL]
- Implementazione base del sistema ODL
- CRUD operations per ordini di lavoro
- Integrazione con parti e tools
- Sistema di stati base

## [2024-01-15 - Correzioni UX e Ottimizzazioni]

### 🎨 **Interfaccia e UX**
- **Migliorata visualizzazione calendario**: Aggiunto supporto completo per modalità dark con stili CSS personalizzati
- **Nuova pagina Impostazioni**: Creata pagina dedicata con switch visibile per modalità dark/light
- **Rimozione ID dalle visualizzazioni**: Nascosti tutti gli ID da tabelle ODL, calendario e moduli per migliorare l'UX
- **Menu laterale aggiornato**: Aggiunta voce "Impostazioni" con icona appropriata

### 📋 **ODL (Ordini di Lavoro)**
- **Ordinamento cronologico**: Gli ODL sono ora ordinati dal più recente al più vecchio
- **Rimozione duplicati**: Ogni ODL viene mostrato una sola volta con stato progressivo
- **Bug fix avanzamento**: Corretto il bug del pulsante di avanzamento con refresh automatico della pagina
- **Toast migliorati**: Messaggi di successo/errore più chiari e informativi

### 🔧 **Tool/Stampi**
- **Aggiornamento automatico stato**: I Tool vengono automaticamente marcati "In Autoclave" quando usati da ODL in fase "Cura"
- **Refresh automatico**: Aggiornamento stato ogni 30 secondi nella tabella strumenti
- **Nuovo endpoint API**: `/tools/update-status-from-odl` per sincronizzazione automatica
- **Indicatori visivi**: Badge "In Autoclave" per Tool non disponibili

### 🗄️ **Database**
- **Flag configurazione**: Aggiunto flag `USE_SQLITE` per passare facilmente tra SQLite e PostgreSQL
- **Compatibilità SQLite**: Assicurata compatibilità completa con SQLite per sviluppo
- **Logging migliorato**: Messaggi più chiari sulla configurazione database attiva

### 🌙 **Modalità Dark**
- **Calendario ottimizzato**: Stili CSS personalizzati per perfetta leggibilità in dark mode
- **Modali responsive**: Tutti i modali supportano correttamente la modalità dark
- **Componenti uniformi**: Tutti i componenti UI seguono il tema selezionato

### 🔄 **Refresh e Sincronizzazione**
- **Aggiornamento automatico Tool**: Sincronizzazione stato basata su ODL attivi
- **Refresh pagina ODL**: Forzato reload dopo avanzamento per aggiornare tutte le liste
- **Cache disabilitata**: Rimozione cache API per dati sempre aggiornati

### 🎯 **Miglioramenti Tecnici**
- **Gestione errori**: Migliore handling degli errori con try/catch appropriati
- **Performance**: Ottimizzazioni per ridurre chiamate API non necessarie
- **Logging**: Messaggi di debug più informativi per troubleshooting

## [2024-01-15 - Risoluzione Bug CPX-102 e Miglioramenti Nesting]

### 🐛 **Bug Risolti**
- **CPX-102**: Risolto problema critico nell'algoritmo di posizionamento degli ODL nell'anteprima del nesting
  - **Problema**: Gli ODL si sovrapponevano nell'anteprima del layout dell'autoclave
  - **Causa**: Algoritmo di posizionamento inadeguato che non gestiva correttamente il wrapping alle righe successive
  - **Soluzione**: Implementato algoritmo bin packing avanzato con gestione intelligente delle righe multiple

### ✨ **Nuove Funzionalità**
- **Anteprima Layout Migliorata**: 
  - Algoritmo di posizionamento ottimizzato che evita sovrapposizioni
  - Colori distintivi per ogni ODL per facilità di identificazione
  - Griglia di sfondo per migliore orientamento visivo
  - Indicatori per ODL che non entrano nel layout (overflow)
  - Tooltip informativi con dettagli ODL

- **Sistema di Filtri e Ricerca Avanzato**:
  - Ricerca per ID nesting, nome autoclave, codice autoclave, part number
  - Filtro per autoclave specifica
  - Ordinamento per data creazione, utilizzo area, utilizzo valvole
  - Direzione di ordinamento (crescente/decrescente)

- **Dashboard Statistiche**:
  - Card informative con statistiche generali
  - Nesting totali generati
  - ODL processati complessivamente
  - Utilizzo medio area e valvole

- **UI/UX Migliorata**:
  - Design moderno e responsive
  - Badge colorati per indicatori di performance
  - Progress bar per visualizzazione utilizzo
  - Stati di caricamento migliorati
  - Messaggi informativi per stati vuoti

### 🔧 **Miglioramenti Tecnici**
- **Conversione Unità di Misura**: Implementato fattore di scala corretto da millimetri a pixel
- **Gestione Proporzioni**: L'anteprima mantiene le proporzioni reali dell'autoclave e dei tool
- **Performance**: Ottimizzazione del rendering dell'anteprima layout
- **Accessibilità**: Aggiunto supporto screen reader e tooltip informativi

### 📊 **Modifiche ai Modelli DB**
- Nessuna modifica ai modelli database richiesta
- Utilizzo delle strutture dati esistenti ottimizzato

### 🎨 **Effetti sulla UI**
- **Pagina Nesting**: Completamente ridisegnata con layout moderno
- **Dialog Dettagli**: Espanso con più informazioni e anteprima migliorata
- **Tabella Nesting**: Aggiunta colonne informative e azioni migliorate
- **Responsive Design**: Ottimizzato per dispositivi mobili e desktop

### 🧪 **Testing**
- ✅ Test algoritmo posizionamento ODL
- ✅ Test filtri e ricerca
- ✅ Test responsive design
- ✅ Test performance anteprima layout
- ✅ Test accessibilità

### 📝 **Note per Sviluppatori**
- Il nuovo algoritmo di posizionamento è in `calculateODLPositions()` nel componente `NestingDetails`
- I filtri utilizzano `useEffect` per aggiornamento reattivo
- Le statistiche sono calcolate in tempo reale dai dati esistenti
- Il sistema è pronto per future implementazioni di export PDF/PNG

_Il formato di questo changelog è basato su [Keep a Changelog](https://keepachangelog.com/it/1.0.0/)._ 