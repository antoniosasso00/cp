from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

# Enum per rappresentare i vari stati operativi di un'autoclave
class StatoAutoclaveEnum(str, Enum):
    DISPONIBILE = "DISPONIBILE"
    IN_USO = "IN_USO"
    MANUTENZIONE = "MANUTENZIONE"
    GUASTO = "GUASTO"
    SPENTA = "SPENTA"

# Schema base per le proprietà comuni
class AutoclaveBase(BaseModel):
    nome: str = Field(..., max_length=100, description="Nome identificativo dell'autoclave")
    codice: str = Field(..., max_length=50, description="Codice univoco dell'autoclave")
    
    # Dimensioni fisiche
    lunghezza: float = Field(..., gt=0, description="Lunghezza interna in mm")
    larghezza_piano: float = Field(..., gt=0, description="Larghezza utile del piano di carico")
    
    # Capacità e specifiche tecniche
    num_linee_vuoto: int = Field(..., gt=0, description="Numero di linee vuoto disponibili")
    temperatura_max: float = Field(..., gt=0, description="Temperatura massima in gradi Celsius")
    pressione_max: float = Field(..., gt=0, description="Pressione massima in bar")
    
    # Informazioni aggiuntive
    produttore: Optional[str] = Field(None, max_length=100, description="Nome del produttore dell'autoclave")
    anno_produzione: Optional[int] = Field(None, description="Anno di produzione dell'autoclave")
    note: Optional[str] = Field(None, description="Note aggiuntive sull'autoclave")

# Schema per la creazione
class AutoclaveCreate(AutoclaveBase):
    stato: StatoAutoclaveEnum = Field(StatoAutoclaveEnum.DISPONIBILE, description="Stato attuale dell'autoclave")

# Schema per gli aggiornamenti
class AutoclaveUpdate(BaseModel):
    nome: Optional[str] = Field(None, max_length=100, description="Nome identificativo dell'autoclave")
    codice: Optional[str] = Field(None, max_length=50, description="Codice univoco dell'autoclave")
    
    lunghezza: Optional[float] = Field(None, gt=0, description="Lunghezza interna in mm")
    larghezza_piano: Optional[float] = Field(None, gt=0, description="Larghezza utile del piano di carico")
    
    num_linee_vuoto: Optional[int] = Field(None, gt=0, description="Numero di linee vuoto disponibili")
    temperatura_max: Optional[float] = Field(None, gt=0, description="Temperatura massima in gradi Celsius")
    pressione_max: Optional[float] = Field(None, gt=0, description="Pressione massima in bar")
    
    stato: Optional[StatoAutoclaveEnum] = Field(None, description="Stato attuale dell'autoclave")
    
    produttore: Optional[str] = Field(None, max_length=100, description="Nome del produttore dell'autoclave")
    anno_produzione: Optional[int] = Field(None, description="Anno di produzione dell'autoclave")
    note: Optional[str] = Field(None, description="Note aggiuntive sull'autoclave")

# Schema per la risposta (include i campi generati dal database)
class AutoclaveResponse(AutoclaveBase):
    id: int = Field(..., description="ID univoco dell'autoclave")
    stato: StatoAutoclaveEnum = Field(..., description="Stato attuale dell'autoclave")
    created_at: datetime = Field(..., description="Data e ora di creazione del record")
    updated_at: datetime = Field(..., description="Data e ora dell'ultimo aggiornamento")

    class Config:
        from_attributes = True 