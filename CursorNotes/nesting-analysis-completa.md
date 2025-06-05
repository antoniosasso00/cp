# 🎯 ANALISI COMPLETA MODULO NESTING MULTI-AUTOCLAVE
## CarbonPilot - Raccolta Dettagli Funzionali e Tecnici

---

## ✅ 1. ENUM DI STATO

### StatoBatchNestingEnum
**File:** `backend/models/batch_nesting.py:7-15`
```python
class StatoBatchNestingEnum(PyEnum):
    DRAFT = "draft"              # Bozza in preparazione
    SOSPESO = "sospeso"         # In attesa di conferma
    CONFERMATO = "confermato"   # Confermato e pronto per produzione
    LOADED = "loaded"           # Caricato in autoclave
    CURED = "cured"             # Cura completata
    TERMINATO = "terminato"     # Completato
```

**Descrizioni complete** (da `backend/models/batch_nesting.py:183-188`):
- `DRAFT`: "Bozza in preparazione"
- `SOSPESO`: "In attesa di conferma" (stato default)
- `CONFERMATO`: "Confermato e pronto per produzione"
- `LOADED`: "Caricato in autoclave"
- `CURED`: "Cura completata"
- `TERMINATO`: "Completato"

### StatoAutoclaveEnum
**File:** `backend/models/autoclave.py:6-11`
```python
class StatoAutoclaveEnum(str, PyEnum):
    DISPONIBILE = "DISPONIBILE"    # Autoclave operativa e libera
    IN_USO = "IN_USO"             # Autoclave in funzione
    MANUTENZIONE = "MANUTENZIONE" # In manutenzione programmata
    GUASTO = "GUASTO"             # Guasta e non utilizzabile
    SPENTA = "SPENTA"             # Spenta manualmente
```

### StatoODL
❌ **Non esiste un enum StatoODL specifico**. Gli ODL utilizzano campi stringa per lo stato (es. `status: String` nei modelli).

---

## ✅ 2. TOOL, TOOL_SIMPLE & PARTE

### Differenza Tool vs ToolSimple

**Tool** (`backend/models/tool.py`):
- Modello **esteso** con campi aggiuntivi per nesting multi-piano
- Campi: `peso`, `materiale`, relazioni con `Parte`
- Utilizzato nella **logica di nesting** dove serve peso e materiale

**ToolSimple** (`backend/models/tool_simple.py`):
- Modello **compatibilità** con database esistente
- Solo campi base: `part_number_tool`, `descrizione`, `lunghezza_piano`, `larghezza_piano`
- Proprietà calcolate: `peso` (default 10.0), `stato` (da `disponibile`)
- Utilizzato nel **frontend** per visualizzazione semplificata

### Relazione Parte → Tool → Ciclo di Cura
```
Parte (componente fisico)
  ↓ (many-to-many via parte_tool_association)
Tool (stampo/attrezzatura)
  ↓ (one-to-many)
ODL (ordine di lavorazione)
  ↓ (aggregazione in)
BatchNesting
  ↓ (associato a)
Autoclave → Ciclo di Cura
```

---

## ✅ 3. SOLVER & ALGORITMO DI NESTING

### Posizione del Solver
**File principale:** `backend/services/nesting/solver.py`
**Service wrapper:** `backend/services/nesting_service.py`

### Tecnologie Utilizzate
- **OR-Tools CP-SAT**: algoritmo principale di ottimizzazione
- **Fallback greedy**: Bottom-Left First-Fit Decreasing (BL-FFD)
- **Euristica RRGH**: Ruin-&-Recreate Goal-Driven per +5-10% area

### Algoritmo Multi-Autoclave
**Classe:** `NestingModel` in `backend/services/nesting/solver.py:107`

**Funzionalità principali v1.4.17-DEMO:**
1. **Rotazione 90°** integrata nei modelli OR-Tools
2. **Timeout adaptivo**: min(90s, 2s × n_pieces)
3. **Vincoli pezzi pesanti**: nella metà inferiore (y ≥ H/2)
4. **Objective ottimizzato**: Z = 0.8·area_pct + 0.2·vacuum_util_pct
5. **Rilevamento overlap**: con correzione automatica BL-FFD

### Determinazione Posizioni
**Metodo:** `_solve_cpsat()` in `backend/services/nesting/solver.py:349`

**Variabili di decisione:**
- `included[tool_id]`: tool incluso nel layout
- `x[tool_id]`, `y[tool_id]`: posizione
- `rotated[tool_id]`: rotazione 90°
- Intervalli separati per orientamenti normale/ruotato

**Vincoli:**
- Non sovrapposizione (via `AddNoOverlap2D`)
- Limiti autoclave
- Capacità linee vuoto
- Posizionamento pezzi pesanti

---

## ✅ 4. BATCH NESTING: CICLO DI VITA

### Stati e Transizioni
```
DRAFT → SOSPESO → CONFERMATO → LOADED → CURED → TERMINATO
   ↑        ↑          ↑         ↑       ↑       ↑
[creazione][default][approvazione][carico][cura][fine]
```

### Autorizzazioni Modifica Stati
**File:** `backend/api/routers/batch_nesting.py:648-649`
- `SOSPESO → CONFERMATO`: richiede conferma esplicita
- `CONFERMATO → LOADED`: operatori produzione
- `LOADED → CURED`: automatico/manuale dopo ciclo
- Solo batch in stato `SOSPESO` possono essere modificati

### Gestione Ciclo Completo
**Campi tracciabilità:**
- `creato_da_utente`, `creato_da_ruolo`
- `confermato_da_utente`, `confermato_da_ruolo`
- `data_conferma`, `data_completamento`
- `durata_ciclo_minuti` (calcolata automaticamente)

---

## ✅ 5. CANVAS & FRONTEND

### File Principale Canvas
**File:** `frontend/src/modules/nesting/result/[batch_id]/NestingCanvas.tsx`

### Tecnologie Rendering
- **React Konva** (via wrapper `CanvasWrapper`)
- **SVG Ground-Truth Overlay** per debug
- **CSS Transform scaling** (non stage.scale())

### Funzionalità Supportate
✅ **Zoom**: controlli ZoomIn/ZoomOut
✅ **Visualizzazione metriche**: efficienza, area, peso
✅ **Drag & drop**: NO (solo visualizzazione)
✅ **Salvataggio layout**: tramite `configurazione_json`
❌ **Multi-piano**: DA RIMUOVERE (legacy)

### Componenti Correlati
- `frontend/src/modules/nesting/preview/page.tsx`: preview pre-conferma
- `frontend/src/app/dashboard/curing/nesting/preview/page.tsx`: duplicato da consolidare

---

## ✅ 6. METRICHE DI EFFICIENZA

### Definizione Metriche
**File:** `backend/models/batch_nesting.py:115-121`

**Metriche principali:**
- `area_pct`: Percentuale area utilizzata vs area totale autoclave
- `vacuum_util_pct`: Percentuale linee vuoto utilizzate
- `efficiency_score`: Formula Z = 0.7·area_pct + 0.3·vacuum_util_pct
- `efficiency_level`: green (≥80%), yellow (≥60%), red (<60%)

### Calcoli Implementati
**Proprietà calcolate in BatchNesting:**
```python
@property
def area_pct(self) -> float:
    """area_utilizzata_mm² / area_totale_autoclave_mm² * 100"""
    
@property  
def efficiency_score(self) -> float:
    """0.7·area_pct + 0.3·vacuum_util_pct"""
```

### Utilizzo Attuale
✅ **Già implementate** e utilizzate per:
- Valutazione batch nesting
- Classificazione livelli efficienza
- Dashboard metriche

---

## ✅ 7. INFRA & BACKGROUND

### Job Schedulati
**File:** `backend/services/schedule_service.py`
- `auto_generate_schedules()`: generazione automatica schedulazioni
- **NO** nightly_std_update specifico trovato
- **Tecnologia**: FastAPI background tasks (NO Celery/cron attualmente)

### Configurazione .env
❌ **File .env non presente** nel repository

**Chiavi minime necessarie:**
```env
# Database
DATABASE_URL=postgresql://user:pass@localhost/carbonpilot

# FastAPI
SECRET_KEY=your-secret-key
API_HOST=0.0.0.0
API_PORT=8000

# Development
DEBUG=true
LOG_LEVEL=INFO

# OR-Tools
ORTOOLS_TIMEOUT_SECONDS=90
```

---

## ✅ 8. FILE OBSOLETI

### Ricerca File Legacy
**Ricerca effettuata:** `legacy|obsolete|deprecated|TODO.*remove|old_|_old`
**Risultato:** ❌ **Nessun file legacy esplicito trovato**

### Candidati Potenziali da Verificare
- `frontend/src/app/dashboard/curing/nesting/preview/page.tsx` (duplicato di modules/nesting/preview)
- Eventuali componenti multi-piano (da rimuovere secondo richiesta)

---

## ✅ 9. DATI DI TEST

### File Seed Principali
**File:** `tools/complete_nesting_seed.py`

**Dati generati:**
- **3 autoclavi diverse** (Large, Medium, Compact)
- **Tool dimensioni variate** per test nesting
- **ODL realistici** con relazioni Parte-Tool
- **Batch di test** con vari livelli efficienza

### Test Efficienza
**File:** `backend/tests/seed_efficiency_test.py`
- Crea batch con efficienza 55% per testing
- Verifica sistema di valutazione efficienza

### Test Edge Cases
**File:** `tools/edge_tests.py`
- Scenari A-D per test robustezza
- Validazione con vari padding e configurazioni

---

## ✅ 10. OUTPUT JSON DI NESTING

### Struttura Configurazione Layout
**Schema:** `backend/schemas/batch_nesting.py:44-70`

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
      "peso": 25.5,
      "rotated": false,
      "part_number": "PT-001",
      "tool_nome": "Tool ABC"
    },
    {
      "odl_id": 2,
      "x": 320.0,
      "y": 150.0,
      "width": 150.0,
      "height": 180.0,
      "peso": 30.2,
      "rotated": true,
      "part_number": "PT-002", 
      "tool_nome": "Tool XYZ"
    }
  ],
  "plane_assignments": {
    "1": 1,
    "2": 1
  }
}
```

### Risposta Endpoint Solve
**Schema:** `NestingSolveResponse` in `backend/schemas/batch_nesting.py:278-312`

```json
{
  "success": true,
  "message": "Nesting completato: 15 ODL posizionati, efficienza 84.2%",
  "positioned_tools": [
    {
      "odl_id": 1,
      "tool_id": 101,
      "x": 100.0,
      "y": 150.0,
      "width": 200.0,
      "height": 100.0,
      "rotated": false,
      "plane": 1,
      "weight_kg": 25.5
    }
  ],
  "excluded_odls": [
    {
      "odl_id": 99,
      "reason": "Dimensioni troppo grandi per autoclave",
      "part_number": "PT-LARGE",
      "tool_dimensions": "500x600mm"
    }
  ],
  "metrics": {
    "area_utilization_pct": 84.2,
    "vacuum_util_pct": 75.0,
    "efficiency_score": 81.6,
    "weight_utilization_pct": 65.3,
    "time_solver_ms": 1250.0,
    "fallback_used": false,
    "heuristic_iters": 3,
    "algorithm_status": "CP-SAT_OPTIMAL",
    "rotation_used": true,
    "pieces_positioned": 15,
    "pieces_excluded": 2
  },
  "autoclave_info": {
    "id": 1,
    "nome": "Autoclave-Large-001",
    "width": 1500.0,
    "height": 2500.0,
    "max_load_kg": 800.0,
    "num_linee_vuoto": 12
  }
}
```

---

## 📋 RIEPILOGO TECNICO

### Core Components
1. **Solver**: OR-Tools CP-SAT + Fallback BL-FFD
2. **Models**: BatchNesting, Tool/ToolSimple, Autoclave
3. **Frontend**: React Konva canvas con wrapper
4. **API**: FastAPI con schema Pydantic v2

### Key Features v1.4.17-DEMO
- ✅ Rotazione 90° integrata
- ✅ Multi-autoclave optimization
- ✅ Efficienza formula: 0.8·area + 0.2·vacuum
- ✅ Timeout adaptivo
- ✅ Overlap detection & correction

### Ready for Refactoring
- Schema modelli ben definiti
- Separation of concerns (Tool vs ToolSimple)
- Metriche efficienza implementate
- Test data disponibili 