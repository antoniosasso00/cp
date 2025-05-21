import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import desc
from datetime import datetime

from api.database import get_db
from models.odl import ODL, ODLStatus, ODLPhase
from models.parte import Parte
from models.tool import Tool
from models.tempo_fase import TempoFase
from schemas.odl import ODLCreate, ODLRead, ODLUpdate, ParteInODL

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
    - **code**: codice univoco dell'ODL
    - **description**: descrizione dell'ODL
    - **parti**: lista di parti da includere nell'ODL con relative quantità
    """
    try:
        # Verifica che tutte le parti esistano e abbiano un tool assegnato
        for parte_data in odl.parti:
            parte = db.query(Parte).filter(Parte.id == parte_data.parte_id).first()
            if not parte:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Parte con ID {parte_data.parte_id} non trovata"
                )
            if not parte.tools:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Parte {parte.part_number} non ha tool assegnati"
                )

        # Crea l'ODL
        db_odl = ODL(
            code=odl.code,
            description=odl.description,
            status=ODLStatus.CREATED,
            current_phase=ODLPhase.LAMINAZIONE
        )
        db.add(db_odl)
        db.flush()

        # Aggiungi le parti all'ODL
        for parte_data in odl.parti:
            parte = db.query(Parte).filter(Parte.id == parte_data.parte_id).first()
            db_odl.parti.append(parte)
            # Aggiorna lo stato della parte
            parte.status = "in_odl"
            parte.last_updated = datetime.utcnow()

        db.commit()
        db.refresh(db_odl)
        return db_odl

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Errore durante la creazione dell'ODL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vincolo di integrità violato. Verifica che il codice ODL sia unico."
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
    status: Optional[ODLStatus] = Query(None, description="Filtra per stato"),
    phase: Optional[ODLPhase] = Query(None, description="Filtra per fase"),
    db: Session = Depends(get_db)
):
    """
    Recupera una lista di ordini di lavoro con supporto per paginazione e filtri:
    - **skip**: numero di elementi da saltare
    - **limit**: numero massimo di elementi da restituire
    - **status**: filtro opzionale per stato
    - **phase**: filtro opzionale per fase
    """
    query = db.query(ODL)
    
    # Applicazione filtri
    if status:
        query = query.filter(ODL.status == status)
    if phase:
        query = query.filter(ODL.current_phase == phase)
    
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
        # Aggiorna i campi
        update_data = odl.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_odl, key, value)
        
        db_odl.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_odl)
        return db_odl

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Errore durante l'aggiornamento dell'ODL {odl_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vincolo di integrità violato."
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Errore durante l'aggiornamento dell'ODL {odl_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Si è verificato un errore durante l'aggiornamento dell'ODL."
        )

@router.post("/{odl_id}/advance", response_model=ODLRead,
             summary="Avanza l'ODL alla fase successiva")
def advance_odl_phase(odl_id: int, db: Session = Depends(get_db)):
    """
    Avanza l'ODL alla fase successiva se tutte le parti sono pronte.
    Le fasi sono: Laminazione -> Pre-nesting -> Nesting -> Autoclave -> Post
    """
    db_odl = db.query(ODL).filter(ODL.id == odl_id).first()
    
    if db_odl is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ODL con ID {odl_id} non trovato"
        )

    try:
        # Determina la fase successiva
        phases = list(ODLPhase)
        current_index = phases.index(db_odl.current_phase)
        if current_index >= len(phases) - 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ODL già completato"
            )
        next_phase = phases[current_index + 1]

        # Verifica che tutte le parti siano pronte per la fase successiva
        for parte in db_odl.parti:
            if not _can_advance_part(parte, db_odl.current_phase):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Parte {parte.part_number} non è pronta per la fase {next_phase}"
                )

        # Aggiorna la fase
        db_odl.current_phase = next_phase
        db_odl.updated_at = datetime.utcnow()

        # Aggiorna lo stato delle parti
        for parte in db_odl.parti:
            parte.status = f"in_{next_phase}"
            parte.last_updated = datetime.utcnow()

        db.commit()
        db.refresh(db_odl)
        return db_odl

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Errore durante l'avanzamento della fase dell'ODL {odl_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Si è verificato un errore durante l'avanzamento della fase."
        )

def _can_advance_part(parte: Parte, current_phase: ODLPhase) -> bool:
    """Verifica se una parte può avanzare alla fase successiva"""
    if current_phase == ODLPhase.LAMINAZIONE:
        return parte.status == "laminated"
    elif current_phase == ODLPhase.PRE_NESTING:
        return parte.status == "ready_for_nesting"
    elif current_phase == ODLPhase.NESTING:
        return parte.status == "nested"
    elif current_phase == ODLPhase.AUTOCLAVE:
        return parte.status == "ready_for_autoclave"
    return False 