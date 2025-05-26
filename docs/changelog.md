# Changelog Manta Group

Questo file contiene il registro dei cambiamenti più significativi del progetto.

## [v2.3.1] - Fix Definitivo Errore Select Components

### [2025-01-15 - Risoluzione Completa Errore Radix UI Select]
- **Problema risolto**: Errore "A <Select.Item /> must have a value prop that is not an empty string" nelle dashboard admin e responsabile
- **Causa identificata**: I componenti Radix UI Select non accettano valori vuoti (`""`) per le SelectItem
- **Soluzione implementata**:
  - Sostituito `value=""` con `value="all"` in tutti i SelectItem di filtro "Tutti"
  - Aggiornata la logica `onValueChange` per convertire `"all"` in stringa vuota internamente
  - Pattern standardizzato: `value={filter || 'all'}` e `onValueChange={(value) => setFilter(value === 'all' ? '' : value)}`
- **File modificati**:
  - `frontend/src/components/dashboard/ODLHistoryTable.tsx` - Fix filtro stato ODL
  - `frontend/src/app/dashboard/admin/logs/page.tsx` - Fix filtri tipo evento, ruolo e livello
  - `frontend/src/app/dashboard/responsabile/logs/page.tsx` - Fix filtri tipo evento, ruolo e livello
- **Effetti**: Eliminazione completa degli errori runtime nelle dashboard, miglioramento della stabilità dell'applicazione
- **Riferimento**: Soluzione basata su [Radix UI GitHub Issue #1569](https://github.com/radix-ui/primitives/issues/1569) e [Code with Mosh Forum](https://forum.codewithmosh.com/t/a-select-item-must-have-a-value-prop-that-is-not-an-empty-string-this-is-because-the-select-value-can-be-set-to-an-empty-string-to-clear-the-selection-and-show-the-placeholder/23078/7)

## [v2.3.0] - Fix Dashboard e Implementazione Dati Reali per Tutti i Ruoli

### [2025-01-28 - Correzione Crash Select e Dashboard Operative con Dati Reali]
- **Completato**: Risoluzione crash Select.Item nelle dashboard admin/responsabile
- **Dashboard Laminatore**: Eliminazione mockup, implementazione dati reali con ODL filtrati per ruolo
- **Dashboard Autoclavista**: Eliminazione mockup, implementazione dati reali con nesting confermati
- **Hook Specializzato**: Nuovo hook `useODLByRole` per gestione ODL filtrati per ruolo specifico
- **Funzionalità Operative**: Pulsanti funzionali per cambio stato ODL con feedback real-time

#### Fix Crash Select Component
- **Problema risolto**: Select.Item riceveva valori `undefined` causando crash applicazione
- **File corretto**: `frontend/src/components/dashboard/ODLHistoryTable.tsx`
- **Modifiche implementate**:
  - Inizializzazione sicura valori Select con fallback a stringa vuota
  - Controlli di sicurezza per `statusFilter` e `dateRange` non undefined
  - Validazione dati ODL prima del rendering con filtro `odl?.id`
  - Gestione graceful di campi mancanti con operatore optional chaining
  - Fallback per dati mancanti (es. 'N/A', 'Data non disponibile')

#### Hook useODLByRole Implementato
- **File**: `frontend/src/hooks/useODLByRole.ts`
- **Funzionalità**:
  - Filtro automatico ODL per ruolo: LAMINATORE (Preparazione, Laminazione), AUTOCLAVISTA (Attesa Cura, Cura)
  - Ordinamento per priorità e data di creazione
  - Refresh automatico configurabile (default 30 secondi)
  - Metodi specifici per cambio stato: `updateStatusLaminatore`, `updateStatusAutoclavista`
  - Gestione errori con messaggi specifici per ruolo
  - Aggiornamento locale lista dopo cambio stato con rimozione ODL non più rilevanti

#### Dashboard Laminatore Rinnovata
- **File**: `frontend/src/components/dashboard/DashboardLaminatore.tsx`
- **Eliminato**: Tutti i dati mockup hardcoded (activeODLs, operativeMetrics, laminatoreSections)
- **Implementato**:
  - ODL reali filtrati per stati "Preparazione" e "Laminazione"
  - Metriche operative calcolate dinamicamente dai dati reali
  - Pulsanti funzionali: "Avvia Laminazione" (Preparazione → Laminazione), "Completa Laminazione" (Laminazione → Attesa Cura)
  - Loading states con spinner e skeleton
  - Gestione errori con possibilità di retry
  - Informazioni turno con KPI reali
  - Azioni rapide con link alle pagine esistenti

#### Dashboard Autoclavista Rinnovata
- **File**: `frontend/src/components/dashboard/DashboardAutoclavista.tsx`
- **Eliminato**: Tutti i dati mockup (autoclavistaSections, autoclaviStatus, scheduledCycles)
- **Implementato**:
  - ODL reali filtrati per stati "Attesa Cura" e "Cura"
  - Nesting confermati caricabili da API reale
  - Pulsanti funzionali: "Avvia Cura" (Attesa Cura → Cura), "Completa Cura" (Cura → Finito)
  - Sezione nesting confermati con possibilità di caricamento in autoclave
  - Metriche operative reali: ODL per stato, nesting disponibili, utilizzo autoclavi
  - Informazioni turno e stato sistema con dati KPI reali

#### Funzionalità Operative Implementate
- **Cambio Stato ODL**:
  - Laminatore: Preparazione → Laminazione → Attesa Cura
  - Autoclavista: Attesa Cura → Cura → Finito
  - Feedback visivo durante aggiornamento (spinner sui pulsanti)
  - Gestione errori con alert utente
  - Aggiornamento automatico lista dopo cambio stato

#### Gestione Nesting per Autoclavista
- **Caricamento**: Nesting confermati da `nestingApi.getAll()` filtrati per stato "confermato"
- **Visualizzazione**: Dettagli autoclave, ODL inclusi, utilizzo area, valvole
- **Azioni**: Link per caricamento in autoclave e visualizzazione dettagli
- **Refresh**: Aggiornamento automatico insieme agli ODL

#### Metriche Reali Implementate
- **Laminatore**:
  - ODL in Preparazione (conteggio dinamico)
  - ODL in Laminazione (conteggio dinamico)
  - Totale ODL Assegnati (somma stati rilevanti)
  - Efficienza Turno (da KPI reali)
- **Autoclavista**:
  - ODL in Attesa Cura (conteggio dinamico)
  - ODL in Cura (conteggio dinamico)
  - Nesting Confermati (conteggio dinamico)
  - Utilizzo Autoclavi (da KPI reali)

#### UI/UX Miglioramenti
- **Loading States**: Spinner per caricamento ODL e nesting, skeleton per metriche
- **Error Handling**: Messaggi chiari con pulsanti retry
- **Empty States**: Messaggi informativi quando non ci sono ODL/nesting
- **Refresh Manuale**: Pulsanti di aggiornamento in header
- **Badge Informativi**: Conteggi ODL e nesting visibili
- **Priorità Visualizzate**: Colori e etichette per priorità ODL (Alta/Media/Bassa)

#### Integrazione API
- **ODL**: Utilizzo `odlApi.getAll()` per recupero dati reali
- **Nesting**: Utilizzo `nestingApi.getAll()` per nesting confermati
- **Cambio Stato**: Metodi specifici `updateStatusLaminatore` e `updateStatusAutoclavista`
- **KPI**: Integrazione con `useDashboardKPI` per metriche sistema

#### Sicurezza e Validazione
- **Controlli Ruolo**: Validazione stati permessi per ogni ruolo
- **Gestione Errori**: Try-catch con messaggi specifici
- **Fallback Graceful**: Continuazione funzionamento anche con API parzialmente non disponibili
- **Validazione Dati**: Controlli su esistenza campi prima del rendering

#### File Modificati
- `frontend/src/components/dashboard/ODLHistoryTable.tsx` - Fix crash Select
- `frontend/src/hooks/useODLByRole.ts` - Nuovo hook per ODL filtrati
- `frontend/src/components/dashboard/DashboardLaminatore.tsx` - Dashboard reale
- `frontend/src/components/dashboard/DashboardAutoclavista.tsx` - Dashboard reale

#### Test e Validazione
- **Build**: `npm run build` completata senza errori
- **TypeScript**: Tutti i tipi validati correttamente
- **Funzionalità**: Cambio stato ODL testato per entrambi i ruoli
- **Performance**: Caricamento ottimizzato con refresh automatico

#### Benefici Implementazione
- **Stabilità**: Eliminazione crash Select che bloccava le dashboard
- **Operatività**: Dashboard completamente funzionali per tutti i ruoli
- **Dati Reali**: Eliminazione completa mockup, solo dati effettivi dal database
- **Usabilità**: Pulsanti funzionali per flusso operativo completo
- **Monitoraggio**: Metriche real-time per controllo produzione
- **Scalabilità**: Hook riutilizzabile per future estensioni

## [v2.2.0] - Dashboard KPI Reali e Storico ODL

### [2025-01-28 - Dashboard Funzionale con Dati Reali e Eliminazione Mockup]
- **Completato**: Dashboard operativa per responsabile e admin con KPI reali basati sui dati effettivi del sistema
- **Storico ODL**: Tabella filtrabile e ricercabile per cronologia ordini di lavorazione
- **Scorciatoie funzionali**: Collegamenti diretti alle pagine esistenti, eliminazione link non funzionanti
- **Eliminazione mockup**: Rimozione completa di dati fittizi e placeholder non funzionali

#### Componenti Dashboard Implementati
- **KPIBox.tsx**: Componente riutilizzabile per metriche con stati colorati, skeleton loading e trend
- **ODLHistoryTable.tsx**: Tabella storico ODL con filtri per stato, ricerca testuale e range date
- **DashboardShortcuts.tsx**: Scorciatoie personalizzate per ruolo con link reali alle funzionalità
- **useDashboardKPI.ts**: Hook personalizzato per calcolo KPI reali con aggiornamento automatico

#### KPI Reali Implementati
- **Dashboard Responsabile**:
  - ODL Totali con conteggio completati
  - ODL in Attesa Nesting con alert se > 5
  - Efficienza Produzione (verde > 80%, giallo > 60%, rosso < 60%)
  - ODL Completati Oggi con aggiornamento real-time
- **Dashboard Admin**:
  - ODL Totali (stesso calcolo responsabile)
  - Utilizzo Autoclavi (percentuale autoclavi in uso)
  - Nesting Attivi (conteggio nesting in corso)
  - Efficienza Sistema (performance globale)

#### Storico ODL Funzionale
- **Filtri implementati**: Stato ODL, ricerca per PN/Tool/ID, range date (7/30/90 giorni)
- **Dati reali**: Recupero tramite `odlApi.getAll()` con ordinamento cronologico
- **Link funzionali**: Collegamento diretto ai dettagli ODL esistenti
- **Paginazione**: Limitazione configurabile elementi visualizzati
- **Refresh manuale**: Pulsante aggiornamento dati

#### Scorciatoie per Ruolo
- **Responsabile**: Nuovo ODL, Gestisci ODL, Nesting Attivi, Reports, Statistiche, Catalogo Parti
- **Admin**: Nuovo ODL, Impostazioni, Catalogo Parti, Nesting Attivi, Log Sistema
- **Indicatori stato**: Funzioni in sviluppo chiaramente marcate
- **Link verificati**: Tutti i collegamenti puntano a route esistenti

#### Aggiornamento Automatico
- **Intervallo**: KPI aggiornati ogni 5 minuti automaticamente
- **Refresh manuale**: Pulsante di aggiornamento disponibile
- **Gestione errori**: Fallback graceful con possibilità di retry
- **Performance**: Hook ottimizzato con memoizzazione

#### UI/UX Miglioramenti
- **Loading states**: Skeleton loading per KPI, spinner per tabelle
- **Error handling**: Messaggi chiari con possibilità di retry
- **Responsive design**: Grid adattivo per KPI, tabelle scrollabili
- **Stati colorati**: Codifica colori per status e trend

#### API Utilizzate
- **ODL**: `odlApi.getAll()` per statistiche e storico
- **Nesting**: `nestingApi.getAll()` per conteggi (con fallback)
- **Autoclavi**: `autoclaveApi.getAll()` per utilizzo (con fallback)
- **Gestione errori**: Continuazione caricamento anche se alcune API falliscono

#### File Implementati
- `frontend/src/components/dashboard/KPIBox.tsx` - Componente KPI riutilizzabile
- `frontend/src/components/dashboard/ODLHistoryTable.tsx` - Tabella storico ODL
- `frontend/src/components/dashboard/DashboardShortcuts.tsx` - Scorciatoie per ruolo
- `frontend/src/hooks/useDashboardKPI.ts` - Hook KPI reali
- `frontend/src/components/dashboard/DashboardResponsabile.tsx` - Dashboard aggiornata
- `frontend/src/components/dashboard/DashboardAdmin.tsx` - Dashboard aggiornata
- `docs/dashboard-kpi-reali.md` - Documentazione implementazione

#### Benefici Implementazione
- **Dati reali**: Eliminazione completa mockup, dashboard mostra dati effettivi
- **Usabilità**: Scorciatoie dirette alle funzioni più utilizzate
- **Monitoraggio**: KPI real-time per decisioni informate
- **Performance**: Caricamento ottimizzato con skeleton loading
- **Scalabilità**: Componenti riutilizzabili per future estensioni

#### Test e Validazione
- **Build verificata**: `npm run build` completata senza errori
- **TypeScript**: Tutti i tipi corretti e validati
- **Responsive**: Test su diverse dimensioni schermo
- **Performance**: Caricamento ottimizzato e aggiornamenti efficienti

## [v2.1.1] - Pulizia e Consolidamento Progetto

### [2025-05-26 - Pulizia File Inutilizzati e Consolidamento Tools]
- **Completato**: Pulizia completa del progetto da file obsoleti, duplicati e di test
- **Archivio organizzato**: Creazione cartella `/_archivio_non_usati/` con struttura organizzata
- **Tools consolidati**: Cartella `/tools/` ridotta a soli 3 script essenziali
- **Build ottimizzata**: Rimozione file che causavano warning o errori di build

#### Struttura Tools Finale
- **Script mantenuti**:
  - `snapshot_structure.py`: Genera snapshot struttura progetto
  - `seed_test_data.py`: Popola database con dati di test (versione aggiornata)
  - `debug_local.py`: Utilities per debug locale (nuovo)
- **Script archiviati**: push_git.py, reset_database.py, setup_db.py, run_migration.py

#### File Root Puliti
- **Archiviati**: check_logs_db.py, check_database.py, test_logging_system.py
- **Rimossi**: test_backup.json (99KB), test_api.py
- **Mantenuti**: Solo file di configurazione essenziali

#### Frontend Ottimizzato
- **File test rimossi**: test_role_page.html, test_role_logic.js, test_sidebar_roles.html
- **Componenti puliti**: test-select.tsx spostato in archivio
- **Documentazione**: test_select_fix.md archiviato
- **Build verificata**: npm run build completata senza errori

#### Backend Consolidato
- **Script test archiviati**: test_two_level_nesting*.py, test_logging.py, test_create_logs.py
- **Duplicati rimossi**: cartella frontend/ dal backend, file database corrotti
- **Tools backend**: inspect_models.py, update_version.py spostati in archivio
- **Struttura pulita**: Solo file di produzione mantenuti

#### Archivio Organizzato
- **Struttura**: `/_archivio_non_usati/` con sottocartelle per categoria
  - `/root_files/`: File di test dal root del progetto
  - `/tools/`: Script tools non più necessari
  - `/frontend/`: File di test e debug frontend
  - `/backend/`: Script di test e debug backend
- **Documentazione**: README_ARCHIVIO.md con inventario completo
- **Recupero**: Istruzioni per eventuale recupero file

#### Nuovo Script Debug
- **File**: `tools/debug_local.py`
- **Funzionalità**:
  - Verifica salute backend e connessione database
  - Lista tutti gli endpoint API con conteggio record
  - Debug stato ODL e statistiche
  - Debug ottimizzazione nesting
  - Modalità debug completo o specifico
- **Utilizzo**: `python tools/debug_local.py --health|--endpoints|--odl|--nesting|--full`

#### Statistiche Pulizia
- **File spostati**: ~25 file di test e debug
- **Spazio liberato**: ~150KB di file non utilizzati
- **Duplicati eliminati**: 3 file duplicati identificati e rimossi
- **Cartelle consolidate**: tools/ da 7 a 3 script essenziali

#### Test Post-Pulizia
- **Frontend build**: ✅ Completata senza errori o warning
- **Backend health**: ✅ Raggiungibile e database connesso
- **Script tools**: ✅ Tutti e 3 gli script funzionanti
- **Navigazione**: ✅ Routing frontend verificato

#### Benefici Implementazione
- **Manutenibilità**: Codebase più pulito e organizzato
- **Performance**: Rimozione file non necessari dalla build
- **Chiarezza**: Struttura tools semplificata e focalizzata
- **Archivio**: Possibilità di recupero file se necessario
- **Debug**: Nuovo strumento centralizzato per troubleshooting

#### Effetti sulla Produzione
- **Stabilità**: Rimozione potenziali conflitti da file obsoleti
- **Deploy**: Build più veloce senza file di test
- **Manutenzione**: Struttura più chiara per sviluppi futuri
- **Documentazione**: Archivio organizzato per riferimenti storici

## [v2.1.0] - Sistema di Logging Avanzato e Audit Trail

### [2025-01-28 - Sistema Completo di Logging e Tracciabilità Operazioni]
- **Completato**: Sistema avanzato di logging per tracciare tutte le operazioni critiche del sistema
- **Audit Trail**: Tracciabilità completa di cambi stato ODL, operazioni nesting, cicli di cura e modifiche critiche
- **Dashboard Analytics**: Interfaccia dedicata per admin e responsabile con statistiche e filtri avanzati
- **Export Funzionalità**: Esportazione logs in formato CSV per analisi esterne
- **Monitoraggio Real-time**: Visualizzazione errori recenti e attività sistema in tempo reale

#### Modello Database SystemLog
- **Tabella**: `system_logs` con enumerazioni PostgreSQL per tipizzazione forte
- **Campi principali**:
  - `timestamp`: Data/ora operazione con timezone
  - `level`: Livello log (INFO, WARNING, ERROR, CRITICAL)
  - `event_type`: Tipo evento (13 categorie: odl_state_change, nesting_confirm, cura_start, etc.)
  - `user_role`: Ruolo utente (admin, responsabile, autoclavista, laminatore, sistema)
  - `user_id`: ID utente che ha eseguito l'operazione
  - `action`: Descrizione azione eseguita
  - `entity_type`, `entity_id`: Riferimento entità coinvolta (ODL, Tool, Autoclave, etc.)
  - `details`: Dettagli aggiuntivi in formato JSON
  - `old_value`, `new_value`: Valori prima/dopo per audit modifiche
  - `ip_address`: Indirizzo IP per tracciabilità accessi

#### Enumerazioni Tipizzate
- **LogLevel**: INFO, WARNING, ERROR, CRITICAL
- **EventType**: 13 tipi di eventi tracciati
  - `odl_state_change`: Cambi stato ODL
  - `nesting_confirm`, `nesting_modify`: Operazioni nesting
  - `cura_start`, `cura_complete`: Cicli di cura
  - `tool_modify`, `autoclave_modify`, `ciclo_modify`: Modifiche entità
  - `backup_operation`, `database_reset`: Operazioni database
  - `user_login`, `user_logout`: Accessi utente
  - `system_error`, `api_error`: Errori sistema
- **UserRole**: admin, responsabile, autoclavista, laminatore, sistema

#### Servizio di Logging Centralizzato
- **File**: `backend/services/system_log_service.py`
- **Metodi specializzati**:
  - `log_odl_state_change()`: Traccia cambi stato ODL con dettagli transizione
  - `log_nesting_confirm()`, `log_nesting_modify()`: Operazioni nesting con statistiche
  - `log_cura_start()`, `log_cura_complete()`: Cicli di cura con parametri
  - `log_tool_modify()`, `log_autoclave_modify()`: Modifiche configurazioni
  - `log_backup_operation()`: Operazioni backup/ripristino database
- **Funzioni query**:
  - `get_logs()`: Recupero logs con filtri e paginazione
  - `get_log_stats()`: Statistiche per dashboard analytics
  - `get_recent_errors()`: Monitoraggio errori recenti

#### API Router Completo
- **File**: `backend/api/routers/system_logs.py`
- **Endpoints implementati**:
  - `GET /system-logs/`: Lista logs con filtri avanzati
  - `GET /system-logs/stats`: Statistiche dashboard
  - `GET /system-logs/recent-errors`: Errori recenti per monitoraggio
  - `GET /system-logs/by-entity/{type}/{id}`: Logs specifici per entità
  - `GET /system-logs/export`: Export CSV con filtri personalizzabili
- **Filtri disponibili**: event_type, user_role, level, date_range, entity_type, limit
- **Autorizzazioni**: Accesso limitato a ADMIN e RESPONSABILE

#### Integrazione Automatica Sistema
- **ODL Router**: Logging automatico cambi stato laminatore/autoclavista
- **Nesting Router**: Tracciamento conferme e modifiche nesting
- **Schedule Router**: Logging operazioni cura start/complete
- **Admin Router**: Tracciamento operazioni backup/ripristino/reset
- **Mapping ruoli**: Conversione automatica ruoli frontend → enum database

#### Dashboard Frontend Admin/Responsabile
- **Pagine**: `/dashboard/admin/logs` e `/dashboard/responsabile/logs`
- **Statistiche dashboard**:
  - Totale logs nel sistema
  - Errori recenti (ultime 24h)
  - Tipo evento più frequente
  - Ruolo più attivo
- **Filtri avanzati**:
  - Tipo evento (dropdown con traduzioni italiane)
  - Ruolo utente (admin, responsabile, autoclavista, laminatore, sistema)
  - Livello log (info, warning, error, critical)
  - Range date (picker con presets)
  - Tipo entità (ODL, Tool, Autoclave, etc.)
  - Limite risultati (10-1000)

#### Interfaccia Utente Avanzata
- **Tabella logs**: Sortable con colonne timestamp, livello, evento, ruolo, azione
- **Badge colorati**: Livelli log con colori distintivi (blu=info, giallo=warning, rosso=error, nero=critical)
- **Traduzioni complete**: Tutti i tipi evento e ruoli tradotti in italiano
- **Link entità**: Collegamenti diretti a ODL, Tool, Autoclave quando disponibili
- **Dettagli espandibili**: JSON details formattato per analisi approfondita
- **Export CSV**: Pulsante export con applicazione filtri correnti
- **Refresh real-time**: Aggiornamento manuale per monitoraggio live

#### Migrazione Database
- **File**: `backend/alembic/versions/add_system_logs_table.py`
- **Creazione tabella**: system_logs con tutti i campi e constraint
- **Enumerazioni PostgreSQL**: Definizione tipi custom per type safety
- **Indici performance**: Su timestamp, event_type, user_role, entity_id
- **Compatibilità**: Supporto PostgreSQL e SQLite per sviluppo

#### Schemi Pydantic
- **File**: `backend/schemas/system_log.py`
- **Modelli**:
  - `SystemLogBase`: Campi base per creazione
  - `SystemLogCreate`: Schema per inserimento nuovo log
  - `SystemLogResponse`: Schema completo per API response
  - `SystemLogFilter`: Parametri filtri con validazione
  - `SystemLogStats`: Statistiche dashboard

#### Controlli di Sicurezza
- **Autorizzazioni**: Solo ADMIN e RESPONSABILE possono accedere ai logs
- **Validazione input**: Controllo parametri filtri e range date
- **Rate limiting**: Protezione endpoint export per evitare abusi
- **Sanitizzazione**: Escape caratteri speciali in export CSV
- **Audit immutabile**: Logs non modificabili una volta creati

#### File Implementati/Modificati
- `backend/models/system_log.py` - Modello database completo
- `backend/schemas/system_log.py` - Schemi Pydantic per API
- `backend/services/system_log_service.py` - Servizio centralizzato logging
- `backend/api/routers/system_logs.py` - Router API completo
- `backend/alembic/versions/add_system_logs_table.py` - Migrazione database
- `backend/api/routers/odl.py` - Integrazione logging cambi stato
- `backend/api/routers/nesting.py` - Logging operazioni nesting
- `backend/api/routers/schedule.py` - Logging cicli cura
- `frontend/src/app/dashboard/admin/logs/page.tsx` - Dashboard admin
- `frontend/src/app/dashboard/responsabile/logs/page.tsx` - Dashboard responsabile

#### Traduzioni Italiane
- **Tipi evento**: 'odl_state_change' → 'Cambio Stato ODL', 'nesting_confirm' → 'Conferma Nesting', etc.
- **Ruoli utente**: 'laminatore' → 'Laminatore', 'autoclavista' → 'Autoclavista', etc.
- **Livelli log**: Badge colorati con testo italiano
- **Interfaccia**: Tutti i testi UI tradotti per usabilità

#### Benefici Implementazione
- **Tracciabilità completa**: Audit trail di tutte le operazioni critiche
- **Monitoraggio proattivo**: Identificazione rapida errori e problemi
- **Analisi operativa**: Statistiche utilizzo e pattern comportamentali
- **Compliance**: Documentazione operazioni per audit esterni
- **Debug avanzato**: Cronologia dettagliata per troubleshooting
- **Sicurezza**: Tracciamento accessi e modifiche sensibili

#### Effetti sulla Produzione
- **Qualità processo**: Visibilità completa ciclo di vita ODL
- **Responsabilità**: Tracciamento azioni per ogni operatore
- **Ottimizzazione**: Analisi pattern per miglioramento processi
- **Conformità**: Documentazione per certificazioni qualità
- **Manutenzione**: Identificazione proattiva problemi sistema

## [v2.0.9] - Impostazioni Accessibili, Backup e Reset Database

### [2025-01-27 - Sistema Completo Gestione Database e Impostazioni Globali]
- **Completato**: Sistema completo per gestione database con backup, ripristino e reset
- **Menu utente**: Impostazioni accessibili da menu dropdown nell'header per tutti i ruoli
- **Backup automatico**: Esportazione completa database in formato JSON con timestamp
- **Ripristino sicuro**: Upload e ripristino da file backup con validazione
- **Reset controllato**: Svuotamento database con conferma parola chiave "reset"

#### Menu Utente e Navigazione
- **Menu dropdown**: Nuovo componente `UserMenu` nell'header con icona utente
- **Opzioni disponibili**: 
  - 📁 Impostazioni (accessibili a tutti i ruoli)
  - 🔄 Cambia ruolo (solo in sviluppo)
  - 🚪 Logout con reset ruolo
- **Rimozione sidebar**: Impostazioni spostate da sidebar admin a menu globale
- **Accessibilità**: Tutti i ruoli possono accedere alle impostazioni di base

#### Sistema Backup Database
- **API Endpoint**: `GET /api/v1/admin/backup`
- **Formato export**: JSON strutturato con metadati e timestamp
- **Contenuto completo**: Tutte le tabelle con dati, colonne e conteggi
- **Download automatico**: File scaricato con nome timestamp
- **Gestione errori**: Validazione e logging dettagliato

#### Sistema Ripristino Database
- **API Endpoint**: `POST /api/v1/admin/restore`
- **Upload sicuro**: Validazione formato JSON e struttura backup
- **Ripristino atomico**: Transazione completa con rollback in caso errore
- **Sostituzione dati**: Svuotamento tabelle e inserimento nuovi dati
- **Report dettagliato**: Statistiche tabelle ripristinate ed eventuali errori

#### Sistema Reset Database
- **API Endpoint**: `POST /api/v1/admin/database/reset`
- **Conferma sicurezza**: Richiesta parola chiave esatta "reset"
- **Svuotamento completo**: Eliminazione tutti i record da tutte le tabelle
- **Reset sequenze**: Azzeramento auto-increment per SQLite
- **Statistiche complete**: Report record eliminati per tabella

#### Interfaccia Utente Avanzata
- **Pagina impostazioni**: `/dashboard/impostazioni` accessibile a tutti
- **Sezioni organizzate**:
  - 🎨 Aspetto e Tema (selettore tema esistente)
  - 💾 Gestione Database (backup, ripristino, reset)
  - ⚡ Prestazioni e Aggiornamenti
  - ℹ️ Informazioni Accesso
- **Dialog conferma**: Modal per reset con input validazione
- **Feedback visivo**: Toast notifications per tutte le operazioni
- **Indicatori stato**: Connessione database e statistiche

#### Controlli di Sicurezza
- **Validazione file**: Controllo formato JSON per ripristino
- **Conferma reset**: Parola chiave esatta richiesta per operazioni distruttive
- **Gestione errori**: Try-catch completo con rollback transazioni
- **Logging operazioni**: Tracciabilità completa tutte le operazioni database

#### File Implementati/Modificati
- `backend/api/routers/admin.py` - Router completo per gestione database
- `backend/api/routes.py` - Registrazione router admin
- `frontend/src/components/ui/user-menu.tsx` - Nuovo menu dropdown utente
- `frontend/src/app/dashboard/layout.tsx` - Integrazione UserMenu in header
- `frontend/src/app/dashboard/impostazioni/page.tsx` - Pagina impostazioni completa
- `backend/requirements.txt` - Aggiunta dipendenza python-multipart

#### Dipendenze Aggiunte
- **python-multipart==0.0.20**: Necessaria per gestione upload file
- **Componenti UI**: Dialog, Button, Input, Label per interfaccia avanzata
- **Icone Lucide**: Trash2, Upload, Download per azioni database

#### Test e Validazione
- **Script test**: `test_api.py` per validazione completa API
- **Test automatici**: Verifica backup, ripristino e reset
- **Gestione errori**: Test scenari fallimento e validazione
- **Performance**: Test con database popolato (224 record, 16 tabelle)

#### Effetti sulla UX
- **Accessibilità migliorata**: Impostazioni sempre disponibili da header
- **Gestione dati semplificata**: Backup/ripristino con un click
- **Sicurezza operazioni**: Conferme e validazioni per operazioni critiche
- **Feedback immediato**: Notifiche toast per tutte le operazioni
- **Interfaccia moderna**: Design coerente con stile Manta Group

## [v2.0.8] - Interfaccia Visiva Nesting su Due Piani + Conferma Autoclavista

### [2025-01-27 - Interfaccia Interattiva per Visualizzazione e Modifica Nesting]
- **Completato**: Interfaccia visiva completa per il nesting su due piani con funzionalità di modifica e conferma
- **Visualizzazione 2D**: Layout interattivo che mostra la disposizione dei tool sui due piani dell'autoclave
- **Modifica manuale**: Possibilità per l'autoclavista di spostare tool tra piano 1 e piano 2 prima del carico
- **Configurazione avanzata**: Modifica della superficie effettiva del piano 2 e parametri di nesting
- **Workflow completo**: Dalla generazione automatica alla conferma finale con cambio stato ODL

#### Componenti Frontend Implementati
- **NestingPreview**: Visualizzazione 2D interattiva dei due piani con tool posizionati
  - Layout scalato con rappresentazione fedele delle dimensioni reali
  - Tool cliccabili con informazioni dettagliate (part number, peso, dimensioni)
  - Colori distinti per piano 1 (blu) e piano 2 (verde)
  - Controlli per spostamento tool tra piani con feedback visivo
- **NestingConfigForm**: Form avanzato per configurazione parametri nesting
  - Modifica superficie massima piano 2 con validazione
  - Assegnazione manuale ODL ai piani tramite dropdown
  - Statistiche aggiornate in tempo reale (peso, area, conteggi)
  - Validazione carico con blocco conferma se eccessivo

#### Pagina Interfaccia Visiva
- **Route**: `/dashboard/autoclavista/nesting/visual`
- **Funzionalità complete**:
  - Generazione automatica nesting all'apertura
  - Tabs per visualizzazione 2D e configurazione avanzata
  - Modifica interattiva con anteprima in tempo reale
  - Conferma nesting con cambio stato a "In sospeso"
  - Gestione errori e validazioni complete

#### Funzionalità di Visualizzazione
- **Layout 2D responsivo**: Rappresentazione scalata dell'autoclave (1mm = 0.2px)
- **Tool interattivi**: Click per selezione, hover per informazioni, drag visuale
- **Statistiche live**: Aggiornamento automatico peso, area, conteggi per piano
- **Indicatori stato**: Badge colorati per carico valido/eccessivo
- **ODL esclusi**: Visualizzazione separata con motivi di esclusione

#### Workflow Autoclavista
1. **Generazione**: Nesting automatico con algoritmo ottimizzato
2. **Visualizzazione**: Layout 2D interattivo con tool posizionati
3. **Modifica**: Spostamento tool tra piani e configurazione superficie
4. **Validazione**: Controllo automatico limiti peso e superficie
5. **Conferma**: Salvataggio nesting in stato "In sospeso"
6. **Carico**: ODL pronti per inserimento in autoclave

#### Controlli di Sicurezza
- **Validazione peso**: Blocco conferma se carico supera limite autoclave
- **Controllo superficie**: Validazione area utilizzata vs superficie disponibile
- **Autorizzazioni**: Accesso limitato a AUTOCLAVISTA e RESPONSABILE
- **Stato consistency**: Aggiornamento atomico stato nesting e ODL

#### Integrazione con Sistema Esistente
- **API esistenti**: Utilizzo endpoint `/nesting/two-level` per generazione
- **Aggiornamento stato**: Integrazione con sistema di gestione stati nesting
- **Navigazione**: Link dalla pagina principale nesting con pulsante "Interfaccia Visiva"
- **Persistenza**: Salvataggio automatico modifiche con possibilità ripristino

#### File Implementati
- `frontend/src/components/nesting/NestingPreview.tsx` - Visualizzazione 2D interattiva
- `frontend/src/components/ui/NestingConfigForm.tsx` - Form configurazione avanzata
- `frontend/src/app/dashboard/autoclavista/nesting/visual/page.tsx` - Pagina principale
- `frontend/src/lib/api.ts` - Estensione interfaccia TwoLevelNestingResponse

#### Miglioramenti UX
- **Interfaccia intuitiva**: Design moderno con icone e colori distintivi
- **Feedback immediato**: Toast notifications per ogni azione
- **Responsive design**: Adattamento automatico a diverse dimensioni schermo
- **Accessibilità**: Fallback input per modifiche senza drag/drop
- **Pulsante fisso**: Conferma nesting sempre visibile in basso a destra

#### Effetti sulla Produzione
- **Controllo qualità**: Verifica visiva disposizione prima del carico
- **Flessibilità operativa**: Adattamento layout in base a esigenze specifiche
- **Riduzione errori**: Validazione automatica prima della conferma
- **Tracciabilità**: Salvataggio configurazione per audit e analisi
- **Efficienza**: Workflow ottimizzato dalla generazione alla conferma

## [v2.0.7] - Nesting su Due Piani Ottimizzato per Peso e Dimensione

### [2025-05-26 - Implementazione Completa Nesting su Due Piani]
- **Completato**: Sistema completo di nesting su due piani ottimizzato per peso e dimensione
- **Algoritmo avanzato**: Posizionamento intelligente dei pezzi pesanti/grandi nel piano inferiore e leggeri/piccoli nel piano superiore
- **Controllo carico**: Validazione automatica del peso totale rispetto al limite massimo dell'autoclave
- **API completa**: Endpoint dedicato per esecuzione nesting su due piani con parametri configurabili
- **Test completi**: Suite di test per algoritmo, servizio e API con validazione funzionalità

#### Funzionalità Algoritmo di Nesting
- **Ordinamento intelligente**: Tool ordinati per priorità peso/area decrescente (70% peso, 30% area)
- **Assegnazione ottimizzata**: Pezzi pesanti (≥5kg) prioritariamente al piano 1, leggeri al piano 2
- **Superficie configurabile**: Piano 2 con superficie massima editabile (default 80% del piano 1)
- **Posizionamento 2D**: Calcolo automatico posizioni X,Y per ogni tool sui due piani
- **Validazione carico**: Controllo peso totale vs limite massimo autoclave

#### Modelli Database Estesi
- **Tool**: Aggiunti campi `peso` (Float) e `materiale` (String) per ottimizzazione
- **Autoclave**: Aggiunto campo `max_load_kg` per controllo carico massimo
- **NestingResult**: Esteso con campi specifici per due piani:
  - `peso_totale_kg`: Peso totale del carico
  - `area_piano_1`, `area_piano_2`: Aree utilizzate per piano
  - `superficie_piano_2_max`: Superficie massima configurabile piano 2
  - `posizioni_tool`: Posizioni 2D con assegnazione piano

#### API Endpoint Implementato
- **Route**: `POST /api/nesting/two-level`
- **Parametri**: 
  - `autoclave_id`: ID autoclave target
  - `odl_ids`: Lista ODL da includere (opzionale, default tutti in attesa)
  - `superficie_piano_2_max_cm2`: Superficie massima piano 2
  - `note`: Note opzionali per il nesting
- **Response**: Risultato dettagliato con statistiche, posizioni e validazioni

#### Servizio di Nesting Esteso
- **Funzione**: `run_two_level_nesting()` in `services/nesting_service.py`
- **Validazioni**: Controllo autoclave disponibile, ODL validi, carico massimo
- **Salvataggio DB**: Creazione automatica record NestingResult con dati completi
- **Aggiornamento ODL**: Cambio stato automatico ODL pianificati a "Cura"
- **Gestione errori**: Eccezioni specifiche per problemi validazione

#### Algoritmo di Ottimizzazione
- **File**: `nesting_optimizer/two_level_nesting.py`
- **Classe risultato**: `TwoLevelNestingResult` con statistiche complete
- **Validazione ODL**: Controllo parte, catalogo, tool, ciclo cura associati
- **Calcolo priorità**: Score basato su peso e area per ordinamento
- **Posizionamento**: Algoritmo 2D con margini sicurezza e controllo sovrapposizioni

#### Test Implementati
- **Test diretto algoritmo**: Verifica funzionamento `compute_two_level_nesting()`
- **Test servizio**: Validazione `run_two_level_nesting()` con salvataggio DB
- **Test simulazione API**: Verifica endpoint con dati reali
- **Dati di test**: 6 tool con pesi diversi (15kg-2.5kg) e materiali vari
- **Scenari**: Test carico normale e carico eccessivo per validazione limiti

#### File Implementati/Modificati
- `backend/models/tool.py` - Aggiunti campi peso e materiale
- `backend/models/autoclave.py` - Aggiunto campo max_load_kg
- `backend/models/nesting_result.py` - Esteso per nesting due piani
- `backend/nesting_optimizer/two_level_nesting.py` - Algoritmo completo
- `backend/services/nesting_service.py` - Servizio run_two_level_nesting()
- `backend/api/routers/nesting.py` - Endpoint POST /two-level
- `backend/test_two_level_nesting.py` - Test algoritmo base
- `backend/test_two_level_nesting_api.py` - Test completo algoritmo+API

#### Logica di Business Implementata
- **Soglia peso**: 5kg per distinguere pezzi pesanti/leggeri
- **Priorità piano 1**: Pezzi pesanti e grandi per stabilità
- **Priorità piano 2**: Pezzi leggeri e piccoli per ottimizzazione spazio
- **Controllo carico**: Validazione peso totale vs limite autoclave
- **Efficienza calcolo**: Percentuali utilizzo per piano 1, piano 2 e totale

#### Effetti sulla UX
- **Ottimizzazione automatica**: Nesting intelligente senza intervento manuale
- **Controllo sicurezza**: Prevenzione sovraccarico autoclave
- **Flessibilità configurazione**: Superficie piano 2 editabile per diverse esigenze
- **Tracciabilità completa**: Salvataggio posizioni e statistiche per audit
- **Integrazione seamless**: Compatibile con sistema nesting esistente

## [v2.0.6] - Sistema Switch Stato ODL per Ruoli Specifici

### [2025-01-26 - Implementazione Switch Stato ODL per Laminatore e Autoclavista]
- **Completato**: Sistema completo per permettere ai ruoli LAMINATORE e AUTOCLAVISTA di far avanzare gli ODL solo nei rispettivi stati previsti
- **Interfacce dedicate**: Pagine semplici e focalizzate per ogni ruolo con controlli specifici
- **API sicure**: Endpoint dedicati con validazione transizioni e controlli di ruolo
- **Gestione automatica tempi**: Registrazione automatica delle fasi di produzione
- **UX ottimizzata**: Dialog di conferma, feedback utente e gestione errori completa

#### Funzionalità LAMINATORE
- **Pagina dedicata**: `/dashboard/laminatore/produzione` completamente riscritta
- **Stati gestiti**: Preparazione → Laminazione → Attesa Cura
- **Interfaccia semplificata**: Tabella ODL con pulsanti di avanzamento
- **Filtri intelligenti**: Visualizza solo ODL in Preparazione e Laminazione
- **Controlli sicurezza**: Validazione transizioni consentite per il ruolo

#### Funzionalità AUTOCLAVISTA  
- **Nuova pagina**: `/dashboard/autoclavista/produzione` creata da zero
- **Stati gestiti**: Attesa Cura → Cura → Finito
- **Layout a colonne**: Separazione visiva tra ODL in attesa e in cura
- **Integrazione nesting**: Collegamento rapido alla gestione nesting
- **Note di sicurezza**: Promemoria per conferma nesting prima di avviare cura

#### API Backend Implementate
- **Endpoint laminatore**: `PATCH /api/v1/odl/{id}/laminatore-status`
- **Endpoint autoclavista**: `PATCH /api/v1/odl/{id}/autoclavista-status`
- **Controlli di sicurezza**: Validazione ruolo e transizioni consentite
- **Gestione automatica**: Apertura/chiusura fasi con calcolo durata
- **Logging dettagliato**: Tracciabilità completa delle operazioni

#### Controlli di Sicurezza
- **Transizioni validate**: Solo avanzamenti consentiti per ogni ruolo
- **Prevenzione errori**: Blocco operazioni non autorizzate
- **Gestione stati**: Impossibile saltare fasi o tornare indietro
- **Logging operazioni**: Tracciabilità completa con dettagli ruolo

#### File Implementati/Modificati
- `backend/api/routers/odl.py` - Aggiunti endpoint specifici per ruoli
- `frontend/src/lib/api.ts` - Nuove funzioni API per switch stato
- `frontend/src/app/dashboard/laminatore/produzione/page.tsx` - Riscritta completamente
- `frontend/src/app/dashboard/autoclavista/produzione/page.tsx` - Nuova pagina
- `frontend/src/app/dashboard/layout.tsx` - Aggiunto link sidebar autoclavista
- `docs/switch-stato-odl.md` - Documentazione completa sistema

#### Logica di Business Implementata
- **LAMINATORE**: Preparazione → Laminazione → Attesa Cura
- **AUTOCLAVISTA**: Attesa Cura → Cura → Finito  
- **Gestione tempi fasi**: Automatica con calcolo durata e note
- **Prevenzione duplicati**: Controllo fasi attive esistenti
- **Integrazione nesting**: Collegamento con sistema di ottimizzazione

#### Effetti sulla UX
- **Interfacce specifiche**: Ogni ruolo vede solo i propri ODL e azioni
- **Operazioni semplificate**: Pulsanti chiari per avanzamento stato
- **Feedback immediato**: Toast informativi per ogni operazione
- **Sicurezza visiva**: Conferme per operazioni critiche
- **Navigazione ottimizzata**: Collegamenti rapidi tra funzionalità correlate

## [v2.0.5] - Landing Page Selezione Ruolo `/role`

### [2025-01-26 - Implementazione Route `/role` per Selezione Ruolo Utente]
- **Completato**: Creazione nuova route `/role` per selezione ruolo utente come richiesto
- **Funzionalità**: Pagina identica a `/select-role` ma accessibile tramite percorso `/role`
- **Persistenza**: Salvataggio ruolo in localStorage con chiave `userRole`
- **Redirect automatico**: Reindirizzamento a `/dashboard` dopo selezione ruolo
- **Controllo accessi**: Aggiornamento RoleGuard per includere la nuova route
- **UX coerente**: Interfaccia moderna con 4 card per i ruoli disponibili

#### Funzionalità Implementate
- **Pagina `/role`**: 4 card cliccabili per ADMIN, RESPONSABILE, LAMINATORE, AUTOCLAVISTA
- **Salvataggio localStorage**: Utilizzo hook `useUserRole()` per persistenza ruolo
- **Redirect automatico**: Navigazione automatica a `/dashboard` dopo selezione
- **Controllo globale**: RoleGuard verifica presenza ruolo e reindirizza se mancante
- **Accesso condizionato**: Sidebar e contenuti si adattano al ruolo selezionato

#### Ruoli Disponibili
- **ADMIN**: Accesso completo con icona Shield (rosso)
  - Gestione completa del sistema, configurazione utenti, accesso tutti i moduli
- **RESPONSABILE**: Supervisione produzione con icona Users (blu)
  - Gestione ODL, supervisione operazioni, reports e pianificazione
- **LAMINATORE**: Operazioni laminazione con icona Wrench (verde)
  - Gestione parti, operazioni laminazione, controllo qualità
- **AUTOCLAVISTA**: Gestione autoclavi con icona Flame (arancione)
  - Gestione autoclavi, cicli di cura, nesting e scheduling

#### File Implementati/Modificati
- `frontend/src/app/role/page.tsx` - Nuova pagina selezione ruolo
- `frontend/src/components/RoleGuard.tsx` - Aggiunta route `/role` alle pagine permesse
- `frontend/src/app/page.tsx` - Aggiornamento link da `/select-role` a `/role`
- `docs/changelog.md` - Documentazione nuova funzionalità

#### Logica di Controllo Implementata
- **Lettura localStorage**: Hook `useUserRole()` legge ruolo all'avvio
- **Redirect condizionale**: Se ruolo mancante → redirect automatico a `/role`
- **Pagine permesse**: `/`, `/role`, `/select-role` accessibili senza ruolo
- **Persistenza**: Ruolo salvato sopravvive a ricaricamenti pagina

#### Effetti sulla UX
- **Accesso semplificato**: URL più intuitivo `/role` invece di `/select-role`
- **Interfaccia moderna**: Design responsive con animazioni hover e transizioni
- **Controllo sicuro**: Impossibile accedere al sistema senza selezione ruolo
- **Esperienza fluida**: Transizione automatica dopo selezione ruolo

## [v2.0.4] - Sidebar Dinamica Basata su Ruoli

### [2025-01-25 - Implementazione Sidebar Dinamica per Ruoli Utente]
- **Completato**: Riorganizzazione completa della sidebar per adattarsi ai ruoli specifici
- **Controllo accessi**: Implementazione filtri client-side basati su localStorage
- **Configurazione ruoli**: Definizione precisa delle voci visibili per ogni ruolo
- **Fallback sicuro**: Reindirizzamento automatico alla landing se ruolo mancante
- **UX migliorata**: Interfaccia pulita e specifica per ogni tipo di utente

#### Configurazione Ruoli Implementata
- **ADMIN**: Accesso completo a tutte le funzionalità del sistema
  - Dashboard, ODL, Monitoraggio, Produzione, Tools, Nesting, Autoclavi, Reports, Schedule
  - Catalogo, Parti, Cicli Cura, Statistiche, Tempi & Performance, Impostazioni
- **RESPONSABILE**: Accesso limitato a gestione e supervisione
  - Dashboard, ODL, Monitoraggio ODL, Schedule
- **LAMINATORE**: Accesso focalizzato su produzione
  - Dashboard, Produzione, Tools/Stampi
- **AUTOCLAVISTA**: Accesso specifico per processo autoclave
  - Dashboard, Nesting, Autoclavi, Reports

#### Struttura Sidebar Riorganizzata
- **Dashboard**: Sezione comune per tutti i ruoli
- **Gestione ODL**: Visibile solo ad Admin e Responsabile
- **Produzione**: Specifica per Admin e Laminatore
- **Autoclave**: Dedicata ad Admin e Autoclavista
- **Pianificazione**: Per Admin e Responsabile
- **Amministrazione**: Esclusiva per Admin

#### Logica di Filtraggio Implementata
- **Lettura ruolo**: Utilizzo `useUserRole()` hook per accesso localStorage
- **Filtro sezioni**: Controllo `roles` array per visibilità sezioni
- **Filtro items**: Controllo individuale per ogni voce di menu
- **Fallback graceful**: Messaggio informativo se nessuna funzionalità disponibile

#### File Modificati
- `frontend/src/app/dashboard/layout.tsx` - Riorganizzazione completa configurazione sidebar
- `docs/changelog.md` - Documentazione modifiche

#### Effetti sulla UX
- **Interfaccia specifica**: Ogni ruolo vede solo le funzionalità pertinenti
- **Riduzione confusione**: Eliminazione voci non accessibili per il ruolo
- **Navigazione ottimizzata**: Menu più pulito e focalizzato
- **Sicurezza migliorata**: Controllo accessi visivo coerente con autorizzazioni

## [v2.0.3] - Rebranding Frontend da CarbonPilot a Manta Group

### [2025-01-25 - Aggiornamento Branding Frontend]
- **Completato**: Sostituzione completa di tutti i riferimenti "CarbonPilot" con "Manta Group" nel frontend
- **Scope**: Modificati solo i testi visualizzati all'utente, mantenuti i nomi tecnici nei file di configurazione
- **Impatto**: Interfaccia utente ora riflette il nuovo brand aziendale
- **Compatibilità**: Nessun impatto su funzionalità o API backend

#### File Modificati
- `frontend/src/app/page.tsx` - Titolo principale e footer
- `frontend/src/app/layout.tsx` - Metadata title della pagina
- `frontend/src/app/select-role/page.tsx` - Messaggio di benvenuto
- `frontend/src/app/dashboard/layout.tsx` - Logo nell'header della dashboard
- `frontend/src/components/dashboard/DashboardAdmin.tsx` - Descrizione sistema admin
- `frontend/src/app/styleguide/page.tsx` - Guida componenti UI
- `frontend/src/app/dashboard/impostazioni/page.tsx` - Descrizione configurazioni
- `frontend/src/app/dashboard/odl/README.md` - Documentazione sezione ODL

#### Testi Aggiornati
- **Pagina principale**: "CarbonPilot" → "Manta Group" nel titolo e footer
- **Metadata browser**: "CarbonPilot - Gestione Compositi" → "Manta Group - Gestione Compositi"
- **Pagina selezione ruolo**: "Benvenuto in CarbonPilot" → "Benvenuto in Manta Group"
- **Header dashboard**: Logo "CarbonPilot" → "Manta Group"
- **Dashboard admin**: "sistema CarbonPilot" → "sistema Manta Group"
- **Style guide**: "componenti UI di CarbonPilot" → "componenti UI di Manta Group"
- **Impostazioni**: "applicazione CarbonPilot" → "applicazione Manta Group"
- **Documentazione ODL**: "CarbonPilot" → "Manta Group" nel titolo

#### Effetti sulla UX
- **Brand consistency**: Interfaccia utente allineata al nuovo brand aziendale
- **Esperienza coerente**: Tutti i testi visibili all'utente aggiornati uniformemente
- **Nessun impatto funzionale**: Tutte le funzionalità rimangono invariate
- **Mantenimento configurazioni**: Nomi tecnici nei package.json e file di build non modificati

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

## [v1.6.0] - Riorganizzazione Struttura per Ruoli

### [2024-12-26 - Riorganizzazione Completa Dashboard per Ruoli]
- **Completato**: Riorganizzazione completa della struttura dashboard basata sui ruoli utente
- **Obiettivo**: Migliorare organizzazione, manutenibilità e scalabilità del codice

#### Nuova Struttura Directory
- **Directory per Ruolo**: Creazione di directory specifiche per ogni ruolo (admin/, responsabile/, laminatore/, autoclavista/)
- **Directory Condivise**: Centralizzazione pagine condivise in shared/ (catalog/, odl/)
- **Layout Gerarchici**: Implementazione layout specifici per ogni ruolo che ereditano dal layout principale

#### Mappatura Pagine per Ruolo

**ADMIN (Accesso Completo)**:
- `impostazioni/` → `admin/impostazioni/` - Configurazioni di sistema

**RESPONSABILE (Gestione e Supervisione)**:
- `reports/` → `responsabile/reports/` - Reports e analytics
- `odl/monitoring/` → `responsabile/odl-monitoring/` - Monitoraggio ODL tempo reale
- `catalog/statistiche/` → `responsabile/statistiche/` - Statistiche catalogo

**LAMINATORE (Produzione)**:
- `parts/` → `laminatore/parts/` - Gestione parti
- `tools/` → `laminatore/tools/` - Tools e stampi
- `produzione/` → `laminatore/produzione/` - Operazioni produzione
- `tempi/` → `laminatore/tempi/` - Tempi e performance

**AUTOCLAVISTA (Autoclave)**:
- `nesting/` → `autoclavista/nesting/` - Gestione nesting
- `autoclavi/` → `autoclavista/autoclavi/` - Controllo autoclavi
- `cicli-cura/` → `autoclavista/cicli-cura/` - Cicli di cura
- `schedule/` → `autoclavista/schedule/` - Scheduling produzione

**CONDIVISE (Tutti i Ruoli)**:
- `catalog/` → `shared/catalog/` - Catalogo parti (escluse statistiche)
- `odl/` → `shared/odl/` - Gestione ODL (escluso monitoring)

#### Aggiornamenti Tecnici

**Sidebar Dinamica**:
- Aggiornamento configurazione `sidebarSections` con nuovi percorsi
- Aggiunta sezione "Laminazione" per tempi e performance
- Mantenimento filtri per ruolo esistenti

**Layout System**:
- Creazione layout specifici per ogni directory ruolo
- Ereditarietà dal layout principale del dashboard
- Mantenimento funzionalità sidebar dinamica

**Routing**:
- Aggiornamento tutti i link interni per nuovi percorsi
- Mantenimento sistema routing dinamico esistente
- Compatibilità con dashboard per ruolo esistenti

#### Vantaggi Implementati

**Organizzazione**:
- Struttura logica e intuitiva per ruoli
- Separazione chiara delle responsabilità
- Facilità di navigazione e manutenzione

**Manutenibilità**:
- Codice organizzato per competenze
- Facile aggiunta nuove funzionalità per ruolo
- Isolamento modifiche per ruolo specifico

**Scalabilità**:
- Struttura pronta per nuovi ruoli
- Sistema di permessi granulare
- Espandibilità senza impatti su altri ruoli

**Performance**:
- Caricamento ottimizzato per ruolo
- Bundle separati per funzionalità specifiche
- Lazy loading mantenuto

#### File Creati/Modificati:
- `frontend/src/app/dashboard/admin/layout.tsx` (nuovo)
- `frontend/src/app/dashboard/responsabile/layout.tsx` (nuovo)
- `frontend/src/app/dashboard/laminatore/layout.tsx` (nuovo)
- `frontend/src/app/dashboard/autoclavista/layout.tsx` (nuovo)
- `frontend/src/app/dashboard/shared/layout.tsx` (nuovo)
- `frontend/src/app/dashboard/layout.tsx` (aggiornato sidebar)
- `docs/struttura-ruoli.md` (nuova documentazione)
- `docs/changelog.md` (documentazione aggiornamenti)

#### Effetti sulla UI e UX
- Navigazione più intuitiva con pagine organizzate per ruolo
- Sidebar dinamica con sezioni specifiche per competenze
- Mantenimento completa funzionalità esistente
- Miglioramento organizzazione visuale contenuti
- Preparazione per future espansioni funzionalità per ruolo

#### Note di Migrazione
- **URL Aggiornati**: Tutti i percorsi sono stati aggiornati per riflettere la nuova struttura
- **Compatibilità**: Mantenuta piena compatibilità funzionale
- **API**: Nessuna modifica agli endpoint backend richiesta
- **Componenti**: Tutti i componenti esistenti mantenuti e funzionanti

---

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

## [v1.6.0] - Riorganizzazione Struttura per Ruoli

### [2024-12-26 - Riorganizzazione Completa Dashboard per Ruoli]
- **Completato**: Riorganizzazione completa della struttura dashboard basata sui ruoli utente
- **Obiettivo**: Migliorare organizzazione, manutenibilità e scalabilità del codice

#### Nuova Struttura Directory
- **Directory per Ruolo**: Creazione di directory specifiche per ogni ruolo (admin/, responsabile/, laminatore/, autoclavista/)
- **Directory Condivise**: Centralizzazione pagine condivise in shared/ (catalog/, odl/)
- **Layout Gerarchici**: Implementazione layout specifici per ogni ruolo che ereditano dal layout principale

#### Mappatura Pagine per Ruolo

**ADMIN (Accesso Completo)**:
- `impostazioni/` → `admin/impostazioni/` - Configurazioni di sistema

**RESPONSABILE (Gestione e Supervisione)**:
- `reports/` → `responsabile/reports/` - Reports e analytics
- `odl/monitoring/` → `responsabile/odl-monitoring/` - Monitoraggio ODL tempo reale
- `catalog/statistiche/` → `responsabile/statistiche/` - Statistiche catalogo

**LAMINATORE (Produzione)**:
- `parts/` → `laminatore/parts/` - Gestione parti
- `tools/` → `laminatore/tools/` - Tools e stampi
- `produzione/` → `laminatore/produzione/` - Operazioni produzione
- `tempi/` → `laminatore/tempi/` - Tempi e performance

**AUTOCLAVISTA (Autoclave)**:
- `nesting/` → `autoclavista/nesting/` - Gestione nesting
- `autoclavi/` → `autoclavista/autoclavi/` - Controllo autoclavi
- `cicli-cura/` → `autoclavista/cicli-cura/` - Cicli di cura
- `schedule/` → `autoclavista/schedule/` - Scheduling produzione

**CONDIVISE (Tutti i Ruoli)**:
- `catalog/` → `shared/catalog/` - Catalogo parti (escluse statistiche)
- `odl/` → `shared/odl/` - Gestione ODL (escluso monitoring)

#### Aggiornamenti Tecnici

**Sidebar Dinamica**:
- Aggiornamento configurazione `sidebarSections` con nuovi percorsi
- Aggiunta sezione "Laminazione" per tempi e performance
- Mantenimento filtri per ruolo esistenti

**Layout System**:
- Creazione layout specifici per ogni directory ruolo
- Ereditarietà dal layout principale del dashboard
- Mantenimento funzionalità sidebar dinamica

**Routing**:
- Aggiornamento tutti i link interni per nuovi percorsi
- Mantenimento sistema routing dinamico esistente
- Compatibilità con dashboard per ruolo esistenti

#### Vantaggi Implementati

**Organizzazione**:
- Struttura logica e intuitiva per ruoli
- Separazione chiara delle responsabilità
- Facilità di navigazione e manutenzione

**Manutenibilità**:
- Codice organizzato per competenze
- Facile aggiunta nuove funzionalità per ruolo
- Isolamento modifiche per ruolo specifico

**Scalabilità**:
- Struttura pronta per nuovi ruoli
- Sistema di permessi granulare
- Espandibilità senza impatti su altri ruoli

**Performance**:
- Caricamento ottimizzato per ruolo
- Bundle separati per funzionalità specifiche
- Lazy loading mantenuto

#### File Creati/Modificati:
- `frontend/src/app/dashboard/admin/layout.tsx` (nuovo)
- `frontend/src/app/dashboard/responsabile/layout.tsx` (nuovo)
- `frontend/src/app/dashboard/laminatore/layout.tsx` (nuovo)
- `frontend/src/app/dashboard/autoclavista/layout.tsx` (nuovo)
- `frontend/src/app/dashboard/shared/layout.tsx` (nuovo)
- `frontend/src/app/dashboard/layout.tsx` (aggiornato sidebar)
- `docs/struttura-ruoli.md` (nuova documentazione)
- `docs/changelog.md` (documentazione aggiornamenti)

#### Effetti sulla UI e UX
- Navigazione più intuitiva con pagine organizzate per ruolo
- Sidebar dinamica con sezioni specifiche per competenze
- Mantenimento completa funzionalità esistente
- Miglioramento organizzazione visuale contenuti
- Preparazione per future espansioni funzionalità per ruolo

#### Note di Migrazione
- **URL Aggiornati**: Tutti i percorsi sono stati aggiornati per riflettere la nuova struttura
- **Compatibilità**: Mantenuta piena compatibilità funzionale
- **API**: Nessuna modifica agli endpoint backend richiesta
- **Componenti**: Tutti i componenti esistenti mantenuti e funzionanti

---

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

## [v1.6.0] - Riorganizzazione Struttura per Ruoli

### [2024-12-26 - Riorganizzazione Completa Dashboard per Ruoli]
- **Completato**: Riorganizzazione completa della struttura dashboard basata sui ruoli utente
- **Obiettivo**: Migliorare organizzazione, manutenibilità e scalabilità del codice

#### Nuova Struttura Directory
- **Directory per Ruolo**: Creazione di directory specifiche per ogni ruolo (admin/, responsabile/, laminatore/, autoclavista/)
- **Directory Condivise**: Centralizzazione pagine condivise in shared/ (catalog/, odl/)
- **Layout Gerarchici**: Implementazione layout specifici per ogni ruolo che ereditano dal layout principale

#### Mappatura Pagine per Ruolo

**ADMIN (Accesso Completo)**:
- `impostazioni/` → `admin/impostazioni/` - Configurazioni di sistema

**RESPONSABILE (Gestione e Supervisione)**:
- `reports/` → `responsabile/reports/` - Reports e analytics
- `odl/monitoring/` → `responsabile/odl-monitoring/` - Monitoraggio ODL tempo reale
- `catalog/statistiche/` → `responsabile/statistiche/` - Statistiche catalogo

**LAMINATORE (Produzione)**:
- `parts/` → `laminatore/parts/` - Gestione parti
- `tools/` → `laminatore/tools/` - Tools e stampi
- `produzione/` → `laminatore/produzione/` - Operazioni produzione
- `tempi/` → `laminatore/tempi/` - Tempi e performance

**AUTOCLAVISTA (Autoclave)**:
- `nesting/` → `autoclavista/nesting/` - Gestione nesting
- `autoclavi/` → `autoclavista/autoclavi/` - Controllo autoclavi
- `cicli-cura/` → `autoclavista/cicli-cura/` - Cicli di cura
- `schedule/` → `autoclavista/schedule/` - Scheduling produzione

**CONDIVISE (Tutti i Ruoli)**:
- `catalog/` → `shared/catalog/` - Catalogo parti (escluse statistiche)
- `odl/` → `shared/odl/` - Gestione ODL (escluso monitoring)

#### Aggiornamenti Tecnici

**Sidebar Dinamica**:
- Aggiornamento configurazione `sidebarSections` con nuovi percorsi
- Aggiunta sezione "Laminazione" per tempi e performance
- Mantenimento filtri per ruolo esistenti

**Layout System**:
- Creazione layout specifici per ogni directory ruolo
- Ereditarietà dal layout principale del dashboard
- Mantenimento funzionalità sidebar dinamica

**Routing**:
- Aggiornamento tutti i link interni per nuovi percorsi
- Mantenimento sistema routing dinamico esistente
- Compatibilità con dashboard per ruolo esistenti

#### Vantaggi Implementati

**Organizzazione**:
- Struttura logica e intuitiva per ruoli
- Separazione chiara delle responsabilità
- Facilità di navigazione e manutenzione

**Manutenibilità**:
- Codice organizzato per competenze
- Facile aggiunta nuove funzionalità per ruolo
- Isolamento modifiche per ruolo specifico

**Scalabilità**:
- Struttura pronta per nuovi ruoli
- Sistema di permessi granulare
- Espandibilità senza impatti su altri ruoli

**Performance**:
- Caricamento ottimizzato per ruolo
- Bundle separati per funzionalità specifiche
- Lazy loading mantenuto

#### File Creati/Modificati:
- `frontend/src/app/dashboard/admin/layout.tsx` (nuovo)
- `frontend/src/app/dashboard/responsabile/layout.tsx` (nuovo)
- `frontend/src/app/dashboard/laminatore/layout.tsx` (nuovo)
- `frontend/src/app/dashboard/autoclavista/layout.tsx` (nuovo)
- `frontend/src/app/dashboard/shared/layout.tsx` (nuovo)
- `frontend/src/app/dashboard/layout.tsx` (aggiornato sidebar)
- `docs/struttura-ruoli.md` (nuova documentazione)
- `docs/changelog.md` (documentazione aggiornamenti)

#### Effetti sulla UI e UX
- Navigazione più intuitiva con pagine organizzate per ruolo
- Sidebar dinamica con sezioni specifiche per competenze
- Mantenimento completa funzionalità esistente
- Miglioramento organizzazione visuale contenuti
- Preparazione per future espansioni funzionalità per ruolo

#### Note di Migrazione
- **URL Aggiornati**: Tutti i percorsi sono stati aggiornati per riflettere la nuova struttura
- **Compatibilità**: Mantenuta piena compatibilità funzionale
- **API**: Nessuna modifica agli endpoint backend richiesta
- **Componenti**: Tutti i componenti esistenti mantenuti e funzionanti

---

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