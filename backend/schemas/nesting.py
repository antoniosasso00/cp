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
    
class NestingResultSchema(BaseModel):
    """Schema per il risultato dell'operazione di nesting"""
    success: bool
    message: str
    autoclavi: List[AutoclaveNestingInfo] = []
    odl_pianificati: List[ODLNestingInfo] = []
    odl_non_pianificabili: List[ODLNestingInfo] = []
    
# Schema per la risposta del database
class ParteInNestingResponse(BaseModel):
    id: int
    part_number: str
    descrizione_breve: str
    area: Optional[float] = None
    num_valvole_richieste: int
    
class ToolInNestingResponse(BaseModel):
    id: int
    codice: str
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
    created_at: datetime
    
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