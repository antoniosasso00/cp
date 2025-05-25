# Changelog CarbonPilot

Questo file contiene il registro dei cambiamenti più significativi del progetto.

## [v2.0.2] - Fix Crash Select Monitoraggio ODL

### [2025-01-25 - Correzione Crash Select nel Dashboard ODL Monitoring]
- **Risolto**: Crash critico nella pagina di monitoraggio ODL causato da valori `undefined` nei componenti Select
- **Problema**: I componenti Select per filtri stato e priorità ricevevano valori `undefined` che causavano errori runtime
- **Soluzione**: Implementata gestione sicura degli stati con inizializzazione a stringa vuota e controlli preventivi
- **Impatto**: Dashboard di monitoraggio ODL ora funziona senza crash e filtri operativi

#### Dettagli Tecnici della Correzione
- **Stati iniziali corretti**: Cambiato da `useState<string | undefined>(undefined)` a `useState<string>('')`
- **Protezione valori Select**: Aggiunto `value={statusFilter || ''}` per prevenire valori undefined
- **Gestione onChange sicura**: Implementato `onValueChange={(value) => setStatusFilter(value || '')}`
- **Validazione parametri API**: Aggiornato controllo da `if (value && value !== '')` a `if (value !== '')`

#### File Modificati
- `frontend/src/components/odl-monitoring/ODLMonitoringDashboard.tsx` - Correzione principale
- `frontend/test_select_fix.md` - Documentazione test e validazione

#### Controlli Preventivi Aggiunti
- **Protezione da undefined**: Doppio controllo `|| ''` per tutti i valori Select
- **Gestione sicura onChange**: Prevenzione valori null/undefined in setState
- **Validazione fetch**: Controlli semplificati per parametri URL

#### Effetti sulla UX
- **Eliminazione crash**: Pagina di monitoraggio ODL carica senza errori
- **Filtri funzionanti**: Select "Filtra per stato" e "Priorità minima" operativi
- **Esperienza fluida**: Navigazione senza interruzioni nel sistema di monitoraggio
- **Robustezza migliorata**: Sistema più resistente a valori non validi

## [v2.0.1] - Fix Errore Componente Select Frontend

### [2025-01-25 - Risoluzione Errore Runtime Select Radix UI]
- **Risolto**: Errore runtime nel componente Select di Radix UI nel sistema di monitoraggio ODL
- **Problema**: Componente Select riceveva prop `value` con stringa vuota, violando i requisiti di Radix UI
- **Soluzione**: Implementato pattern sicuro con gestione `undefined` per valori non selezionati
- **Impatto**: Sistema di monitoraggio ODL ora funziona senza errori runtime
- **Pattern standardizzato**: Creato pattern riutilizzabile per tutti i componenti Select del progetto

#### Dettagli Tecnica della Correzione
- **State types aggiornati**: `useState<string | undefined>(undefined)` invece di `useState<string>('')`
- **Conversione sicura**: `value={statusFilter || ''}` per il rendering del componente
- **Gestione bidirezionale**: `onValueChange={(value) => setValue(value === '' ? undefined : value)}`
- **Validazione filtri**: Controlli aggiuntivi `if (value && value !== '')` per API calls

#### File Modificati
- `frontend/src/components/odl-monitoring/ODLMonitoringDashboard.tsx` - Fix principale
- `frontend/src/components/test-select.tsx` - Componente di test per validazione
- `FIX_SELECT_ERROR.md` - Documentazione dettagliata del fix

#### Effetti sulla UX
- **Eliminazione errori**: Nessun più errore runtime che bloccava il rendering
- **Filtri funzionanti**: Componenti Select per stato e priorità ora operativi
- **Esperienza fluida**: Navigazione senza interruzioni nel sistema di monitoraggio

## [v2.0.0] - Sistema Monitoraggio ODL Avanzato

### [2025-01-25 - Implementazione Completa Sistema Monitoraggio ODL]
- **Completato**: Sistema di monitoraggio avanzato per ODL con tracciabilità completa
- **Dashboard dedicata**: Interfaccia completa per monitoraggio in tempo reale degli ODL
- **Timeline eventi**: Cronologia dettagliata con visualizzazione temporale avanzata
- **Sistema di alert**: Notifiche automatiche per ODL in ritardo o bloccati
- **API complete**: Endpoint RESTful per integrazione e monitoraggio esterno
- **Test suite completa**: 5/5 test superati con validazione completa del sistema

#### Funzionalità Implementate
- **Vista dashboard avanzata**: Monitoraggio stato attuale, cicli completati, nesting associato
- **Log di avanzamento**: Timeline interattiva con eventi chiave, date/ora, responsabili
- **Statistiche in tempo reale**: Totale ODL, in ritardo, completati oggi, tempo medio
- **Filtri avanzati**: Per stato, priorità, termine di ricerca, solo attivi
- **Sistema di alert**: Automatici per ODL in ritardo (>24h) o bloccati
- **Dettaglio completo**: Vista singolo ODL con tutte le informazioni correlate

#### API Backend Implementate
- **GET `/api/v1/odl-monitoring/monitoring/stats`**: Statistiche generali sistema
- **GET `/api/v1/odl-monitoring/monitoring/`**: Lista ODL con filtri avanzati
- **GET `/api/v1/odl-monitoring/monitoring/{odl_id}`**: Dettaglio completo ODL
- **GET `/api/v1/odl-monitoring/monitoring/{odl_id}/logs`**: Log dettagliati ODL
- **GET `/api/v1/odl-monitoring/monitoring/{odl_id}/timeline`**: Timeline eventi
- **POST `/api/v1/odl-monitoring/monitoring/{odl_id}/logs`**: Creazione log manuale

#### Componenti Frontend Implementati
- **ODLMonitoringDashboard**: Dashboard principale con statistiche e filtri
- **ODLMonitoringDetail**: Vista dettaglio ODL con tabs informazioni/timeline/logs
- **ODLMonitoringList**: Lista ODL con informazioni essenziali e azioni
- **ODLMonitoringStats**: Statistiche avanzate con distribuzione per stato
- **ODLTimelineEnhanced**: Timeline eventi con icone, colori e durate
- **ODLAlertsPanel**: Pannello alert con azioni suggerite

#### Sistema di Log Avanzato
- **Eventi tracciati**: Creazione, assegnazione nesting, avvio cura, completamento
- **Informazioni dettagliate**: Timestamp, responsabile, stato precedente→nuovo
- **Correlazioni**: Nesting associato, autoclave utilizzata, ciclo di cura
- **Calcolo durate**: Tempo nello stato corrente, tempo totale produzione
- **Generazione automatica**: Log di creazione per ODL esistenti

#### Integrazione con Sistema Esistente
- **Compatibilità completa**: Nessuna nuova entità scollegata
- **Relazioni verificate**: ODL ↔ Parte ↔ Tool ↔ Nesting ↔ Autoclave
- **Modelli esistenti**: Utilizzo `descrizione_breve` per Parte, `part_number_tool` per Tool
- **Schema database**: Aggiornamento colonne mancanti in `nesting_results`

#### Performance e Robustezza
- **Tempi di risposta**: <0.15s per tutte le API principali
- **Gestione errori**: Toast notifications, fallback graceful, retry automatico
- **Scalabilità**: Ottimizzato per centinaia di ODL con paginazione
- **Validazione**: Controlli completi lato client e server

#### Test e Validazione
- **Test database**: Verifica integrità relazioni e conteggi
- **Test API**: Validazione tutti endpoint con scenari reali
- **Test performance**: Misurazione tempi di risposta sotto carico
- **Test scenari**: Filtri, priorità, stati, dati demo
- **Dati di test**: 10 ODL in stati differenti con 14+ log eventi

#### Accesso e Utilizzo
- **URL dashboard**: `http://localhost:3000/dashboard/odl/monitoring`
- **Ruoli autorizzati**: ADMIN, RESPONSABILE (configurato nel menu)
- **Navigazione**: Integrato nel menu principale sezione "Controllo"
- **API pubbliche**: Disponibili per integrazioni esterne

#### File creati/modificati:
- `backend/api/routers/odl_monitoring.py` (nuovo)
- `backend/services/odl_monitoring_service.py` (nuovo)
- `backend/schemas/odl_monitoring.py` (nuovo)
- `frontend/src/components/odl-monitoring/` (6 componenti nuovi)
- `frontend/src/app/dashboard/odl/monitoring/page.tsx` (nuovo)
- `backend/test_sistema_completo.py` (test suite completa)
- `docs/MONITORAGGIO_ODL_COMPLETATO.md` (documentazione completa)

#### Effetti sulla UI e UX
- **Tracciabilità completa**: Visibilità totale del ciclo di vita ODL
- **Identificazione rapida**: Alert automatici per situazioni critiche
- **Workflow ottimizzato**: Filtri e ricerca per gestione efficiente
- **Informazioni centralizzate**: Tutte le informazioni ODL in un'unica vista
- **Esperienza intuitiva**: Interfaccia moderna con icone, colori e feedback

## [v1.9.0] - Verifica e Ottimizzazione Sistema Nesting

### [2024-12-25 - Verifica Algoritmo Nesting e Pulizia Progetto]
- **Completato**: Verifica completa dell'algoritmo di nesting con posizionamento 2D reale
- **Pulizia progetto**: Eliminazione sistematica di file temporanei, test obsoleti e duplicati
- **Validazione frontend**: Correzione import e verifica build senza errori
- **Algoritmo consolidato**: Confermata implementazione corretta di tutti i vincoli richiesti
- **Visualizzazione migliorata**: Verificata corretta visualizzazione tool con dimensioni reali

#### Verifica Algoritmo di Nesting
- **✅ Dimensioni reali tool**: L'algoritmo considera `lunghezza_piano`, `larghezza_piano`, `altezza`, `peso`
- **✅ Superficie disponibile**: Calcolo preciso dell'area autoclave e verifica spazio disponibile
- **✅ Cicli di cura compatibili**: Raggruppamento automatico ODL per ciclo di cura identico
- **✅ Posizionamento 2D reale**: Algoritmo bin packing 2D con prevenzione sovrapposizioni
- **✅ Vincoli altezza e peso**: Parti pesanti nel piano inferiore, controllo altezza massima
- **✅ Margini di sicurezza**: 5mm di margine tra tool per evitare interferenze

#### Funzionalità Algoritmo Verificate
- **Bin Packing 2D**: Algoritmo First Fit Decreasing per ottimizzazione spazio
- **Rotazione automatica**: Tool ruotati di 90° se necessario per adattamento
- **Ordinamento per peso**: Parti più pesanti posizionate per prime (piano inferiore)
- **Verifica sovrapposizioni**: Controllo matematico rigoroso per evitare conflitti
- **Efficienza calcolo**: Statistiche area e valvole utilizzate per ogni autoclave
- **Gestione fallimenti**: ODL non posizionabili con motivazioni dettagliate

#### Visualizzazione Frontend Verificata
- **Posizioni reali dal backend**: Utilizzo coordinate calcolate dall'algoritmo
- **Scala appropriata**: Conversione mm → pixel con fattori di scala corretti
- **Fallback intelligente**: Layout a griglia se posizioni backend non disponibili
- **Zoom e navigazione**: Controlli zoom, hover details, ricerca ODL
- **Ciclo di cura visibile**: Etichetta ciclo di cura nell'anteprima autoclave
- **Legenda priorità**: Colori distintivi per priorità alta/media/bassa

#### Pulizia File Progetto
**File eliminati dalla root:**
- `test_nesting_quick.py`, `test_nesting_cicli_cura.py`, `check_nesting_states.py`
- `test_frontend_connectivity.py`, `test_nesting_complete.py`, `test_endpoints.py`
- `test_nesting_system.py`, `test_manual_nesting.py`, `check_implementation.py`
- `test_endpoint.py`, `debug_reports.py`, `test_report.json`, `test_fixes.py`

**File eliminati dal backend:**
- `quick_test_manual_nesting.py`, `debug_reports.py`, `test_integration.py`
- `debug_scheduling.py`, `test_scheduling_complete.py`, `test_nesting_status.json`
- `test_nesting_endpoint.py`

**File duplicati eliminati:**
- `frontend/src/hooks/use-debounce.ts` (mantenuto `useDebounce.ts` con documentazione)

#### Correzioni Frontend
- **Import corretti**: Aggiornato import da `use-debounce` a `useDebounce` in `odl-modal-improved.tsx`
- **Build verificata**: Frontend compila senza errori o warning
- **Bundle ottimizzato**: Dimensioni bundle appropriate per tutte le pagine
- **TypeScript valido**: Nessun errore di tipizzazione

#### Algoritmo Nesting - Dettagli Tecnici
```python
# Vincoli implementati nell'algoritmo:
- Dimensioni tool reali (mm): lunghezza_piano × larghezza_piano
- Area autoclave disponibile: lunghezza × larghezza_piano
- Cicli di cura: raggruppamento automatico per compatibilità
- Posizionamento 2D: algoritmo bin packing con margini sicurezza
- Peso tool: ordinamento decrescente per stabilità
- Altezza massima: controllo vincolo altezza_max autoclave
- Valvole: verifica num_linee_vuoto disponibili
- Sovrapposizioni: controllo matematico rigoroso
```

#### File mantenuti (importanti):
- `test_nesting_verification.py`: Script di verifica completa sistema
- Tutti i file di migrazione database attivi
- File di seed per dati di test
- Componenti frontend di visualizzazione nesting
- Algoritmo `auto_nesting.py` completo e funzionante

#### Effetti sulla UI e UX
- **Visualizzazione accurata**: Tool mostrati con dimensioni e posizioni reali
- **Ciclo di cura visibile**: Informazione ciclo sempre presente nell'interfaccia
- **Performance migliorate**: Eliminazione file inutili riduce overhead progetto
- **Build più veloce**: Meno file da processare durante compilazione
- **Debugging semplificato**: Solo file necessari per manutenzione

#### Validazione Completata
- **✅ Algoritmo nesting**: Tutti i vincoli richiesti implementati correttamente
- **✅ Visualizzazione 2D**: Rendering accurato con posizioni reali
- **✅ Cicli di cura**: Gestione e visualizzazione corretta
- **✅ Prevenzione sovrapposizioni**: Controlli matematici rigorosi
- **✅ Frontend build**: Compilazione senza errori
- **✅ Pulizia progetto**: File superflui eliminati sistematicamente

## [v1.8.0] - Dashboard Nesting con Gestione Stati Avanzata

### [2024-12-25 - Componente Dashboard per Visualizzazione e Gestione Stati Nesting]
- **Completato**: Nuovo componente `NestingStatusCard` per visualizzazione panoramica nesting nelle dashboard
- **Integrazione dashboard**: Aggiunto componente nelle dashboard AUTOCLAVISTA e RESPONSABILE
- **Gestione stati avanzata**: Visualizzazione nesting raggruppati per stato con statistiche in tempo reale
- **Controllo ruoli specifico**: Interfaccia personalizzata per AUTOCLAVISTA (focus su conferme) e RESPONSABILE (gestione completa)
- **Azioni contestuali**: Pulsanti di azione specifici per ruolo con navigazione diretta alle funzionalità
- **Aggiornamento automatico**: Refresh automatico dei dati con gestione errori robusta

#### Funzionalità Implementate
- **Statistiche visuali**: Contatori colorati per ogni stato nesting (In sospeso, Confermato, Completato, Annullato)
- **Lista prioritaria**: Visualizzazione nesting in attesa di conferma per AUTOCLAVISTA
- **Lista recenti**: Panoramica nesting recenti per RESPONSABILE con tutti gli stati
- **Badge informativi**: Indicatori stato con ruolo di conferma e percentuale utilizzo area
- **Navigazione diretta**: Link alle pagine di gestione nesting con parametri specifici
- **Gestione errori**: Feedback visivo per errori di connessione con possibilità di retry

#### Personalizzazione per Ruolo
- **AUTOCLAVISTA**: Focus su nesting "In sospeso" che richiedono conferma di carico
- **RESPONSABILE**: Panoramica completa con accesso a tutte le funzionalità di gestione
- **Altri ruoli**: Visualizzazione generale dello stato dei nesting di produzione

#### Backend Integration
- **Endpoint esistente**: Utilizza `/api/v1/nesting/` con filtro per ruolo utente
- **Filtro automatico**: L'autoclavista vede solo nesting in sospeso, il responsabile vede tutto
- **Dati in tempo reale**: Aggiornamento automatico con refresh manuale disponibile

#### Frontend (Next.js + TypeScript + React)
- **Componente `NestingStatusCard`**: Gestione completa stati UI e interazioni per ruolo
- **Hook integration**: Integrazione con `useUserRole()` per personalizzazione interfaccia
- **API client**: Riutilizzo `nestingApi.getAll()` esistente con parametri ruolo
- **UI responsive**: Design adattivo per desktop, tablet e mobile
- **Feedback utente**: Loading states, error handling, empty states con azioni suggerite

#### File creati/modificati:
- `frontend/src/components/dashboard/NestingStatusCard.tsx` (nuovo)
- `frontend/src/components/dashboard/DashboardAutoclavista.tsx` (aggiornato)
- `frontend/src/components/dashboard/DashboardResponsabile.tsx` (aggiornato)
- `docs/changelog.md` (documentazione aggiornamenti)

#### Effetti sulla UI e UX
- Dashboard più informative con visibilità immediata stato nesting
- Workflow ottimizzato per identificare rapidamente azioni richieste per ruolo
- Riduzione tempo di navigazione con accesso diretto alle funzionalità pertinenti
- Esperienza utente personalizzata in base alle responsabilità del ruolo
- Integrazione seamless con sistema nesting esistente senza duplicazione codice

## [v1.7.0] - Interfaccia Avanzata per Nesting Manuale

### [2024-12-25 - Interfaccia Completa per Selezione ODL e Gestione Errori Avanzata]
- **Completato**: Interfaccia completa per la selezione degli ODL per nesting manuale con gestione errori robusta
- **Debug avanzato**: Sistema di logging dettagliato con cronologia errori e modalità debug
- **Validazione lato client**: Controlli avanzati per ODL selezionati con feedback in tempo reale
- **Gestione errori API**: Intercettazione e gestione dettagliata di errori 422, 400, 500 con suggerimenti specifici
- **UI migliorata**: Interfaccia responsiva con indicatori di stato, filtri avanzati e feedback visivo
- **Script di test**: Nuovo script per creare dati di test per ODL in attesa di nesting

#### Funzionalità Implementate
- **Selezione ODL multipla**: Tabella con checkbox per selezione singola o multipla di ODL
- **Filtri avanzati**: Ricerca per ID, Part Number, descrizione e filtro per priorità
- **Validazione robusta**: Controlli lato client per ODL validi, limiti di selezione, stato corretto
- **Gestione errori dettagliata**: Intercettazione errori API con messaggi specifici e suggerimenti
- **Modalità debug**: Pannello debug con cronologia errori, statistiche e dettagli richieste
- **Feedback visivo**: Indicatori di stato, colori distintivi, badge di priorità, alert informativi

#### Sistema di Gestione Errori
- **Errori 422 (Validazione)**: Messaggi specifici con suggerimenti per risoluzione
- **Errori 400 (Business Logic)**: Gestione errori di logica aziendale con spiegazioni
- **Errori 500 (Server)**: Gestione errori server con indicazioni per debug
- **Errori di connessione**: Rilevamento problemi di rete con istruzioni per risoluzione
- **Cronologia errori**: Memorizzazione ultimi 10 errori con timestamp e dettagli completi

#### Validazione Lato Client Avanzata
- **Controllo selezione**: Almeno 1 ODL, massimo 50 ODL selezionabili
- **Verifica stato**: Solo ODL in stato "Attesa Cura" selezionabili
- **Controllo disponibilità**: Verifica che ODL selezionati esistano ancora
- **Limite valvole**: Avviso per selezioni con troppe valvole richieste (>100)
- **Feedback in tempo reale**: Aggiornamento validazione ad ogni cambio selezione

#### Interfaccia Utente Migliorata
- **Tabella responsiva**: Visualizzazione ottimizzata per desktop, tablet e mobile
- **Indicatori visivi**: Righe evidenziate per ODL selezionati, opacità per ODL non validi
- **Badge priorità**: Colori distintivi per priorità alta (P3+) e bassa (P1-2)
- **Statistiche selezione**: Conteggio ODL selezionati e totale valvole richieste
- **Modalità debug**: Pannello collassabile con informazioni tecniche dettagliate

#### Backend (FastAPI + SQLAlchemy)
- **Endpoint robusto**: `/nesting/manual` con validazione completa e gestione errori
- **Validazione server**: Controllo stato ODL, disponibilità, limiti di sistema
- **Logging dettagliato**: Tracciamento operazioni per debugging e monitoraggio
- **Messaggi di errore specifici**: Errori dettagliati con codici HTTP appropriati

#### Frontend (Next.js + TypeScript + React)
- **Componente `ManualNestingSelector`**: Gestione completa selezione ODL e creazione nesting
- **Hook personalizzati**: Gestione stato asincrono con `useState` e `useEffect`
- **API integration**: Metodi `odlApi.getPendingNesting()` e `nestingApi.generateManual()`
- **UI responsive**: Design adattivo con componenti shadcn/ui
- **TypeScript completo**: Tipizzazione forte per tutte le interfacce e stati

#### Script di Test e Debugging
- **Script `seed_test_data_simple.py`**: Creazione automatica ODL di test per nesting
- **Verifica prerequisiti**: Controllo backend, parti, tool necessari per test
- **Setup automatico**: Creazione 5 ODL di test con priorità diverse
- **Validazione finale**: Verifica che tutto sia pronto per test interfaccia

#### File creati/modificati:
- `frontend/src/app/dashboard/nesting/components/manual-nesting-selector.tsx` (migliorato)
- `backend/seed_test_data_simple.py` (nuovo)
- `backend/api/routers/nesting.py` (endpoint `/manual` già esistente)
- `backend/services/nesting_service.py` (funzione `run_manual_nesting` già esistente)
- `docs/changelog.md` (documentazione aggiornamenti)

#### Effetti sulla UI e UX
- Interfaccia intuitiva per selezione ODL con feedback immediato
- Gestione errori trasparente con messaggi comprensibili e azioni suggerite
- Workflow ottimizzato per creazione nesting manuale con validazione preventiva
- Modalità debug per sviluppatori con informazioni tecniche dettagliate
- Esperienza utente fluida con loading states e transizioni animate
- Riduzione errori utente grazie a validazione in tempo reale

#### Test e Validazione
- **Test manuali**: Selezione ODL validi e non validi, gestione errori API
- **Test di connessione**: Simulazione errori di rete e server non disponibile
- **Test di validazione**: Verifica limiti selezione e controlli stato ODL
- **Test UI responsiva**: Verifica funzionamento su desktop, tablet e mobile
- **Test modalità debug**: Verifica logging errori e visualizzazione dettagli tecnici

## [v1.6.0] - Dashboard Responsabile con ODL in Attesa Nesting

### [2024-12-25 - Visualizzazione ODL in Attesa di Nesting per Responsabile]
- **Completato**: Aggiornamento dashboard RESPONSABILE per mostrare ODL in attesa di nesting
- **Nuovo endpoint API**: `/odl/pending-nesting` per recuperare ODL pronti per il nesting
- **Componente dedicato**: `ODLPendingNestingCard` con gestione stati (loading, errore, vuoto)
- **Integrazione dashboard**: Nuovo pannello nella sidebar della dashboard RESPONSABILE
- **Metriche aggiornate**: Aggiunta metrica "In Attesa Nesting" con conteggio dinamico
- **Logica filtro**: Utilizza la logica esistente `get_odl_attesa_cura_filtered()` per determinare ODL validi

#### Funzionalità Implementate
- **Visualizzazione ODL**: Lista degli ODL in stato "Attesa Cura" non ancora assegnati a nesting
- **Informazioni dettagliate**: Codice ODL, parte associata, tool, priorità, data creazione
- **Stati interfaccia**: Loading spinner, gestione errori, messaggio fallback per lista vuota
- **Refresh manuale**: Pulsante per aggiornare i dati in tempo reale
- **Navigazione diretta**: Link alla sezione nesting per gestione completa
- **Conteggio dinamico**: Metrica nella dashboard che mostra il numero di ODL in attesa

#### Criteri ODL "Pronto per Nesting"
- Stato ODL: "Attesa Cura"
- Non già incluso in nesting attivo (stati: "In attesa schedulazione", "Schedulato", "In corso")
- Parte con catalogo associato e area_cm2 valida
- Numero valvole richieste definito e maggiore di 0
- Tutti i dati necessari per l'algoritmo di ottimizzazione presenti

#### Backend (FastAPI + SQLAlchemy)
- **Nuovo endpoint**: `GET /api/v1/odl/pending-nesting` con logica di filtro avanzata
- **Riutilizzo servizi**: Integrazione con `nesting_service.get_odl_attesa_cura_filtered()`
- **Validazione completa**: Controllo integrità dati e compatibilità nesting
- **Logging**: Tracciamento operazioni per debugging e monitoraggio

#### Frontend (Next.js + TypeScript + React)
- **Componente `ODLPendingNestingCard`**: Gestione completa stati UI e interazioni
- **Hook personalizzati**: `useState` e `useEffect` per gestione stato asincrono
- **API integration**: Nuovo metodo `odlApi.getPendingNesting()` nel client API
- **UI responsive**: Design adattivo per desktop, tablet e mobile
- **Feedback utente**: Loading states, error handling, empty states

#### File creati/modificati:
- `backend/api/routers/odl.py` (aggiunto endpoint `/pending-nesting`)
- `frontend/src/lib/api.ts` (aggiunto metodo `getPendingNesting`)
- `frontend/src/components/dashboard/DashboardResponsabile.tsx` (aggiornato con nuovo componente)
- `docs/changelog.md` (documentazione aggiornamenti)

#### Effetti sulla UI e UX
- Dashboard RESPONSABILE più informativa con visibilità immediata ODL in attesa
- Workflow ottimizzato per identificare rapidamente ODL pronti per nesting
- Riduzione tempo di identificazione ODL da processare
- Integrazione seamless con sistema nesting esistente
- Esperienza utente migliorata con feedback visivo e navigazione diretta

## [v1.5.0] - Dashboard Dinamica per Ruoli

### [2024-12-25 - Implementazione Dashboard Dinamica Basata su Ruoli]
- **Completato**: Sistema di dashboard dinamica che carica automaticamente l'interfaccia appropriata in base al ruolo utente
- **Caricamento dinamico**: Implementato lazy loading con `dynamic()` di Next.js per ottimizzare le performance
- **4 Dashboard specializzate**: Componenti dedicati per ogni ruolo con funzionalità specifiche
- **Bundle optimization**: Ogni dashboard è un chunk separato, caricato solo quando necessario
- **Reindirizzamento automatico**: Gestione automatica di ruoli mancanti o invalidi con redirect a `/select-role`

#### Dashboard Implementate
1. **Dashboard Admin**: Gestione utenti, configurazioni sistema, monitoraggio completo, database management, reports avanzati, audit & logs
2. **Dashboard Responsabile**: Gestione ODL, pianificazione produzione, supervisione team, controllo qualità, alert in tempo reale
3. **Dashboard Laminatore**: Gestione parti, operazioni laminazione, controllo qualità, ODL attivi con progress bar, registrazione tempi
4. **Dashboard Autoclavista**: Gestione autoclavi, cicli di cura, nesting & scheduling, monitoraggio processi in tempo reale

#### Funzionalità Tecniche
- **Lazy Loading**: Componenti caricati dinamicamente solo quando necessari
- **Code Splitting**: Ogni dashboard è un bundle separato per performance ottimali
- **SSR Disabled**: Evita problemi di idratazione con localStorage
- **Loading States**: Feedback visivo durante il caricamento dei componenti
- **Error Handling**: Gestione robusta di errori e ruoli non validi

#### Metriche e Visualizzazioni per Ruolo
- **Admin**: Utenti attivi, sistema uptime, ODL totali, performance generale
- **Responsabile**: ODL attivi, efficienza media, ritardi, completamenti giornalieri, alert sistema
- **Laminatore**: ODL in lavorazione, efficienza turno, tempo medio ciclo, controlli QC
- **Autoclavista**: Autoclavi attive, efficienza media, cicli completati, stato temperatura/pressione

#### Architettura e Performance
- **Router Intelligente**: `/dashboard/page.tsx` come router che determina quale componente caricare
- **Hook Integration**: Integrazione completa con `useUserRole()` per gestione stato
- **Responsive Design**: Tutte le dashboard ottimizzate per desktop, tablet e mobile
- **Transizioni Fluide**: Cambio dashboard automatico al cambio ruolo senza reload

#### File creati/modificati:
- `frontend/src/app/dashboard/page.tsx` (completamente riscritto)
- `frontend/src/components/dashboard/DashboardAdmin.tsx` (nuovo)
- `frontend/src/components/dashboard/DashboardResponsabile.tsx` (nuovo)
- `frontend/src/components/dashboard/DashboardLaminatore.tsx` (nuovo)
- `frontend/src/components/dashboard/DashboardAutoclavista.tsx` (nuovo)
- `docs/dashboard-dinamica.md` (documentazione completa)

#### Effetti sulla UI e UX
- Interfaccia personalizzata e ottimizzata per ogni ruolo specifico
- Caricamento più veloce grazie al code splitting
- Esperienza utente fluida con transizioni automatiche
- Informazioni e azioni rilevanti per ogni tipo di utente
- Riduzione cognitive load mostrando solo funzionalità pertinenti

## [v1.4.0] - Sistema di Gestione Ruoli Utente

### [2024-12-15 - Implementazione Sistema Ruoli e Autenticazione]
- **Completato**: Sistema completo di gestione ruoli utente con controllo accessi
- **Pagina selezione ruolo**: Nuova interfaccia `/select-role` con design moderno e cards interattive
- **Hook personalizzato**: `useUserRole()` per gestione stato ruolo con localStorage e React state
- **Sidebar dinamica**: Filtro automatico delle voci menu in base al ruolo selezionato
- **Protezione route**: Componente `RoleGuard` per redirect automatico se ruolo non impostato
- **Indicatore ruolo**: Badge nell'header che mostra il ruolo corrente
- **Cambio ruolo**: Pulsante debug per cambio ruolo (solo in sviluppo)

#### Ruoli Implementati
1. **ADMIN**: Accesso completo a tutte le funzionalità del sistema
2. **RESPONSABILE**: Supervisione produzione, reports, statistiche
3. **LAMINATORE**: Gestione parti, catalogo, ODL, produzione
4. **AUTOCLAVISTA**: Gestione autoclavi, nesting, scheduling, cicli cura

#### Frontend (Next.js + TypeScript + Tailwind)
- **Hook `useUserRole`**: Gestione ruolo con localStorage, state React, funzioni helper
- **Pagina `/select-role`**: Interfaccia moderna con cards animate, icone distintive, descrizioni dettagliate
- **Componente `RoleGuard`**: Protezione route con redirect automatico e loading states
- **Layout dashboard**: Sidebar dinamica con filtro ruoli, indicatore ruolo corrente
- **Tipizzazione TypeScript**: Type `UserRole` per type safety completa

#### Funzionalità Implementate
1. **Selezione Ruolo**: Interfaccia intuitiva con cards colorate e animazioni hover
2. **Persistenza**: Salvataggio ruolo in localStorage con sincronizzazione React state
3. **Protezione Route**: Redirect automatico a `/select-role` se ruolo non impostato
4. **Sidebar Dinamica**: Filtro automatico voci menu in base ai permessi ruolo
5. **Indicatore Visivo**: Badge nell'header con ruolo corrente e icona
6. **Debug Mode**: Pulsante cambio ruolo visibile solo in sviluppo

#### Controllo Accessi per Ruolo
- **Produzione**: Dashboard (tutti), Catalogo/Parti/ODL/Tools/Produzione (Admin/Responsabile/Laminatore)
- **Autoclave**: Nesting/Autoclavi/Cicli/Scheduling (Admin/Responsabile/Autoclavista)
- **Controllo**: Reports/Statistiche (Admin/Responsabile), Impostazioni (solo Admin)

#### File creati/modificati:
- `frontend/src/hooks/useUserRole.ts` (nuovo)
- `frontend/src/app/select-role/page.tsx` (nuovo)
- `frontend/src/components/RoleGuard.tsx` (nuovo)
- `frontend/src/app/layout.tsx` (aggiornato)
- `frontend/src/app/dashboard/layout.tsx` (aggiornato)
- `frontend/src/app/page.tsx` (aggiornato)

#### Effetti sulla UI
- Interfaccia personalizzata in base al ruolo utente
- Navigazione semplificata con solo le funzioni accessibili
- Workflow di onboarding con selezione ruolo obbligatoria
- Feedback visivo del ruolo corrente nell'interfaccia
- Possibilità di cambio ruolo per testing e sviluppo

## [v1.3.0] - Sistema di Scheduling Completo

### [2024-12-15 - Implementazione Sistema Scheduling Avanzato]
- **Completato**: Sistema di scheduling completo per autoclavate con tutte le funzionalità richieste
- **Form semplificato**: Nuovo componente `ScheduleForm.tsx` con calcolo automatico tempi di fine
- **Calendario avanzato**: Aggiornato `CalendarSchedule.tsx` con supporto completo per nuovi tipi e stati
- **Schedulazioni ricorrenti**: Nuovo componente `RecurringScheduleForm.tsx` per frequenze produttive
- **Azioni operatore**: Sistema completo per avvio, posticipo e completamento schedulazioni
- **Gestione priorità**: Visualizzazione e gestione priorità ODL con colori e badge distintivi
- **Associazione automatica ODL**: Algoritmo per assegnazione automatica ODL compatibili
- **Tempi di produzione**: Nuova tabella `tempi_produzione` per calcoli automatici durata

#### Backend (FastAPI + SQLAlchemy)
- **Modello esteso**: `ScheduleEntry` con nuovi campi per tipo, categoria, ricorrenza, durata stimata
- **Nuovo modello**: `TempoProduzione` per gestione tempi storici di produzione
- **API estese**: Nuovi endpoint per schedulazioni ricorrenti, azioni operatore, tempi produzione
- **Servizi avanzati**: `schedule_service.py` con logica business completa
- **Schema database**: Aggiornamento SQLite con nuove colonne e tabelle

#### Frontend (Next.js + TypeScript + Tailwind)
- **Tipi aggiornati**: Enum `ScheduleEntryType` e `ScheduleEntryStatus` estesi
- **Componenti modulari**: Form separati per diversi tipi di schedulazione
- **UI/UX migliorata**: Tooltip interattivi, colori distintivi, modalità dark completa
- **API client**: `scheduleApi` esteso con tutti i nuovi endpoint

#### Funzionalità Implementate
1. **Form Semplificato**: Data/ora inizio, selezione autoclave, categoria/sotto-categoria, calcolo automatico fine
2. **Visualizzazione Calendario**: Eventi con stati, tooltip, preview nesting, modalità dark
3. **Schedulazione Automatica**: Configurazione frequenza, distribuzione eventi mensili
4. **Associazione ODL**: Ricerca automatica ODL compatibili con priorità
5. **Gestione Priorità**: Colori diversi, badge numerici, ordinamento automatico
6. **Conferma Operatore**: Azioni avvia/posticipa/completa con feedback toast

#### Database Schema Updates
- **Nuove colonne `schedule_entries`**: `schedule_type`, `categoria`, `sotto_categoria`, `is_recurring`, `pieces_per_month`, `note`, `estimated_duration_minutes`
- **Nuova tabella `tempi_produzione`**: Gestione tempi storici con statistiche
- **Indici ottimizzati**: Per query veloci su categorie e tipi

#### UI/UX Features
- **Colori distintivi**: Blu (ODL), Viola (categoria), Ciano (sotto-categoria), Verde (ricorrente), Rosso (priorità alta)
- **Badge emoji**: 🔥 priorità alta, 📋 previsionale, ⏳ in attesa, 🔄 in corso, ⏸️ posticipato
- **Modalità dark**: Supporto completo con stili personalizzati per react-big-calendar
- **Tooltip interattivi**: Dettagli completi con azioni disponibili

#### File modificati/creati:
- `backend/models/schedule_entry.py` (esteso)
- `backend/models/tempo_produzione.py` (nuovo)
- `backend/services/schedule_service.py` (esteso)
- `backend/api/routers/schedule.py` (esteso)
- `backend/update_schedule_schema_sqlite.py` (nuovo)
- `frontend/src/components/ScheduleForm.tsx` (nuovo)
- `frontend/src/components/RecurringScheduleForm.tsx` (nuovo)
- `frontend/src/components/CalendarSchedule.tsx` (aggiornato)
- `frontend/src/lib/types/schedule.ts` (esteso)
- `frontend/src/lib/api.ts` (esteso)
- `frontend/src/app/dashboard/schedule/page.tsx` (aggiornato)

#### Effetti sulla UI
- Calendario scheduling completamente funzionale con tutte le funzionalità richieste
- Interfaccia intuitiva per creazione e gestione schedulazioni
- Workflow operatore completo per gestione flusso produttivo
- Integrazione seamless con sistema ODL e nesting esistente

## [v1.2.0] - Completamento Roadmap Nesting Avanzato

### [2024-01-15 - Punto 5: Fix Nesting]
- **Completato**: Correzione e miglioramento dell'algoritmo di nesting automatico
- **Validazione ODL migliorata**: Nuova funzione `validate_odl_for_nesting()` per controlli completi
- **Filtri ODL "Attesa Cura"**: Implementata funzione `get_odl_attesa_cura_filtered()` per filtrare ODL validi
- **Salvataggio temporaneo**: Nuove funzioni `save_nesting_draft()` e `load_nesting_draft()` per bozze
- **Gestione errori robusta**: Migliorata gestione errori nell'algoritmo di ottimizzazione
- **API endpoints**: Nuovi endpoint `/nesting/draft/save`, `/nesting/draft/{id}`, `/nesting/drafts`
- **File modificati**:
  - `backend/nesting_optimizer/auto_nesting.py` (aggiornato)
  - `backend/services/nesting_service.py` (aggiornato)
  - `backend/api/routers/nesting.py` (aggiornato)
  - `frontend/src/lib/api.ts` (aggiornato)
- **Effetti sulla UI**: Nesting più affidabile, possibilità di salvare configurazioni temporanee

### [2024-01-15 - Punto 6: Preview e Manipolazione Nesting]
- **Completato**: Interfaccia interattiva per preview e manipolazione manuale del nesting
- **Preview interattiva**: Nuovo componente `NestingPreviewModal` con drag & drop
- **Manipolazione manuale**: Possibilità di spostare ODL tra autoclavi tramite drag & drop
- **Esclusione/Inclusione ODL**: Funzionalità per escludere/includere ODL manualmente
- **Salvataggio modifiche**: Salvataggio automatico delle modifiche come bozza
- **Approvazione nesting**: Workflow di approvazione prima della generazione finale
- **Statistiche real-time**: Aggiornamento automatico delle statistiche di utilizzo
- **File modificati**:
  - `frontend/src/app/dashboard/nesting/components/nesting-preview-modal.tsx` (nuovo)
  - `frontend/src/app/dashboard/nesting/page.tsx` (aggiornato)
- **Dipendenze aggiunte**: `react-beautiful-dnd` per drag & drop
- **Effetti sulla UI**: Controllo completo sul nesting, interfaccia intuitiva e visuale

### [2024-01-15 - Punto 7: Gestione ODL Esclusi]
- **Completato**: Sistema completo per gestire ODL esclusi dal nesting
- **Visualizzazione separata**: Nuovo componente `ExcludedODLManager` per ODL esclusi
- **Filtri avanzati**: Ricerca e filtri per status, priorità e motivo di esclusione
- **Reintegrazione ODL**: Possibilità di reintegrare ODL nel prossimo nesting
- **Forzatura nuovo nesting**: Opzione per forzare generazione di nuovo nesting con ODL selezionati
- **Selezione multipla**: Gestione di selezione multipla per operazioni batch
- **Statistiche dettagliate**: Contatori e informazioni sui motivi di esclusione
- **File modificati**:
  - `frontend/src/app/dashboard/nesting/components/excluded-odl-manager.tsx` (nuovo)
  - `frontend/src/app/dashboard/nesting/page.tsx` (aggiornato)
- **Effetti sulla UI**: Gestione completa degli ODL esclusi, possibilità di riutilizzo

### [2024-01-15 - Roadmap Completata]
- **Tutti i 7 punti implementati**: 
  1. ✅ Merge pagine produzione (unificazione monitoraggio)
  2. ✅ ODL + Tool (gestione coda automatica)
  3. ✅ Sidebar riorganizzata (gruppi logici)
  4. ✅ Bug Form ODL + Shortcut (ricerca dinamica e creazione rapida)
  5. ✅ Fix Nesting (correzione algoritmo e salvataggio temporaneo)
  6. ✅ Preview e Manipolazione Nesting (interfaccia interattiva drag & drop)
  7. ✅ Gestione ODL Esclusi (visualizzazione separata e riutilizzo)
- **Miglioramenti architetturali**: Servizi backend ottimizzati, componenti frontend modulari
- **UX migliorata**: Interfacce intuitive, feedback visivo, operazioni drag & drop
- **Robustezza**: Gestione errori completa, validazioni, salvataggio automatico
- **Performance**: Debounce, lazy loading, ottimizzazioni query database

## [v1.1.0] - Miglioramenti Interfaccia e Gestione ODL

### [2024-01-20 - Unificazione Pagine e Miglioramenti UX]

- **Componente Anteprima Nesting Interattivo Completato**:
  - Implementato hover interattivo sugli ODL nell'anteprima layout
  - Pannello informativo dinamico che mostra dettagli ODL al passaggio del mouse
  - Effetti visivi migliorati: scale hover, ring di selezione, transizioni smooth
  - Visualizzazione dettagliata: Part Number, descrizione, tool, dimensioni, valvole, priorità
  - Codifica colori distintiva per ogni ODL con legenda integrata
  - Algoritmo di posizionamento ottimizzato per massimizzare l'utilizzo spazio
  - Indicatori per ODL non posizionati (overflow) con conteggio visivo

- **Unificazione pagine Monitoraggio ODL + Tempi Produzione**:
  - Creata nuova pagina unificata `/dashboard/produzione`
  - Sezione 1: Stato avanzamento ODL attivi con barre visuali
  - Sezione 2: Tempi registrati completi e modificabili
  - Sezione 3: Storico ODL completati
  - Eliminazione duplicati e miglioramento UX

- **Nuovo stato ODL "In Coda"**:
  - Aggiunto stato "In Coda" quando tutti i Tool associati a una Parte sono occupati
  - Logica automatica per mettere ODL in coda e riattivazione quando tool disponibili
  - Visualizzazione motivo blocco nella pagina produzione
  - Aggiornamento modelli backend e frontend

- **Sidebar riorganizzata**:
  - Eliminato scroll verticale
  - Organizzazione in gruppi logici:
    - Sezione "Produzione": Dashboard, Catalogo, Parti, ODL, Produzione
    - Sezione "Autoclave": Nesting, Autoclavi, Scheduling
    - Sezione "Controllo": Reports, Statistiche, Impostazioni
  - Miglioramento navigazione e UX

- **Miglioramenti Form ODL**:
  - Campo "Parte" con ricerca dinamica e debounce
  - Shortcut "+ Crea Parte" con modal embedded
  - Selezione automatica parte creata
  - Validazione robusta e gestione errori

- **Fix e miglioramenti Nesting**:
  - Correzione errori generazione nesting automatico
  - Filtro corretto per ODL in "Attesa Cura"
  - Verifica disponibilità autoclave
  - Implementazione salvataggio temporaneo

- **Preview e manipolazione Nesting interattiva**:
  - Schermata preview con layout nesting per tutte le autoclavi
  - Possibilità di spostare ODL manualmente tra autoclavi
  - Forzatura inserimento ODL specifici
  - Esclusione manuale ODL
  - Approvazione/rifiuto nesting con gestione stati ODL

- **Gestione ODL esclusi**:
  - Visualizzazione separata ODL esclusi per area o valvole
  - Non salvataggio nel nesting finale
  - Riutilizzo successivo degli ODL esclusi

### Funzionalità Tecniche
- Aggiornamento modelli SQLAlchemy per nuovo stato ODL
- Nuove API per gestione stati e disponibilità tool
- Componenti React riutilizzabili per preview nesting
- Logica di ottimizzazione migliorata con gestione esclusioni
- Sistema di notifiche per feedback utente

### Miglioramenti UX
- Interfaccia più intuitiva e organizzata
- Feedback visivo migliorato per stati ODL
- Navigazione semplificata con sidebar raggruppata
- Preview interattiva per controllo completo nesting
- Gestione errori più robusta

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