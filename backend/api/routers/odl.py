import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import desc

from api.database import get_db
from models.odl import ODL
from models.parte import Parte
from models.tool import Tool
from schemas.odl import ODLCreate, ODLRead, ODLUpdate

# Configurazione logger
logger = logging.getLogger(__name__)

# Creazione router
router = APIRouter(
    tags=["ODL"],
    responses={404: {"description": "ODL non trovato"}}
)

@router.post("/", response_model=ODLRead, status_code=status.HTTP_201_CREATED,
             summary="Crea un nuovo ordine di lavoro")
def create_odl(odl: ODLCreate, db: Session = Depends(get_db)):
    """
    Crea un nuovo ordine di lavoro (ODL) con le seguenti informazioni:
    - **parte_id**: ID della parte associata all'ODL
    - **tool_id**: ID del tool utilizzato per l'ODL
    - **priorita**: livello di priorità dell'ordine (default 1)
    - **status**: stato dell'ordine ("Preparazione", "Laminazione", "Attesa Cura", "Cura", "Finito")
    - **note**: note aggiuntive (opzionale)
    """
    # Verifica che la parte esista
    parte = db.query(Parte).filter(Parte.id == odl.parte_id).first()
    if not parte:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parte con ID {odl.parte_id} non trovata"
        )
    
    # Verifica che il tool esista
    tool = db.query(Tool).filter(Tool.id == odl.tool_id).first()
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool con ID {odl.tool_id} non trovato"
        )
    
    try:
        # Crea l'istanza di ODL
        db_odl = ODL(**odl.model_dump())
        
        db.add(db_odl)
        db.commit()
        db.refresh(db_odl)
        return db_odl
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Errore durante la creazione dell'ODL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vincolo di integrità violato. Verifica che i riferimenti a parte e tool siano corretti."
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Errore imprevisto durante la creazione dell'ODL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Si è verificato un errore durante la creazione dell'ODL."
        )

@router.get("/", response_model=List[ODLRead], 
            summary="Ottiene la lista degli ordini di lavoro")
def read_odl(
    skip: int = 0, 
    limit: int = 100,
    parte_id: Optional[int] = Query(None, description="Filtra per ID parte"),
    tool_id: Optional[int] = Query(None, description="Filtra per ID tool"),
    status: Optional[str] = Query(None, description="Filtra per stato"),
    db: Session = Depends(get_db)
):
    """
    Recupera una lista di ordini di lavoro con supporto per paginazione e filtri:
    - **skip**: numero di elementi da saltare
    - **limit**: numero massimo di elementi da restituire
    - **parte_id**: filtro opzionale per ID parte
    - **tool_id**: filtro opzionale per ID tool
    - **status**: filtro opzionale per stato
    """
    query = db.query(ODL)
    
    # Applicazione filtri
    if parte_id:
        query = query.filter(ODL.parte_id == parte_id)
    if tool_id:
        query = query.filter(ODL.tool_id == tool_id)
    if status:
        query = query.filter(ODL.status == status)
    
    # Ordina per priorità decrescente
    query = query.order_by(desc(ODL.priorita))
    
    return query.offset(skip).limit(limit).all()

@router.get("/{odl_id}", response_model=ODLRead, 
            summary="Ottiene un ordine di lavoro specifico")
def read_one_odl(odl_id: int, db: Session = Depends(get_db)):
    """
    Recupera un ordine di lavoro specifico tramite il suo ID.
    """
    db_odl = db.query(ODL).filter(ODL.id == odl_id).first()
    if db_odl is None:
        logger.warning(f"Tentativo di accesso a ODL inesistente: {odl_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"ODL con ID {odl_id} non trovato"
        )
    return db_odl

@router.put("/{odl_id}", response_model=ODLRead, 
            summary="Aggiorna un ordine di lavoro")
def update_odl(odl_id: int, odl: ODLUpdate, db: Session = Depends(get_db)):
    """
    Aggiorna i dati di un ordine di lavoro esistente.
    Solo i campi inclusi nella richiesta verranno aggiornati.
    """
    db_odl = db.query(ODL).filter(ODL.id == odl_id).first()
    
    if db_odl is None:
        logger.warning(f"Tentativo di aggiornamento di ODL inesistente: {odl_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"ODL con ID {odl_id} non trovato"
        )
    
    try:
        # Verifica che la parte esista se viene aggiornata
        if odl.parte_id is not None:
            parte = db.query(Parte).filter(Parte.id == odl.parte_id).first()
            if not parte:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Parte con ID {odl.parte_id} non trovata"
                )
        
        # Verifica che il tool esista se viene aggiornato
        if odl.tool_id is not None:
            tool = db.query(Tool).filter(Tool.id == odl.tool_id).first()
            if not tool:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Tool con ID {odl.tool_id} non trovato"
                )
        
        # Aggiorna i campi
        update_data = odl.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_odl, key, value)
        
        db.commit()
        db.refresh(db_odl)
        return db_odl
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Errore durante l'aggiornamento dell'ODL {odl_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vincolo di integrità violato. Verifica che i riferimenti a parte e tool siano corretti."
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Errore durante l'aggiornamento dell'ODL {odl_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Si è verificato un errore durante l'aggiornamento dell'ODL."
        )

@router.delete("/{odl_id}", status_code=status.HTTP_204_NO_CONTENT, 
               summary="Elimina un ordine di lavoro")
def delete_odl(odl_id: int, db: Session = Depends(get_db)):
    """
    Elimina un ordine di lavoro tramite il suo ID.
    """
    db_odl = db.query(ODL).filter(ODL.id == odl_id).first()
    
    if db_odl is None:
        logger.warning(f"Tentativo di cancellazione di ODL inesistente: {odl_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"ODL con ID {odl_id} non trovato"
        )
    
    try:
        db.delete(db_odl)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Errore durante l'eliminazione dell'ODL {odl_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Si è verificato un errore durante l'eliminazione dell'ODL."
        ) 