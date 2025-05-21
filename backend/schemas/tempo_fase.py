from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator
from enum import Enum


class TipoFase(str, Enum):
    LAMINAZIONE = "laminazione"
    ATTESA_CURA = "attesa_cura"
    CURA = "cura"


class TempoFaseBase(BaseModel):
    odl_id: int
    fase: TipoFase
    inizio_fase: datetime
    fine_fase: Optional[datetime] = None
    durata_minuti: Optional[int] = None
    note: Optional[str] = None
    
    @validator('durata_minuti', always=True)
    def calcola_durata(cls, v, values):
        """Calcola automaticamente la durata in minuti se sono presenti inizio e fine"""
        inizio = values.get('inizio_fase')
        fine = values.get('fine_fase')
        
        if inizio and fine and fine > inizio:
            # Calcola differenza in minuti
            delta = fine - inizio
            return int(delta.total_seconds() / 60)
        return None


class TempoFaseCreate(TempoFaseBase):
    pass


class TempoFaseUpdate(BaseModel):
    fase: Optional[TipoFase] = None
    inizio_fase: Optional[datetime] = None
    fine_fase: Optional[datetime] = None
    note: Optional[str] = None
    

class TempoFaseInDB(TempoFaseBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


# Schema per la risposta previsionale
class PrevisioneTempo(BaseModel):
    fase: TipoFase
    media_minuti: float
    numero_osservazioni: int 