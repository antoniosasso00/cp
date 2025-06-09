# Router manutenzione e operazioni batch

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from api.database import get_db
from models.batch_nesting import BatchNesting, StatoBatchNestingEnum
from models.autoclave import Autoclave
from models.odl import ODL

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Batch Nesting - Maintenance"]
)

@router.get("/diagnosi-sistema", response_model=Dict[str, Any])
def diagnosi_sistema_multi_batch(db: Session = Depends(get_db)):
    """Diagnosi completa del sistema"""
    try:
        batch_sospesi = db.query(BatchNesting).filter(
            BatchNesting.stato == StatoBatchNestingEnum.SOSPESO.value
        ).count()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "batch_sospesi": batch_sospesi,
            "status": "OK"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/cleanup")
def cleanup_old_batch_nesting(
    days_threshold: int = Query(7),
    dry_run: bool = Query(False),
    db: Session = Depends(get_db)
):
    """Cleanup automatico batch vecchi"""
    try:
        threshold_date = datetime.now() - timedelta(days=days_threshold)
        
        query = db.query(BatchNesting).filter(
            BatchNesting.created_at < threshold_date,
            BatchNesting.stato == StatoBatchNestingEnum.SOSPESO.value
        )
        
        batches_to_delete = query.all()
        
        result = {
            "dry_run": dry_run,
            "found_batches": len(batches_to_delete),
            "deleted_count": 0 if dry_run else len(batches_to_delete)
        }
        
        if not dry_run:
            for batch in batches_to_delete:
                db.delete(batch)
            db.commit()
        
        return result
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/bulk")
def delete_multiple_batch_nesting(
    batch_ids: List[str] = Body(...),
    confirm: bool = Query(False),
    db: Session = Depends(get_db)
):
    """Eliminazione multipla batch"""
    try:
        batches = db.query(BatchNesting).filter(BatchNesting.id.in_(batch_ids)).all()
        
        for batch in batches:
            db.delete(batch)
        db.commit()
        
        return {
            "deleted_count": len(batches),
            "deleted_ids": [b.id for b in batches]
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) 