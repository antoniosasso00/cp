from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

# Importiamo gli enum direttamente dal modello per evitare inconsistenze
from models.system_log import LogLevel, EventType, UserRole

class SystemLogBase(BaseModel):
    """Schema base per i log di sistema"""
    level: LogLevel = LogLevel.INFO
    event_type: EventType
    user_role: UserRole
    user_id: Optional[str] = None
    action: str = Field(..., max_length=200, description="Descrizione breve dell'azione")
    entity_type: Optional[str] = Field(None, max_length=50, description="Tipo di entità (odl, tool, etc.)")
    entity_id: Optional[int] = None
    details: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    ip_address: Optional[str] = Field(None, max_length=45)

class SystemLogCreate(SystemLogBase):
    """Schema per la creazione di un log"""
    pass

class SystemLogResponse(SystemLogBase):
    """Schema per la risposta di un log"""
    id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True

class SystemLogFilter(BaseModel):
    """Schema per filtrare i log"""
    event_type: Optional[EventType] = None
    user_role: Optional[UserRole] = None
    level: Optional[LogLevel] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: Optional[int] = Field(100, ge=1, le=1000)
    offset: Optional[int] = Field(0, ge=0)

class SystemLogStats(BaseModel):
    """Schema per le statistiche dei log"""
    total_logs: int
    logs_by_type: dict
    logs_by_role: dict
    logs_by_level: dict
    recent_errors: List[SystemLogResponse] 