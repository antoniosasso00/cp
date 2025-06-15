from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# Import per la relazione autoclave
from schemas.autoclave import AutoclaveResponse

# Enum per rappresentare i vari stati di un batch nesting
class StatoBatchNestingEnum(str, Enum):
    DRAFT = "draft"           # Risultati generati, NON persistiti se non confermati
    SOSPESO = "sospeso"       # Confermato dall'operatore, pronto per caricamento  
    IN_CURA = "in_cura"       # Autoclave caricata, cura in corso, timing attivo
    TERMINATO = "terminato"   # Cura completata, workflow chiuso

# Schema per i parametri di nesting
class ParametriNesting(BaseModel):
    """Schema per validare i parametri utilizzati nella generazione del nesting"""
    padding_mm: float = Field(default=1.0, ge=0, le=100, 
                             description="Padding in millimetri tra i tool")
    min_distance_mm: float = Field(default=1.0, ge=0, le=50,
                                  description="Distanza minima tra i tool in millimetri")
    priorita_area: bool = Field(default=True,
                               description="Priorità alla massimizzazione dell'area utilizzata")
    accorpamento_odl: bool = Field(default=False,
                                  description="Permette di accorpare ODL simili")
    use_secondary_plane: bool = Field(default=False,
                                     description="Utilizza il piano secondario se disponibile")
    max_weight_per_plane_kg: Optional[float] = Field(default=None, ge=0,
                                                    description="Peso massimo per piano in kg")
    
    class Config:
        json_schema_extra = {
            "example": {
                "padding_mm": 1.0,
                "min_distance_mm": 1.0,
                "priorita_area": True,
                "accorpamento_odl": False,
                "use_secondary_plane": False,
                "max_weight_per_plane_kg": 500.0
            }
        }

# Schema per la configurazione del layout (output del canvas React)
class ConfigurazioneLayout(BaseModel):
    """Schema per la configurazione del layout generato dal frontend"""
    canvas_width: Optional[float] = Field(None, description="Larghezza del canvas in pixel")
    canvas_height: Optional[float] = Field(None, description="Altezza del canvas in pixel")
    scale_factor: float = Field(default=1.0, description="Fattore di scala del canvas")
    tool_positions: List[Dict[str, Any]] = Field(default=[], 
                                                description="Posizioni dei tool sul canvas")
    # 🆕 NUOVO: Supporto per positioned_tools (formato 2L)
    positioned_tools: List[Dict[str, Any]] = Field(default=[], 
                                                  description="Tool posizionati (formato 2L)")
    plane_assignments: Dict[str, int] = Field(default={}, 
                                            description="Assegnazione dei tool ai piani")
    
    class Config:
        json_schema_extra = {
            "example": {
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
        }

# Schema base per le proprietà comuni
class BatchNestingBase(BaseModel):
    nome: Optional[str] = Field(None, max_length=255, 
                               description="Nome opzionale del batch")
    stato: StatoBatchNestingEnum = Field(StatoBatchNestingEnum.SOSPESO,
                                       description="Stato corrente del batch")
    autoclave_id: int = Field(..., description="ID dell'autoclave")
    odl_ids: List[int] = Field(default=[], description="Lista degli ID ODL inclusi")
    parametri: Optional[ParametriNesting] = Field(default=None,
                                                 description="Parametri utilizzati per il nesting")
    configurazione_json: Optional[ConfigurazioneLayout] = Field(default=None,
                                                               description="Configurazione layout")
    note: Optional[str] = Field(None, description="Note aggiuntive")

# Schema per la creazione
class BatchNestingCreate(BatchNestingBase):
    creato_da_utente: Optional[str] = Field(None, max_length=100,
                                          description="ID dell'utente creatore")
    creato_da_ruolo: Optional[str] = Field(None, max_length=50,
                                         description="Ruolo dell'utente creatore")

# Schema per gli aggiornamenti
class BatchNestingUpdate(BaseModel):
    nome: Optional[str] = Field(None, max_length=255)
    stato: Optional[StatoBatchNestingEnum] = None
    odl_ids: Optional[List[int]] = None
    parametri: Optional[ParametriNesting] = None
    configurazione_json: Optional[ConfigurazioneLayout] = None
    note: Optional[str] = None
    confermato_da_utente: Optional[str] = Field(None, max_length=100)
    confermato_da_ruolo: Optional[str] = Field(None, max_length=50)

# Schema per la risposta (include i campi generati dal database)
class BatchNestingResponse(BatchNestingBase):
    id: str = Field(..., description="ID UUID del batch")
    
    # Relazione autoclave
    autoclave: Optional[AutoclaveResponse] = Field(None, description="Dati completi dell'autoclave associata")
    
    # Statistiche aggregate
    numero_nesting: int = Field(default=0, description="Numero di nesting nel batch")
    peso_totale_kg: float = Field(default=0, description="Peso totale in kg")
    area_totale_utilizzata: float = Field(default=0, description="Area totale utilizzata in cm²")
    valvole_totali_utilizzate: int = Field(default=0, description="Valvole totali utilizzate")
    
    # ✅ NUOVI: Campi per il sistema di valutazione efficienza
    efficiency: float = Field(default=0.0, description="Efficienza complessiva del batch")
    area_pct: Optional[float] = Field(None, description="Percentuale di area utilizzata")
    vacuum_util_pct: Optional[float] = Field(None, description="Percentuale di utilizzo linee vuoto")
    efficiency_score: Optional[float] = Field(None, description="Score di efficienza: 0.7·area + 0.3·vacuum")
    efficiency_level: Optional[str] = Field(None, description="Livello di efficienza: green/yellow/red")
    efficiency_color_class: Optional[str] = Field(None, description="Classe CSS per il badge di efficienza")
    
    # Informazioni di audit
    creato_da_utente: Optional[str] = None
    creato_da_ruolo: Optional[str] = None
    confermato_da_utente: Optional[str] = None
    confermato_da_ruolo: Optional[str] = None
    data_conferma: Optional[datetime] = None
    data_completamento: Optional[datetime] = Field(None, description="Data e ora di completamento del ciclo")
    durata_ciclo_minuti: Optional[int] = Field(None, description="Durata del ciclo di cura in minuti")
    
    # Timestamp
    created_at: datetime
    updated_at: datetime
    
    # Proprietà calcolate
    stato_descrizione: Optional[str] = Field(None, description="Descrizione testuale dello stato")
    
    class Config:
        from_attributes = True

# Schema semplificato per elenchi
class BatchNestingList(BaseModel):
    id: str
    nome: Optional[str]
    stato: StatoBatchNestingEnum
    autoclave_id: int
    numero_nesting: int
    peso_totale_kg: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ========== SCHEMI PER ENDPOINT SOLVE v1.4.12-DEMO ==========

class NestingParamsRequest(BaseModel):
    """Schema per i parametri di nesting"""
    padding_mm: float = Field(default=10, ge=0.1, le=100, description="Padding aggiuntivo attorno ai pezzi (mm)")
    min_distance_mm: float = Field(default=15, ge=0.1, le=50, description="Distanza minima tra i pezzi (mm)")
    vacuum_lines_capacity: int = Field(default=20, ge=1, le=50, description="Capacità massima linee di vuoto")
    use_fallback: bool = Field(default=True, description="Usa fallback greedy se CP-SAT fallisce")
    allow_heuristic: bool = Field(default=True, description="Usa euristiche avanzate")
    timeout_override: Optional[int] = Field(default=None, description="Override del timeout predefinito")
    
    class Config:
        json_schema_extra = {
            "example": {
                "padding_mm": 10,
                "min_distance_mm": 15,
                "vacuum_lines_capacity": 20,
                "use_fallback": True,
                "allow_heuristic": True,
                "timeout_override": None,
            }
        }

class NestingSolveRequest(BaseModel):
    """Schema per la richiesta dell'endpoint solve v1.4.12-DEMO"""
    autoclave_id: int = Field(..., description="ID dell'autoclave da utilizzare")
    odl_ids: Optional[List[int]] = Field(None, description="IDs degli ODL da processare (None = tutti disponibili)")
    padding_mm: float = Field(default=20, ge=0.1, le=50, description="Padding tra i tool (0.1-50mm) - OTTIMIZZATO per efficienza reale")
    min_distance_mm: float = Field(default=15, ge=0.1, le=30, description="Distanza minima dai bordi (0.1-30mm) - OTTIMIZZATO per spazio massimo")
    vacuum_lines_capacity: Optional[int] = Field(None, ge=1, le=50, description="Capacità massima linee vuoto")
    allow_heuristic: bool = Field(default=False, description="Abilita heuristica RRGH")
    timeout_override: Optional[int] = Field(None, ge=30, le=300, description="Override timeout (30-300s)")
    heavy_piece_threshold_kg: float = Field(default=50.0, ge=0, description="Soglia peso per constraint posizionamento")
    
    class Config:
        json_schema_extra = {
            "example": {
                "autoclave_id": 1,
                "odl_ids": [5, 6, 7],
                "padding_mm": 0.2,
                "min_distance_mm": 0.2,
                "vacuum_lines_capacity": 20,
                "allow_heuristic": True,
                "timeout_override": 90,
                "heavy_piece_threshold_kg": 50.0
            }
        }

class NestingMetricsResponse(BaseModel):
    """Schema per le metriche del nesting v1.4.17-DEMO"""
    area_utilization_pct: float = Field(..., description="Percentuale utilizzo area")
    vacuum_util_pct: float = Field(..., description="Percentuale utilizzo linee vuoto")
    efficiency_score: float = Field(..., description="Score efficienza: 0.8·area + 0.2·vacuum")  # 🔄 NUOVO v1.4.17-DEMO: aggiornato formula
    weight_utilization_pct: float = Field(..., description="Percentuale utilizzo peso")
    
    # Metriche tecniche
    time_solver_ms: float = Field(..., description="Tempo risoluzione solver in ms")
    fallback_used: bool = Field(..., description="Se è stato usato algoritmo fallback")
    heuristic_iters: int = Field(default=0, description="Numero iterazioni euristica RRGH")
    algorithm_status: str = Field(..., description="Stato algoritmo (CP-SAT_OPTIMAL, BL_FFD_FALLBACK, etc.)")
    
    # 🎯 NUOVO v1.4.16-DEMO: Campo per indicare sovrapposizioni
    invalid: bool = Field(default=False, description="True se ci sono sovrapposizioni non risolte nel layout")
    
    # 🔄 NUOVO v1.4.17-DEMO: Campo per indicare utilizzo rotazione
    rotation_used: bool = Field(default=False, description="True se è stata utilizzata rotazione 90° nel layout")
    
    # Statistiche fisiche
    total_area_cm2: float = Field(..., description="Area totale utilizzata in cm²")
    total_weight_kg: float = Field(..., description="Peso totale in kg")
    vacuum_lines_used: int = Field(..., description="Linee vuoto utilizzate")
    pieces_positioned: int = Field(..., description="Numero pezzi posizionati")
    pieces_excluded: int = Field(..., description="Numero pezzi esclusi")

class NestingToolPosition(BaseModel):
    """Schema per la posizione di un tool nel nesting"""
    odl_id: int = Field(..., description="ID dell'ODL")
    tool_id: int = Field(..., description="ID del tool")
    x: float = Field(..., description="Posizione X in mm")
    y: float = Field(..., description="Posizione Y in mm")
    width: float = Field(..., description="Larghezza in mm")
    height: float = Field(..., description="Altezza in mm")
    rotated: bool = Field(default=False, description="Se il tool è ruotato")
    plane: int = Field(default=1, description="Piano di posizionamento (1 o 2)")
    weight_kg: float = Field(..., description="Peso del tool in kg")

class NestingExcludedODL(BaseModel):
    """Schema per ODL esclusi dal nesting"""
    odl_id: int = Field(..., description="ID dell'ODL escluso")
    reason: str = Field(..., description="Motivo esclusione")
    part_number: Optional[str] = Field(None, description="Part number della parte")
    tool_dimensions: Optional[str] = Field(None, description="Dimensioni tool")

class NestingSolveResponse(BaseModel):
    """Schema per la risposta dell'endpoint solve v1.4.12-DEMO"""
    success: bool = Field(..., description="Se il nesting è stato risolto con successo")
    message: str = Field(..., description="Messaggio descrittivo del risultato")
    
    # Risultati posizionamento
    positioned_tools: List[NestingToolPosition] = Field(default=[], description="Tool posizionati")
    excluded_odls: List[NestingExcludedODL] = Field(default=[], description="ODL esclusi")
    
    # 🔍 NUOVO v1.4.14: Motivi di esclusione dettagliati per debug
    excluded_reasons: Dict[str, int] = Field(default={}, description="Riassunto motivi esclusione: {motivo: count}")
    
    # 🎯 NUOVO v1.4.16-DEMO: Dettagli sovrapposizioni per debug
    overlaps: Optional[List[Dict[str, Any]]] = Field(default=None, description="Dettagli sovrapposizioni rilevate nel layout")
    
    # Metriche dettagliate
    metrics: NestingMetricsResponse = Field(..., description="Metriche dettagliate del nesting")
    
    # Informazioni autoclave
    autoclave_info: Dict[str, Any] = Field(..., description="Informazioni autoclave utilizzata")
    
    # Timestamp
    solved_at: datetime = Field(default_factory=datetime.now, description="Timestamp risoluzione")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Nesting risolto con successo utilizzando algoritmo CP-SAT",
                "positioned_tools": [
                    {
                        "odl_id": 1,
                        "tool_id": 5,
                        "x": 100.0,
                        "y": 200.0,
                        "width": 300.0,
                        "height": 250.0,
                        "rotated": False,
                        "plane": 1,
                        "weight_kg": 25.5
                    }
                ],
                "excluded_odls": [
                    {
                        "odl_id": 15,
                        "reason": "Dimensioni eccessive per autoclave",
                        "part_number": "WING-BRACKET-XL",
                        "tool_dimensions": "1500x800mm"
                    }
                ],
                "excluded_reasons": {
                    "Dimensioni eccessive per autoclave": 1
                },
                "overlaps": None,
                "metrics": {
                    "area_utilization_pct": 78.5,
                    "vacuum_util_pct": 87.5,
                    "efficiency_score": 81.6,
                    "weight_utilization_pct": 65.2,
                    "time_solver_ms": 2450.0,
                    "fallback_used": False,
                    "heuristic_iters": 3,
                    "algorithm_status": "CP-SAT_OPTIMAL",
                    "total_area_cm2": 188400.0,
                    "total_weight_kg": 326.0,
                    "vacuum_lines_used": 7,
                    "pieces_positioned": 12,
                    "pieces_excluded": 3
                },
                "autoclave_info": {
                    "id": 1,
                    "nome": "AeroTest-v1.4.12",
                    "larghezza_piano": 1200.0,
                    "lunghezza": 2000.0,
                    "max_load_kg": 500.0,
                    "num_linee_vuoto": 8
                },
                "solved_at": "2025-06-02T12:30:45.123456"
            }
        } 

# ========== SCHEMI PER NESTING A DUE LIVELLI v2.0 ==========

class PosizionamentoTool2L(BaseModel):
    """Schema per il posizionamento di un tool nel nesting 2L"""
    odl_id: int = Field(..., description="ID dell'ODL")
    tool_id: int = Field(..., description="ID del tool")
    x: float = Field(..., description="Posizione X")
    y: float = Field(..., description="Posizione Y") 
    width: float = Field(..., gt=0, description="Larghezza del tool")
    height: float = Field(..., gt=0, description="Altezza del tool")
    rotated: bool = Field(False, description="Se il tool è ruotato di 90°")
    weight_kg: float = Field(..., ge=0, description="Peso del tool in kg")
    level: int = Field(..., ge=0, le=1, description="Livello: 0=piano base, 1=cavalletto")
    z_position: float = Field(..., ge=0, description="Posizione Z (altezza dal piano base)")
    lines_used: int = Field(..., ge=1, description="Numero di linee vuoto utilizzate")
    # 🆕 NUOVI CAMPI per compatibilità frontend
    part_number: Optional[str] = Field(None, description="Part number della parte")
    descrizione_breve: Optional[str] = Field(None, description="Descrizione breve della parte")
    numero_odl: Optional[str] = Field(None, description="Numero ODL formattato")
    
    @validator('z_position', pre=True, always=True)
    def validate_z_position(cls, v, values):
        """Assicura che z_position sia coerente con il livello"""
        level = values.get('level', 0) if values else 0
        if level == 0 and v != 0:
            return 0.0  # Piano base deve essere a z=0
        elif level == 1 and v == 0:
            return 100.0  # Cavalletto ha altezza default 100mm
        return float(v) if v is not None else 0.0
    
    @validator('numero_odl', pre=True, always=True)
    def ensure_numero_odl_string(cls, v, values):
        """Assicura che numero_odl sia sempre una stringa"""
        if v is not None:
            return str(v)
        # Fallback sicuro se odl_id non è disponibile
        odl_id = values.get('odl_id', 0) if values else 0
        return f"ODL{str(odl_id).zfill(3)}"

class CavallettoPosizionamento(BaseModel):
    """Schema per la posizione di un cavalletto sotto un tool"""
    # Coordinate assolute del cavalletto
    x: float = Field(..., description="Posizione X del cavalletto in mm")
    y: float = Field(..., description="Posizione Y del cavalletto in mm")
    width: float = Field(..., description="Larghezza del cavalletto in mm")
    height: float = Field(..., description="Profondità del cavalletto in mm")
    
    # Riferimento al tool supportato
    tool_odl_id: int = Field(..., description="ID ODL del tool che questo cavalletto supporta")
    tool_id: Optional[int] = Field(None, description="ID del tool che questo cavalletto supporta")
    sequence_number: int = Field(..., description="Numero di sequenza del cavalletto per questo tool (0, 1, 2...)")
    
    # Metadati aggiuntivi
    center_x: Optional[float] = Field(None, description="Centro X del cavalletto (calcolato)")
    center_y: Optional[float] = Field(None, description="Centro Y del cavalletto (calcolato)")
    support_area_mm2: Optional[float] = Field(None, description="Area di supporto fornita in mm²")
    
    class Config:
        json_schema_extra = {
            "example": {
                "x": 200.0,
                "y": 350.0,
                "width": 80.0,
                "height": 60.0,
                "tool_odl_id": 5,
                "tool_id": 12,
                "sequence_number": 0,
                "center_x": 240.0,
                "center_y": 380.0,
                "support_area_mm2": 4800.0
            }
        }

class NestingMetrics2L(BaseModel):
    """Schema per le metriche del nesting a due livelli"""
    # Metriche base compatibili con NestingMetricsResponse
    area_utilization_pct: float = Field(..., description="Percentuale utilizzo area totale")
    vacuum_util_pct: float = Field(..., description="Percentuale utilizzo linee vuoto")
    efficiency_score: float = Field(..., description="Score efficienza complessivo")
    weight_utilization_pct: float = Field(..., description="Percentuale utilizzo peso")
    
    # Metriche tecniche
    time_solver_ms: float = Field(..., description="Tempo risoluzione solver in ms")
    fallback_used: bool = Field(..., description="Se è stato usato algoritmo fallback")
    algorithm_status: str = Field(..., description="Stato algoritmo")
    
    # Statistiche fisiche totali
    total_area_cm2: float = Field(..., description="Area totale utilizzata in cm²")
    total_weight_kg: float = Field(..., description="Peso totale in kg")
    vacuum_lines_used: int = Field(..., description="Linee vuoto utilizzate")
    pieces_positioned: int = Field(..., description="Numero pezzi posizionati")
    pieces_excluded: int = Field(..., description="Numero pezzi esclusi")
    
    # 🆕 NUOVO: Metriche specifiche per livelli
    level_0_count: int = Field(default=0, description="Numero tool posizionati sul piano base")
    level_1_count: int = Field(default=0, description="Numero tool posizionati su cavalletti")
    level_0_weight_kg: float = Field(default=0.0, description="Peso totale sul piano base in kg")
    level_1_weight_kg: float = Field(default=0.0, description="Peso totale su cavalletti in kg")
    level_0_area_pct: float = Field(default=0.0, description="Percentuale area utilizzata livello 0")
    level_1_area_pct: float = Field(default=0.0, description="Percentuale area utilizzata livello 1")
    
    # Metriche cavalletti
    cavalletti_used: int = Field(default=0, description="Numero totale di cavalletti utilizzati")
    cavalletti_coverage_pct: float = Field(default=0.0, description="Percentuale copertura cavalletti sui tool livello 1")
    
    # Score complessità e ottimizzazione
    complexity_score: float = Field(default=0.0, description="Score di complessità del dataset")
    timeout_used_seconds: float = Field(default=0.0, description="Timeout utilizzato dal solver")
    
    class Config:
        json_schema_extra = {
            "example": {
                "area_utilization_pct": 72.5,
                "vacuum_util_pct": 85.0,
                "efficiency_score": 76.8,
                "weight_utilization_pct": 68.2,
                "time_solver_ms": 3250.0,
                "fallback_used": False,
                "algorithm_status": "CP-SAT_OPTIMAL_2L",
                "total_area_cm2": 174000.0,
                "total_weight_kg": 341.0,
                "vacuum_lines_used": 8,
                "pieces_positioned": 15,
                "pieces_excluded": 2,
                "level_0_count": 8,
                "level_1_count": 7,
                "level_0_weight_kg": 180.5,
                "level_1_weight_kg": 160.5,
                "level_0_area_pct": 41.7,
                "level_1_area_pct": 25.0,
                "cavalletti_used": 14,
                "cavalletti_coverage_pct": 92.5,
                "complexity_score": 1.8,
                "timeout_used_seconds": 3.25
            }
        }

class NestingSolveRequest2L(BaseModel):
    """Schema per la richiesta dell'endpoint solve a due livelli"""
    autoclave_id: int = Field(..., description="ID dell'autoclave da utilizzare")
    odl_ids: Optional[List[int]] = Field(None, description="IDs degli ODL da processare (None = tutti disponibili)")
    
    # Parametri base
    padding_mm: float = Field(default=10.0, ge=0.1, le=100, description="Padding tra i tool (mm)")
    min_distance_mm: float = Field(default=15.0, ge=0.1, le=50, description="Distanza minima dai bordi (mm)")
    vacuum_lines_capacity: Optional[int] = Field(None, ge=1, le=50, description="Capacità massima linee vuoto")
    
    # 🆕 PARAMETRI SPECIFICI 2L - cavalletto_height_mm rimosso (ora in AutoclaveInfo2L)
    use_cavalletti: bool = Field(default=True, description="Abilita utilizzo cavalletti (secondo livello)")
    # cavalletto_height_mm: RIMOSSO - ora preso dal database autoclave tramite AutoclaveInfo2L.cavalletto_height
    # max_weight_per_level_kg: RIMOSSO - ora preso dal database autoclave tramite AutoclaveInfo2L.peso_max_per_cavalletto_kg
    prefer_base_level: bool = Field(default=True, description="Preferisci posizionamento su piano base")
    
    # Parametri avanzati
    allow_heuristic: bool = Field(default=True, description="Abilita euristiche avanzate")
    timeout_override: Optional[int] = Field(None, ge=30, le=600, description="Override timeout (30-600s)")
    heavy_piece_threshold_kg: float = Field(default=50.0, ge=0, description="Soglia peso per pezzi pesanti")
    use_multithread: bool = Field(default=True, description="Utilizza solver multithread")
    
    class Config:
        json_schema_extra = {
            "example": {
                "autoclave_id": 1,
                "odl_ids": [5, 6, 7, 8],
                "padding_mm": 10.0,
                "min_distance_mm": 15.0,
                "vacuum_lines_capacity": 25,
                "use_cavalletti": True,
                # "cavalletto_height_mm": RIMOSSO - ora dal database autoclave
                # "max_weight_per_level_kg": RIMOSSO - ora dal database autoclave
                "prefer_base_level": True,
                "allow_heuristic": True,
                "timeout_override": 120,
                "heavy_piece_threshold_kg": 50.0,
                "use_multithread": True
            }
        }

class NestingSolveResponse2L(BaseModel):
    """Schema per la risposta dell'endpoint solve a due livelli"""
    success: bool = Field(..., description="Se il nesting è stato risolto con successo")
    message: str = Field(..., description="Messaggio descrittivo del risultato")
    
    # 🆕 NUOVO: Risultati posizionamento a due livelli
    positioned_tools: List[PosizionamentoTool2L] = Field(default=[], description="Tool posizionati con informazioni livello")
    cavalletti: List[CavallettoPosizionamento] = Field(default=[], description="Cavalletti utilizzati per il supporto")
    excluded_odls: List[NestingExcludedODL] = Field(default=[], description="ODL esclusi")
    
    # Motivi di esclusione dettagliati
    excluded_reasons: Dict[str, int] = Field(default={}, description="Riassunto motivi esclusione")
    
    # 🆕 NUOVO: Metriche dettagliate per due livelli
    metrics: NestingMetrics2L = Field(..., description="Metriche dettagliate del nesting 2L")
    
    # Informazioni autoclave
    autoclave_info: Dict[str, Any] = Field(..., description="Informazioni autoclave utilizzata")
    
    # Configurazione cavalletti utilizzata
    cavalletti_config: Optional[Dict[str, Any]] = Field(None, description="Configurazione cavalletti utilizzata")
    
    # Timestamp
    solved_at: datetime = Field(default_factory=datetime.now, description="Timestamp risoluzione")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Nesting 2L risolto con successo utilizzando algoritmo CP-SAT",
                "positioned_tools": [
                    {
                        "odl_id": 5,
                        "tool_id": 12,
                        "x": 150.0,
                        "y": 300.0,
                        "width": 400.0,
                        "height": 250.0,
                        "rotated": False,
                        "weight_kg": 35.5,
                        "level": 0,
                        "z_position": 0.0,
                        "lines_used": 2
                    },
                    {
                        "odl_id": 6,
                        "tool_id": 15,
                        "x": 200.0,
                        "y": 100.0,
                        "width": 300.0,
                        "height": 200.0,
                        "rotated": True,
                        "weight_kg": 28.0,
                        "level": 1,
                        "z_position": 100.0,
                        "lines_used": 1
                    }
                ],
                "cavalletti": [
                    {
                        "x": 220.0,
                        "y": 120.0,
                        "width": 80.0,
                        "height": 60.0,
                        "tool_odl_id": 6,
                        "tool_id": 15,
                        "sequence_number": 0,
                        "center_x": 260.0,
                        "center_y": 150.0,
                        "support_area_mm2": 4800.0
                    },
                    {
                        "x": 220.0,
                        "y": 240.0,
                        "width": 80.0,
                        "height": 60.0,
                        "tool_odl_id": 6,
                        "tool_id": 15,
                        "sequence_number": 1,
                        "center_x": 260.0,
                        "center_y": 270.0,
                        "support_area_mm2": 4800.0
                    }
                ],
                "excluded_odls": [],
                "excluded_reasons": {},
                "metrics": {
                    "area_utilization_pct": 72.5,
                    "vacuum_util_pct": 85.0,
                    "efficiency_score": 76.8,
                    "weight_utilization_pct": 68.2,
                    "time_solver_ms": 3250.0,
                    "fallback_used": False,
                    "algorithm_status": "CP-SAT_OPTIMAL_2L",
                    "total_area_cm2": 174000.0,
                    "total_weight_kg": 63.5,
                    "vacuum_lines_used": 3,
                    "pieces_positioned": 2,
                    "pieces_excluded": 0,
                    "level_0_count": 1,
                    "level_1_count": 1,
                    "level_0_weight_kg": 35.5,
                    "level_1_weight_kg": 28.0,
                    "level_0_area_pct": 41.7,
                    "level_1_area_pct": 25.0,
                    "cavalletti_used": 2,
                    "cavalletti_coverage_pct": 95.0,
                    "complexity_score": 1.8,
                    "timeout_used_seconds": 3.25
                },
                "autoclave_info": {
                    "id": 1,
                    "nome": "AeroTest-2L",
                    "larghezza_piano": 1200.0,
                    "lunghezza": 2000.0,
                    "max_load_kg": 500.0,
                    "num_linee_vuoto": 10,
                    "has_cavalletti": True,
                    "cavalletto_height": 100.0
                },
                "cavalletti_config": {
                    "cavalletto_width": 80.0,
                    "cavalletto_height": 60.0,
                    "min_distance_from_edge": 30.0,
                    "max_span_without_support": 400.0,
                    "prefer_symmetric": True
                },
                "solved_at": "2025-06-02T14:15:30.456789"
            }
        }

# ========== SCHEMI DI COMPATIBILITÀ PER MIGRAZIONE ==========

class NestingToolPositionCompat(BaseModel):
    """Schema di compatibilità che supporta sia il formato tradizionale che 2L"""
    # Campi base sempre presenti
    odl_id: int = Field(..., description="ID dell'ODL")
    tool_id: int = Field(..., description="ID del tool")
    x: float = Field(..., description="Posizione X in mm")
    y: float = Field(..., description="Posizione Y in mm")
    width: float = Field(..., description="Larghezza in mm")
    height: float = Field(..., description="Altezza in mm")
    rotated: bool = Field(default=False, description="Se il tool è ruotato")
    weight_kg: float = Field(..., description="Peso del tool in kg")
    
    # Campo per compatibilità con formato tradizionale
    plane: Optional[int] = Field(None, description="Piano di posizionamento (legacy: 1 o 2)")
    
    # Campo per nesting 2L
    level: Optional[int] = Field(None, description="Livello di posizionamento (2L: 0=piano, 1=cavalletto)")
    
    # Metadati aggiuntivi
    z_position: Optional[float] = Field(None, description="Posizione Z calcolata")
    lines_used: int = Field(default=1, description="Numero di linee vuoto utilizzate")
    
    def to_2l_format(self) -> PosizionamentoTool2L:
        """Converte al formato 2L, mappando plane->level se necessario"""
        level = self.level
        if level is None and self.plane is not None:
            # Mappa plane tradizionale (1,2) a level 2L (0,1)
            level = max(0, self.plane - 1)
        elif level is None:
            level = 0  # Default al piano base
            
        return PosizionamentoTool2L(
            odl_id=self.odl_id,
            tool_id=self.tool_id,
            x=self.x,
            y=self.y,
            width=self.width,
            height=self.height,
            rotated=self.rotated,
            weight_kg=self.weight_kg,
            level=level,
            z_position=self.z_position or (level * 100.0),
            lines_used=self.lines_used
        ) 