from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

# Schema base per le proprietà comuni
class CicloCuraBase(BaseModel):
    nome: str = Field(..., description="Nome identificativo del ciclo di cura")
    temperatura_max: float = Field(..., gt=0, description="Temperatura massima in gradi Celsius")
    pressione_max: float = Field(..., gt=0, description="Pressione massima in bar")
    
    # Stasi 1 (obbligatoria)
    temperatura_stasi1: float = Field(..., gt=0, description="Temperatura della prima stasi in gradi Celsius")
    pressione_stasi1: float = Field(..., gt=0, description="Pressione della prima stasi in bar")
    durata_stasi1: int = Field(..., gt=0, description="Durata della prima stasi in minuti")
    
    # Stasi 2 (opzionale)
    attiva_stasi2: bool = Field(False, description="Indica se è presente la seconda stasi")
    temperatura_stasi2: Optional[float] = Field(None, description="Temperatura della seconda stasi in gradi Celsius")
    pressione_stasi2: Optional[float] = Field(None, description="Pressione della seconda stasi in bar")
    durata_stasi2: Optional[int] = Field(None, description="Durata della seconda stasi in minuti")
    
    descrizione: Optional[str] = Field(None, description="Descrizione dettagliata del ciclo di cura")
    
    @validator('temperatura_stasi2', 'pressione_stasi2', 'durata_stasi2', pre=True, always=True)
    def validate_stasi2_fields(cls, v, values):
        if values.get('attiva_stasi2', False) and v is None:
            raise ValueError("Se la seconda stasi è attiva, questo campo non può essere vuoto")
        return v

# Schema per la creazione
class CicloCuraCreate(CicloCuraBase):
    pass

# Schema per gli aggiornamenti
class CicloCuraUpdate(BaseModel):
    nome: Optional[str] = Field(None, description="Nome identificativo del ciclo di cura")
    temperatura_max: Optional[float] = Field(None, gt=0, description="Temperatura massima in gradi Celsius")
    pressione_max: Optional[float] = Field(None, gt=0, description="Pressione massima in bar")
    
    temperatura_stasi1: Optional[float] = Field(None, gt=0, description="Temperatura della prima stasi in gradi Celsius")
    pressione_stasi1: Optional[float] = Field(None, gt=0, description="Pressione della prima stasi in bar")
    durata_stasi1: Optional[int] = Field(None, gt=0, description="Durata della prima stasi in minuti")
    
    attiva_stasi2: Optional[bool] = Field(None, description="Indica se è presente la seconda stasi")
    temperatura_stasi2: Optional[float] = Field(None, description="Temperatura della seconda stasi in gradi Celsius")
    pressione_stasi2: Optional[float] = Field(None, description="Pressione della seconda stasi in bar")
    durata_stasi2: Optional[int] = Field(None, description="Durata della seconda stasi in minuti")
    
    descrizione: Optional[str] = Field(None, description="Descrizione dettagliata del ciclo di cura")

# Schema per la risposta (include i campi generati dal database)
class CicloCuraResponse(CicloCuraBase):
    id: int = Field(..., description="ID univoco del ciclo di cura")
    created_at: datetime = Field(..., description="Data e ora di creazione del record")
    updated_at: datetime = Field(..., description="Data e ora dell'ultimo aggiornamento")

    class Config:
        from_attributes = True 