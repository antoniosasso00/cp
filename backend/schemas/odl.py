from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

# Schema base per le proprietà comuni
class ODLBase(BaseModel):
    parte_id: int = Field(..., description="ID della parte associata all'ordine di lavoro")
    tool_id: int = Field(..., description="ID del tool utilizzato per l'ordine di lavoro")
    priorita: int = Field(1, ge=1, description="Priorità dell'ordine di lavoro (numero più alto = priorità maggiore)")
    status: Literal["Preparazione", "Laminazione", "Attesa Cura", "Cura", "Finito"] = Field(
        "Preparazione", description="Stato corrente dell'ordine di lavoro"
    )
    note: Optional[str] = Field(None, description="Note aggiuntive sull'ordine di lavoro")

# Schema per la creazione
class ODLCreate(ODLBase):
    pass

# Schema per gli aggiornamenti
class ODLUpdate(BaseModel):
    parte_id: Optional[int] = Field(None, description="ID della parte associata all'ordine di lavoro")
    tool_id: Optional[int] = Field(None, description="ID del tool utilizzato per l'ordine di lavoro")
    priorita: Optional[int] = Field(None, ge=1, description="Priorità dell'ordine di lavoro (numero più alto = priorità maggiore)")
    status: Optional[Literal["Preparazione", "Laminazione", "Attesa Cura", "Cura", "Finito"]] = Field(
        None, description="Stato corrente dell'ordine di lavoro"
    )
    note: Optional[str] = Field(None, description="Note aggiuntive sull'ordine di lavoro")

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
class ODLRead(ODLBase):
    id: int = Field(..., description="ID univoco dell'ordine di lavoro")
    parte: ParteInODLResponse = Field(..., description="Informazioni sulla parte associata")
    tool: ToolInODLResponse = Field(..., description="Informazioni sul tool utilizzato")
    created_at: datetime = Field(..., description="Data e ora di creazione del record")
    updated_at: datetime = Field(..., description="Data e ora dell'ultimo aggiornamento")

    class Config:
        from_attributes = True

# Schema per la risposta semplificata (senza relazioni dettagliate)
class ODLReadBasic(ODLBase):
    id: int = Field(..., description="ID univoco dell'ordine di lavoro")
    created_at: datetime = Field(..., description="Data e ora di creazione del record")
    updated_at: datetime = Field(..., description="Data e ora dell'ultimo aggiornamento")

    class Config:
        from_attributes = True 