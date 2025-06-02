from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# Enum per rappresentare i vari stati di un batch nesting
class StatoBatchNestingEnum(str, Enum):
    DRAFT = "draft"
    SOSPESO = "sospeso"
    CONFERMATO = "confermato"
    LOADED = "loaded"
    CURED = "cured"
    TERMINATO = "terminato"

# Schema per i parametri di nesting
class ParametriNesting(BaseModel):
    """Schema per validare i parametri utilizzati nella generazione del nesting"""
    padding_mm: float = Field(default=20.0, ge=0, le=100, 
                             description="Padding in millimetri tra i tool")
    min_distance_mm: float = Field(default=15.0, ge=0, le=50,
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
                "padding_mm": 20.0,
                "min_distance_mm": 15.0,
                "priorita_area": True,
                "accorpamento_odl": False,
                "use_secondary_plane": False,
                "max_weight_per_plane_kg": 500.0
            }
        }

# Schema per la configurazione del layout (output del canvas React)
class ConfigurazioneLayout(BaseModel):
    """Schema per la configurazione del layout generato dal frontend"""
    canvas_width: float = Field(..., description="Larghezza del canvas in pixel")
    canvas_height: float = Field(..., description="Altezza del canvas in pixel")
    scale_factor: float = Field(default=1.0, description="Fattore di scala del canvas")
    tool_positions: List[Dict[str, Any]] = Field(default=[], 
                                                description="Posizioni dei tool sul canvas")
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

class NestingSolveRequest(BaseModel):
    """Schema per la richiesta di risoluzione nesting v1.4.12-DEMO"""
    autoclave_id: int = Field(..., description="ID dell'autoclave da utilizzare")
    odl_ids: Optional[List[int]] = Field(None, description="Lista specifica di ODL (se None, usa tutti quelli disponibili)")
    
    # Parametri algoritmo
    padding_mm: float = Field(default=20.0, ge=5, le=50, description="Padding tra tool in mm")
    min_distance_mm: float = Field(default=15.0, ge=5, le=30, description="Distanza minima dai bordi in mm")
    vacuum_lines_capacity: int = Field(default=10, ge=1, le=50, description="Capacità massima linee vuoto")
    
    # Nuovi parametri v1.4.12-DEMO
    allow_heuristic: bool = Field(default=False, description="Abilita euristica RRGH")
    timeout_override: Optional[int] = Field(None, ge=30, le=300, description="Override timeout in secondi")
    heavy_piece_threshold_kg: float = Field(default=50.0, ge=10, le=200, description="Soglia peso per constraint posizionamento")
    
    class Config:
        json_schema_extra = {
            "example": {
                "autoclave_id": 1,
                "odl_ids": None,
                "padding_mm": 20.0,
                "min_distance_mm": 15.0,
                "vacuum_lines_capacity": 8,
                "allow_heuristic": True,
                "timeout_override": None,
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