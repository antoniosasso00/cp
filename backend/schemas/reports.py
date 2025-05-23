from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class ReportRangeType(str, Enum):
    """Enum per i tipi di periodo del report"""
    GIORNO = "giorno"
    SETTIMANA = "settimana"
    MESE = "mese"

class ReportIncludeSection(str, Enum):
    """Enum per le sezioni opzionali da includere nel report"""
    ODL = "odl"
    TEMPI = "tempi"

class ReportGenerateRequest(BaseModel):
    """Schema per la richiesta di generazione report"""
    range_type: ReportRangeType = Field(..., description="Tipo di periodo per il report")
    include_sections: Optional[List[ReportIncludeSection]] = Field(
        default=[], 
        description="Sezioni opzionali da includere nel report"
    )
    download: Optional[bool] = Field(
        default=True, 
        description="Se true, restituisce il file per download diretto"
    )

class ReportFileInfo(BaseModel):
    """Schema per le informazioni di un file report"""
    filename: str
    size: int
    created_at: str
    modified_at: str

class ReportListResponse(BaseModel):
    """Schema per la risposta della lista report"""
    reports: List[ReportFileInfo]

class ReportGenerateResponse(BaseModel):
    """Schema per la risposta di generazione report"""
    message: str
    file_path: str
    file_name: str

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Report generato con successo",
                "file_path": "/app/reports/report_giorno_2024-01-15.pdf",
                "file_name": "report_giorno_2024-01-15.pdf"
            }
        } 