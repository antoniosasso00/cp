import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from api.database import get_db
from models.parte import Parte
from models.tool import Tool
from schemas.parte import ParteCreate, ParteResponse, ParteUpdate

# Configurazione logger
logger = logging.getLogger(__name__)

# Creazione router
router = APIRouter(
    tags=["Parte"],
    responses={404: {"description": "Parte non trovata"}}
)

@router.post("/", response_model=ParteResponse, status_code=status.HTTP_201_CREATED,
             summary="Crea una nuova parte")
def create_parte(parte: ParteCreate, db: Session = Depends(get_db)):
    """
    Crea una nuova parte con le seguenti informazioni:
    - **part_number**: codice associato dal catalogo
    - **descrizione_breve**: breve descrizione della parte
    - **num_valvole_richieste**: numero di valvole necessarie
    - **note_produzione**: note per la produzione (opzionale)
    - **ciclo_cura_id**: ID del ciclo di cura associato (opzionale)
    - **tool_ids**: lista di ID degli stampi associati
    """
    # Estrai i tool_ids prima di creare l'oggetto Parte
    tool_ids = parte.tool_ids
    parte_data = parte.model_dump(exclude={"tool_ids"})
    
    # Crea l'istanza di Parte senza gli strumenti
    db_parte = Parte(**parte_data)
    
    try:
        # Aggiungi gli strumenti se presenti
        if tool_ids:
            tools = db.query(Tool).filter(Tool.id.in_(tool_ids)).all()
            found_ids = {tool.id for tool in tools}
            missing_ids = set(tool_ids) - found_ids
            
            if missing_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Tools con ID {missing_ids} non trovati"
                )
            
            db_parte.tools = tools
        
        db.add(db_parte)
        db.commit()
        db.refresh(db_parte)
        return db_parte
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Errore durante la creazione della parte: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vincolo di integrità violato. Verifica che il part_number esista nel catalogo."
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Errore imprevisto durante la creazione della parte: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Si è verificato un errore durante la creazione della parte."
        )

@router.get("/", response_model=List[ParteResponse], 
            summary="Ottiene la lista delle parti")
def read_parti(
    skip: int = 0, 
    limit: int = 100,
    part_number: Optional[str] = Query(None, description="Filtra per part number"),
    db: Session = Depends(get_db)
):
    """
    Recupera una lista di parti con supporto per paginazione e filtri:
    - **skip**: numero di elementi da saltare
    - **limit**: numero massimo di elementi da restituire
    - **part_number**: filtro opzionale per part number
    """
    query = db.query(Parte)
    
    # Applicazione filtri
    if part_number:
        query = query.filter(Parte.part_number == part_number)
    
    return query.offset(skip).limit(limit).all()

@router.get("/{parte_id}", response_model=ParteResponse, 
            summary="Ottiene una parte specifica")
def read_parte(parte_id: int, db: Session = Depends(get_db)):
    """
    Recupera una parte specifica tramite il suo ID.
    """
    db_parte = db.query(Parte).filter(Parte.id == parte_id).first()
    if db_parte is None:
        logger.warning(f"Tentativo di accesso a parte inesistente: {parte_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Parte con ID {parte_id} non trovata"
        )
    return db_parte

@router.put("/{parte_id}", response_model=ParteResponse, 
            summary="Aggiorna una parte")
def update_parte(parte_id: int, parte: ParteUpdate, db: Session = Depends(get_db)):
    """
    Aggiorna i dati di una parte esistente.
    Solo i campi inclusi nella richiesta verranno aggiornati.
    """
    db_parte = db.query(Parte).filter(Parte.id == parte_id).first()
    
    if db_parte is None:
        logger.warning(f"Tentativo di aggiornamento di parte inesistente: {parte_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Parte con ID {parte_id} non trovata"
        )
    
    try:
        # Gestione degli aggiornamenti dei tool solo se specificato
        tool_ids = parte.tool_ids
        update_data = parte.model_dump(exclude={"tool_ids"}, exclude_unset=True)
        
        # Aggiorna i campi base
        for key, value in update_data.items():
            setattr(db_parte, key, value)
        
        # Aggiorna i tool se presenti nella richiesta
        if tool_ids is not None:
            tools = db.query(Tool).filter(Tool.id.in_(tool_ids)).all()
            found_ids = {tool.id for tool in tools}
            missing_ids = set(tool_ids) - found_ids
            
            if missing_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Tools con ID {missing_ids} non trovati"
                )
            
            db_parte.tools = tools
        
        db.commit()
        db.refresh(db_parte)
        return db_parte
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Errore durante l'aggiornamento della parte {parte_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vincolo di integrità violato. Verifica che il part_number esista nel catalogo."
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Errore durante l'aggiornamento della parte {parte_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Si è verificato un errore durante l'aggiornamento della parte."
        )

@router.delete("/{parte_id}", status_code=status.HTTP_204_NO_CONTENT, 
               summary="Elimina una parte")
def delete_parte(parte_id: int, db: Session = Depends(get_db)):
    """
    Elimina una parte tramite il suo ID.
    """
    db_parte = db.query(Parte).filter(Parte.id == parte_id).first()
    
    if db_parte is None:
        logger.warning(f"Tentativo di cancellazione di parte inesistente: {parte_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Parte con ID {parte_id} non trovata"
        )
    
    try:
        db.delete(db_parte)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Errore durante l'eliminazione della parte {parte_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Si è verificato un errore durante l'eliminazione della parte."
        ) 