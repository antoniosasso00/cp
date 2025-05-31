from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# Enum per rappresentare i vari stati di un batch nesting
class StatoBatchNestingEnum(str, Enum):
    SOSPESO = "sospeso"
    CONFERMATO = "confermato"
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
    
    # Informazioni di audit
    creato_da_utente: Optional[str] = None
    creato_da_ruolo: Optional[str] = None
    confermato_da_utente: Optional[str] = None
    confermato_da_ruolo: Optional[str] = None
    data_conferma: Optional[datetime] = None
    
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