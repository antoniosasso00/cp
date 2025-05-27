# 📋 Changelog - CarbonPilot

Questo file documenta tutte le modifiche significative apportate al progetto CarbonPilot.

## 🎯 Formato
Ogni entry segue il formato:
```
### [Data - Nome Feature]
- Descrizione sintetica della funzionalità
- Modifiche ai modelli DB (se presenti)
- Effetti sulla UI e sul comportamento dell'app
```

---

### [2025-05-28 - Rifattorizzazione Completa Sistema Nesting] ✅ IMPLEMENTATO

#### 🎯 Obiettivo
Rifattorizzazione completa del sistema di nesting con gestione degli stati strutturata, parametri personalizzabili, algoritmo batch multi-autoclave intelligente e blocco autoclavi solo alla conferma.

#### 🏗️ Implementazione Backend

##### ✅ Modello NestingResult Rifattorizzato
**File**: `backend/models/nesting_result.py`

**Nuovo Enum Stati**:
```python
class StatoNestingEnum(str, PyEnum):
    BOZZA = "bozza"              # Generato, autoclave libera, modificabile
    IN_SOSPESO = "in_sospeso"    # Autoclave bloccata, ODL in attesa, modificabile
    CONFERMATO = "confermato"    # ODL in cura, processo attivo, non modificabile
    ANNULLATO = "annullato"      # Annullato, risorse liberate
    COMPLETATO = "completato"    # Completato, autoclave liberata
```

**Nuovi Campi Parametri Personalizzabili**:
- `padding_mm: Float` (default 10.0) - Spaziatura tra tool in mm (0-50)
- `borda_mm: Float` (default 20.0) - Bordo minimo dall'autoclave in mm (0-100)
- `max_valvole_per_autoclave: Integer` (opzionale) - Limite valvole per autoclave
- `rotazione_abilitata: Boolean` (default True) - Rotazione automatica tool
- `confermato_da_ruolo: String(50)` - Ruolo utente che ha confermato

**Nuovi Campi Statistiche Avanzate**:
- `peso_totale_kg: Float` - Peso totale del carico in kg
- `area_piano_1: Float` - Area utilizzata piano 1 in cm²
- `area_piano_2: Float` - Area utilizzata piano 2 in cm²
- `superficie_piano_2_max: Float` - Superficie massima configurabile piano 2
- `posizioni_tool: JSON` - Posizioni 2D dei tool con coordinate
- `note: Text` - Note aggiuntive dettagliate

**Proprietà Calcolate**:
- `is_editable` - Indica se modificabile (BOZZA/IN_SOSPESO)
- `is_confirmed` - Indica se confermato
- `efficienza_piano_1/2` - Calcolo efficienza utilizzo per piano
- `efficienza_totale` - Efficienza complessiva utilizzo spazio

##### ✅ Schemi Pydantic Completi
**File**: `backend/schemas/nesting.py`

**Nuovi Schemi Parametri**:
```python
class NestingParameters(BaseModel):
    """Parametri personalizzabili del nesting con validazione"""
    padding_mm: float = Field(default=10.0, ge=0.0, le=50.0, description="Spaziatura tra tool in mm")
    borda_mm: float = Field(default=20.0, ge=0.0, le=100.0, description="Bordo minimo dall'autoclave in mm")
    max_valvole_per_autoclave: Optional[int] = Field(None, ge=1, description="Limite massimo valvole")
    rotazione_abilitata: bool = Field(True, description="Abilita rotazione automatica tool")
    priorita_ottimizzazione: PrioritaOttimizzazione = Field("EQUILIBRATO", description="Criterio priorità")

class BatchNestingRequest(BaseModel):
    """Richiesta batch nesting intelligente multi-autoclave"""
    parametri: Optional[NestingParameters] = None
    note: Optional[str] = None
    forza_generazione: bool = Field(False, description="Forza generazione con pochi ODL")

class BatchNestingResponse(BaseModel):
    """Risposta batch con statistiche complete"""
    success: bool
    message: str
    nesting_creati: List[NestingResponse] = []
    odl_non_assegnati: List[ODLNestingInfo] = []
    statistiche: Dict[str, Any] = {}
```

**Schemi CRUD Completi**:
- `NestingCreate` - Creazione nesting con parametri
- `NestingUpdate` - Aggiornamento stato e parametri
- `NestingResponse` - Risposta completa con tutte le informazioni

##### ✅ Service Layer Rifattorizzato
**File**: `backend/services/nesting_service.py`

**Algoritmo Batch Intelligente**:
```python
async def run_batch_nesting(db: Session, request: BatchNestingRequest) -> BatchNestingResponse:
    """
    Algoritmo batch intelligente multi-autoclave:
    1. Recupera ODL in attesa e autoclavi disponibili
    2. Raggruppa ODL per ciclo di cura compatibile
    3. Algoritmo assegnazione ottimale (gruppi grandi prioritari)
    4. Calcola punteggio compatibilità (area, valvole, peso)
    5. Crea nesting in stato BOZZA (non blocca autoclavi)
    6. Distribuzione bilanciata per ridurre numero totale nesting
    """

def calcola_punteggio_autoclave(autoclave: Autoclave, odl_list: List[ODL], 
                               parametri: Optional[NestingParameters]) -> float:
    """
    Calcola punteggio compatibilità autoclave-ODL:
    - Verifica vincoli capacità (area, valvole, peso)
    - Calcola efficienza utilizzo risorse
    - Punteggio bilanciato per ottimizzazione globale
    """

async def crea_nesting_bozza(db: Session, autoclave: Autoclave, odl_list: List[ODL], 
                           ciclo_id: int, parametri: Optional[NestingParameters], 
                           note: Optional[str]) -> Optional[NestingResult]:
    """Crea nesting in stato BOZZA con parametri personalizzabili"""
```

**Gestione Stati Avanzata**:
```python
async def update_nesting_status(db: Session, nesting_id: int, nuovo_stato: StatoNestingEnum, 
                               note: str = None, ruolo_utente: str = None) -> NestingResult:
    """
    Gestione transizioni di stato con logica appropriata:
    - CONFERMATO: ODL → "Cura", autoclave rimane IN_USO
    - ANNULLATO: ODL → "Attesa Cura", autoclave → DISPONIBILE
    - COMPLETATO: autoclave → DISPONIBILE, genera report PDF
    - Validazione permessi per ruolo utente
    """
```

##### ✅ API Endpoints Estesi
**File**: `backend/api/routers/nesting.py`

**Nuovi Endpoint Batch**:
```python
@router.post("/batch", response_model=BatchNestingResponse)
async def batch_nesting(request: BatchNestingRequest, db: Session = Depends(get_db)):
    """
    🚀 BATCH NESTING INTELLIGENTE MULTI-AUTOCLAVE
    - Ottimizzazione globale invece che sequenziale
    - Utilizzo bilanciato delle risorse
    - Parametri personalizzabili per ogni batch
    - Stato BOZZA permette revisione prima della conferma
    """

@router.post("/{nesting_id}/promote", response_model=NestingResponse)
async def promote_nesting(nesting_id: int, ruolo_utente: str = "management", 
                         db: Session = Depends(get_db)):
    """
    🔄 PROMOZIONE NESTING: BOZZA → IN_SOSPESO
    - Blocca l'autoclave (stato → IN_USO)
    - Mantiene ODL in ATTESA CURA
    - Permette successiva conferma da parte del Curing
    """
```

**Endpoint Aggiornati**:
- `PUT /{nesting_id}/status` - Usa StatoNestingEnum invece di stringhe
- `GET /preview` - Supporta parametri personalizzabili completi
- `POST /auto-multiple` - Automazione nesting su autoclavi disponibili

#### 🗄️ Migrazione Database Completa

##### ✅ Script Migrazione Principale
**File**: `backend/migrations/add_nesting_enum_and_parameters.py`

**Operazioni Migrazione**:
1. **Crea enum PostgreSQL**: `CREATE TYPE statonesting AS ENUM ('bozza', 'in_sospeso', 'confermato', 'annullato', 'completato')`
2. **Aggiunge campi parametri personalizzabili**:
   - `padding_mm FLOAT DEFAULT 10.0`
   - `borda_mm FLOAT DEFAULT 20.0`
   - `max_valvole_per_autoclave INTEGER`
   - `rotazione_abilitata BOOLEAN DEFAULT TRUE`
3. **Aggiunge campi audit e note**:
   - `confermato_da_ruolo VARCHAR(50)`
   - `note TEXT`
4. **Migrazione stati esistenti**:
   ```sql
   "In sospeso" → "in_sospeso"
   "Confermato" → "confermato"
   "Completato" → "completato"
   "Annullato" → "annullato"
   ```
5. **Aggiorna colonna stato**: Da VARCHAR a enum con constraint NOT NULL
6. **Imposta valori default**: Per tutti i record esistenti
7. **Verifica integrità**: Controlli finali e statistiche

**Sicurezza Migrazione**:
- Transazione completa con rollback automatico su errore
- Backup automatico stati esistenti
- Validazione dati prima e dopo migrazione
- Log dettagliato di tutte le operazioni

#### 🔧 Strumenti di Validazione e Manutenzione

##### ✅ Script Validazione Completo
**File**: `tools/validate_nesting_states.py`

**Funzionalità di Validazione**:
```python
class NestingStateValidator:
    def validate_nesting_states(self) -> bool:
        """Valida coerenza stati nesting e parametri"""
    
    def validate_odl_nesting_consistency(self) -> bool:
        """Verifica allineamento stati ODL/nesting"""
    
    def validate_autoclave_availability(self) -> bool:
        """Controlla stati autoclavi vs nesting attivi"""
    
    def validate_data_integrity(self) -> bool:
        """Verifica riferimenti orfani e dati inconsistenti"""
```

**Controlli Implementati**:
- **Stati Enum**: Verifica validità enum StatoNestingEnum
- **Parametri Range**: Controllo padding_mm (0-50), borda_mm (0-100)
- **Coerenza ODL**: Allineamento stati ODL con stati nesting
- **Disponibilità Autoclavi**: Verifica IN_USO vs nesting attivi
- **Riferimenti Orfani**: Nesting con autoclavi/ODL inesistenti
- **Correzioni Automatiche**: Flag `--fix` per riparazioni automatiche

**Uso Strumento**:
```bash
# Validazione completa con output dettagliato
python tools/validate_nesting_states.py --verbose

# Validazione con correzioni automatiche
python tools/validate_nesting_states.py --fix --verbose

# Exit codes: 0=OK, 1=Errori critici, 2=Solo avvisi, 3=Errore sistema
```

#### 🔄 Logica Flusso Stati Implementata

##### ✅ Transizioni di Stato Complete
```
1. GENERAZIONE → BOZZA
   - Nesting creato con parametri personalizzabili
   - Autoclave rimane DISPONIBILE
   - ODL rimangono in "Attesa Cura"
   - Modificabile da Management

2. PROMOZIONE → IN_SOSPESO
   - Autoclave passa a IN_USO (bloccata)
   - ODL rimangono in "Attesa Cura"
   - Modificabile da Management
   - Pronto per conferma Curing

3. CONFERMA → CONFERMATO
   - ODL passano a "Cura" (in autoclave)
   - Autoclave rimane IN_USO
   - Non più modificabile
   - Solo Curing può confermare

4. COMPLETAMENTO → COMPLETATO
   - ODL passano a "Finito"
   - Autoclave torna DISPONIBILE
   - Genera report PDF automatico
   - Processo terminato

5. ANNULLAMENTO → ANNULLATO
   - ODL tornano a "Attesa Cura"
   - Autoclave torna DISPONIBILE
   - Risorse completamente liberate
   - Possibile da qualsiasi stato precedente
```

##### ✅ Algoritmo Batch Multi-Autoclave
```
FASE 1: RACCOLTA DATI
- Recupera ODL in "Attesa Cura" validati
- Recupera autoclavi in stato DISPONIBILE
- Filtra ODL con dati completi (tool, parte, valvole)

FASE 2: RAGGRUPPAMENTO INTELLIGENTE
- Raggruppa ODL per ciclo di cura compatibile
- Ordina gruppi per numero ODL (priorità ai grandi)
- Calcola requisiti totali (area, valvole, peso)

FASE 3: ASSEGNAZIONE OTTIMALE
- Per ogni gruppo, trova autoclave migliore
- Calcola punteggio compatibilità:
  * Efficienza area = (area_richiesta / area_disponibile) * 100
  * Efficienza valvole = (valvole_richieste / valvole_totali) * 100
  * Efficienza peso = (peso_stimato / carico_max) * 100
  * Punteggio = (eff_area + eff_valvole + eff_peso) / 3

FASE 4: CREAZIONE BOZZE
- Crea nesting in stato BOZZA (non blocca autoclavi)
- Applica parametri personalizzabili
- Registra statistiche complete
- Mantiene ODL in "Attesa Cura"

FASE 5: RISULTATI E STATISTICHE
- Report ODL assegnati vs non assegnati
- Statistiche efficienza globale
- Suggerimenti ottimizzazione
```

#### 🎯 Parametri Personalizzabili Avanzati

##### ✅ Configurazioni Disponibili
```python
class NestingParameters:
    padding_mm: float = 10.0          # Spaziatura tra tool (0-50mm)
    borda_mm: float = 20.0            # Bordo minimo autoclave (0-100mm)
    max_valvole_per_autoclave: int    # Limite valvole (opzionale)
    rotazione_abilitata: bool = True  # Rotazione automatica tool
    priorita_ottimizzazione: str      # PESO/AREA/EQUILIBRATO
```

**Validazione Parametri**:
- **Lato Schema**: Validazione Pydantic con Field constraints
- **Lato Database**: Check constraints PostgreSQL
- **Lato Service**: Validazione business logic
- **Correzione Automatica**: Script validazione ripara valori fuori range

**Suggerimenti Utilizzo**:
- `padding_mm`: 5-15mm per tool piccoli, 10-20mm per tool grandi
- `borda_mm`: 15-25mm standard, 30-50mm per sicurezza extra
- `max_valvole_per_autoclave`: Utile per bilanciare carichi
- `rotazione_abilitata`: False solo per tool con orientamento fisso

#### 📊 Statistiche e Monitoring

##### ✅ Metriche Implementate
- **Efficienza Utilizzo**: Area, valvole, peso per piano
- **Performance Batch**: ODL assegnati vs totali
- **Distribuzione Carichi**: Bilanciamento tra autoclavi
- **Tempi Processo**: Durata fasi nesting
- **Errori e Correzioni**: Log inconsistenze e fix applicati

##### ✅ Report Automatici
- **Generazione PDF**: Automatica al completamento nesting
- **Log Audit**: Tracciamento modifiche stati e parametri
- **Statistiche Giornaliere**: Utilizzo autoclavi e efficienza
- **Alert Inconsistenze**: Notifiche problemi validazione

#### 🔒 Sicurezza e Permessi

##### ✅ Controllo Accessi
- **Management**: Può creare, modificare, promuovere, annullare nesting
- **Curing**: Può solo confermare nesting IN_SOSPESO
- **Validazione Ruoli**: Controllo permessi per ogni operazione
- **Audit Trail**: Log completo di chi ha fatto cosa e quando

##### ✅ Validazione Dati
- **Constraint Database**: Enum, range, NOT NULL appropriati
- **Validazione Schema**: Pydantic con Field constraints
- **Business Logic**: Controlli coerenza stati e transizioni
- **Integrità Referenziale**: Verifica esistenza autoclavi e ODL

#### 🚀 Benefici Implementazione

##### ✅ Miglioramenti Operativi
1. **Flusso Stati Chiaro**: Transizioni ben definite e tracciabili
2. **Blocco Autoclave Ottimizzato**: Solo quando necessario (conferma)
3. **Parametri Personalizzabili**: Adattabilità a diverse esigenze produttive
4. **Batch Intelligente**: Ottimizzazione globale invece che sequenziale
5. **Validazione Automatica**: Controllo coerenza e correzione errori

##### ✅ Vantaggi Tecnici
1. **Enum PostgreSQL**: Performance e integrità migliorate
2. **Schema Strutturato**: Validazione completa lato API
3. **Transazioni Sicure**: Rollback automatico su errori
4. **Monitoring Completo**: Statistiche e audit trail
5. **Manutenzione Facilitata**: Strumenti validazione e correzione

##### ✅ Scalabilità
1. **Algoritmo Batch**: Gestisce centinaia di ODL e decine di autoclavi
2. **Parametri Flessibili**: Adattabile a nuovi requisiti
3. **Stati Estendibili**: Facile aggiunta nuovi stati se necessario
4. **API Versionate**: Backward compatibility mantenuta
5. **Database Ottimizzato**: Indici e constraint per performance

#### 🔧 Prossimi Passi

##### ✅ Implementazione Frontend
1. **Componenti Stati**: Badge e indicatori per nuovi stati
2. **Form Parametri**: UI per configurazione parametri personalizzabili
3. **Dashboard Batch**: Interfaccia per batch nesting multi-autoclave
4. **Monitoring**: Grafici efficienza e statistiche utilizzo

##### ✅ Ottimizzazioni Future
1. **Machine Learning**: Predizione parametri ottimali basata su storico
2. **Algoritmi Avanzati**: Ottimizzazione genetica per assegnazione
3. **Real-time Updates**: WebSocket per aggiornamenti stati in tempo reale
4. **API GraphQL**: Query flessibili per dashboard complesse

---