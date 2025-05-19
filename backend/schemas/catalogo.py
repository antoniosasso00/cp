from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Schema base per le proprietà comuni
class CatalogoBase(BaseModel):
    descrizione: str = Field(..., description="Descrizione dettagliata del part number")
    categoria: Optional[str] = Field(None, description="Categoria del prodotto")
    attivo: bool = Field(True, description="Indica se il part number è ancora attivo nel catalogo")
    note: Optional[str] = Field(None, description="Note aggiuntive sul part number")

# Schema per la creazione
class CatalogoCreate(CatalogoBase):
    part_number: str = Field(..., max_length=50, description="Codice Part Number univoco")

# Schema per gli aggiornamenti
class CatalogoUpdate(CatalogoBase):
    descrizione: Optional[str] = Field(None, description="Descrizione dettagliata del part number")
    attivo: Optional[bool] = Field(None, description="Indica se il part number è ancora attivo")

# Schema per la risposta (include i campi generati dal database)
class CatalogoResponse(CatalogoBase):
    part_number: str = Field(..., description="Codice Part Number univoco")
    created_at: datetime = Field(..., description="Data e ora di creazione del record")
    updated_at: datetime = Field(..., description="Data e ora dell'ultimo aggiornamento")

    class Config:
        from_attributes = True 