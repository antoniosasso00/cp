from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

# Schema per i log ODL
class ODLLogBase(BaseModel):
    evento: str = Field(..., description="Tipo di evento")
    stato_precedente: Optional[str] = Field(None, description="Stato precedente dell'ODL")
    stato_nuovo: str = Field(..., description="Nuovo stato dell'ODL")
    descrizione: Optional[str] = Field(None, description="Descrizione dettagliata dell'evento")
    responsabile: Optional[str] = Field(None, description="Responsabile dell'evento")
    nesting_id: Optional[int] = Field(None, description="ID del nesting associato")
    autoclave_id: Optional[int] = Field(None, description="ID dell'autoclave utilizzata")
    schedule_entry_id: Optional[int] = Field(None, description="ID della schedulazione associata")

class ODLLogCreate(ODLLogBase):
    odl_id: int = Field(..., description="ID dell'ODL")

class ODLLogRead(ODLLogBase):
    id: int
    odl_id: int
    timestamp: datetime
    
    # Informazioni correlate (opzionali)
    nesting_stato: Optional[str] = Field(None, description="Stato del nesting associato")
    autoclave_nome: Optional[str] = Field(None, description="Nome dell'autoclave")
    
    class Config:
        from_attributes = True

# Schema per il monitoraggio completo di un ODL
class ODLMonitoringRead(BaseModel):
    # Informazioni base ODL
    id: int
    parte_id: int
    tool_id: int
    priorita: int
    status: str
    note: Optional[str]
    motivo_blocco: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    # Informazioni correlate
    parte_nome: str = Field(..., description="Nome della parte")
    parte_categoria: Optional[str] = Field(None, description="Categoria della parte")
    tool_nome: str = Field(..., description="Nome del tool")
    
    # Informazioni nesting
    nesting_id: Optional[int] = Field(None, description="ID del nesting corrente")
    nesting_stato: Optional[str] = Field(None, description="Stato del nesting")
    nesting_created_at: Optional[datetime] = Field(None, description="Data creazione nesting")
    
    # Informazioni autoclave
    autoclave_id: Optional[int] = Field(None, description="ID dell'autoclave assegnata")
    autoclave_nome: Optional[str] = Field(None, description="Nome dell'autoclave")
    
    # Informazioni ciclo di cura
    ciclo_cura_id: Optional[int] = Field(None, description="ID del ciclo di cura")
    ciclo_cura_nome: Optional[str] = Field(None, description="Nome del ciclo di cura")
    
    # Informazioni schedulazione
    schedule_entry_id: Optional[int] = Field(None, description="ID della schedulazione")
    schedule_start: Optional[datetime] = Field(None, description="Inizio schedulazione")
    schedule_end: Optional[datetime] = Field(None, description="Fine schedulazione")
    schedule_status: Optional[str] = Field(None, description="Stato schedulazione")
    
    # Log di avanzamento
    logs: List[ODLLogRead] = Field(default_factory=list, description="Log di avanzamento")
    
    # Statistiche temporali
    tempo_in_stato_corrente: Optional[int] = Field(None, description="Minuti nello stato corrente")
    tempo_totale_produzione: Optional[int] = Field(None, description="Minuti totali in produzione")
    
    class Config:
        from_attributes = True

# Schema per la vista riassuntiva del monitoraggio
class ODLMonitoringSummary(BaseModel):
    id: int
    parte_nome: str
    tool_nome: str
    status: str
    priorita: int
    created_at: datetime
    updated_at: datetime
    
    # Informazioni essenziali
    nesting_stato: Optional[str] = None
    autoclave_nome: Optional[str] = None
    ultimo_evento: Optional[str] = None
    ultimo_evento_timestamp: Optional[datetime] = None
    tempo_in_stato_corrente: Optional[int] = None
    
    class Config:
        from_attributes = True

# Schema per le statistiche generali del monitoraggio
class ODLMonitoringStats(BaseModel):
    totale_odl: int = Field(..., description="Numero totale di ODL")
    per_stato: dict = Field(..., description="Conteggio ODL per stato")
    in_ritardo: int = Field(0, description="ODL in ritardo")
    completati_oggi: int = Field(0, description="ODL completati oggi")
    media_tempo_completamento: Optional[float] = Field(None, description="Tempo medio di completamento in ore")
    
    class Config:
        from_attributes = True 