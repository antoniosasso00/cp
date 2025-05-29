# 🔧 Guida Integrazione Backend - Layout Visuale Nesting

## 📋 Panoramica

Questa guida documenta l'integrazione completa del backend per il sistema di layout visuale del nesting con orientamento automatico. L'implementazione collega i componenti frontend React/TypeScript alle API FastAPI per fornire dati reali e calcoli in tempo reale.

## 🏗️ Architettura Integrazione

### 📊 Flusso Dati
```
Frontend (React/TS) ↔ API Client ↔ FastAPI Endpoints ↔ Service Layer ↔ Database (SQLite)
```

### 🔄 Componenti Principali

1. **Frontend Components**: `EnhancedNestingCanvas`, `MultiNestingCanvas`
2. **API Client**: `frontend/src/lib/api/nesting-layout.ts`
3. **FastAPI Endpoints**: `backend/api/routers/nesting.py`
4. **Service Layer**: `backend/services/nesting_layout_service.py`
5. **Database Models**: Modelli esistenti + nuove colonne

## 🚀 Setup e Configurazione

### 📋 Prerequisiti

```bash
# Backend
- Python 3.8+
- FastAPI
- SQLAlchemy
- Pydantic

# Frontend  
- Node.js 18+
- Next.js 13+
- TypeScript
- React 18+
```

### 🔧 Installazione

1. **Preparazione Database**:
```bash
cd backend
python migrations/add_tool_peso_materiale.py
```

2. **Verifica Integrazione**:
```bash
python tools/validate_nesting_canvas.py
```

3. **Test API** (opzionale):
```bash
python tools/test_nesting_api_integration.py
```

## 📡 Endpoint API Implementati

### 🎨 Layout Singolo Nesting
```http
GET /api/nesting/{nesting_id}/layout
```

**Parametri Query**:
- `padding_mm`: Spaziatura tra tool (0.0-50.0mm, default: 10.0)
- `borda_mm`: Bordo dall'autoclave (0.0-100.0mm, default: 20.0)
- `rotazione_abilitata`: Abilita orientamento automatico (default: true)

**Risposta**:
```json
{
  "id": 1,
  "autoclave": {
    "id": 1,
    "nome": "Autoclave Alpha",
    "lunghezza": 1200.0,
    "larghezza_piano": 800.0,
    "temperatura_max": 180
  },
  "odl_list": [...],
  "posizioni_tool": [
    {
      "odl_id": 101,
      "x": 50.0,
      "y": 50.0,
      "width": 600.0,
      "height": 400.0,
      "rotated": false,
      "piano": 1
    }
  ],
  "area_utilizzata": 240000.0,
  "area_totale": 960000.0,
  "valvole_utilizzate": 3,
  "valvole_totali": 12,
  "stato": "In corso",
  "padding_mm": 10.0,
  "borda_mm": 20.0,
  "rotazione_abilitata": true
}
```

### 🖼️ Multi-Canvas Layout
```http
GET /api/nesting/layout/multi
```

**Parametri Query**:
- `limit`: Numero massimo nesting (1-50, default: tutti)
- `stato_filtro`: Filtra per stato ("In corso", "Schedulato", "Completato")
- `padding_mm`, `borda_mm`, `rotazione_abilitata`: Come sopra

**Risposta**:
```json
{
  "nesting_list": [...],
  "statistiche_globali": {
    "totale_nesting": 5,
    "totale_odl": 15,
    "totale_valvole": 45,
    "area_media_utilizzo": 67.5,
    "tool_ruotati_percentuale": 23.3,
    "autoclavi_utilizzate": 3,
    "stati_distribuzione": {
      "In corso": 2,
      "Schedulato": 2,
      "Completato": 1
    }
  }
}
```

### 🔄 Calcolo Orientamento
```http
POST /api/nesting/calculate-orientation
```

**Body**:
```json
{
  "tool_lunghezza": 600.0,
  "tool_larghezza": 400.0,
  "autoclave_lunghezza": 1200.0,
  "autoclave_larghezza": 800.0
}
```

**Risposta**:
```json
{
  "should_rotate": false,
  "normal_efficiency": 0.500,
  "rotated_efficiency": 0.333,
  "improvement_percentage": 0.0,
  "recommended_orientation": "Normale"
}
```

### 📊 Statistiche Layout
```http
GET /api/nesting/layout/statistics
```

**Parametri Query**:
- `giorni_precedenti`: Periodo analisi (1-365, default: 30)

## 🔧 Service Layer

### 📍 NestingLayoutService

#### Calcolo Orientamento Ottimale
```python
@staticmethod
def calculate_optimal_orientation(tool_length, tool_width, autoclave_length, autoclave_width):
    """
    Calcola l'orientamento ottimale basato su efficienza spaziale.
    
    Returns:
        dict: {
            'should_rotate': bool,
            'normal_efficiency': float,
            'rotated_efficiency': float,
            'improvement_percentage': float,
            'recommended_orientation': str
        }
    """
```

**Algoritmo**:
1. **Efficienza Normale**: `min(tool_length/autoclave_length, tool_width/autoclave_width)`
2. **Efficienza Ruotata**: `min(tool_width/autoclave_length, tool_length/autoclave_width)`
3. **Decisione**: Sceglie orientamento con efficienza maggiore
4. **Miglioramento**: `((max_eff - min_eff) / min_eff) * 100`

#### Calcolo Posizioni Tool
```python
@staticmethod
def calculate_tool_positions(nesting, padding_mm=10.0, borda_mm=20.0, rotazione_abilitata=True):
    """
    Calcola posizioni 2D dei tool con layout automatico.
    
    Args:
        nesting: Oggetto NestingResult
        padding_mm: Spaziatura tra tool
        borda_mm: Bordo dall'autoclave
        rotazione_abilitata: Abilita orientamento automatico
        
    Returns:
        List[ToolPosition]: Lista posizioni calcolate
    """
```

**Algoritmo Layout**:
1. Ordina tool per priorità (alta → bassa)
2. Per ogni tool:
   - Calcola orientamento ottimale (se abilitato)
   - Trova prima posizione disponibile
   - Considera bordi e spaziatura
   - Gestisce overflow con nuove righe

## 💻 Frontend Integration

### 🔗 API Client TypeScript

#### Funzioni Principali
```typescript
// Recupera layout singolo
export async function getNestingLayout(
  nestingId: number, 
  params: LayoutParameters
): Promise<NestingLayoutData>

// Recupera multi-canvas
export async function getMultiNestingLayout(
  params: MultiLayoutParameters
): Promise<MultiNestingLayoutData>

// Calcola orientamento
export async function calculateToolOrientation(
  request: OrientationCalculationRequest
): Promise<OrientationCalculationResponse>
```

#### Hook React Personalizzati
```typescript
// Hook per layout singolo con gestione stato
export function useNestingLayout(nestingId: number, params: LayoutParameters) {
  const [data, setData] = useState<NestingLayoutData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // Implementazione con useEffect e gestione errori
}

// Hook per multi-layout
export function useMultiNestingLayout(params: MultiLayoutParameters) {
  // Simile al precedente ma per multi-canvas
}
```

### 🎛️ Componenti Integrati

#### Pagina Test con Toggle API/Mock
```typescript
// Stati per gestione modalità
const [useRealApi, setUseRealApi] = useState(false)
const [realNestingData, setRealNestingData] = useState<any[]>([])
const [loading, setLoading] = useState(false)
const [apiError, setApiError] = useState<string | null>(null)

// Funzione caricamento dati reali
const loadRealData = async () => {
  try {
    setLoading(true)
    const multiData = await getMultiNestingLayout({...})
    const convertedData = multiData.nesting_list.map(convertApiDataToComponentFormat)
    setRealNestingData(convertedData)
    setUseRealApi(true)
  } catch (error) {
    // Fallback automatico ai dati mock
    setUseRealApi(false)
    setApiError(error.message)
  }
}
```

## 🧪 Testing e Validazione

### 📋 Script di Validazione

#### validate_nesting_canvas.py
```bash
python tools/validate_nesting_canvas.py
```

**Test Implementati**:
1. **Dimensioni Reali**: Verifica scala e adattamento tool
2. **Orientamento Automatico**: Controllo calcoli efficienza  
3. **Quote e Label**: Validazione dati completi
4. **Multi-Canvas**: Test gestione multipli nesting

#### test_nesting_api_integration.py
```bash
python tools/test_nesting_api_integration.py
```

**Test API**:
1. **Connessione Base**: Verifica disponibilità API
2. **Lista Nesting**: Test endpoint lista
3. **Multi-Canvas**: Test endpoint multi-layout
4. **Layout Singolo**: Test endpoint specifico
5. **Calcolo Orientamento**: Test algoritmo
6. **Statistiche**: Test endpoint statistiche

### ✅ Risultati Attesi
```
🎯 Test superati: 4/4 (validazione canvas)
🎯 Test superati: 6/6 (integrazione API)
🎉 Tutti i test sono stati superati!
```

## 🔒 Gestione Errori

### 🛡️ Resilienza Sistema

#### Fallback Automatico
```typescript
// Frontend gestisce automaticamente errori API
try {
  const data = await getMultiNestingLayout(params)
  setRealData(data)
} catch (error) {
  console.error('API Error:', error)
  // Fallback automatico ai dati mock
  setUseMockData(true)
  showToast('Errore API - Utilizzo dati mock')
}
```

#### Validazione Parametri
```python
# Backend valida tutti i parametri
@router.get("/layout/multi")
async def get_multi_nesting_layout(
    padding_mm: float = Query(10.0, ge=0.0, le=50.0),  # Validazione range
    borda_mm: float = Query(20.0, ge=0.0, le=100.0),
    rotazione_abilitata: bool = Query(True)
):
```

#### Gestione Dati Mancanti
```python
# Service gestisce gracefully dati incompleti
def convert_nesting_to_layout_data(nesting, ...):
    try:
        # Calcoli con dati disponibili
        return layout_data
    except Exception as e:
        logger.warning(f"Dati incompleti per nesting {nesting.id}: {e}")
        # Ritorna struttura base con valori default
        return default_layout_data
```

## 📊 Performance e Ottimizzazioni

### ⚡ Ottimizzazioni Implementate

#### Database
```python
# Query ottimizzate con joinedload
nesting_list = db.query(NestingResult)\
    .options(
        joinedload(NestingResult.autoclave),
        joinedload(NestingResult.odl_list).joinedload(ODL.parte),
        joinedload(NestingResult.odl_list).joinedload(ODL.tool)
    )\
    .filter(...)\
    .all()
```

#### Cache Calcoli
```python
# Memoization per calcoli ripetuti
@lru_cache(maxsize=1000)
def calculate_optimal_orientation_cached(tool_length, tool_width, autoclave_length, autoclave_width):
    return calculate_optimal_orientation(tool_length, tool_width, autoclave_length, autoclave_width)
```

#### Frontend
```typescript
// Lazy loading e debounce
const debouncedSearch = useMemo(
  () => debounce((query: string) => {
    // Ricerca con debounce 300ms
  }, 300),
  []
)

// Memoization componenti pesanti
const MemoizedCanvas = React.memo(EnhancedNestingCanvas)
```

## 🔧 Configurazione Avanzata

### 🌐 Variabili Ambiente

#### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_ENABLE_REAL_API=true
NEXT_PUBLIC_API_TIMEOUT=10000
```

#### Backend (.env)
```bash
DATABASE_URL=sqlite:///./carbonpilot.db
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
ENABLE_CORS=true
```

### ⚙️ Parametri Configurabili

#### Layout Parameters
```typescript
interface LayoutParameters {
  padding_mm: number      // 0.0 - 50.0
  borda_mm: number       // 0.0 - 100.0
  rotazione_abilitata: boolean
}

interface MultiLayoutParameters extends LayoutParameters {
  limit?: number         // 1 - 50
  stato_filtro?: string  // "In corso" | "Schedulato" | "Completato"
}
```

## 🚀 Deployment

### 🐳 Docker Setup

#### Backend
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Frontend
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

### 🔄 CI/CD Pipeline

#### GitHub Actions
```yaml
name: Test Integration
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r backend/requirements.txt
      - name: Run validation tests
        run: python tools/validate_nesting_canvas.py
      - name: Run API integration tests
        run: python tools/test_nesting_api_integration.py
```

## 🔮 Roadmap Futuro

### 🎯 Prossime Implementazioni

#### WebSocket Real-time
```python
# Backend WebSocket per aggiornamenti live
@app.websocket("/ws/nesting/{nesting_id}")
async def websocket_nesting_updates(websocket: WebSocket, nesting_id: int):
    await websocket.accept()
    # Stream aggiornamenti in tempo reale
```

#### Cache Redis
```python
# Cache distribuita per performance
import redis
cache = redis.Redis(host='localhost', port=6379, db=0)

@lru_cache_with_redis(expire=300)
def get_nesting_layout_cached(nesting_id, params):
    return calculate_layout(nesting_id, params)
```

#### Machine Learning
```python
# Predizione parametri ottimali
class LayoutOptimizer:
    def predict_optimal_parameters(self, nesting_data):
        # ML model per suggerire padding/bordi ottimali
        return optimized_params
```

## 📞 Supporto e Troubleshooting

### 🐛 Problemi Comuni

#### API Non Raggiungibile
```bash
# Verifica backend in esecuzione
curl http://localhost:8000/api/

# Controlla logs
tail -f backend/logs/app.log
```

#### Errori Database
```bash
# Verifica migrazione
python backend/migrations/add_tool_peso_materiale.py

# Controlla integrità
python tools/validate_nesting_canvas.py
```

#### Performance Lente
```bash
# Profiling API
python -m cProfile tools/test_nesting_api_integration.py

# Monitoring database
EXPLAIN QUERY PLAN SELECT ...
```

### 📧 Contatti

Per supporto tecnico o domande sull'integrazione:
- **Documentazione**: `docs/`
- **Issues**: GitHub Issues
- **Testing**: `tools/validate_nesting_canvas.py`

---

**Versione**: 1.0.0  
**Ultimo Aggiornamento**: 2024-01-28  
**Compatibilità**: FastAPI 0.104+, React 18+, TypeScript 5+ 