# Router workflow batch (conferma, caricamento, cura, terminazione)

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime

from api.database import get_db
from models.batch_nesting import BatchNesting, StatoBatchNestingEnum
from models.autoclave import Autoclave, StatoAutoclaveEnum
from models.odl import ODL
from schemas.batch_nesting import BatchNestingResponse
from .utils import (
    handle_database_error,
    validate_batch_state_transition,
    format_batch_for_response
)

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Batch Nesting - Workflow"]
)

@router.patch("/{batch_id}/confirm", response_model=BatchNestingResponse,
              summary="🔄 Conferma batch - Transizione SOSPESO → CONFERMATO")
def confirm_batch_nesting(
    batch_id: str, 
    confermato_da_utente: str = Query(..., description="ID dell'utente che conferma il batch"),
    confermato_da_ruolo: str = Query(..., description="Ruolo dell'utente che conferma"),
    db: Session = Depends(get_db)
):
    """Conferma un batch nesting"""
    try:
        # Trova il batch
        batch = db.query(BatchNesting).filter(BatchNesting.id == batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail="Batch non trovato")
        
        # Valida transizione di stato
        validate_batch_state_transition(batch.stato, StatoBatchNestingEnum.CONFERMATO)
        
        # Aggiorna batch
        batch.stato = StatoBatchNestingEnum.CONFERMATO
        batch.confermato_da_utente = confermato_da_utente
        batch.confermato_da_ruolo = confermato_da_ruolo
        batch.data_conferma = datetime.now()
        
        # Aggiorna ODL associate a "Cura"
        if batch.odl_ids:
            odls = db.query(ODL).filter(ODL.id.in_(batch.odl_ids)).all()
            for odl in odls:
                if odl.status != "Cura":
                    odl.status = "Cura"
                    odl.updated_at = datetime.now()
                    logger.info(f"📋 ODL {odl.id} aggiornato a stato CURA")
        
        # Aggiorna autoclave a "IN_USO"
        if batch.autoclave_id:
            autoclave = db.query(Autoclave).filter(Autoclave.id == batch.autoclave_id).first()
            if autoclave and autoclave.stato != StatoAutoclaveEnum.IN_USO:
                autoclave.stato = StatoAutoclaveEnum.IN_USO
                autoclave.updated_at = datetime.now()
                logger.info(f"🏭 Autoclave {autoclave.id} aggiornata a stato IN_USO")
        
        db.commit()
        db.refresh(batch)
        
        logger.info(f"✅ Batch {batch_id} confermato da {confermato_da_utente}")
        
        # Converti a BatchNestingResponse appropriato
        return format_batch_for_response(batch)
        
    except HTTPException:
        raise
    except Exception as e:
        return handle_database_error(db, e, f"conferma batch {batch_id}")

@router.patch("/{batch_id}/load", response_model=BatchNestingResponse,
              summary="🔄 Carica batch - Transizione CONFERMATO → LOADED")
def load_batch_nesting(
    batch_id: str,
    caricato_da_utente: str = Query(..., description="ID dell'utente che carica il batch"),
    caricato_da_ruolo: str = Query(..., description="Ruolo dell'utente che carica"),
    db: Session = Depends(get_db)
):
    """Carica un batch nell'autoclave"""
    try:
        batch = db.query(BatchNesting).filter(BatchNesting.id == batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail="Batch non trovato")
        
        # Valida transizione di stato
        validate_batch_state_transition(batch.stato, StatoBatchNestingEnum.LOADED)
        
        # Aggiorna batch
        batch.stato = StatoBatchNestingEnum.LOADED
        batch.caricato_da_utente = caricato_da_utente
        batch.caricato_da_ruolo = caricato_da_ruolo
        batch.data_caricamento = datetime.now()
        
        db.commit()
        db.refresh(batch)
        
        logger.info(f"✅ Batch {batch_id} caricato da {caricato_da_utente}")
        return format_batch_for_response(batch)
        
    except HTTPException:
        raise
    except Exception as e:
        return handle_database_error(db, e, f"caricamento batch {batch_id}")

@router.patch("/{batch_id}/cure", response_model=BatchNestingResponse,
              summary="🔄 Avvia cura - Transizione LOADED → CURED")  
def cure_batch_nesting(
    batch_id: str,
    avviato_da_utente: str = Query(..., description="ID dell'utente che avvia la cura"),
    avviato_da_ruolo: str = Query(..., description="Ruolo dell'utente che avvia la cura"),
    db: Session = Depends(get_db)
):
    """Avvia la cura del batch"""
    try:
        batch = db.query(BatchNesting).filter(BatchNesting.id == batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail="Batch non trovato")
        
        # Valida transizione di stato
        validate_batch_state_transition(batch.stato, StatoBatchNestingEnum.CURED)
        
        # Aggiorna batch
        batch.stato = StatoBatchNestingEnum.CURED
        batch.avviato_da_utente = avviato_da_utente
        batch.avviato_da_ruolo = avviato_da_ruolo
        batch.data_avvio_cura = datetime.now()
        
        db.commit()
        db.refresh(batch)
        
        logger.info(f"✅ Cura avviata per batch {batch_id} da {avviato_da_utente}")
        return format_batch_for_response(batch)
        
    except HTTPException:
        raise
    except Exception as e:
        return handle_database_error(db, e, f"avvio cura batch {batch_id}")

@router.patch("/{batch_id}/terminate", response_model=BatchNestingResponse,
              summary="🔄 Termina batch - Transizione CURED → TERMINATO")
def terminate_batch_nesting(
    batch_id: str,
    terminato_da_utente: str = Query(..., description="ID dell'utente che termina il batch"),
    terminato_da_ruolo: str = Query(..., description="Ruolo dell'utente che termina"),
    db: Session = Depends(get_db)
):
    """Termina un batch completando la cura"""
    try:
        batch = db.query(BatchNesting).filter(BatchNesting.id == batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail="Batch non trovato")
        
        # Valida transizione di stato
        validate_batch_state_transition(batch.stato, StatoBatchNestingEnum.TERMINATO)
        
        # Aggiorna batch
        batch.stato = StatoBatchNestingEnum.TERMINATO
        batch.terminato_da_utente = terminato_da_utente
        batch.terminato_da_ruolo = terminato_da_ruolo
        batch.data_termine = datetime.now()
        
        # Aggiorna ODL associate a "Finito"
        if batch.odl_ids:
            odls = db.query(ODL).filter(ODL.id.in_(batch.odl_ids)).all()
            for odl in odls:
                if odl.status != "Finito":
                    odl.status = "Finito"
                    odl.updated_at = datetime.now()
                    logger.info(f"📋 ODL {odl.id} aggiornato a stato FINITO")
        
        # Aggiorna autoclave a "DISPONIBILE"
        if batch.autoclave_id:
            autoclave = db.query(Autoclave).filter(Autoclave.id == batch.autoclave_id).first()
            if autoclave and autoclave.stato != StatoAutoclaveEnum.DISPONIBILE:
                autoclave.stato = StatoAutoclaveEnum.DISPONIBILE
                autoclave.updated_at = datetime.now()
                logger.info(f"🏭 Autoclave {autoclave.id} aggiornata a stato DISPONIBILE")
        
        db.commit()
        db.refresh(batch)
        
        logger.info(f"✅ Batch {batch_id} terminato da {terminato_da_utente}")
        return format_batch_for_response(batch)
        
    except HTTPException:
        raise
    except Exception as e:
        return handle_database_error(db, e, f"terminazione batch {batch_id}")

# Endpoint legacy per compatibilità
@router.patch("/{batch_id}/conferma", response_model=BatchNestingResponse,
              summary="⚠️ DEPRECATO: usa /confirm")
def conferma_batch_nesting_legacy(
    batch_id: str,
    confermato_da_utente: str = Query(...),
    confermato_da_ruolo: str = Query(...),
    db: Session = Depends(get_db)
):
    """Endpoint legacy - usa /confirm"""
    return confirm_batch_nesting(batch_id, confermato_da_utente, confermato_da_ruolo, db)

@router.patch("/{batch_id}/loaded", response_model=BatchNestingResponse,
              summary="⚠️ ALIAS: usa /load")
def load_batch_nesting_legacy(
    batch_id: str,
    caricato_da_utente: str = Query(...),
    caricato_da_ruolo: str = Query(...),
    db: Session = Depends(get_db)
):
    """Endpoint legacy - usa /load"""
    return load_batch_nesting(batch_id, caricato_da_utente, caricato_da_ruolo, db)

@router.patch("/{batch_id}/cured", response_model=BatchNestingResponse,
              summary="⚠️ ALIAS: usa /cure") 
def cure_batch_nesting_legacy(
    batch_id: str,
    avviato_da_utente: str = Query(...),
    avviato_da_ruolo: str = Query(...),
    db: Session = Depends(get_db)
):
    """Endpoint legacy - usa /cure"""
    return cure_batch_nesting(batch_id, avviato_da_utente, avviato_da_ruolo, db) 