import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
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

# Configurazione logger
logger = logging.getLogger(__name__)

# Creazione router
router = APIRouter(
    prefix="/batch_nesting",
    tags=["Batch Nesting"],
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
    Recupera un batch nesting specifico tramite il suo UUID.
    Include tutte le informazioni dettagliate e le statistiche.
    """
    db_batch = db.query(BatchNesting).filter(BatchNesting.id == batch_id).first()
    if db_batch is None:
        logger.warning(f"Tentativo di accesso a batch nesting inesistente: {batch_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Batch nesting con ID {batch_id} non trovato"
        )
    
    # Aggiunge proprietà calcolate per la risposta
    response_data = db_batch.__dict__.copy()
    response_data['stato_descrizione'] = db_batch.stato_descrizione
    
    return db_batch

@router.put("/{batch_id}", response_model=BatchNestingResponse, 
            summary="Aggiorna un batch nesting")
def update_batch_nesting(
    batch_id: str, 
    batch_update: BatchNestingUpdate, 
    db: Session = Depends(get_db)
):
    """
    Aggiorna i dati di un batch nesting esistente.
    Solo i campi inclusi nella richiesta verranno aggiornati.
    
    Permette di aggiornare:
    - Nome del batch
    - Stato del batch  
    - Lista degli ODL
    - Parametri di nesting
    - Configurazione del layout
    - Note
    - Informazioni di conferma
    """
    db_batch = db.query(BatchNesting).filter(BatchNesting.id == batch_id).first()
    
    if db_batch is None:
        logger.warning(f"Tentativo di aggiornamento di batch nesting inesistente: {batch_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Batch nesting con ID {batch_id} non trovato"
        )
    
    try:
        # Salva i valori precedenti per il logging
        old_state = db_batch.stato.value if db_batch.stato else None
        
        # Aggiornamento dei campi presenti nella richiesta
        update_data = batch_update.model_dump(exclude_unset=True)
        modified_fields = []
        
        for key, value in update_data.items():
            old_value = getattr(db_batch, key)
            
            # Gestione speciale per enum
            if hasattr(old_value, 'value'):
                old_value = old_value.value
            
            # Gestione speciale per oggetti Pydantic nei campi JSON
            if key in ['parametri', 'configurazione_json'] and value is not None:
                if hasattr(value, 'model_dump'):
                    value = value.model_dump()
            
            if old_value != value:
                modified_fields.append(f"{key}: {old_value} → {value}")
                setattr(db_batch, key, value)
        
        # Gestione speciale per il cambio di stato a "CONFERMATO"
        if (batch_update.stato == StatoBatchNestingEnumSchema.CONFERMATO and 
            old_state != StatoBatchNestingEnumSchema.CONFERMATO.value):
            db_batch.data_conferma = datetime.now()
            if batch_update.confermato_da_utente:
                db_batch.confermato_da_utente = batch_update.confermato_da_utente
            if batch_update.confermato_da_ruolo:
                db_batch.confermato_da_ruolo = batch_update.confermato_da_ruolo
        
        db.commit()
        db.refresh(db_batch)
        
        # Log dell'evento se ci sono state modifiche
        if modified_fields:
            modification_details = f"Campi modificati: {', '.join(modified_fields)}"
            logger.info(f"Batch nesting {batch_id} aggiornato: {modification_details}")
        
        return db_batch
        
    except Exception as e:
        db.rollback()
        logger.error(f"Errore durante l'aggiornamento del batch nesting {batch_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Si è verificato un errore durante l'aggiornamento del batch nesting: {str(e)}"
        )

@router.delete("/{batch_id}", status_code=status.HTTP_204_NO_CONTENT, 
               summary="Elimina un batch nesting")
def delete_batch_nesting(batch_id: str, db: Session = Depends(get_db)):
    """
    Elimina un batch nesting esistente.
    
    ⚠️ **Attenzione**: Questa operazione è irreversibile.
    Il batch può essere eliminato solo se è in stato "SOSPESO".
    """
    db_batch = db.query(BatchNesting).filter(BatchNesting.id == batch_id).first()
    
    if db_batch is None:
        logger.warning(f"Tentativo di eliminazione di batch nesting inesistente: {batch_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Batch nesting con ID {batch_id} non trovato"
        )
    
    # Verifica che il batch sia in stato modificabile
    if db_batch.stato != StatoBatchNestingEnum.SOSPESO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Impossibile eliminare il batch nesting in stato '{db_batch.stato.value}'. "
                   f"Solo i batch in stato 'sospeso' possono essere eliminati."
        )
    
    try:
        db.delete(db_batch)
        db.commit()
        logger.info(f"Batch nesting {batch_id} eliminato con successo")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Errore durante l'eliminazione del batch nesting {batch_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Si è verificato un errore durante l'eliminazione del batch nesting: {str(e)}"
        )

@router.get("/{batch_id}/statistics", summary="Ottiene statistiche dettagliate del batch")
def get_batch_statistics(batch_id: str, db: Session = Depends(get_db)):
    """
    Recupera statistiche dettagliate per un batch nesting specifico.
    Include informazioni sui nesting results collegati e metriche di efficienza.
    """
    db_batch = db.query(BatchNesting).filter(BatchNesting.id == batch_id).first()
    
    if db_batch is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Batch nesting con ID {batch_id} non trovato"
        )
    
    # Calcola statistiche aggiuntive
    statistics = {
        "batch_id": batch_id,
        "nome": db_batch.nome,
        "stato": db_batch.stato.value,
        "autoclave_id": db_batch.autoclave_id,
        "numero_odl": len(db_batch.odl_ids) if db_batch.odl_ids else 0,
        "numero_nesting": db_batch.numero_nesting,
        "peso_totale_kg": db_batch.peso_totale_kg,
        "area_totale_utilizzata": db_batch.area_totale_utilizzata,
        "valvole_totali_utilizzate": db_batch.valvole_totali_utilizzate,
        "efficienza_media": db_batch.efficienza_media,
        "created_at": db_batch.created_at,
        "updated_at": db_batch.updated_at,
        "data_conferma": db_batch.data_conferma
    }
    
    return statistics 