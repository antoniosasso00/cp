from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

class ParteProduzioneRead(BaseModel):
    """Schema per le informazioni della parte nell'API di produzione"""
    id: int
    part_number: str
    descrizione_breve: str
    num_valvole_richieste: int
    
    class Config:
        from_attributes = True

class ToolProduzioneRead(BaseModel):
    """Schema per le informazioni del tool nell'API di produzione"""
    id: int
    part_number_tool: str
    descrizione: Optional[str] = None
    
    class Config:
        from_attributes = True

class ODLProduzioneRead(BaseModel):
    """Schema per ODL nell'API di produzione con informazioni essenziali"""
    id: int
    parte_id: int
    tool_id: int
    priorita: int
    status: str
    note: Optional[str] = None
    motivo_blocco: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Relazioni
    parte: Optional[ParteProduzioneRead] = None
    tool: Optional[ToolProduzioneRead] = None
    
    class Config:
        from_attributes = True

class StatisticheProduzione(BaseModel):
    """Schema per le statistiche di produzione"""
    totale_attesa_cura: int
    totale_in_cura: int
    ultima_sincronizzazione: datetime

class ProduzioneODLResponse(BaseModel):
    """Schema per la risposta dell'endpoint /produzione/odl"""
    attesa_cura: List[ODLProduzioneRead]
    in_cura: List[ODLProduzioneRead]
    statistiche: StatisticheProduzione

class AutoclaveStats(BaseModel):
    """Schema per le statistiche delle autoclavi"""
    disponibili: int
    occupate: int
    totali: int

class BatchNestingStats(BaseModel):
    """Schema per le statistiche dei batch nesting"""
    attivi: int

class ProduzioneGiornaliera(BaseModel):
    """Schema per la produzione giornaliera"""
    odl_completati_oggi: int
    data: str

class StatisticheGeneraliResponse(BaseModel):
    """Schema per la risposta dell'endpoint /produzione/statistiche"""
    odl_per_stato: Dict[str, int]
    autoclavi: AutoclaveStats
    batch_nesting: BatchNestingStats
    produzione_giornaliera: ProduzioneGiornaliera
    timestamp: datetime

class HealthCheckResponse(BaseModel):
    """Schema per la risposta dell'endpoint /produzione/health"""
    status: str
    database: str
    odl_totali: str
    autoclavi_totali: str
    timestamp: datetime 