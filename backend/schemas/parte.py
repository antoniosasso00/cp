from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Schema base per le proprietà comuni
class ParteBase(BaseModel):
    part_number: str = Field(..., description="Part Number associato dal catalogo")
    descrizione_breve: str = Field(..., max_length=255, description="Descrizione breve della parte")
    num_valvole_richieste: int = Field(1, ge=1, description="Numero di valvole richieste per la cura")
    note_produzione: Optional[str] = Field(None, description="Note specifiche per la produzione")

# Schema per la creazione
class ParteCreate(ParteBase):
    ciclo_cura_id: Optional[int] = Field(None, description="ID del ciclo di cura associato")
    tool_ids: List[int] = Field([], description="Lista di ID degli stampi associati alla parte")

# Schema per gli aggiornamenti
class ParteUpdate(BaseModel):
    part_number: Optional[str] = Field(None, description="Part Number associato dal catalogo")
    descrizione_breve: Optional[str] = Field(None, max_length=255, description="Descrizione breve della parte")
    num_valvole_richieste: Optional[int] = Field(None, ge=1, description="Numero di valvole richieste per la cura")
    note_produzione: Optional[str] = Field(None, description="Note specifiche per la produzione")
    ciclo_cura_id: Optional[int] = Field(None, description="ID del ciclo di cura associato")
    tool_ids: Optional[List[int]] = Field(None, description="Lista di ID degli stampi associati alla parte")

# Schema per tool incluso nella risposta
class ToolInParteResponse(BaseModel):
    id: int = Field(..., description="ID univoco dello stampo")
    part_number_tool: str = Field(..., description="Part Number Tool identificativo univoco dello stampo")
    descrizione: Optional[str] = Field(None, description="Descrizione dettagliata dello stampo")

    class Config:
        from_attributes = True

# Schema per ciclo di cura incluso nella risposta
class CicloCuraInParteResponse(BaseModel):
    id: int = Field(..., description="ID univoco del ciclo di cura")
    nome: str = Field(..., description="Nome identificativo del ciclo di cura") 

    class Config:
        from_attributes = True

# Schema per catalogo incluso nella risposta
class CatalogoInParteResponse(BaseModel):
    part_number: str = Field(..., description="Codice Part Number univoco")
    descrizione: str = Field(..., description="Descrizione dettagliata del part number")
    categoria: Optional[str] = Field(None, description="Categoria del prodotto")

    class Config:
        from_attributes = True

# Schema per la risposta (include i campi generati dal database e le relazioni)
class ParteResponse(ParteBase):
    id: int = Field(..., description="ID univoco della parte")
    ciclo_cura: Optional[CicloCuraInParteResponse] = Field(None, description="Ciclo di cura associato")
    tools: List[ToolInParteResponse] = Field([], description="Stampi associati alla parte")
    catalogo: CatalogoInParteResponse = Field(..., description="Informazioni dal catalogo")
    created_at: datetime = Field(..., description="Data e ora di creazione del record")
    updated_at: datetime = Field(..., description="Data e ora dell'ultimo aggiornamento")

    class Config:
        from_attributes = True 