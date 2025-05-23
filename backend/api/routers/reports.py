"""
Router per la generazione e gestione dei report PDF.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
import os
from datetime import datetime, timedelta
from models.db import get_db
from services.report_service import ReportService
from schemas.reports import ReportGenerateRequest

# Crea un router per la gestione dei report
router = APIRouter(
    tags=["reports"],
    responses={404: {"description": "Non trovato"}},
)

@router.get(
    "/generate",
    summary="Genera e scarica un report PDF",
    description="""
    Genera un report PDF per il periodo specificato contenente:
    - Dettagli nesting (autoclavi, valvole, area, ODL assegnati)
    - Layout grafico nesting (rappresentazione visiva)
    - Dati opzionali: ODL con tempi, fasi, stato
    
    Il file viene salvato automaticamente su disco e può essere scaricato.
    """
)
async def generate_report(
    range_type: str = Query(..., description="Tipo di periodo: 'giorno', 'settimana', 'mese'"),
    include: Optional[str] = Query(None, description="Sezioni da includere separate da virgola: 'odl,tempi'"),
    download: bool = Query(True, description="Se true, restituisce il file per il download"),
    db: Session = Depends(get_db)
):
    """
    Endpoint per generare report PDF.
    
    Args:
        range_type: Tipo di periodo (giorno, settimana, mese)
        include: Sezioni opzionali da includere (CSV: "odl", "tempi")
        download: Se restituire il file per il download
        db: Sessione del database
        
    Returns:
        FileResponse con il PDF generato o info sul file salvato
    """
    try:
        # Validazione del range_type
        if range_type not in ["giorno", "settimana", "mese"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="range_type deve essere 'giorno', 'settimana' o 'mese'"
            )
        
        # Parse delle sezioni da includere
        include_sections = []
        if include:
            include_sections = [section.strip() for section in include.split(",")]
        
        # Inizializza il servizio report
        report_service = ReportService(db)
        
        # Genera il report
        file_path = await report_service.generate_report(
            range_type=range_type,
            include_sections=include_sections
        )
        
        if download:
            # Restituisce il file per il download
            return FileResponse(
                path=file_path,
                filename=os.path.basename(file_path),
                media_type="application/pdf"
            )
        else:
            # Restituisce solo le informazioni del file
            return {
                "message": "Report generato con successo",
                "file_path": file_path,
                "file_name": os.path.basename(file_path)
            }
            
    except Exception as e:
        # In caso di errore, solleva una HTTPException
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante la generazione del report: {str(e)}"
        )

@router.get(
    "/list",
    summary="Lista dei report generati",
    description="Restituisce la lista dei report PDF disponibili su disco"
)
async def list_reports():
    """
    Endpoint per ottenere la lista dei report disponibili.
    
    Returns:
        Lista dei file report disponibili con metadata
    """
    try:
        reports_dir = "/app/reports"
        
        if not os.path.exists(reports_dir):
            return {"reports": []}
        
        reports = []
        for filename in os.listdir(reports_dir):
            if filename.endswith('.pdf'):
                file_path = os.path.join(reports_dir, filename)
                file_stats = os.stat(file_path)
                
                reports.append({
                    "filename": filename,
                    "size": file_stats.st_size,
                    "created_at": datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
                    "modified_at": datetime.fromtimestamp(file_stats.st_mtime).isoformat()
                })
        
        # Ordina per data di creazione (più recente prima)
        reports.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {"reports": reports}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante il recupero dei report: {str(e)}"
        )

@router.get(
    "/download/{filename}",
    summary="Scarica un report specifico",
    description="Scarica un report PDF esistente tramite nome file"
)
async def download_report(filename: str):
    """
    Endpoint per scaricare un report specifico.
    
    Args:
        filename: Nome del file da scaricare
        
    Returns:
        FileResponse con il PDF richiesto
    """
    try:
        file_path = f"/app/reports/{filename}"
        
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File non trovato"
            )
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/pdf"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante il download del report: {str(e)}"
        ) 