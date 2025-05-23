"""
Router per la gestione delle schedulazioni degli ODL nelle autoclavi.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from models.db import get_db
from models.schedule_entry import ScheduleEntry
from schemas.schedule import (
    ScheduleEntryCreate, ScheduleEntryUpdate, ScheduleEntryRead,
    ScheduleEntryAutoCreate, AutoScheduleResponse
)
from services.schedule_service import (
    get_all_schedules, get_schedule_by_id, create_schedule,
    update_schedule, delete_schedule, auto_generate_schedules
)

# Crea un router per la gestione delle schedulazioni
router = APIRouter(
    tags=["schedule"],
    responses={404: {"description": "Non trovato"}}
)

@router.get(
    "/",
    response_model=List[ScheduleEntryRead],
    summary="Recupera tutte le schedulazioni",
    description="Recupera l'elenco di tutte le schedulazioni, opzionalmente filtrando quelle completate"
)
def list_schedules(
    include_done: bool = Query(False, description="Se True, include anche le schedulazioni completate"),
    db: Session = Depends(get_db)
):
    """
    Recupera l'elenco di tutte le schedulazioni dal database.
    
    Args:
        include_done: Se True, include anche le schedulazioni con status="done"
        db: Sessione del database
        
    Returns:
        Lista di oggetti ScheduleEntryRead
    """
    return get_all_schedules(db, include_done)

@router.get(
    "/{schedule_id}",
    response_model=ScheduleEntryRead,
    summary="Recupera una schedulazione specifica",
    description="Recupera i dettagli di una schedulazione specifica tramite il suo ID"
)
def get_schedule(schedule_id: int, db: Session = Depends(get_db)):
    """
    Recupera una specifica schedulazione dal database.
    
    Args:
        schedule_id: ID della schedulazione da recuperare
        db: Sessione del database
        
    Returns:
        Oggetto ScheduleEntryRead
        
    Raises:
        HTTPException: Se la schedulazione non è trovata
    """
    schedule = get_schedule_by_id(db, schedule_id)
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedulazione con ID {schedule_id} non trovata"
        )
    return schedule

@router.post(
    "/",
    response_model=ScheduleEntryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crea una nuova schedulazione",
    description="Crea una nuova schedulazione per un ODL in un'autoclave"
)
def create_new_schedule(schedule_data: ScheduleEntryCreate, db: Session = Depends(get_db)):
    """
    Crea una nuova schedulazione nel database.
    
    Args:
        schedule_data: Dati per la creazione della schedulazione
        db: Sessione del database
        
    Returns:
        La nuova schedulazione creata
        
    Raises:
        HTTPException: Se ci sono problemi nella creazione
    """
    try:
        return create_schedule(db, schedule_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante la creazione della schedulazione: {str(e)}"
        )

@router.put(
    "/{schedule_id}",
    response_model=ScheduleEntryRead,
    summary="Aggiorna una schedulazione",
    description="Aggiorna i dettagli di una schedulazione esistente"
)
def update_existing_schedule(
    schedule_id: int, 
    schedule_data: ScheduleEntryUpdate, 
    db: Session = Depends(get_db)
):
    """
    Aggiorna una schedulazione esistente.
    
    Args:
        schedule_id: ID della schedulazione da aggiornare
        schedule_data: Dati per l'aggiornamento della schedulazione
        db: Sessione del database
        
    Returns:
        La schedulazione aggiornata
        
    Raises:
        HTTPException: Se la schedulazione non è trovata
    """
    updated_schedule = update_schedule(db, schedule_id, schedule_data)
    if not updated_schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedulazione con ID {schedule_id} non trovata"
        )
    return updated_schedule

@router.delete(
    "/{schedule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Elimina una schedulazione",
    description="Elimina una schedulazione esistente"
)
def delete_existing_schedule(schedule_id: int, db: Session = Depends(get_db)):
    """
    Elimina una schedulazione dal database.
    
    Args:
        schedule_id: ID della schedulazione da eliminare
        db: Sessione del database
        
    Raises:
        HTTPException: Se la schedulazione non è trovata
    """
    success = delete_schedule(db, schedule_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedulazione con ID {schedule_id} non trovata"
        )
    return {"message": "Schedulazione eliminata con successo"}

@router.get(
    "/auto-generate",
    response_model=AutoScheduleResponse,
    summary="Genera automaticamente le schedulazioni",
    description="Esegue l'algoritmo di nesting per generare automaticamente le schedulazioni per una data specifica"
)
def auto_generate(
    date: str = Query(..., description="Data in formato YYYY-MM-DD per cui generare le schedulazioni"),
    db: Session = Depends(get_db)
):
    """
    Genera automaticamente le schedulazioni per una data specifica.
    
    Args:
        date: Data in formato YYYY-MM-DD per cui generare le schedulazioni
        db: Sessione del database
        
    Returns:
        Oggetto AutoScheduleResponse con i risultati dell'operazione
        
    Raises:
        HTTPException: Se ci sono problemi nella generazione
    """
    try:
        return auto_generate_schedules(db, date)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante la generazione automatica delle schedulazioni: {str(e)}"
        ) 