from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from api.database import get_db
from services.system_log_service import SystemLogService
from schemas.system_log import (
    SystemLogResponse, 
    SystemLogFilter, 
    SystemLogStats,
    EventType,
    UserRole,
    LogLevel
)

router = APIRouter(prefix="/system-logs", tags=["System Logs"])

@router.get("/", response_model=List[SystemLogResponse])
async def get_system_logs(
    event_type: Optional[EventType] = Query(None, description="Filtra per tipo di evento"),
    user_role: Optional[UserRole] = Query(None, description="Filtra per ruolo utente"),
    level: Optional[LogLevel] = Query(None, description="Filtra per livello di log"),
    entity_type: Optional[str] = Query(None, description="Filtra per tipo di entità"),
    entity_id: Optional[int] = Query(None, description="Filtra per ID entità"),
    start_date: Optional[datetime] = Query(None, description="Data inizio (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="Data fine (ISO format)"),
    limit: int = Query(100, ge=1, le=1000, description="Numero massimo di log da restituire"),
    offset: int = Query(0, ge=0, description="Offset per paginazione"),
    db: Session = Depends(get_db)
):
    """
    Ottiene i log di sistema con filtri opzionali
    
    Accessibile solo ad admin e management
    """
    try:
        filters = SystemLogFilter(
            event_type=event_type,
            user_role=user_role,
            level=level,
            entity_type=entity_type,
            entity_id=entity_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        
        logs = SystemLogService.get_logs(db, filters)
        return [SystemLogResponse.from_orm(log) for log in logs]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore nel recupero dei log: {str(e)}")

@router.get("/stats", response_model=SystemLogStats)
async def get_log_statistics(
    days: int = Query(30, ge=1, le=365, description="Numero di giorni da considerare"),
    db: Session = Depends(get_db)
):
    """
    Ottiene statistiche sui log di sistema
    
    Accessibile solo ad admin e management
    """
    try:
        stats = SystemLogService.get_log_stats(db, days)
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore nel calcolo delle statistiche: {str(e)}")

@router.get("/recent-errors", response_model=List[SystemLogResponse])
async def get_recent_errors(
    limit: int = Query(20, ge=1, le=100, description="Numero di errori da restituire"),
    db: Session = Depends(get_db)
):
    """
    Ottiene gli errori più recenti
    
    Accessibile solo ad admin e management
    """
    try:
        filters = SystemLogFilter(
            level=LogLevel.ERROR,
            limit=limit,
            offset=0
        )
        
        error_logs = SystemLogService.get_logs(db, filters)
        
        # Aggiungi anche i log critici
        critical_filters = SystemLogFilter(
            level=LogLevel.CRITICAL,
            limit=limit,
            offset=0
        )
        
        critical_logs = SystemLogService.get_logs(db, critical_filters)
        
        # Combina e ordina per timestamp
        all_errors = error_logs + critical_logs
        all_errors.sort(key=lambda x: x.timestamp, reverse=True)
        
        return [SystemLogResponse.from_orm(log) for log in all_errors[:limit]]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore nel recupero degli errori: {str(e)}")

@router.get("/by-entity/{entity_type}/{entity_id}", response_model=List[SystemLogResponse])
async def get_logs_by_entity(
    entity_type: str,
    entity_id: int,
    limit: int = Query(50, ge=1, le=200, description="Numero di log da restituire"),
    db: Session = Depends(get_db)
):
    """
    Ottiene i log relativi a una specifica entità (ODL, tool, autoclave, etc.)
    
    Accessibile solo ad admin e management
    """
    try:
        filters = SystemLogFilter(
            entity_type=entity_type,
            entity_id=entity_id,
            limit=limit,
            offset=0
        )
        
        logs = SystemLogService.get_logs(db, filters)
        return [SystemLogResponse.from_orm(log) for log in logs]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore nel recupero dei log per entità: {str(e)}")

@router.get("/export")
async def export_logs_csv(
    event_type: Optional[EventType] = Query(None),
    user_role: Optional[UserRole] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Esporta i log in formato CSV
    
    Accessibile solo ad admin e management
    """
    try:
        from fastapi.responses import StreamingResponse
        import csv
        import io
        
        filters = SystemLogFilter(
            event_type=event_type,
            user_role=user_role,
            start_date=start_date,
            end_date=end_date,
            limit=1000,  # Limite massimo consentito
            offset=0
        )
        
        logs = SystemLogService.get_logs(db, filters)
        
        # Crea CSV in memoria
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'ID', 'Timestamp', 'Livello', 'Tipo Evento', 'Ruolo Utente', 
            'User ID', 'Azione', 'Tipo Entità', 'ID Entità', 'Dettagli',
            'Valore Precedente', 'Nuovo Valore', 'IP Address'
        ])
        
        # Dati
        for log in logs:
            writer.writerow([
                log.id,
                log.timestamp.isoformat() if log.timestamp else '',
                log.level.value if log.level else '',
                log.event_type.value if log.event_type else '',
                log.user_role.value if log.user_role else '',
                log.user_id or '',
                log.action or '',
                log.entity_type or '',
                log.entity_id or '',
                log.details or '',
                log.old_value or '',
                log.new_value or '',
                log.ip_address or ''
            ])
        
        output.seek(0)
        
        # Crea response
        response = StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8')),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=system_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore nell'esportazione: {str(e)}") 