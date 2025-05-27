from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

class StatoNestingEnum(str, Enum):
    """Enum per lo stato del nesting"""
    BOZZA = "bozza"
    IN_SOSPESO = "in_sospeso"
    CONFERMATO = "confermato"
    ANNULLATO = "annullato"
    COMPLETATO = "completato"

class NestingODLStatus(str, Enum):
    """Enum per gli stati degli ODL nel processo di nesting"""
    PIANIFICATO = "pianificato"
    NON_PIANIFICABILE = "non_pianificabile"
    
# ✅ NUOVO: Enum per la priorità di ottimizzazione
class PrioritaOttimizzazione(str, Enum):
    """Enum per la priorità di ottimizzazione del nesting"""
    PESO = "peso"
    AREA = "area"
    EQUILIBRATO = "equilibrato"

# ✅ AGGIORNATO: Schema per i parametri di nesting regolabili
class NestingParameters(BaseModel):
    """Schema per i parametri regolabili del nesting"""
    padding_mm: float = Field(
        default=10.0, 
        ge=0.0, 
        le=50.0,
        description="Spaziatura tra tool in mm"
    )
    borda_mm: float = Field(
        default=20.0, 
        ge=0.0, 
        le=100.0,
        description="Bordo minimo dall'autoclave in mm"
    )
    max_valvole_per_autoclave: Optional[int] = Field(
        default=None,
        ge=1,
        description="Limite massimo valvole per autoclave (opzionale)"
    )
    rotazione_abilitata: bool = Field(
        default=True,
        description="Abilita la rotazione automatica dei tool per ottimizzare lo spazio"
    )
    priorita_ottimizzazione: PrioritaOttimizzazione = Field(
        default=PrioritaOttimizzazione.EQUILIBRATO,
        description="Priorità di ottimizzazione: peso, area o equilibrato"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "padding_mm": 10.0,
                "borda_mm": 20.0,
                "max_valvole_per_autoclave": None,
                "rotazione_abilitata": True,
                "priorita_ottimizzazione": "equilibrato"
            }
        }

class ODLNestingInfo(BaseModel):
    """Schema per l'informazione di un ODL nel nesting"""
    id: int
    parte_descrizione: str
    num_valvole: int
    priorita: int
    status: NestingODLStatus
    
class AutoclaveNestingInfo(BaseModel):
    """Schema per l'informazione di un'autoclave nel nesting"""
    id: int
    nome: str
    area_disponibile: float
    valvole_disponibili: int
    peso_max_kg: float
    
class NestingResultSchema(BaseModel):
    """Schema per il risultato dell'operazione di nesting"""
    success: bool
    message: str
    autoclavi: List[AutoclaveNestingInfo] = []
    odl_pianificati: List[ODLNestingInfo] = []
    odl_non_pianificabili: List[ODLNestingInfo] = []

# Nuovi schemi per la preview
class ODLPreviewInfo(BaseModel):
    """Schema per l'anteprima di un ODL nel nesting"""
    id: int
    part_number: str
    descrizione: str
    area_cm2: float
    num_valvole: int
    priorita: int
    color: str = Field(default="#3B82F6", description="Colore per la visualizzazione")

class AutoclavePreviewInfo(BaseModel):
    """Schema per l'anteprima dell'autoclave nel nesting"""
    id: int
    nome: str
    codice: str
    lunghezza: float  # mm
    larghezza_piano: float  # mm
    area_totale_cm2: float
    area_utilizzata_cm2: float
    valvole_totali: int
    valvole_utilizzate: int
    odl_inclusi: List[ODLPreviewInfo] = []
    ciclo_cura_id: Optional[int] = Field(None, description="ID del ciclo di cura assegnato")
    ciclo_cura_nome: Optional[str] = Field(None, description="Nome del ciclo di cura assegnato")
    
# ✅ NUOVO: Schema per la creazione di un nesting
class NestingCreate(BaseModel):
    """Schema per la creazione di un nuovo nesting"""
    autoclave_id: int
    odl_ids: List[int]
    parametri: Optional[NestingParameters] = None
    note: Optional[str] = None

# ✅ NUOVO: Schema per l'aggiornamento di un nesting
class NestingUpdate(BaseModel):
    """Schema per l'aggiornamento di un nesting"""
    stato: Optional[StatoNestingEnum] = None
    parametri: Optional[NestingParameters] = None
    note: Optional[str] = None
    confermato_da_ruolo: Optional[str] = None

# ✅ NUOVO: Schema per la risposta di un nesting
class NestingResponse(BaseModel):
    """Schema per la risposta di un nesting"""
    id: int
    autoclave_id: int
    autoclave_nome: Optional[str] = None
    odl_ids: List[int]
    odl_esclusi_ids: List[int] = []
    motivi_esclusione: List[Dict] = []
    stato: StatoNestingEnum
    confermato_da_ruolo: Optional[str] = None
    
    # Parametri utilizzati
    padding_mm: float
    borda_mm: float
    max_valvole_per_autoclave: Optional[int] = None
    rotazione_abilitata: bool
    
    # Statistiche
    area_utilizzata: float
    area_totale: float
    valvole_utilizzate: int
    valvole_totali: int
    peso_totale_kg: float
    area_piano_1: float
    area_piano_2: float
    superficie_piano_2_max: Optional[float] = None
    
    # Posizioni e note
    posizioni_tool: List[Dict] = []
    note: Optional[str] = None
    
    # Timestamp
    created_at: datetime
    updated_at: datetime
    
    # Proprietà calcolate
    is_editable: bool
    is_confirmed: bool
    
    class Config:
        from_attributes = True

# ✅ NUOVO: Schema per il batch multi-autoclave
class BatchNestingRequest(BaseModel):
    """Schema per la richiesta di batch nesting multi-autoclave"""
    parametri: Optional[NestingParameters] = None
    note: Optional[str] = None
    forza_generazione: bool = Field(default=False, description="Forza la generazione anche se ci sono pochi ODL")

class BatchNestingResponse(BaseModel):
    """Schema per la risposta del batch nesting multi-autoclave"""
    success: bool
    message: str
    nesting_creati: List[NestingResponse] = []
    odl_non_assegnati: List[ODLNestingInfo] = []
    statistiche: Dict[str, Any] = {}

# ✅ AGGIORNATO: Schema per l'anteprima del nesting
class NestingPreviewSchema(BaseModel):
    """Schema per l'anteprima del nesting con parametri personalizzabili"""
    success: bool
    message: str
    parametri_utilizzati: NestingParameters
    autoclavi_disponibili: List[AutoclaveNestingInfo] = []
    odl_disponibili: List[ODLNestingInfo] = []
    preview_risultati: List[Dict[str, Any]] = []
    statistiche_globali: Dict[str, Any] = {}

# Schema per la risposta del database
class ParteInNestingResponse(BaseModel):
    id: int
    part_number: str
    descrizione_breve: str
    area: Optional[float] = None
    num_valvole_richieste: int
    
class ToolInNestingResponse(BaseModel):
    id: int
    part_number_tool: str
    descrizione: Optional[str] = None

class ODLInNestingResponse(BaseModel):
    id: int
    parte: ParteInNestingResponse
    tool: ToolInNestingResponse
    priorita: int
    
class AutoclaveInNestingResponse(BaseModel):
    id: int
    nome: str
    codice: str
    num_linee_vuoto: int
    lunghezza: float
    larghezza_piano: float
    
class NestingResultRead(BaseModel):
    id: int
    autoclave: AutoclaveInNestingResponse
    odl_list: List[ODLInNestingResponse]
    area_utilizzata: float
    area_totale: float
    valvole_utilizzate: int
    valvole_totali: int
    stato: str
    confermato_da_ruolo: Optional[str] = None
    odl_esclusi_ids: List[int] = []
    motivi_esclusione: List[Dict] = []
    created_at: datetime
    updated_at: Optional[datetime] = None
    note: Optional[str] = None
    ciclo_cura_id: Optional[int] = None
    ciclo_cura_nome: Optional[str] = None
    
    class Config:
        from_attributes = True

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Nesting completato con successo",
                "autoclavi": [
                    {
                        "id": 1,
                        "nome": "Autoclave 1",
                        "odl_assegnati": [10, 15, 18],
                        "valvole_utilizzate": 5,
                        "valvole_totali": 12,
                        "area_utilizzata": 4.5,
                        "area_totale": 10.0
                    }
                ],
                "odl_pianificati": [
                    {
                        "id": 10,
                        "parte_descrizione": "Pannello A",
                        "num_valvole": 2,
                        "priorita": 3,
                        "status": "pianificato"
                    }
                ],
                "odl_non_pianificabili": [
                    {
                        "id": 11,
                        "parte_descrizione": "Pannello B",
                        "num_valvole": 8,
                        "priorita": 1,
                        "status": "non_pianificabile"
                    }
                ]
            }
        }

# Schema per il nesting manuale
class ManualNestingRequest(BaseModel):
    """Schema per la richiesta di nesting manuale"""
    odl_ids: List[int] = Field(..., description="Lista degli ID degli ODL da includere nel nesting", min_items=1)
    note: Optional[str] = Field(None, description="Note opzionali per il nesting")
    
    class Config:
        json_schema_extra = {
            "example": {
                "odl_ids": [1, 2, 3],
                "note": "Nesting manuale creato dal management"
            }
        } 