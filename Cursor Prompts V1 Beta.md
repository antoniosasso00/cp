# 🧠 Prompt Cursor – CarbonPilot v1.0.0-beta

Ogni prompt è autonomo e pensato per lo sviluppo **in locale**, senza Docker. Includono validazione e debug.

---

## ✅ Fase 1 – Refactoring e Struttura Ruoli

### 🎯 Prompt 1.1 – Creazione pagina selezione ruolo

```md
Crea una pagina `/select-role` dove l’utente può scegliere tra i ruoli: Admin, Responsabile, Laminatore, Autoclavista. Salva la scelta nel `localStorage`. Al caricamento dell'app, se non è presente il ruolo in `localStorage`, reindirizza alla pagina di selezione. Crea un context React globale `useUserRole()` che restituisce ruolo e funzione di aggiornamento. La scelta deve sopravvivere al refresh.

Validazione:
- Al primo accesso viene mostrata la pagina /select-role
- Al refresh il ruolo resta salvato e accessibile
- Il ruolo è disponibile globalmente via hook
```

### 🎯 Prompt 1.2 – Sidebar e routing basato sul ruolo

```md
Modifica il layout dell’applicazione per mostrare una sidebar diversa in base al ruolo ottenuto dal context. Blocca l’accesso alle route non autorizzate (es. con Redirect). Crea un oggetto di configurazione `routesPerRole` con componenti visibili per ciascun ruolo. Mostra una sidebar minima al Laminatore, media all’Autoclavista, completa all’Admin e al Responsabile.

Validazione:
- Ogni ruolo vede solo le pagine autorizzate
- Tentare di accedere a una route non valida forza redirect
- Sidebar cambia correttamente in base al ruolo selezionato
```

### 🎯 Prompt 1.3 – Pulizia file e componenti inutili

```md
Effettua una pulizia del progetto rimuovendo:
- Componenti non usati
- Pagine obsolete
- File con `import` mai usati
Conserva solo i file attivi, `seed_test_data.py`, `snapshot_structure.py`, `debug_local.py`.

Validazione:
- Build frontend funziona senza warning
- Importazioni pulite e coerenti
- Nessun componente inutilizzato
```

---

## ✅ Fase 2 – Nesting e Autoclavi

### 🎯 Prompt 2.1 – Aggiunta peso e materiale ai Tool

```md
Aggiorna modello SQLAlchemy, schema Pydantic, form frontend e API per i Tool. Aggiungi i campi:
- `peso_kg: float`
- `materiale: str`
Entrambi devono essere editabili. Visualizza questi dati anche nella tabella tools.

Validazione:
- Posso creare/modificare un Tool con peso/materiale
- I campi appaiono nel form e in tabella
- I dati sono salvati correttamente nel DB
```

### 🎯 Prompt 2.2 – Aggiunta limiti di carico e superficie piano 2 alle autoclavi

```md
Modifica modello Autoclave per includere:
- `carico_massimo_kg: float`
- `superficie_piano_2_cm2: Optional[float]`
Aggiorna API e form. Questi campi devono essere validati nel backend.

Validazione:
- Creazione e modifica autoclave con i nuovi campi
- Superficie piano 2 può essere nulla
- I dati compaiono correttamente nel form e in tabella
```

### 🎯 Prompt 2.3 – Nesting a 2 piani con logica di peso e dimensione

```md
Modifica algoritmo di nesting OR-Tools:
- Priorità agli stampi più pesanti e grandi nel piano basso
- Riempimento dei piani dagli estremi opposti
- Superficie piano 2 letta da `superficie_piano_2_cm2`
- Salvataggio nesting in stato "sospeso"
- Aggiungi campo `status` nel modello NestingResult con valori: `sospeso`, `confermato`, `eseguito`

Validazione:
- Nesting propone due piani distinti con logica corretta
- I nesting sospesi restano accessibili e modificabili
- Il carico complessivo è inferiore al limite massimo dell’autoclave
```

---

## ✅ Fase 3 – Produzione e Avanzamento ODL

### 🎯 Prompt 3.1 – Visualizzazione avanzata stato ODL

```md
Nella pagina Produzione, crea una visualizzazione grafica dell’avanzamento ODL con:
- Segmenti colorati per stato
- Tooltip con tempi e nome stato
- Layout tipo Gantt o barra orizzontale

Validazione:
- Ogni ODL mostra il proprio stato in colore
- Hover mostra informazioni corrette
- Componente è responsive e coerente con UI
```

### 🎯 Prompt 3.2 – Storico tempi produzione e esportazione

```md
Traccia in automatico i tempi trascorsi tra ogni cambio stato di un ODL. Mostra una tabella cronologica con filtri per data, PN e operatore. Aggiungi pulsante “esporta CSV”. Accessibile da pagina Produzione o nuova sezione "Storico".

Validazione:
- Ogni ODL mostra data/ora per ogni stato
- Posso esportare il file CSV
- I dati restano coerenti al refresh
```

### 🎯 Prompt 3.3 – Conferma cura e generazione report

```md
Alla conferma “fine cura” di un nesting:
- Cambia stato ODL → `finito`
- Genera automaticamente report PDF con dettagli nesting, ciclo e parti coinvolte
- Salva il report nel DB e rendilo scaricabile da sezione Reports

Validazione:
- Tutti gli ODL collegati passano a "finito"
- Il report PDF è generato e scaricabile
- Il report mostra info coerenti e leggibili
```

---

## ✅ Fase 4 – Impostazioni e Utility

### 🎯 Prompt 4.1 – Spostamento sezione Impostazioni

```md
Sposta l’accesso alla pagina Impostazioni nella parte alta dell’interfaccia, vicino all’icona utente. L’icona utente deve aprire un menu con:
- Cambio ruolo
- Impostazioni
- (Futuro: Logout)

Validazione:
- Menu accessibile da ogni pagina
- Cambio ruolo forza redirect a `/select-role`
```

### 🎯 Prompt 4.2 – Backup e Ripristino DB

```md
Crea nella pagina Impostazioni due pulsanti:
- Backup DB → esporta file `.sql`
- Ripristino DB → carica `.sql` e riavvia app
Operazione disponibile solo per ruolo Admin. Mostrare messaggi di successo o errore.

Validazione:
- Backup genera un file `.sql` valido
- Ripristino carica correttamente lo schema
- Blocchi visibili se ruolo ≠ admin
```

---

## ✅ Fase 5 – Testing e Debug

### 🎯 Prompt 5.1 – Test automatici pulsanti e flussi

```md
Implementa test automatici (unit o e2e) per:
- Funzionalità dei pulsanti (es. conferma nesting, cambia stato ODL)
- Corretta validazione frontend
- Coerenza stato ODL

Validazione:
- Tutti i test passano senza errori
- I flussi principali sono coperti
```

### 🎯 Prompt 5.2 – Fix bug e ottimizzazione

```md
Analizza l’intero flusso frontend/backend e correggi:
- Nesting incompleti o duplicati
- Refresh dati mancante
- Errori 500 non gestiti
- Problemi nelle API

Validazione:
- L’app funziona senza crash
- I dati sono sincronizzati correttamente
- Tutte le operazioni CRUD sono operative
```

---

## ✅ Versione Finale v1.0.0-beta

Quando tutti i prompt sono completati e validati, procedi con:

* Commit finale `v1.0.0-beta`
* Test utente reale in locale
* Preparazione futura versione Docker
