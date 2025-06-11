# Router workflow batch - NUOVO FLUSSO SEMPLIFICATO
# Flusso: DRAFT → SOSPESO → IN_CURA → TERMINATO

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime

from api.database import get_db
from models.batch_nesting import BatchNesting, StatoBatchNestingEnum
from models.autoclave import Autoclave, StatoAutoclaveEnum
from models.odl import ODL
from models.tempo_fase import TempoFase
from schemas.batch_nesting import BatchNestingResponse
from .utils import (
    handle_database_error,
    validate_batch_state_transition,
    format_batch_for_response
)

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Batch Nesting - Workflow Semplificato"]
)

@router.patch("/{batch_id}/confirm", response_model=BatchNestingResponse,
              summary="🔄 Conferma batch - Transizione DRAFT → SOSPESO")
def confirm_batch_nesting(
    batch_id: str, 
    confermato_da_utente: str = Query(..., description="ID dell'utente che conferma il batch"),
    confermato_da_ruolo: str = Query(..., description="Ruolo dell'utente che conferma"),
    db: Session = Depends(get_db)
):
    """
    Conferma un batch dalla bozza allo stato sospeso (pronto per caricamento)
    
    Azioni automatiche:
    - Batch: DRAFT → SOSPESO
    - ODL: → "Attesa Cura" 
    """
    try:
        # Trova il batch
        batch = db.query(BatchNesting).filter(BatchNesting.id == batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail="Batch non trovato")
        
        # Valida transizione di stato
        validate_batch_state_transition(batch.stato, StatoBatchNestingEnum.SOSPESO)
        
        # Aggiorna batch
        batch.stato = StatoBatchNestingEnum.SOSPESO.value
        batch.confermato_da_utente = confermato_da_utente
        batch.confermato_da_ruolo = confermato_da_ruolo
        batch.data_conferma = datetime.now()
        
        # Aggiorna ODL associate a "Attesa Cura"
        if batch.odl_ids:
            odls = db.query(ODL).filter(ODL.id.in_(batch.odl_ids)).all()
            for odl in odls:
                if odl.status != "Attesa Cura":
                    odl.status = "Attesa Cura"
                    odl.updated_at = datetime.now()
                    logger.info(f"📋 ODL {odl.id} aggiornato a stato ATTESA CURA")
        
        db.commit()
        db.refresh(batch)
        
        logger.info(f"✅ Batch {batch_id} confermato da {confermato_da_utente} - pronto per caricamento")
        
        return format_batch_for_response(batch)
        
    except HTTPException:
        raise
    except Exception as e:
        return handle_database_error(db, e, f"conferma batch {batch_id}")

@router.patch("/{batch_id}/start-cure", response_model=BatchNestingResponse,
              summary="🔄 Inizia cura - Transizione SOSPESO → IN_CURA")
def start_cure_batch_nesting(
    batch_id: str,
    caricato_da_utente: str = Query(..., description="ID dell'utente che carica l'autoclave"),
    caricato_da_ruolo: str = Query(..., description="Ruolo dell'utente che carica l'autoclave"),
    db: Session = Depends(get_db)
):
    """
    Inizia il ciclo di cura caricando l'autoclave
    
    Azioni automatiche:
    - Batch: SOSPESO → IN_CURA
    - ODL: "Attesa Cura" → "Cura"
    - Autoclave: DISPONIBILE → IN_USO
    - Timing: Inizia conteggio durata cura
    """
    try:
        batch = db.query(BatchNesting).filter(BatchNesting.id == batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail="Batch non trovato")
        
        # Valida transizione di stato
        validate_batch_state_transition(batch.stato, StatoBatchNestingEnum.IN_CURA)
        
        # Aggiorna batch
        batch.stato = StatoBatchNestingEnum.IN_CURA.value
        batch.caricato_da_utente = caricato_da_utente
        batch.caricato_da_ruolo = caricato_da_ruolo
        
        # Aggiorna ODL associate a "Cura" + REGISTRA TEMPO INIZIO CURA
        if batch.odl_ids:
            odls = db.query(ODL).filter(ODL.id.in_(batch.odl_ids)).all()
            for odl in odls:
                if odl.status != "Cura":
                    odl.status = "Cura"
                    odl.updated_at = datetime.now()
                    
                    # ✅ REGISTRA INIZIO CURA tramite TempoFase 
                    tempo_cura = TempoFase(
                        odl_id=odl.id,
                        fase="cura",
                        inizio_fase=datetime.now(),
                        note=f"Cura iniziata da {caricato_da_utente} (batch {batch_id})"
                    )
                    db.add(tempo_cura)
                    
                    logger.info(f"📋 ODL {odl.id} aggiornato a stato CURA + TIMING REGISTRATO")
        
        # Aggiorna autoclave a "IN_USO"
        if batch.autoclave_id:
            autoclave = db.query(Autoclave).filter(Autoclave.id == batch.autoclave_id).first()
            if autoclave and autoclave.stato != StatoAutoclaveEnum.IN_USO.value:
                autoclave.stato = StatoAutoclaveEnum.IN_USO.value
                autoclave.updated_at = datetime.now()
                logger.info(f"🏭 Autoclave {autoclave.id} aggiornata a stato IN_USO - CURA INIZIATA")
        
        db.commit()
        db.refresh(batch)
        
        logger.info(f"✅ Cura INIZIATA per batch {batch_id} da {caricato_da_utente} - timing attivo")
        
        return format_batch_for_response(batch)
        
    except HTTPException:
        raise
    except Exception as e:
        return handle_database_error(db, e, f"inizio cura batch {batch_id}")

@router.patch("/{batch_id}/terminate", response_model=BatchNestingResponse,
              summary="🔄 Termina cura - Transizione IN_CURA → TERMINATO")
def terminate_batch_nesting(
    batch_id: str,
    terminato_da_utente: str = Query(..., description="ID dell'utente che termina la cura"),
    terminato_da_ruolo: str = Query(..., description="Ruolo dell'utente che termina la cura"),
    db: Session = Depends(get_db)
):
    """
    Termina il ciclo di cura completando il workflow
    
    Azioni automatiche:
    - Batch: IN_CURA → TERMINATO
    - ODL: "Cura" → "Finito"
    - Autoclave: IN_USO → DISPONIBILE
    - Timing: Calcola durata effettiva cura
    """
    try:
        batch = db.query(BatchNesting).filter(BatchNesting.id == batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail="Batch non trovato")
        
        # Valida transizione di stato
        validate_batch_state_transition(batch.stato, StatoBatchNestingEnum.TERMINATO)
        
        # Aggiorna batch
        batch.stato = StatoBatchNestingEnum.TERMINATO.value
        batch.terminato_da_utente = terminato_da_utente
        batch.terminato_da_ruolo = terminato_da_ruolo
        
        # Aggiorna ODL associate a "Finito" + REGISTRA FINE CURA
        if batch.odl_ids:
            odls = db.query(ODL).filter(ODL.id.in_(batch.odl_ids)).all()
            for odl in odls:
                if odl.status != "Finito":
                    odl.status = "Finito"
                    odl.updated_at = datetime.now()
                    
                    # ✅ COMPLETA TIMING CURA tramite TempoFase
                    tempo_cura = db.query(TempoFase).filter(
                        TempoFase.odl_id == odl.id,
                        TempoFase.fase == "cura", 
                        TempoFase.fine_fase.is_(None)
                    ).first()
                    
                    if tempo_cura:
                        tempo_cura.fine_fase = datetime.now()
                        # Calcola durata in minuti
                        delta = tempo_cura.fine_fase - tempo_cura.inizio_fase
                        tempo_cura.durata_minuti = int(delta.total_seconds() / 60)
                        tempo_cura.note = f"{tempo_cura.note or ''} | Completato da {terminato_da_utente}"
                        
                        logger.info(f"📋 ODL {odl.id} aggiornato a stato FINITO + TIMING COMPLETATO ({tempo_cura.durata_minuti}min)")
                    else:
                        logger.warning(f"⚠️ ODL {odl.id}: record TempoFase cura non trovato")
        
        # Aggiorna autoclave a "DISPONIBILE"
        if batch.autoclave_id:
            autoclave = db.query(Autoclave).filter(Autoclave.id == batch.autoclave_id).first()
            if autoclave and autoclave.stato != StatoAutoclaveEnum.DISPONIBILE.value:
                autoclave.stato = StatoAutoclaveEnum.DISPONIBILE.value
                autoclave.updated_at = datetime.now()
                logger.info(f"🏭 Autoclave {autoclave.id} aggiornata a stato DISPONIBILE - CURA COMPLETATA")
        
        db.commit()
        db.refresh(batch)
        
        logger.info(f"✅ Cura COMPLETATA per batch {batch_id} da {terminato_da_utente} - Timing registrato via TempoFase")
        
        return format_batch_for_response(batch)
        
    except HTTPException:
        raise
    except Exception as e:
        return handle_database_error(db, e, f"terminazione cura batch {batch_id}")

# 🗑️ ENDPOINT LEGACY - Mantengono compatibilità ma reindirizzano al nuovo flusso
@router.patch("/{batch_id}/conferma", response_model=BatchNestingResponse,
              summary="⚠️ LEGACY: usa /confirm")
def conferma_batch_nesting_legacy(
    batch_id: str,
    confermato_da_utente: str = Query(...),
    confermato_da_ruolo: str = Query(...),
    db: Session = Depends(get_db)
):
    """Endpoint legacy - reindirizza a /confirm"""
    return confirm_batch_nesting(batch_id, confermato_da_utente, confermato_da_ruolo, db) 