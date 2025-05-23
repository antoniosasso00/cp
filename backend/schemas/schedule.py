from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

# Enum per rappresentare i vari stati di una schedulazione
class ScheduleEntryStatusEnum(str, Enum):
    SCHEDULED = "scheduled"  # Schedulato automaticamente
    MANUAL = "manual"        # Schedulato manualmente
    DONE = "done"            # Completato

# Schema base per le proprietà comuni
class ScheduleEntryBase(BaseModel):
    odl_id: int = Field(..., description="ID dell'ODL schedulato")
    autoclave_id: int = Field(..., description="ID dell'autoclave per cui è schedulato l'ODL")
    start_datetime: datetime = Field(..., description="Data e ora di inizio della schedulazione")
    end_datetime: datetime = Field(..., description="Data e ora di fine della schedulazione")
    priority_override: bool = Field(False, description="Indica se la priorità è stata sovrascritta manualmente")

# Schema per la creazione
class ScheduleEntryCreate(ScheduleEntryBase):
    status: ScheduleEntryStatusEnum = Field(ScheduleEntryStatusEnum.MANUAL, description="Stato corrente della schedulazione")
    created_by: Optional[str] = Field(None, description="Utente che ha creato la schedulazione")

# Schema per la creazione automatica
class ScheduleEntryAutoCreate(BaseModel):
    date: str = Field(..., description="Data per cui generare lo scheduling (YYYY-MM-DD)")

# Schema per gli aggiornamenti
class ScheduleEntryUpdate(BaseModel):
    odl_id: Optional[int] = Field(None, description="ID dell'ODL schedulato")
    autoclave_id: Optional[int] = Field(None, description="ID dell'autoclave per cui è schedulato l'ODL")
    start_datetime: Optional[datetime] = Field(None, description="Data e ora di inizio della schedulazione")
    end_datetime: Optional[datetime] = Field(None, description="Data e ora di fine della schedulazione")
    status: Optional[ScheduleEntryStatusEnum] = Field(None, description="Stato corrente della schedulazione")
    priority_override: Optional[bool] = Field(None, description="Indica se la priorità è stata sovrascritta manualmente")
    created_by: Optional[str] = Field(None, description="Utente che ha creato la schedulazione")

# Schema per ODL incluso nella risposta
class ODLInScheduleResponse(BaseModel):
    id: int = Field(..., description="ID univoco dell'ordine di lavoro")
    priorita: int = Field(..., description="Priorità dell'ordine di lavoro")
    status: str = Field(..., description="Stato corrente dell'ordine di lavoro")
    parte_id: int = Field(..., description="ID della parte associata all'ordine di lavoro")
    tool_id: int = Field(..., description="ID del tool utilizzato per l'ordine di lavoro")

    class Config:
        from_attributes = True

# Schema per Autoclave inclusa nella risposta
class AutoclaveInScheduleResponse(BaseModel):
    id: int = Field(..., description="ID univoco dell'autoclave")
    nome: str = Field(..., description="Nome identificativo dell'autoclave")
    codice: str = Field(..., description="Codice univoco dell'autoclave")
    num_linee_vuoto: int = Field(..., description="Numero di linee vuoto disponibili")

    class Config:
        from_attributes = True

# Schema per la risposta completa
class ScheduleEntryRead(ScheduleEntryBase):
    id: int = Field(..., description="ID univoco della schedulazione")
    status: ScheduleEntryStatusEnum = Field(..., description="Stato corrente della schedulazione")
    created_by: Optional[str] = Field(None, description="Utente che ha creato la schedulazione")
    created_at: datetime = Field(..., description="Data e ora di creazione del record")
    updated_at: datetime = Field(..., description="Data e ora dell'ultimo aggiornamento")
    odl: ODLInScheduleResponse = Field(..., description="Informazioni sull'ODL schedulato")
    autoclave: AutoclaveInScheduleResponse = Field(..., description="Informazioni sull'autoclave per cui è schedulato l'ODL")

    class Config:
        from_attributes = True

# Schema per la risposta dell'auto-generazione
class AutoScheduleResponse(BaseModel):
    schedules: List[ScheduleEntryRead] = Field(..., description="Lista delle schedulazioni generate")
    message: str = Field(..., description="Messaggio informativo sul risultato dell'operazione")
    count: int = Field(..., description="Numero di schedulazioni generate")

    class Config:
        from_attributes = True 