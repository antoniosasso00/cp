from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime

class ODLAlertBase(BaseModel):
    """Schema base per gli alert ODL"""
    odl_id: int = Field(..., description="ID dell'ODL associato")
    tipo: Literal["ritardo", "blocco", "warning", "critico"] = Field(..., description="Tipo di alert")
    titolo: str = Field(..., description="Titolo dell'alert")
    descrizione: str = Field(..., description="Descrizione dettagliata")
    azione_suggerita: Optional[str] = Field(None, description="Azione suggerita per risolvere")

class ODLAlertCreate(ODLAlertBase):
    """Schema per la creazione di un alert ODL"""
    pass

class ODLAlertRead(ODLAlertBase):
    """Schema per la lettura di un alert ODL"""
    id: str = Field(..., description="ID univoco dell'alert")
    timestamp: datetime = Field(..., description="Timestamp di creazione")
    parte_nome: Optional[str] = Field(None, description="Nome della parte")
    tool_nome: Optional[str] = Field(None, description="Nome del tool")
    tempo_in_stato: Optional[int] = Field(None, description="Tempo nello stato corrente (minuti)")
    
    class Config:
        from_attributes = True

class ODLAlertsResponse(BaseModel):
    """Schema per la risposta con lista di alert"""
    alerts: List[ODLAlertRead] = Field(..., description="Lista degli alert")
    totale: int = Field(..., description="Numero totale di alert")
    per_tipo: dict = Field(..., description="Conteggio per tipo di alert") 