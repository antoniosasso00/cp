from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class ReportRangeType(str, Enum):
    """Enum per i tipi di periodo del report"""
    GIORNO = "giorno"
    SETTIMANA = "settimana"
    MESE = "mese"

class ReportTypeEnum(str, Enum):
    """Enum per i tipi di report"""
    PRODUZIONE = "produzione"
    QUALITA = "qualita"
    TEMPI = "tempi"
    COMPLETO = "completo"
    NESTING = "nesting"

class ReportIncludeSection(str, Enum):
    """Enum per le sezioni opzionali da includere nel report"""
    ODL = "odl"
    TEMPI = "tempi"
    NESTING = "nesting"
    HEADER = "header"

class ReportGenerateRequest(BaseModel):
    """Schema per la richiesta di generazione report"""
    report_type: ReportTypeEnum = Field(..., description="Tipo di report da generare")
    range_type: Optional[ReportRangeType] = Field(None, description="Tipo di periodo per il report")
    start_date: Optional[datetime] = Field(None, description="Data di inizio personalizzata")
    end_date: Optional[datetime] = Field(None, description="Data di fine personalizzata")
    include_sections: Optional[List[ReportIncludeSection]] = Field(
        default=[], 
        description="Sezioni opzionali da includere nel report"
    )
    odl_filter: Optional[str] = Field(None, description="Filtro per ODL o PN specifico")
    user_id: Optional[int] = Field(None, description="ID utente per cui generare il report")
    download: Optional[bool] = Field(
        default=True, 
        description="Se true, restituisce il file per download diretto"
    )

class ReportFileInfo(BaseModel):
    """Schema per le informazioni di un file report"""
    id: int
    filename: str
    file_path: str
    report_type: ReportTypeEnum
    generated_for_user_id: Optional[int]
    period_start: Optional[datetime]
    period_end: Optional[datetime]
    include_sections: Optional[str]
    file_size_bytes: Optional[int]
    created_at: datetime
    updated_at: datetime

class ReportListResponse(BaseModel):
    """Schema per la risposta della lista report"""
    reports: List[ReportFileInfo]

class ReportGenerateResponse(BaseModel):
    """Schema per la risposta di generazione report"""
    message: str
    file_path: str
    file_name: str
    report_id: int

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Report generato con successo",
                "file_path": "/app/reports/report_produzione_2024-01-15_1430.pdf",
                "file_name": "report_produzione_2024-01-15_1430.pdf",
                "report_id": 1
            }
        }

class ReportFilterRequest(BaseModel):
    """Schema per i filtri di ricerca report"""
    report_type: Optional[ReportTypeEnum] = Field(None, description="Filtra per tipo di report")
    start_date: Optional[datetime] = Field(None, description="Data di inizio per il filtro")
    end_date: Optional[datetime] = Field(None, description="Data di fine per il filtro")
    odl_filter: Optional[str] = Field(None, description="Filtro per ODL o PN")
    user_id: Optional[int] = Field(None, description="Filtra per utente")
    limit: Optional[int] = Field(50, description="Numero massimo di risultati")
    offset: Optional[int] = Field(0, description="Offset per la paginazione") 