from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

class NestingODLStatus(str, Enum):
    """Enum per gli stati degli ODL nel processo di nesting"""
    PIANIFICATO = "pianificato"
    NON_PIANIFICABILE = "non_pianificabile"
    
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
    odl_assegnati: List[int] = Field(..., description="IDs degli ODL assegnati a questa autoclave")
    valvole_utilizzate: int
    valvole_totali: int
    area_utilizzata: float
    area_totale: float
    ciclo_cura_id: Optional[int] = Field(None, description="ID del ciclo di cura assegnato")
    ciclo_cura_nome: Optional[str] = Field(None, description="Nome del ciclo di cura assegnato")
    
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
    
class NestingPreviewSchema(BaseModel):
    """Schema per l'anteprima del nesting"""
    success: bool
    message: str
    autoclavi: List[AutoclavePreviewInfo] = []
    odl_esclusi: List[Dict[str, Any]] = Field(
        default=[], 
        description="Lista degli ODL esclusi con motivazioni"
    )
    
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
                "note": "Nesting manuale creato dal responsabile"
            }
        } 