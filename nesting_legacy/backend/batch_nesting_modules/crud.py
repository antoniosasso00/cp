"""
Router CRUD base per batch nesting

Questo modulo contiene le operazioni CRUD fondamentali:
- Creazione batch
- Lettura lista batch
- Lettura singolo batch
- Aggiornamento batch
- Eliminazione batch
- Eliminazione multipla batch
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from api.database import get_db
from models.batch_nesting import BatchNesting, StatoBatchNestingEnum
from models.autoclave import Autoclave
from models.odl import ODL
from schemas.batch_nesting import (
    BatchNestingCreate, 
    BatchNestingResponse, 
    BatchNestingUpdate, 
    BatchNestingList,
    StatoBatchNestingEnum as StatoBatchNestingEnumSchema
)

logger = logging.getLogger(__name__)

# Router per operazioni CRUD
router = APIRouter(
    tags=["Batch Nesting - CRUD"],
    responses={404: {"description": "Batch nesting non trovato"}}
)

@router.post("/", response_model=BatchNestingResponse, status_code=status.HTTP_201_CREATED,
             summary="Crea un nuovo batch nesting")
def create_batch_nesting(batch_data: BatchNestingCreate, db: Session = Depends(get_db)):
    """
    Crea un nuovo batch nesting con le seguenti informazioni:
    
    - **nome**: nome opzionale del batch (se non specificato viene generato automaticamente)
    - **autoclave_id**: ID dell'autoclave per cui è destinato il batch
    - **odl_ids**: lista degli ID degli ODL da includere nel batch
    - **parametri**: parametri utilizzati per la generazione del nesting
    - **configurazione_json**: configurazione del layout generata dal frontend
    - **note**: note aggiuntive opzionali
    - **creato_da_utente**: ID dell'utente che crea il batch
    - **creato_da_ruolo**: ruolo dell'utente che crea il batch
    """
    try:
        # Verifica che l'autoclave esista
        autoclave = db.query(Autoclave).filter(Autoclave.id == batch_data.autoclave_id).first()
        if not autoclave:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Autoclave con ID {batch_data.autoclave_id} non trovata"
            )
        
        # Verifica che tutti gli ODL esistano
        if batch_data.odl_ids:
            existing_odl_count = db.query(ODL).filter(ODL.id.in_(batch_data.odl_ids)).count()
            if existing_odl_count != len(batch_data.odl_ids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Uno o più ODL specificati non esistono"
                )
        
        # Genera nome automatico se non specificato
        if not batch_data.nome:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            batch_data.nome = f"Batch_{autoclave.nome}_{timestamp}"
        
        # Converte i dati per il database
        batch_dict = batch_data.model_dump()
        
        # Converte i parametri e configurazione in dict se sono oggetti Pydantic
        if batch_dict.get('parametri'):
            if hasattr(batch_dict['parametri'], 'model_dump'):
                batch_dict['parametri'] = batch_dict['parametri'].model_dump()
        
        if batch_dict.get('configurazione_json'):
            if hasattr(batch_dict['configurazione_json'], 'model_dump'):
                batch_dict['configurazione_json'] = batch_dict['configurazione_json'].model_dump()
        
        # Calcola statistiche iniziali
        batch_dict['numero_nesting'] = 1 if batch_data.odl_ids else 0
        
        db_batch = BatchNesting(**batch_dict)
        
        db.add(db_batch)
        db.commit()
        db.refresh(db_batch)
        
        logger.info(f"Creato nuovo batch nesting: {db_batch.id} per autoclave {batch_data.autoclave_id}")
        return db_batch
        
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Errore di integrità durante la creazione del batch nesting: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Errore di integrità dei dati. Verificare che tutti i riferimenti siano validi."
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Errore imprevisto durante la creazione del batch nesting: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Si è verificato un errore durante la creazione del batch nesting: {str(e)}"
        )

@router.get("/", response_model=List[BatchNestingList], 
            summary="Ottiene la lista dei batch nesting")
def read_batch_nesting_list(
    skip: int = Query(0, ge=0, description="Numero di elementi da saltare"),
    limit: int = Query(100, ge=1, le=1000, description="Numero massimo di elementi da restituire"),
    autoclave_id: Optional[int] = Query(None, description="Filtra per ID autoclave"),
    stato: Optional[StatoBatchNestingEnumSchema] = Query(None, description="Filtra per stato"),
    nome: Optional[str] = Query(None, description="Filtra per nome (ricerca parziale)"),
    db: Session = Depends(get_db)
):
    """
    Recupera una lista di batch nesting con supporto per paginazione e filtri:
    
    - **skip**: numero di elementi da saltare per la paginazione
    - **limit**: numero massimo di elementi da restituire
    - **autoclave_id**: filtro opzionale per ID autoclave
    - **stato**: filtro opzionale per stato del batch
    - **nome**: filtro opzionale per nome (ricerca parziale case-insensitive)
    """
    query = db.query(BatchNesting)
    
    # Applicazione filtri
    if autoclave_id:
        query = query.filter(BatchNesting.autoclave_id == autoclave_id)
    if stato:
        query = query.filter(BatchNesting.stato == stato.value)
    if nome:
        query = query.filter(BatchNesting.nome.ilike(f"%{nome}%"))
    
    # Ordinamento per data di creazione (più recenti prima)
    query = query.order_by(BatchNesting.created_at.desc())
    
    return query.offset(skip).limit(limit).all()

@router.get("/{batch_id}", response_model=BatchNestingResponse, 
            summary="Ottiene un batch nesting specifico")
def read_batch_nesting(batch_id: str, db: Session = Depends(get_db)):
    """
    Recupera un singolo batch nesting per ID
    """
    batch = db.query(BatchNesting).filter(BatchNesting.id == batch_id).first()
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch nesting con ID {batch_id} non trovato"
        )
    return batch

@router.get("/{batch_id}/full", summary="Ottiene un batch nesting con tutte le informazioni")
def read_batch_nesting_full(batch_id: str, db: Session = Depends(get_db)):
    """
    Recupera un batch nesting con tutte le relazioni caricate (autoclave, ODL, etc.)
    """
    batch = db.query(BatchNesting).options(
        joinedload(BatchNesting.autoclave)
    ).filter(BatchNesting.id == batch_id).first()
    
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch nesting con ID {batch_id} non trovato"
        )
    
    # Carica ODL associati
    if batch.odl_ids:
        odls = db.query(ODL).filter(ODL.id.in_(batch.odl_ids)).all()
        batch_data = {
            "batch": batch,
            "autoclave": batch.autoclave,
            "odls": odls,
            "odl_count": len(odls),
            "total_weight": sum(odl.peso or 0 for odl in odls)
        }
        return batch_data
    
    return {
        "batch": batch,
        "autoclave": batch.autoclave,
        "odls": [],
        "odl_count": 0,
        "total_weight": 0
    }

@router.put("/{batch_id}", response_model=BatchNestingResponse, 
            summary="Aggiorna un batch nesting")
def update_batch_nesting(
    batch_id: str, 
    batch_update: BatchNestingUpdate, 
    db: Session = Depends(get_db)
):
    """
    Aggiorna un batch nesting esistente
    """
    try:
        batch = db.query(BatchNesting).filter(BatchNesting.id == batch_id).first()
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch nesting con ID {batch_id} non trovato"
            )
        
        # Verifica che il batch sia modificabile (non in stati finali)
        if batch.stato in ['TERMINATO', 'FALLITO']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Impossibile modificare un batch in stato {batch.stato}"
            )
        
        # Aggiorna solo i campi forniti
        update_data = batch_update.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(batch, field, value)
        
        # Aggiorna timestamp di modifica
        batch.updated_at = datetime.now()
        
        db.commit()
        db.refresh(batch)
        
        logger.info(f"Aggiornato batch nesting: {batch_id}")
        return batch
        
    except Exception as e:
        db.rollback()
        logger.error(f"Errore durante l'aggiornamento del batch nesting {batch_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Si è verificato un errore durante l'aggiornamento: {str(e)}"
        )

@router.delete("/{batch_id}", status_code=status.HTTP_204_NO_CONTENT, 
               summary="Elimina un batch nesting")
def delete_batch_nesting(batch_id: str, db: Session = Depends(get_db)):
    """
    Elimina un batch nesting
    """
    try:
        batch = db.query(BatchNesting).filter(BatchNesting.id == batch_id).first()
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch nesting con ID {batch_id} non trovato"
            )
        
        # Verifica che il batch sia eliminabile
        if batch.stato in ['CONFERMATO', 'LOADED', 'CURED']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Impossibile eliminare un batch in stato {batch.stato}"
            )
        
        db.delete(batch)
        db.commit()
        
        logger.info(f"Eliminato batch nesting: {batch_id}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Errore durante l'eliminazione del batch nesting {batch_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Si è verificato un errore durante l'eliminazione: {str(e)}"
        )

@router.delete("/bulk", status_code=status.HTTP_200_OK,
               summary="🗑️ Elimina multipli batch nesting con controlli di sicurezza")
def delete_multiple_batch_nesting(
    batch_ids: List[str] = Body(..., description="Lista degli ID dei batch da eliminare"),
    confirm: bool = Query(False, description="Conferma eliminazione (obbligatorio per batch confermati/attivi)"),
    db: Session = Depends(get_db)
):
    """
    🗑️ ELIMINAZIONE MULTIPLA BATCH NESTING
    =======================================
    
    Elimina più batch nesting contemporaneamente con controlli di sicurezza:
    - Batch SOSPESO/DRAFT: eliminazione diretta
    - Batch CONFERMATO/LOADED/CURED: richiede conferma esplicita
    - Batch TERMINATO: non eliminabili (solo archivio)
    """
    try:
        if not batch_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lista batch_ids vuota"
            )
        
        logger.info(f"🗑️ Richiesta eliminazione multipla: {len(batch_ids)} batch")
        
        # Recupera tutti i batch richiesti
        batches = db.query(BatchNesting).filter(BatchNesting.id.in_(batch_ids)).all()
        found_ids = [batch.id for batch in batches]
        missing_ids = [bid for bid in batch_ids if bid not in found_ids]
        
        if missing_ids:
            logger.warning(f"❌ Batch non trovati: {missing_ids}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch non trovati: {missing_ids}"
            )
        
        # Analizza stati e controlli di sicurezza
        safe_to_delete = []
        require_confirmation = []
        cannot_delete = []
        
        for batch in batches:
            if batch.stato in ['SOSPESO', 'DRAFT', 'FALLITO']:
                safe_to_delete.append(batch)
            elif batch.stato in ['CONFERMATO', 'LOADED', 'CURED']:
                require_confirmation.append(batch)
            elif batch.stato in ['TERMINATO']:
                cannot_delete.append(batch)
        
        # Controllo batch non eliminabili
        if cannot_delete:
            cannot_delete_info = [f"{b.id} ({b.stato})" for b in cannot_delete]
            logger.error(f"❌ Batch non eliminabili: {cannot_delete_info}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Batch in stato TERMINATO non eliminabili: {cannot_delete_info}"
            )
        
        # Controllo conferma per batch attivi
        if require_confirmation and not confirm:
            confirmation_info = [f"{b.id} ({b.stato})" for b in require_confirmation]
            logger.warning(f"⚠️ Richiesta conferma per: {confirmation_info}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Batch in stati attivi richiedono conferma esplicita (confirm=true): {confirmation_info}"
            )
        
        # Procedi con l'eliminazione
        deleted_count = 0
        deleted_ids = []
        
        all_to_delete = safe_to_delete + (require_confirmation if confirm else [])
        
        for batch in all_to_delete:
            try:
                logger.info(f"🗑️ Eliminando batch {batch.id} (stato: {batch.stato})")
                db.delete(batch)
                deleted_ids.append(batch.id)
                deleted_count += 1
            except Exception as e:
                logger.error(f"❌ Errore eliminazione batch {batch.id}: {e}")
                # Continua con gli altri batch
        
        db.commit()
        
        logger.info(f"✅ Eliminazione multipla completata: {deleted_count}/{len(batch_ids)} batch")
        
        return {
            "message": f"Eliminati {deleted_count} batch nesting",
            "deleted_count": deleted_count,
            "deleted_ids": deleted_ids,
            "total_requested": len(batch_ids),
            "required_confirmation": len(require_confirmation) if not confirm else 0,
            "cannot_delete": len(cannot_delete)
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Errore durante eliminazione multipla: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante eliminazione multipla: {str(e)}"
        ) 