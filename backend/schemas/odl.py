from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime
from enum import Enum

# Schema base per le proprietà comuni
class ODLStatus(str, Enum):
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ODLPhase(str, Enum):
    LAMINAZIONE = "laminazione"
    PRE_NESTING = "pre_nesting"
    NESTING = "nesting"
    AUTOCLAVE = "autoclave"
    POST = "post"

class ParteInODL(BaseModel):
    parte_id: int = Field(..., description="ID della parte da includere nell'ODL")
    quantity: int = Field(gt=0, description="Quantità richiesta")
    status: str = Field(default="created", description="Stato della parte nell'ODL")

class ODLBase(BaseModel):
    code: str = Field(..., description="Codice univoco dell'ODL")
    description: Optional[str] = Field(None, description="Descrizione dell'ODL")

class ODLCreate(ODLBase):
    parti: List[ParteInODL] = Field(..., description="Lista delle parti da includere nell'ODL")

class ODLUpdate(BaseModel):
    description: Optional[str] = None
    status: Optional[ODLStatus] = None
    current_phase: Optional[ODLPhase] = None

class ParteDetail(BaseModel):
    id: int
    part_number: str
    descrizione_breve: str
    num_valvole_richieste: int
    tools: List[dict]
    quantity: int
    status: str
    last_updated: datetime

    class Config:
        from_attributes = True

class ODLInDB(ODLBase):
    id: int
    status: ODLStatus
    current_phase: ODLPhase
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ODL(ODLInDB):
    parti: List[ParteDetail]

    class Config:
        from_attributes = True

# Schema per parte inclusa nella risposta
class ParteInODLResponse(BaseModel):
    id: int = Field(..., description="ID univoco della parte")
    part_number: str = Field(..., description="Part Number associato dal catalogo")
    descrizione_breve: str = Field(..., description="Descrizione breve della parte")

    class Config:
        from_attributes = True

# Schema per tool incluso nella risposta
class ToolInODLResponse(BaseModel):
    id: int = Field(..., description="ID univoco dello stampo")
    codice: str = Field(..., description="Codice identificativo univoco dello stampo")
    descrizione: Optional[str] = Field(None, description="Descrizione dettagliata dello stampo")

    class Config:
        from_attributes = True

# Schema per la risposta completa
class ODLRead(ODLInDB):
    parte: ParteInODLResponse = Field(..., description="Informazioni sulla parte associata")
    tool: ToolInODLResponse = Field(..., description="Informazioni sul tool utilizzato")

    class Config:
        from_attributes = True

# Schema per la risposta semplificata (senza relazioni dettagliate)
class ODLReadBasic(ODLInDB):
    created_at: datetime = Field(..., description="Data e ora di creazione del record")
    updated_at: datetime = Field(..., description="Data e ora dell'ultimo aggiornamento")

    class Config:
        from_attributes = True 