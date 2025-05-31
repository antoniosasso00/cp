# 📋 MODIFICHE SCHEMA DATABASE - CarbonPilot

## 🆕 Interfaccia Frontend Nesting - v1.1.2-DEMO
**Data implementazione**: 2025-01-27

### 🎨 Nuove Pagine Frontend

#### 📄 Pagina: `/dashboard/curing/nesting`
Interfaccia principale per la creazione di nuovi nesting automatici.

**Funzionalità implementate**:
- ✅ Selezione ODL in stato "Attesa Cura" con checkbox
- ✅ Selezione autoclavi disponibili con checkbox  
- ✅ Pulsanti "Seleziona Tutti" / "Deseleziona Tutti"
- ✅ Configurazione parametri nesting (padding, distanza, priorità area, accorpamento)
- ✅ Validazione input e messaggi di errore
- ✅ Generazione nesting con loading state
- ✅ Navigazione automatica ai risultati

**Dati visualizzati per ODL**:
- Part Number e descrizione breve
- Tool associato e dimensioni
- Ciclo di cura (se presente)
- Numero valvole richieste
- Priorità ODL

**Dati visualizzati per Autoclavi**:
- Nome, codice e dimensioni
- Temperatura e pressione massime
- Carico massimo e linee vuoto
- Supporto piano secondario

#### 📄 Pagina: `/dashboard/curing/nesting/result/[batch_id]`
Pagina di visualizzazione risultati nesting generato.

**Funzionalità implementate**:
- ✅ Caricamento dati batch nesting
- ✅ Visualizzazione informazioni generali
- ✅ Parametri utilizzati per la generazione
- ✅ Statistiche risultato (se disponibili)
- ✅ Lista ODL inclusi nel nesting
- ✅ Azioni: download report, nuovo nesting
- ✅ Placeholder per canvas grafico 2D (prossima versione)

### 🔧 Endpoint API Temporaneo

#### 📄 Router: `nesting_temp.py`
Endpoint temporaneo per supportare l'interfaccia frontend.

**Endpoint**: `POST /api/v1/nesting/genera`

**Request Body**:
```typescript
{
  odl_ids: string[],
  autoclave_ids: string[],
  parametri: {
    padding_mm: number,
    min_distance_mm: number,
    priorita_area: boolean,
    accorpamento_odl: boolean
  }
}
```

**Response**:
```typescript
{
  batch_id: string,
  message: string,
  odl_count: number,
  autoclave_count: number
}
```

**Logica implementata**:
- ✅ Validazione input (ODL e autoclavi obbligatori)
- ✅ Conversione richiesta in BatchNesting
- ✅ Utilizzo prima autoclave selezionata
- ✅ Generazione nome batch automatico
- ✅ Logging operazioni e errori
- ✅ Gestione errori con messaggi dettagliati

### 🎯 Sidebar Navigation

#### 📄 Aggiornamento: `dashboard/layout.tsx`
Aggiunto link "Nesting" alla sezione CURING.

**Configurazione**:
```typescript
{
  title: "Nesting",
  href: "/dashboard/curing/nesting",
  icon: <LayoutGrid className="h-4 w-4" />,
  roles: ['ADMIN', 'Curing']
}
```

### 🔄 Proxy API Configuration

#### 📄 File: `next.config.js`
Configurazione proxy già esistente per reindirizzare `/api/*` al backend FastAPI.

**Configurazione**:
```javascript
async rewrites() {
  return [
    {
      source: '/api/:path*',
      destination: 'http://localhost:8000/api/:path*',
    },
  ]
}
```

### 📱 Componenti UI Utilizzati

**Componenti shadcn/ui**:
- ✅ `Card`, `CardContent`, `CardHeader`, `CardTitle`, `CardDescription`
- ✅ `Button` con varianti e stati loading
- ✅ `Checkbox` per selezioni multiple
- ✅ `Input` per parametri numerici
- ✅ `Switch` per opzioni boolean
- ✅ `Badge` per stati e informazioni
- ✅ `Separator` per divisioni visive
- ✅ `useToast` per notifiche utente

**Icone Lucide React**:
- ✅ `Package`, `Flame`, `LayoutGrid` per sezioni
- ✅ `Loader2`, `CheckCircle2`, `AlertCircle` per stati
- ✅ `ArrowLeft`, `Download`, `RefreshCw` per azioni

### 🎨 Design Pattern Implementati

#### 📄 State Management
- ✅ React hooks per gestione stato locale
- ✅ Separazione stato dati/UI/loading
- ✅ Gestione errori con fallback graceful

#### 📄 Data Fetching
- ✅ Fetch API con async/await
- ✅ Gestione errori HTTP con try/catch
- ✅ Loading states e error boundaries

#### 📄 User Experience
- ✅ Feedback visivo per tutte le azioni
- ✅ Validazione input lato client
- ✅ Messaggi di errore informativi
- ✅ Navigazione intuitiva con breadcrumb

### 🚀 Prossimi Sviluppi

#### 📄 Canvas Grafico 2D
- 🔄 Visualizzazione layout nesting interattivo
- 🔄 Drag & drop per riposizionamento tool
- 🔄 Zoom e pan per navigazione
- 🔄 Export immagine layout

#### 📄 Algoritmo Nesting Reale
- 🔄 Sostituzione endpoint temporaneo
- 🔄 Implementazione algoritmi ottimizzazione
- 🔄 Calcolo statistiche reali
- 🔄 Gestione vincoli complessi

## 🆕 Nuove Tabelle Aggiunte

### 📄 Tabella: `batch_nesting`
**Data aggiunta**: 2025-01-27

Nuova tabella per raggruppare i nesting con parametri salvati e configurazioni complete.

#### 📋 Campi:
- **id**: String(36) | PK | INDEX | NOT NULL
  📝 UUID identificativo univoco del batch
- **nome**: String(255) | NULLABLE
  📝 Nome opzionale del batch assegnabile dall'operatore
- **stato**: Enum(StatoBatchNestingEnum) | NOT NULL | DEFAULT=sospeso
  📝 Stato corrente del batch nesting (sospeso, confermato, terminato)
- **autoclave_id**: Integer | FK -> autoclavi.id | NOT NULL | INDEX
  📝 ID dell'autoclave per cui è stato generato il batch
- **odl_ids**: JSON | DEFAULT=[]
  📝 Lista degli ID degli ODL inclusi nel batch nesting
- **configurazione_json**: JSON | NULLABLE
  📝 Configurazione completa del layout nesting generato dal frontend (React canvas)
- **parametri**: JSON | DEFAULT={}
  📝 Parametri utilizzati per la generazione del nesting (padding, margini, vincoli, etc.)
- **numero_nesting**: Integer | DEFAULT=0
  📝 Numero totale di nesting results contenuti nel batch
- **peso_totale_kg**: Integer | DEFAULT=0
  📝 Peso totale aggregato di tutti i nesting del batch in kg
- **area_totale_utilizzata**: Integer | DEFAULT=0
  📝 Area totale utilizzata aggregata in cm²
- **valvole_totali_utilizzate**: Integer | DEFAULT=0
  📝 Numero totale di valvole utilizzate nel batch
- **note**: Text | NULLABLE
  📝 Note aggiuntive sul batch nesting
- **creato_da_utente**: String(100) | NULLABLE
  📝 ID dell'utente che ha creato il batch
- **creato_da_ruolo**: String(50) | NULLABLE
  📝 Ruolo dell'utente che ha creato il batch
- **confermato_da_utente**: String(100) | NULLABLE
  📝 ID dell'utente che ha confermato il batch
- **confermato_da_ruolo**: String(50) | NULLABLE
  📝 Ruolo dell'utente che ha confermato il batch
- **data_conferma**: DateTime | NULLABLE
  📝 Data e ora di conferma del batch
- **created_at**: DateTime | NOT NULL | DEFAULT=now()
- **updated_at**: DateTime | NOT NULL | DEFAULT=now()

#### 🔗 Relazioni:
- **autoclave**: one-to-one -> Autoclave (bidirectional)
- **nesting_results**: one-to-many -> NestingResult (bidirectional)

#### 📊 Indici:
- ix_batch_nesting_id (ID)
- ix_batch_nesting_autoclave_id (autoclave_id)
- ix_batch_nesting_stato (stato)
- ix_batch_nesting_created_at (created_at)

## 🔄 Tabelle Modificate

### 📄 Tabella: `nesting_results`
**Data modifica**: 2025-01-27

#### ➕ Campi Aggiunti:
- **batch_id**: String(36) | FK -> batch_nesting.id | NULLABLE | INDEX
  📝 ID del batch di cui fa parte questo nesting

#### 🔗 Nuove Relazioni:
- **batch**: one-to-one -> BatchNesting (bidirectional)

#### 📊 Nuovi Indici:
- ix_nesting_results_batch_id (batch_id)

### 📄 Tabella: `autoclavi`
**Data modifica**: 2025-01-27

#### 🔗 Nuove Relazioni:
- **batch_nesting**: one-to-many -> BatchNesting (bidirectional)

## 🆕 Nuovi Enum

### StatoBatchNestingEnum
Enum per rappresentare i vari stati di un batch nesting:
- **sospeso**: Batch in attesa di conferma
- **confermato**: Batch confermato e pronto per produzione  
- **terminato**: Batch completato

## 🛠️ Modifiche API

### 🆕 Nuove Rotte API

**Prefisso**: `/api/v1/batch_nesting`

#### Operazioni CRUD:
- **GET** `/` - Lista completa dei batch nesting (con filtri e paginazione)
- **POST** `/` - Creazione nuovo batch nesting
- **GET** `/{batch_id}` - Dettaglio singolo batch nesting
- **PUT** `/{batch_id}` - Aggiornamento batch nesting
- **DELETE** `/{batch_id}` - Eliminazione batch nesting (solo se stato=sospeso)

#### Operazioni Speciali:
- **GET** `/{batch_id}/statistics` - Statistiche dettagliate del batch

### 📝 Parametri Nesting Salvabili

I parametri di nesting vengono salvati nel campo JSON `parametri` con la seguente struttura:

```json
{
  "padding_mm": 20.0,
  "min_distance_mm": 15.0,
  "priorita_area": true,
  "accorpamento_odl": false,
  "use_secondary_plane": false,
  "max_weight_per_plane_kg": 500.0
}
```

### 🎨 Configurazione Layout Salvabile

La configurazione del layout generato dal frontend viene salvata nel campo JSON `configurazione_json`:

```json
{
  "canvas_width": 800.0,
  "canvas_height": 600.0,
  "scale_factor": 1.0,
  "tool_positions": [
    {
      "odl_id": 1,
      "x": 100.0,
      "y": 150.0,
      "width": 200.0,
      "height": 100.0,
      "rotation": 0
    }
  ],
  "plane_assignments": {"1": 1, "2": 2}
}
```

## ✅ Benefici dell'Implementazione

1. **💾 Persistenza Parametri**: I parametri usati per generare ogni nesting sono salvati e recuperabili
2. **🔄 Riproducibilità**: Possibile rigenerare nesting con gli stessi parametri
3. **📊 Tracciabilità**: Completa traccia di chi ha creato/confermato ogni batch
4. **🎯 Organizzazione**: Raggruppamento logico di più nesting correlati
5. **⚡ Performance**: Statistiche pre-calcolate per analisi rapide
6. **🔧 Flessibilità**: Supporto per parametri personalizzati e configurazioni future

## 🗄️ Implementazione Database

- **Tipo Database**: SQLite (sviluppo) / PostgreSQL (produzione)
- **ORM**: SQLAlchemy con migrazioni Alembic
- **Validazione**: Pydantic schemas per input/output
- **Logging**: Eventi di creazione/modifica tracciati in system_logs 