from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any, Union
from datetime import datetime

class NestingParameters(BaseModel):
    """Schema per i parametri di ottimizzazione del nesting"""
    peso_valvole: float = Field(default=1.0, ge=0.0, le=10.0, 
                              description="Peso assegnato all'utilizzo delle valvole (0-10)")
    peso_area: float = Field(default=1.0, ge=0.0, le=10.0, 
                           description="Peso assegnato all'utilizzo dell'area (0-10)")
    peso_priorita: float = Field(default=1.0, ge=0.0, le=10.0, 
                               description="Peso assegnato alla priorità degli ODL (0-10)")
    spazio_minimo_mm: float = Field(default=50.0, ge=0.0, 
                                  description="Spazio minimo in mm tra gli ODL nell'autoclave")

    class Config:
        schema_extra = {
            "example": {
                "peso_valvole": 2.0,
                "peso_area": 3.0,
                "peso_priorita": 5.0,
                "spazio_minimo_mm": 30.0
            }
        }

class NestingRequest(BaseModel):
    """Schema per la richiesta di nesting"""
    odl_ids: Optional[List[int]] = Field(default=None, 
                                     description="Lista degli ID degli ODL da considerare per il nesting. Se non specificato, considera tutti gli ODL in stato 'Attesa Cura'")
    autoclave_ids: Optional[List[int]] = Field(default=None, 
                                          description="Lista degli ID delle autoclavi da considerare. Se non specificato, considera tutte le autoclavi disponibili")
    parameters: Optional[NestingParameters] = Field(default=None, 
                                                description="Parametri di ottimizzazione personalizzati. Se non specificati, usa i parametri di default")
    manual: bool = Field(default=False, 
                       description="Se True, esegue il nesting solo con gli ODL specificati")

class ODLLayout(BaseModel):
    """Dettagli di posizionamento di un ODL nell'autoclave"""
    odl_id: int
    x: float
    y: float
    lunghezza: float
    larghezza: float
    valvole_utilizzate: int
    parte_nome: str
    tool_codice: str
    priorita: int

class AutoclaveLayout(BaseModel):
    """Layout completo degli ODL in un'autoclave"""
    autoclave_id: int
    autoclave_nome: str
    odl_layout: List[ODLLayout]
    area_totale_mm2: float
    area_utilizzata_mm2: float
    efficienza_area: float
    valvole_totali: int
    valvole_utilizzate: int
    nesting_id: Optional[int] = None

class NestingResponse(BaseModel):
    """Schema per la risposta del nesting"""
    success: bool
    message: str
    layouts: List[AutoclaveLayout] = []
    timestamp: datetime = Field(default_factory=datetime.now)

class NestingConfirmRequest(BaseModel):
    """Schema per la conferma di un risultato di nesting"""
    nesting_id: int = Field(..., description="ID del risultato di nesting da confermare")

class NestingResultResponse(BaseModel):
    """Schema per la risposta con i risultati di nesting salvati"""
    id: int
    codice: str
    autoclave_nome: str
    confermato: bool
    data_conferma: Optional[datetime]
    efficienza_area: float
    valvole_utilizzate: int
    valvole_totali: int
    generato_manualmente: bool
    created_at: datetime 