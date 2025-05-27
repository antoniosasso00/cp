"""
Router per la gestione delle schedulazioni degli ODL nelle autoclavi.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date

from models.db import get_db
from models.schedule_entry import ScheduleEntry
from schemas.schedule import (
    ScheduleEntryCreate, ScheduleEntryUpdate, ScheduleEntryRead,
    ScheduleEntryAutoCreate, AutoScheduleResponse, RecurringScheduleCreate,
    ScheduleOperatorAction, TempoProduzioneCreate, TempoProduzioneRead
)
from services.schedule_service import (
    get_all_schedules, get_schedule_by_id, create_schedule,
    update_schedule, delete_schedule, auto_generate_schedules,
    create_recurring_schedules, handle_operator_action,
    get_schedules_by_date_range
)
from services.system_log_service import SystemLogService
from models.system_log import UserRole

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
    start_date: Optional[str] = Query(None, description="Data di inizio filtro (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Data di fine filtro (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Recupera l'elenco di tutte le schedulazioni dal database.
    
    Args:
        include_done: Se True, include anche le schedulazioni con status="done"
        start_date: Data di inizio per il filtro (opzionale)
        end_date: Data di fine per il filtro (opzionale)
        db: Sessione del database
        
    Returns:
        Lista di oggetti ScheduleEntryRead
    """
    try:
        # Se sono specificate le date, usa il filtro per intervallo
        if start_date and end_date:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
            return get_schedules_by_date_range(db, start_date_obj, end_date_obj)
        else:
            return get_all_schedules(db, include_done)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato data non valido: {str(e)}"
        )

# Endpoint per la gestione dei tempi di produzione (DEVONO ESSERE PRIMA DI /{schedule_id})
@router.post(
    "/production-times",
    response_model=TempoProduzioneRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crea un tempo di produzione",
    description="Crea un nuovo record di tempo di produzione per part number, categoria o sotto-categoria"
)
def create_production_time(tempo_data: TempoProduzioneCreate, db: Session = Depends(get_db)):
    """
    Crea un nuovo record di tempo di produzione.
    
    Args:
        tempo_data: Dati del tempo di produzione
        db: Sessione del database
        
    Returns:
        Il record creato
    """
    from models.tempo_produzione import TempoProduzione
    
    try:
        tempo = TempoProduzione(
            part_number=tempo_data.part_number,
            categoria=tempo_data.categoria,
            sotto_categoria=tempo_data.sotto_categoria,
            tempo_medio_minuti=tempo_data.tempo_medio_minuti,
            tempo_minimo_minuti=tempo_data.tempo_minimo_minuti,
            tempo_massimo_minuti=tempo_data.tempo_massimo_minuti,
            numero_osservazioni=tempo_data.numero_osservazioni,
            ultima_osservazione=datetime.now(),
            note=tempo_data.note
        )
        
        db.add(tempo)
        db.commit()
        db.refresh(tempo)
        
        return tempo
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante la creazione del tempo di produzione: {str(e)}"
        )

@router.get(
    "/production-times",
    response_model=List[TempoProduzioneRead],
    summary="Recupera i tempi di produzione",
    description="Recupera tutti i tempi di produzione registrati"
)
def list_production_times(db: Session = Depends(get_db)):
    """
    Recupera tutti i tempi di produzione.
    
    Args:
        db: Sessione del database
        
    Returns:
        Lista dei tempi di produzione
    """
    from models.tempo_produzione import TempoProduzione
    
    return db.query(TempoProduzione).order_by(TempoProduzione.created_at.desc()).all()

@router.get(
    "/production-times/estimate",
    summary="Stima tempo di produzione",
    description="Stima il tempo di produzione per un part number, categoria o sotto-categoria"
)
def estimate_production_time(
    part_number: Optional[str] = Query(None, description="Part number"),
    categoria: Optional[str] = Query(None, description="Categoria"),
    sotto_categoria: Optional[str] = Query(None, description="Sotto-categoria"),
    db: Session = Depends(get_db)
):
    """
    Stima il tempo di produzione basato sui dati storici.
    
    Args:
        part_number: Part number (opzionale)
        categoria: Categoria (opzionale)
        sotto_categoria: Sotto-categoria (opzionale)
        db: Sessione del database
        
    Returns:
        Tempo stimato in minuti o None
    """
    from models.tempo_produzione import TempoProduzione
    
    tempo_stimato = TempoProduzione.get_tempo_stimato(
        db, part_number=part_number, categoria=categoria, sotto_categoria=sotto_categoria
    )
    
    return {
        "part_number": part_number,
        "categoria": categoria,
        "sotto_categoria": sotto_categoria,
        "tempo_stimato_minuti": tempo_stimato,
        "disponibile": tempo_stimato is not None
    }

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
    description="Crea una nuova schedulazione per un ODL o categoria in un'autoclave"
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

@router.post(
    "/recurring",
    response_model=List[ScheduleEntryRead],
    status_code=status.HTTP_201_CREATED,
    summary="Crea schedulazioni ricorrenti",
    description="Crea schedulazioni ricorrenti per un periodo specificato"
)
def create_recurring_schedule(recurring_data: RecurringScheduleCreate, db: Session = Depends(get_db)):
    """
    Crea schedulazioni ricorrenti nel database.
    
    Args:
        recurring_data: Dati per la creazione delle schedulazioni ricorrenti
        db: Sessione del database
        
    Returns:
        Lista delle schedulazioni create
        
    Raises:
        HTTPException: Se ci sono problemi nella creazione
    """
    try:
        return create_recurring_schedules(db, recurring_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante la creazione delle schedulazioni ricorrenti: {str(e)}"
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

@router.post(
    "/{schedule_id}/action",
    response_model=ScheduleEntryRead,
    summary="Esegui azione dell'operatore",
    description="Esegue un'azione dell'operatore su una schedulazione (avvia, posticipa, completa)"
)
def execute_operator_action(
    schedule_id: int,
    action_data: ScheduleOperatorAction,
    db: Session = Depends(get_db)
):
    """
    Esegue un'azione dell'operatore su una schedulazione.
    
    Args:
        schedule_id: ID della schedulazione
        action_data: Dati dell'azione da eseguire
        db: Sessione del database
        
    Returns:
        La schedulazione aggiornata
        
    Raises:
        HTTPException: Se ci sono problemi nell'esecuzione dell'azione
    """
    try:
        result = handle_operator_action(db, schedule_id, action_data)
        
        # Log dell'evento nel sistema
        if action_data.action == "start":
            SystemLogService.log_cura_start(
                db=db,
                schedule_entry_id=schedule_id,
                autoclave_id=result.autoclave_id,
                user_role=UserRole.CURING,
                user_id="curing"
            )
        elif action_data.action == "complete":
            SystemLogService.log_cura_complete(
                db=db,
                schedule_entry_id=schedule_id,
                autoclave_id=result.autoclave_id,
                user_role=UserRole.CURING,
                user_id="curing"
            )
        
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante l'esecuzione dell'azione: {str(e)}"
        )

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

 