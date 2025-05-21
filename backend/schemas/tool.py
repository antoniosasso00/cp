from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Schema base per le proprietà comuni
class ToolBase(BaseModel):
    codice: str = Field(..., max_length=50, description="Codice identificativo univoco dello stampo")
    descrizione: Optional[str] = Field(None, description="Descrizione dettagliata dello stampo")
    
    # Dimensioni fisiche
    lunghezza_piano: float = Field(..., gt=0, description="Lunghezza utile del tool")
    larghezza_piano: float = Field(..., gt=0, description="Larghezza utile del tool")
    
    note: Optional[str] = Field(None, description="Note aggiuntive sullo stampo")

# Schema per la creazione
class ToolCreate(ToolBase):
    disponibile: bool = Field(True, description="Indica se lo stampo è attualmente disponibile")

# Schema per gli aggiornamenti
class ToolUpdate(BaseModel):
    codice: Optional[str] = Field(None, max_length=50, description="Codice identificativo univoco dello stampo")
    descrizione: Optional[str] = Field(None, description="Descrizione dettagliata dello stampo")
    
    lunghezza_piano: Optional[float] = Field(None, gt=0, description="Lunghezza utile del tool")
    larghezza_piano: Optional[float] = Field(None, gt=0, description="Larghezza utile del tool")
    
    disponibile: Optional[bool] = Field(None, description="Indica se lo stampo è attualmente disponibile")
    
    note: Optional[str] = Field(None, description="Note aggiuntive sullo stampo")

# Schema per la risposta (include i campi generati dal database)
class ToolResponse(ToolBase):
    id: int = Field(..., description="ID univoco dello stampo")
    disponibile: bool = Field(..., description="Indica se lo stampo è attualmente disponibile")
    created_at: datetime = Field(..., description="Data e ora di creazione del record")
    updated_at: datetime = Field(..., description="Data e ora dell'ultimo aggiornamento")

    class Config:
        from_attributes = True 