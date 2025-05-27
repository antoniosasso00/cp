"""
Router per la generazione e gestione dei report PDF.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional, List
import os
from datetime import datetime, timedelta
from models.db import get_db
from models.report import Report, ReportTypeEnum
from services.report_service import ReportService
from services.auto_report_service import AutoReportService
from schemas.reports import (
    ReportGenerateRequest, 
    ReportGenerateResponse, 
    ReportListResponse, 
    ReportFileInfo,
    ReportFilterRequest,
    ReportTypeEnum as SchemaReportTypeEnum
)

# Crea un router per la gestione dei report
router = APIRouter(
    tags=["reports"],
    responses={404: {"description": "Non trovato"}},
)

@router.post(
    "/generate",
    response_model=ReportGenerateResponse,
    summary="Genera un nuovo report PDF",
    description="""
    Genera un report PDF personalizzato con le seguenti caratteristiche:
    - Tipi di report: produzione, qualità, tempi, completo, nesting
    - Periodi configurabili: giorno, settimana, mese o date personalizzate
    - Sezioni modulari: header, nesting, ODL, tempi
    - Filtri per ODL o Part Number
    - Salvataggio automatico nel database con metadati
    """
)
async def generate_report(
    request: ReportGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Endpoint per generare report PDF personalizzati.
    
    Args:
        request: Dati della richiesta di generazione report
        db: Sessione del database
        
    Returns:
        Informazioni sul report generato
    """
    try:
        # Inizializza il servizio report
        report_service = ReportService(db)
        
        # Genera il report
        file_path, report_record = await report_service.generate_report(
            report_type=request.report_type,
            range_type=request.range_type,
            start_date=request.start_date,
            end_date=request.end_date,
            include_sections=request.include_sections,
            odl_filter=request.odl_filter,
            user_id=request.user_id
        )
        
        return ReportGenerateResponse(
            message="Report generato con successo",
            file_path=file_path,
            file_name=os.path.basename(file_path),
            report_id=report_record.id
        )
            
    except Exception as e:
        # In caso di errore, solleva una HTTPException
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante la generazione del report: {str(e)}"
        )

@router.post(
    "/auto-generate",
    summary="Genera automaticamente report per cicli di cura completati",
    description="""
    Controlla tutti i cicli di cura completati nelle ultime 24 ore e genera 
    automaticamente i report PDF mancanti. Questo endpoint può essere chiamato:
    - Manualmente dall'interfaccia utente
    - Automaticamente da un job schedulato
    - Come trigger dopo il completamento di un ciclo
    """
)
async def auto_generate_reports(db: Session = Depends(get_db)):
    """
    Endpoint per la generazione automatica di report per cicli completati.
    
    Args:
        db: Sessione del database
        
    Returns:
        Statistiche sui report generati
    """
    try:
        # Inizializza il servizio di auto-report
        auto_report_service = AutoReportService(db)
        
        # Processa tutti i cicli completati
        stats = await auto_report_service.process_all_completed_cycles()
        
        return {
            "message": "Processo di auto-generazione completato",
            "statistics": stats
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante l'auto-generazione dei report: {str(e)}"
        )

@router.post(
    "/trigger-for-nesting/{nesting_id}",
    summary="Genera report per un nesting specifico",
    description="""
    Genera un report PDF per un nesting specifico. Utile quando:
    - Un ciclo di cura è appena terminato
    - Si vuole rigenerare un report per un nesting esistente
    - Si vuole forzare la generazione di un report
    """
)
async def trigger_report_for_nesting(
    nesting_id: int,
    force_regenerate: bool = Query(False, description="Forza la rigenerazione anche se esiste già un report"),
    db: Session = Depends(get_db)
):
    """
    Endpoint per generare un report per un nesting specifico.
    
    Args:
        nesting_id: ID del nesting per cui generare il report
        force_regenerate: Se True, rigenera il report anche se esiste già
        db: Sessione del database
        
    Returns:
        Informazioni sul report generato
    """
    try:
        from models.nesting_result import NestingResult
        from models.schedule_entry import ScheduleEntry, ScheduleEntryStatus
        
        # Trova il nesting
        nesting = db.query(NestingResult).filter(NestingResult.id == nesting_id).first()
        if not nesting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Nesting con ID {nesting_id} non trovato"
            )
        
        # Controlla se esiste già un report
        if nesting.report_id and not force_regenerate:
            existing_report = db.query(Report).filter(Report.id == nesting.report_id).first()
            if existing_report:
                return {
                    "message": "Report già esistente per questo nesting",
                    "existing_report": {
                        "id": existing_report.id,
                        "filename": existing_report.filename,
                        "created_at": existing_report.created_at
                    }
                }
        
        # Trova una schedule entry associata (per simulare un ciclo completato)
        schedule = db.query(ScheduleEntry).filter(
            ScheduleEntry.autoclave_id == nesting.autoclave_id
        ).order_by(ScheduleEntry.updated_at.desc()).first()
        
        if not schedule:
            # Crea una schedule entry fittizia per il report
            schedule = ScheduleEntry(
                autoclave_id=nesting.autoclave_id,
                start_datetime=nesting.created_at,
                end_datetime=datetime.now(),
                status=ScheduleEntryStatus.DONE.value
            )
        
        # Inizializza il servizio di auto-report
        auto_report_service = AutoReportService(db)
        
        # Prepara le informazioni del ciclo
        cycle_info = {
            'schedule_id': schedule.id if schedule.id else 0,
            'nesting_id': nesting.id,
            'autoclave_id': nesting.autoclave_id,
            'odl_id': None,
            'completed_at': datetime.now(),
            'nesting': nesting,
            'schedule': schedule
        }
        
        # Genera il report
        report = await auto_report_service.generate_cycle_completion_report(cycle_info)
        
        if report:
            return {
                "message": "Report generato con successo per il nesting",
                "report": {
                    "id": report.id,
                    "filename": report.filename,
                    "file_path": report.file_path,
                    "created_at": report.created_at
                }
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Errore durante la generazione del report"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante la generazione del report per nesting: {str(e)}"
        )

@router.get(
    "/",
    response_model=ReportListResponse,
    summary="Lista dei report generati con filtri",
    description="Restituisce la lista dei report PDF salvati nel database con possibilità di filtro"
)
async def list_reports(
    report_type: Optional[SchemaReportTypeEnum] = Query(None, description="Filtra per tipo di report"),
    start_date: Optional[datetime] = Query(None, description="Data di inizio per il filtro"),
    end_date: Optional[datetime] = Query(None, description="Data di fine per il filtro"),
    odl_filter: Optional[str] = Query(None, description="Filtro per ODL o PN"),
    user_id: Optional[int] = Query(None, description="Filtra per utente"),
    limit: int = Query(50, description="Numero massimo di risultati"),
    offset: int = Query(0, description="Offset per la paginazione"),
    db: Session = Depends(get_db)
):
    """
    Endpoint per ottenere la lista dei report con filtri.
    
    Args:
        report_type: Filtra per tipo di report
        start_date: Data di inizio per il filtro
        end_date: Data di fine per il filtro
        odl_filter: Filtro per ODL o PN
        user_id: Filtra per utente
        limit: Numero massimo di risultati
        offset: Offset per la paginazione
        db: Sessione del database
    
    Returns:
        Lista dei report filtrati
    """
    try:
        # Inizializza il servizio report
        report_service = ReportService(db)
        
        # Converti il tipo di report se necessario
        db_report_type = None
        if report_type:
            db_report_type = ReportTypeEnum(report_type.value)
        
        # Recupera i report con filtri
        reports = report_service.get_reports_with_filters(
            report_type=db_report_type,
            start_date=start_date,
            end_date=end_date,
            odl_filter=odl_filter,
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        # Converti in formato response
        report_list = []
        for report in reports:
            # Usa direttamente il valore stringa per evitare problemi di conversione enum
            report_type_value = report.report_type.value if hasattr(report.report_type, 'value') else str(report.report_type)
            schema_report_type = SchemaReportTypeEnum(report_type_value)
            
            report_list.append(ReportFileInfo(
                id=report.id,
                filename=report.filename,
                file_path=report.file_path,
                report_type=schema_report_type,
                generated_for_user_id=report.generated_for_user_id,
                period_start=report.period_start,
                period_end=report.period_end,
                include_sections=report.include_sections,
                file_size_bytes=report.file_size_bytes,
                created_at=report.created_at,
                updated_at=report.updated_at
            ))
        
        return ReportListResponse(reports=report_list)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante il recupero dei report: {str(e)}"
        )

@router.get(
    "/{report_id}/download",
    summary="Scarica un report specifico per ID",
    description="Scarica un report PDF esistente tramite ID del database"
)
async def download_report_by_id(
    report_id: int,
    db: Session = Depends(get_db)
):
    """
    Endpoint per scaricare un report specifico tramite ID.
    
    Args:
        report_id: ID del report nel database
        db: Sessione del database
        
    Returns:
        FileResponse con il PDF richiesto
    """
    try:
        # Inizializza il servizio report
        report_service = ReportService(db)
        
        # Trova il report nel database
        report = db.query(Report).filter(Report.id == report_id).first()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report non trovato nel database"
            )
        
        # Verifica che il file esista fisicamente
        if not os.path.exists(report.file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File PDF non trovato su disco"
            )
        
        return FileResponse(
            path=report.file_path,
            filename=report.filename,
            media_type="application/pdf"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante il download del report: {str(e)}"
        )

@router.get(
    "/nesting-efficiency",
    summary="Report di efficienza del nesting",
    description="Restituisce statistiche di efficienza del sistema di nesting"
)
async def get_nesting_efficiency_report(db: Session = Depends(get_db)):
    """
    Endpoint per ottenere il report di efficienza del nesting.
    
    Returns:
        Statistiche di efficienza del sistema di nesting
    """
    try:
        from models.nesting_result import NestingResult
        from sqlalchemy import func
        
        # Calcola statistiche di efficienza
        total_nestings = db.query(NestingResult).count()
        
        # Efficienza media area
        avg_area_efficiency = db.query(
            func.avg((NestingResult.area_utilizzata / NestingResult.area_totale) * 100)
        ).scalar() or 0
        
        # Efficienza media valvole
        avg_valve_efficiency = db.query(
            func.avg((NestingResult.valvole_utilizzate / NestingResult.valvole_totali) * 100)
        ).scalar() or 0
        
        # Nesting per stato
        nesting_by_status = db.query(
            NestingResult.stato,
            func.count(NestingResult.id)
        ).group_by(NestingResult.stato).all()
        
        return {
            "total_nestings": total_nestings,
            "average_area_efficiency": round(avg_area_efficiency, 2),
            "average_valve_efficiency": round(avg_valve_efficiency, 2),
            "nesting_by_status": {status: count for status, count in nesting_by_status},
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante la generazione del report di efficienza: {str(e)}"
        )

@router.get(
    "/nesting/{nesting_id}/download",
    summary="Scarica il report PDF di un nesting specifico",
    description="Scarica il report PDF associato a un nesting completato"
)
async def download_nesting_report(
    nesting_id: int,
    db: Session = Depends(get_db)
):
    """
    Endpoint per scaricare il report PDF di un nesting specifico.
    
    Args:
        nesting_id: ID del nesting di cui scaricare il report
        db: Sessione del database
        
    Returns:
        File PDF del report
    """
    try:
        from models.nesting_result import NestingResult
        
        # Trova il nesting con il report associato
        nesting = db.query(NestingResult).filter(NestingResult.id == nesting_id).first()
        if not nesting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Nesting con ID {nesting_id} non trovato"
            )
        
        # Verifica che il nesting abbia un report associato
        if not nesting.report_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Nessun report trovato per il nesting {nesting_id}"
            )
        
        # Recupera il record del report
        report = db.query(Report).filter(Report.id == nesting.report_id).first()
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Record del report non trovato nel database"
            )
        
        # Verifica che il file esista
        if not os.path.exists(report.file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File del report non trovato: {report.file_path}"
            )
        
        # Restituisce il file PDF
        return FileResponse(
            path=report.file_path,
            filename=report.filename,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={report.filename}",
                "Cache-Control": "no-cache"
            }
        )
        
    except HTTPException:
        # Rilancia le HTTPException così come sono
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante il download del report: {str(e)}"
        )

@router.get(
    "/download/{filename}",
    summary="Scarica un report specifico per nome file",
    description="Scarica un report PDF esistente tramite nome file (compatibilità)"
)
async def download_report_by_filename(
    filename: str,
    db: Session = Depends(get_db)
):
    """
    Endpoint per scaricare un report specifico tramite nome file.
    
    Args:
        filename: Nome del file da scaricare
        db: Sessione del database
        
    Returns:
        FileResponse con il PDF richiesto
    """
    try:
        # Trova il report nel database tramite filename
        report = db.query(Report).filter(Report.filename == filename).first()
        
        if not report:
            # Fallback: cerca direttamente nella directory
            file_path = f"/app/reports/generated/{filename}"
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
        
        # Verifica che il file esista fisicamente
        if not os.path.exists(report.file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File PDF non trovato su disco"
            )
        
        return FileResponse(
            path=report.file_path,
            filename=report.filename,
            media_type="application/pdf"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante il download del report: {str(e)}"
        ) 