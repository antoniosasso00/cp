#!/usr/bin/env python3
"""
Endpoints per gestione batch DRAFT temporanei
============================================

Gestisce batch DRAFT (solo in memoria) e loro conferma a SOSPESO
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from api.database import get_db
from services.nesting_service import get_nesting_service
from schemas.batch_nesting import BatchNestingResponse
from api.routers.batch_nesting_modules.utils import format_batch_for_response

logger = logging.getLogger(__name__)

router = APIRouter()

# === SCHEMI PYDANTIC ===

class DraftBatchListResponse(BaseModel):
    """Schema per lista batch DRAFT"""
    draft_batches: List[Dict[str, Any]]
    total_count: int
    stats: Dict[str, Any]

class ConfirmDraftRequest(BaseModel):
    """Schema per conferma batch DRAFT"""
    draft_id: str
    confermato_da_utente: str = "ADMIN"
    confermato_da_ruolo: str = "ADMIN"

class ConfirmDraftResponse(BaseModel):
    """Schema risposta conferma batch DRAFT"""
    success: bool
    message: str
    persistent_batch_id: str
    draft_id: str

# === ENDPOINTS BATCH DRAFT ===

@router.get("/draft", response_model=DraftBatchListResponse,
            summary="📋 Lista batch DRAFT dal database")
def list_draft_batches(
    autoclave_id: Optional[int] = Query(None, description="Filtra per ID autoclave"),
    odl_ids: Optional[str] = Query(None, description="Filtra per ODL (comma separated)"),
    db: Session = Depends(get_db)
):
    """
    🚀 LISTA BATCH DRAFT DAL DATABASE
    ==================================
    
    Lista batch in stato DRAFT persistiti nel database.
    Sistema completamente integrato - nessun batch temporaneo in memoria.
    """
    try:
        from models.batch_nesting import BatchNesting, StatoBatchNestingEnum
        from sqlalchemy.orm import joinedload
        
        # Query batch DRAFT dal database
        query = db.query(BatchNesting).options(
            joinedload(BatchNesting.autoclave)
        ).filter(
            BatchNesting.stato == StatoBatchNestingEnum.DRAFT.value
        )
        
        # Applica filtri se forniti
        if autoclave_id:
            query = query.filter(BatchNesting.autoclave_id == autoclave_id)
            
        if odl_ids:
            try:
                parsed_odl_ids = [int(id_str.strip()) for id_str in odl_ids.split(',')]
                # Filtra batch che contengono almeno uno degli ODL richiesti
                query = query.filter(BatchNesting.odl_ids.overlap(parsed_odl_ids))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Formato ODL IDs non valido. Usa numeri separati da virgola."
                )
        
        # Ordina per data di creazione (più recenti prima)
        draft_batches = query.order_by(BatchNesting.created_at.desc()).all()
        
        # Converte in formato lista
        draft_list = []
        for batch in draft_batches:
            draft_list.append({
                'id': str(batch.id),
                'nome': batch.nome,
                'autoclave_id': batch.autoclave_id,
                'autoclave_nome': batch.autoclave.nome if batch.autoclave else 'Unknown',
                'odl_ids': batch.odl_ids or [],
                'odl_count': len(batch.odl_ids) if batch.odl_ids else 0,
                'efficiency': float(batch.efficiency) if batch.efficiency else 0.0,
                'peso_totale_kg': batch.peso_totale_kg or 0,
                'created_at': batch.created_at.isoformat() if batch.created_at else None,
                'stato': batch.stato
            })
        
        # Statistiche
        total_drafts = len(draft_batches)
        total_odl_in_drafts = sum(len(batch.odl_ids) if batch.odl_ids else 0 for batch in draft_batches)
        avg_efficiency = sum(float(batch.efficiency) if batch.efficiency else 0.0 for batch in draft_batches) / total_drafts if total_drafts > 0 else 0.0
        
        stats = {
            'total_drafts': total_drafts,
            'total_odl_in_drafts': total_odl_in_drafts,
            'average_efficiency': avg_efficiency,
            'autoclavi_used': len(set(batch.autoclave_id for batch in draft_batches if batch.autoclave_id))
        }
        
        logger.info(f"📋 Lista batch DRAFT: {len(draft_list)} trovati nel database")
        
        return DraftBatchListResponse(
            draft_batches=draft_list,
            total_count=total_drafts,
            stats=stats
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Errore lista batch DRAFT: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore recupero batch DRAFT: {str(e)}"
        )

@router.get("/draft/{draft_id}", summary="📋 Dettagli batch DRAFT dal database")
def get_draft_batch_details(
    draft_id: str,
    db: Session = Depends(get_db)
):
    """
    🚀 DETTAGLI BATCH DRAFT DAL DATABASE
    =====================================
    
    Recupera dettagli completi di un batch DRAFT dal database con correlazioni.
    Include informazioni autoclave, ODL, e correlazioni multi-batch se presenti.
    """
    try:
        from models.batch_nesting import BatchNesting, StatoBatchNestingEnum
        from sqlalchemy.orm import joinedload
        
        # Cerca batch DRAFT nel database
        draft_batch = db.query(BatchNesting).options(
            joinedload(BatchNesting.autoclave)
        ).filter(
            BatchNesting.id == draft_id,
            BatchNesting.stato == StatoBatchNestingEnum.DRAFT.value
        ).first()
        
        if not draft_batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch DRAFT {draft_id} non trovato nel database"
            )
        
        # Controlla per correlazioni multi-batch usando il nesting service
        nesting_service = get_nesting_service()
        correlated_batches = nesting_service.get_correlated_draft_batches(db, draft_id)
        
        # Prepara risposta dettagliata
        draft_details = {
            'id': str(draft_batch.id),
            'nome': draft_batch.nome,
            'stato': draft_batch.stato,
            'autoclave_id': draft_batch.autoclave_id,
            'autoclave': {
                'id': draft_batch.autoclave.id,
                'nome': draft_batch.autoclave.nome,
                'lunghezza': draft_batch.autoclave.lunghezza,
                'larghezza_piano': draft_batch.autoclave.larghezza_piano,
                'max_load_kg': draft_batch.autoclave.max_load_kg
            } if draft_batch.autoclave else None,
            'odl_ids': draft_batch.odl_ids or [],
            'odl_count': len(draft_batch.odl_ids) if draft_batch.odl_ids else 0,
            'parametri': draft_batch.parametri,
            'configurazione_json': draft_batch.configurazione_json,
            'efficiency': float(draft_batch.efficiency) if draft_batch.efficiency else 0.0,
            'peso_totale_kg': draft_batch.peso_totale_kg or 0,
            'area_totale_utilizzata': draft_batch.area_totale_utilizzata or 0,
            'valvole_totali_utilizzate': draft_batch.valvole_totali_utilizzate or 0,
            'numero_nesting': draft_batch.numero_nesting or 0,
            'created_at': draft_batch.created_at.isoformat() if draft_batch.created_at else None,
            'note': draft_batch.note,
            # Correlazioni multi-batch
            'is_multi_batch': len(correlated_batches) > 0,
            'correlated_batches_count': len(correlated_batches),
            'correlated_batch_ids': correlated_batches
        }
        
        logger.info(f"📋 Dettagli batch DRAFT: {draft_id} (correlati: {len(correlated_batches)})")
        return draft_details
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Errore dettagli batch DRAFT {draft_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore recupero dettagli batch DRAFT: {str(e)}"
        )

@router.post("/draft/{draft_id}/confirm", response_model=ConfirmDraftResponse,
             summary="✅ Conferma batch DRAFT - Transizione DRAFT → SOSPESO")
def confirm_draft_batch(
    draft_id: str,
    confermato_da_utente: str = Query("ADMIN", description="Utente che conferma"),
    confermato_da_ruolo: str = Query("ADMIN", description="Ruolo utente"),
    db: Session = Depends(get_db)
):
    """
    🚀 CONFERMA BATCH DRAFT → SOSPESO
    ==================================
    
    Transizione standard database: DRAFT → SOSPESO con aggiornamento ODL.
    
    Azioni automatiche:
    - Batch stato: DRAFT → SOSPESO
    - ODL associati: mantenuti in "Attesa Cura" (confermati per la cura)
    - Timestamp aggiornamento
    - Tracciabilità utente
    """
    try:
        from models.batch_nesting import BatchNesting, StatoBatchNestingEnum
        from models.odl import ODL
        from datetime import datetime
        
        # Trova il batch DRAFT
        draft_batch = db.query(BatchNesting).filter(
            BatchNesting.id == draft_id,
            BatchNesting.stato == StatoBatchNestingEnum.DRAFT.value
        ).first()
        
        if not draft_batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch DRAFT {draft_id} non trovato nel database"
            )
        
        # 🎯 TRANSIZIONE STATO: DRAFT → SOSPESO
        draft_batch.stato = StatoBatchNestingEnum.SOSPESO.value
        draft_batch.confermato_da_utente = confermato_da_utente
        draft_batch.confermato_da_ruolo = confermato_da_ruolo
        draft_batch.data_conferma = datetime.now()
        draft_batch.updated_at = datetime.now()
        
        # 📋 AGGIORNA ODL ASSOCIATI (mantieni "Attesa Cura" - già pronti)
        if draft_batch.odl_ids:
            odl_objects = db.query(ODL).filter(ODL.id.in_(draft_batch.odl_ids)).all()
            for odl in odl_objects:
                if odl.status != "Attesa Cura":
                    logger.info(f"   ODL {odl.id}: {odl.status} → Attesa Cura")
                    odl.status = "Attesa Cura"
                else:
                    logger.info(f"   ODL {odl.id}: già in Attesa Cura")
        
        # 🚀 RIMUOVI CORRELAZIONI DRAFT dal NestingService
        nesting_service = get_nesting_service()
        if hasattr(nesting_service, '_batch_to_generation') and draft_id in nesting_service._batch_to_generation:
            generation_id = nesting_service._batch_to_generation[draft_id]
            # Rimuovi dalla correlazione
            del nesting_service._batch_to_generation[draft_id]
            # Rimuovi dalla lista del gruppo se esiste
            if generation_id in nesting_service._draft_correlations:
                if draft_id in nesting_service._draft_correlations[generation_id]:
                    nesting_service._draft_correlations[generation_id].remove(draft_id)
                    logger.info(f"🧹 Rimossa correlazione DRAFT {draft_id} da gruppo {generation_id}")
        
        db.commit()
        db.refresh(draft_batch)
        
        logger.info(f"✅ Batch DRAFT {draft_id} confermato → SOSPESO con successo")
        
        return ConfirmDraftResponse(
            success=True,
            message=f"Batch DRAFT confermato e promosso a SOSPESO",
            persistent_batch_id=str(draft_batch.id),  # Stesso ID, stato cambiato
            draft_id=draft_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Errore conferma batch DRAFT {draft_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore conferma batch DRAFT: {str(e)}"
        )

@router.delete("/draft/{draft_id}", summary="🗑️ Elimina batch DRAFT dal database")
def delete_draft_batch(
    draft_id: str,
    db: Session = Depends(get_db)
):
    """
    🗑️ ELIMINAZIONE BATCH DRAFT
    =============================
    
    Elimina definitivamente un batch DRAFT dal database.
    Include cleanup correlazioni multi-batch nel NestingService.
    """
    try:
        from models.batch_nesting import BatchNesting, StatoBatchNestingEnum
        
        # Trova il batch DRAFT
        draft_batch = db.query(BatchNesting).filter(
            BatchNesting.id == draft_id,
            BatchNesting.stato == StatoBatchNestingEnum.DRAFT.value
        ).first()
        
        if not draft_batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch DRAFT {draft_id} non trovato nel database"
            )
        
        # 🚀 RIMUOVI CORRELAZIONI DRAFT dal NestingService
        nesting_service = get_nesting_service()
        if hasattr(nesting_service, '_batch_to_generation') and draft_id in nesting_service._batch_to_generation:
            generation_id = nesting_service._batch_to_generation[draft_id]
            # Rimuovi dalla correlazione
            del nesting_service._batch_to_generation[draft_id]
            # Rimuovi dalla lista del gruppo se esiste
            if generation_id in nesting_service._draft_correlations:
                if draft_id in nesting_service._draft_correlations[generation_id]:
                    nesting_service._draft_correlations[generation_id].remove(draft_id)
                    logger.info(f"🧹 Rimossa correlazione DRAFT {draft_id} da gruppo {generation_id}")
        
        # 🗑️ ELIMINA dal database
        db.delete(draft_batch)
        db.commit()
        
        logger.info(f"🗑️ Batch DRAFT {draft_id} eliminato dal database")
        
        return {
            "success": True,
            "message": f"Batch DRAFT {draft_id} eliminato definitivamente dal database",
            "draft_id": draft_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Errore eliminazione batch DRAFT {draft_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore eliminazione batch DRAFT: {str(e)}"
        )

@router.post("/draft/cleanup", summary="🧹 Cleanup batch DRAFT scaduti dal database")
def cleanup_expired_draft_batches(
    max_age_hours: int = Query(24, description="Età massima in ore per batch DRAFT"),
    db: Session = Depends(get_db)
):
    """
    🧹 CLEANUP BATCH DRAFT SCADUTI
    ===============================
    
    Rimuove batch DRAFT scaduti dal database e relative correlazioni.
    Pulisce sia database che correlazioni in memoria nel NestingService.
    """
    try:
        from models.batch_nesting import BatchNesting, StatoBatchNestingEnum
        from datetime import datetime, timedelta
        
        # Calcola soglia di scadenza
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        # Trova batch DRAFT scaduti
        expired_drafts = db.query(BatchNesting).filter(
            BatchNesting.stato == StatoBatchNestingEnum.DRAFT.value,
            BatchNesting.created_at < cutoff_time
        ).all()
        
        # 🚀 CLEANUP CORRELAZIONI dal NestingService
        nesting_service = get_nesting_service()
        correlations_cleaned = 0
        
        for draft_batch in expired_drafts:
            draft_id = str(draft_batch.id)
            if hasattr(nesting_service, '_batch_to_generation') and draft_id in nesting_service._batch_to_generation:
                generation_id = nesting_service._batch_to_generation[draft_id]
                # Rimuovi dalla correlazione
                del nesting_service._batch_to_generation[draft_id]
                # Rimuovi dalla lista del gruppo se esiste
                if generation_id in nesting_service._draft_correlations:
                    if draft_id in nesting_service._draft_correlations[generation_id]:
                        nesting_service._draft_correlations[generation_id].remove(draft_id)
                        correlations_cleaned += 1
        
        # 🗑️ ELIMINA dal database
        cleaned_count = len(expired_drafts)
        for draft_batch in expired_drafts:
            db.delete(draft_batch)
        
        # 🧹 CLEANUP correlazioni orfane nel NestingService
        nesting_service.cleanup_draft_correlations(max_age_hours=max_age_hours)
        
        db.commit()
        
        logger.info(f"🧹 Cleanup batch DRAFT: {cleaned_count} eliminati dal database, {correlations_cleaned} correlazioni rimosse")
        
        return {
            "success": True,
            "message": f"Cleanup completato: {cleaned_count} batch DRAFT scaduti rimossi",
            "cleaned_count": cleaned_count,
            "correlations_cleaned": correlations_cleaned,
            "max_age_hours": max_age_hours
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Errore cleanup batch DRAFT: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore cleanup batch DRAFT: {str(e)}"
        )

@router.get("/draft/stats", summary="📊 Statistiche batch DRAFT dal database")
def get_draft_batches_stats(
    db: Session = Depends(get_db)
):
    """
    📊 STATISTICHE BATCH DRAFT DAL DATABASE
    ========================================
    
    Statistiche complete sui batch DRAFT nel database e correlazioni in memoria.
    Include sia dati persistiti che stato correlazioni multi-batch.
    """
    try:
        from models.batch_nesting import BatchNesting, StatoBatchNestingEnum
        from sqlalchemy import func
        
        # Query statistiche database
        draft_count = db.query(BatchNesting).filter(
            BatchNesting.stato == StatoBatchNestingEnum.DRAFT.value
        ).count()
        
        # Statistiche dettagliate
        draft_stats = db.query(
            func.count(BatchNesting.id).label('total'),
            func.avg(BatchNesting.efficiency).label('avg_efficiency'),
            func.sum(BatchNesting.peso_totale_kg).label('total_weight'),
            func.count(BatchNesting.autoclave_id.distinct()).label('autoclavi_used')
        ).filter(
            BatchNesting.stato == StatoBatchNestingEnum.DRAFT.value
        ).first()
        
        # Statistiche correlazioni dal NestingService
        nesting_service = get_nesting_service()
        correlation_stats = {
            'total_correlation_groups': len(getattr(nesting_service, '_draft_correlations', {})),
            'total_correlated_batches': len(getattr(nesting_service, '_batch_to_generation', {})),
            'active_generations': list(getattr(nesting_service, '_draft_correlations', {}).keys())
        }
        
        # Combina statistiche
        stats = {
            'database_stats': {
                'total_drafts': draft_count,
                'average_efficiency': float(draft_stats.avg_efficiency) if draft_stats.avg_efficiency else 0.0,
                'total_weight_kg': float(draft_stats.total_weight) if draft_stats.total_weight else 0.0,
                'autoclavi_used': int(draft_stats.autoclavi_used) if draft_stats.autoclavi_used else 0
            },
            'correlation_stats': correlation_stats,
            'last_update': datetime.now().isoformat()
        }
        
        logger.info(f"📊 Statistiche batch DRAFT: {draft_count} nel database, {correlation_stats['total_correlated_batches']} correlati")
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"❌ Errore statistiche batch DRAFT: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore recupero statistiche: {str(e)}"
        ) 