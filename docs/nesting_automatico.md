# 🔧 Sistema di Nesting Automatico - Piano Singolo

## 📋 Panoramica

Il sistema di nesting automatico ottimizza automaticamente il posizionamento degli ODL (Ordini di Lavoro) nelle autoclavi, considerando:

- **Compatibilità dei cicli di cura**: Gli ODL vengono raggruppati per ciclo compatibile
- **Dimensioni dei tool**: Calcolo automatico delle dimensioni e del peso
- **Capacità delle autoclavi**: Verifica dei limiti di area e peso
- **Efficienza di utilizzo**: Ottimizzazione dello spazio disponibile

## 🏗️ Architettura

### Backend

#### Moduli Principali

1. **`nesting_optimizer/`** - Modulo di ottimizzazione
   - `auto_nesting.py` - Algoritmi di ottimizzazione
   - `__init__.py` - Esportazioni del modulo

2. **`api/routers/nesting.py`** - API REST
   - Endpoint per generazione automatica
   - Preview degli ODL disponibili
   - Gestione dei risultati

3. **`schemas/nesting.py`** - Schemi Pydantic
   - Validazione dei dati di input/output
   - Tipizzazione forte

#### Algoritmo di Ottimizzazione

```python
class NestingOptimizer:
    def get_compatible_odl_groups(self) -> Dict[str, List[ODL]]
    def get_available_autoclaves(self) -> List[Autoclave]
    def optimize_single_plane_nesting(self, odl_group, autoclave) -> Dict
```

**Processo di ottimizzazione:**

1. **Raggruppamento**: ODL raggruppati per `categoria_sottocategoria`
2. **Ordinamento**: Per priorità decrescente, poi per area decrescente
3. **Algoritmo Greedy**: Selezione ODL fino a saturazione spazio/peso
4. **Calcolo efficienza**: Percentuale di utilizzo dell'autoclave

### Frontend

#### Componenti Principali

1. **`NestingPreview`** - Anteprima ODL disponibili
2. **`AutomaticNestingResults`** - Visualizzazione risultati
3. **Pagina principale** - Interfaccia a tab

#### Interfaccia Utente

- **Tab "Preview Automatico"**: Mostra ODL raggruppati per ciclo
- **Tab "Genera Automatico"**: Configurazione e avvio ottimizzazione
- **Tab "Risultati"**: Visualizzazione nesting generati

## 🔄 Flusso di Lavoro

### 1. Preview degli ODL

```typescript
// Carica preview degli ODL disponibili
const preview = await nestingApi.getPreview({
  include_excluded: true,
  group_by_cycle: true
})
```

**Informazioni mostrate:**
- ODL raggruppati per ciclo di cura
- Statistiche per gruppo (area, peso, numero ODL)
- Autoclavi compatibili per ogni gruppo

### 2. Generazione Automatica

```typescript
// Genera nesting automatico
const result = await nestingApi.generateAutomatic({
  force_regenerate: false,
  max_autoclaves: undefined,
  priority_threshold: undefined
})
```

**Opzioni disponibili:**
- `force_regenerate`: Sovrascrive nesting in bozza esistenti
- `max_autoclaves`: Limite numero autoclavi da utilizzare
- `priority_threshold`: Soglia minima priorità ODL

### 3. Risultati

**Per ogni nesting generato:**
- ID univoco e autoclave assegnata
- ODL inclusi/esclusi con motivazioni
- Statistiche di efficienza
- Stato "Bozza" per revisione

## 📊 Modelli di Dati

### NestingResult

```python
class NestingResult:
    autoclave_id: int
    odl_ids: List[int]           # ODL inclusi
    odl_esclusi_ids: List[int]   # ODL esclusi
    motivi_esclusione: List[str] # Motivazioni esclusione
    stato: str                   # "Bozza", "Confermato", etc.
    area_utilizzata: float       # Area utilizzata in cm²
    peso_totale_kg: float        # Peso totale in kg
    efficienza_totale: float     # Percentuale utilizzo
```

### Calcolo Dimensioni Tool

```python
def calculate_tool_dimensions(self, odl: ODL) -> Tuple[float, float, float]:
    width = odl.tool.larghezza or 100.0    # mm
    length = odl.tool.lunghezza or 100.0   # mm
    
    # Peso stimato: volume * densità
    volume_cm3 = (width * length * 10) / 1000  # Spessore 10mm
    peso_kg = volume_cm3 * 0.002               # Densità 2g/cm³
    
    return (width, length, peso_kg)
```

## 🎯 Criteri di Ottimizzazione

### Compatibilità Cicli

Gli ODL sono compatibili se hanno stesso:
- `categoria` del catalogo parte
- `sotto_categoria` del catalogo parte

### Priorità di Selezione

1. **Priorità ODL** (campo `priorita`, più alto = più importante)
2. **Area tool** (più grande = selezionato prima)

### Vincoli di Capacità

- **Area**: `Σ(larghezza × lunghezza) ≤ autoclave.area_piano`
- **Peso**: `Σ(peso_stimato) ≤ autoclave.max_load_kg`

### Calcolo Efficienza

```
efficienza = (area_utilizzata / area_totale_autoclave) × 100
```

**Classificazione:**
- ≥ 80%: Ottima efficienza
- ≥ 60%: Buona efficienza  
- < 60%: Efficienza migliorabile

## 🔧 API Endpoints

### POST `/nesting/automatic`

Genera nesting automatico per tutti gli ODL in attesa.

**Request:**
```json
{
  "force_regenerate": false,
  "max_autoclaves": 5,
  "priority_threshold": 2
}
```

**Response:**
```json
{
  "success": true,
  "message": "Generati 3 nesting automatici",
  "nesting_results": [...],
  "summary": {
    "total_nesting_created": 3,
    "total_odl_processed": 15,
    "total_odl_excluded": 2,
    "autoclavi_utilizzate": 3
  }
}
```

### GET `/nesting/preview`

Anteprima ODL disponibili raggruppati per ciclo.

**Response:**
```json
{
  "success": true,
  "message": "Preview generata per 4 gruppi di ODL",
  "odl_groups": [...],
  "available_autoclaves": [...],
  "total_odl_pending": 17
}
```

### GET `/nesting/{id}`

Dettagli completi di un nesting specifico.

### PUT `/nesting/{id}/status`

Aggiorna stato di un nesting (es. da "Bozza" a "Confermato").

## 🚀 Utilizzo

### 1. Accesso all'Interfaccia

Naviga su `/nesting` e seleziona il tab **"Preview Automatico"** per vedere gli ODL disponibili.

### 2. Configurazione

Nel tab **"Genera Automatico"**:
- Configura le opzioni di base
- Usa "Opzioni Avanzate" per parametri specifici

### 3. Generazione

Clicca **"Genera Nesting Automatico"** per avviare l'ottimizzazione.

### 4. Revisione Risultati

Nel tab **"Risultati"**:
- Visualizza i nesting generati
- Controlla efficienza e statistiche
- Conferma o modifica i nesting in bozza

## 🔍 Monitoraggio e Debug

### Log di Sistema

```python
logger.info(f"Trovati {len(groups)} gruppi di ODL compatibili")
logger.info(f"Processando gruppo {ciclo_key} con {len(odl_list)} ODL")
logger.info(f"Creato nesting {nesting_result.id} per autoclave {autoclave.nome}")
```

### Gestione Errori

- **Nessun ODL in attesa**: Messaggio informativo
- **Nessuna autoclave disponibile**: Blocco operazione
- **Errori di calcolo**: Rollback transazione DB

## 📈 Metriche di Performance

- **Tempo di elaborazione**: Algoritmo greedy O(n log n)
- **Efficienza media**: Target > 70%
- **ODL processati**: Tracking in summary response
- **Utilizzo autoclavi**: Ottimizzazione distribuzione carico

## 🔮 Sviluppi Futuri

1. **Algoritmi avanzati**: Implementazione OR-Tools per ottimizzazione globale
2. **Nesting su due piani**: Estensione per autoclavi multi-piano
3. **Machine Learning**: Predizione tempi e ottimizzazione basata su storico
4. **Visualizzazione 2D**: Layout grafico del posizionamento tool 