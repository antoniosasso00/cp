from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

# Schema base per le proprietà comuni
class CicloCuraBase(BaseModel):
    nome: str = Field(..., description="Nome identificativo del ciclo di cura")
    temperatura_max: float = Field(..., gt=0, description="Temperatura massima in gradi Celsius")
    pressione_max: float = Field(..., gt=0, description="Pressione massima in bar")
    tempo_totale: int = Field(..., gt=0, description="Tempo totale del ciclo in minuti")
    
    # Parametri per la prima stasi
    stasi1_attiva: bool = Field(True, description="Indica se è presente la prima stasi")
    stasi1_temperatura: Optional[float] = Field(None, description="Temperatura della prima stasi in gradi Celsius")
    stasi1_pressione: Optional[float] = Field(None, description="Pressione della prima stasi in bar")
    stasi1_durata: Optional[int] = Field(None, description="Durata della prima stasi in minuti")
    
    # Parametri per la seconda stasi (opzionale)
    stasi2_attiva: bool = Field(False, description="Indica se è presente la seconda stasi")
    stasi2_temperatura: Optional[float] = Field(None, description="Temperatura della seconda stasi in gradi Celsius")
    stasi2_pressione: Optional[float] = Field(None, description="Pressione della seconda stasi in bar")
    stasi2_durata: Optional[int] = Field(None, description="Durata della seconda stasi in minuti")
    
    descrizione: Optional[str] = Field(None, description="Descrizione dettagliata del ciclo di cura")
    
    @validator('stasi1_temperatura', 'stasi1_pressione', 'stasi1_durata', pre=True, always=True)
    def validate_stasi1_fields(cls, v, values):
        if values.get('stasi1_attiva', True) and v is None:
            raise ValueError("Se la prima stasi è attiva, questo campo non può essere vuoto")
        return v
    
    @validator('stasi2_temperatura', 'stasi2_pressione', 'stasi2_durata', pre=True, always=True)
    def validate_stasi2_fields(cls, v, values):
        if values.get('stasi2_attiva', False) and v is None:
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
    tempo_totale: Optional[int] = Field(None, gt=0, description="Tempo totale del ciclo in minuti")
    
    stasi1_attiva: Optional[bool] = Field(None, description="Indica se è presente la prima stasi")
    stasi1_temperatura: Optional[float] = Field(None, description="Temperatura della prima stasi in gradi Celsius")
    stasi1_pressione: Optional[float] = Field(None, description="Pressione della prima stasi in bar")
    stasi1_durata: Optional[int] = Field(None, description="Durata della prima stasi in minuti")
    
    stasi2_attiva: Optional[bool] = Field(None, description="Indica se è presente la seconda stasi")
    stasi2_temperatura: Optional[float] = Field(None, description="Temperatura della seconda stasi in gradi Celsius")
    stasi2_pressione: Optional[float] = Field(None, description="Pressione della seconda stasi in bar")
    stasi2_durata: Optional[int] = Field(None, description="Durata della seconda stasi in minuti")
    
    descrizione: Optional[str] = Field(None, description="Descrizione dettagliata del ciclo di cura")

# Schema per la risposta (include i campi generati dal database)
class CicloCuraResponse(CicloCuraBase):
    id: int = Field(..., description="ID univoco del ciclo di cura")
    created_at: datetime = Field(..., description="Data e ora di creazione del record")
    updated_at: datetime = Field(..., description="Data e ora dell'ultimo aggiornamento")

    class Config:
        from_attributes = True 