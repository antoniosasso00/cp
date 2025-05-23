"""
Servizio per la gestione della schedulazione degli ODL nelle autoclavi.
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from models.schedule_entry import ScheduleEntry, ScheduleEntryStatus
from models.odl import ODL
from models.autoclave import Autoclave, StatoAutoclaveEnum
from models.parte import Parte
from nesting_optimizer.auto_nesting import compute_nesting
from schemas.schedule import ScheduleEntryCreate, ScheduleEntryUpdate, AutoScheduleResponse

def get_all_schedules(db: Session, include_done: bool = False) -> List[ScheduleEntry]:
    """
    Recupera tutte le schedulazioni dal database, opzionalmente escludendo le schedulazioni completate.
    
    Args:
        db: Sessione del database
        include_done: Se True, include anche le schedulazioni con status="done"
        
    Returns:
        Lista di oggetti ScheduleEntry
    """
    query = db.query(ScheduleEntry).options(
        joinedload(ScheduleEntry.odl),
        joinedload(ScheduleEntry.autoclave)
    )
    
    if not include_done:
        query = query.filter(ScheduleEntry.status != ScheduleEntryStatus.DONE)
    
    return query.order_by(ScheduleEntry.start_datetime).all()

def get_schedule_by_id(db: Session, schedule_id: int) -> Optional[ScheduleEntry]:
    """
    Recupera una specifica schedulazione dal database.
    
    Args:
        db: Sessione del database
        schedule_id: ID della schedulazione da recuperare
        
    Returns:
        Oggetto ScheduleEntry o None se non trovato
    """
    return db.query(ScheduleEntry).options(
        joinedload(ScheduleEntry.odl),
        joinedload(ScheduleEntry.autoclave)
    ).filter(ScheduleEntry.id == schedule_id).first()

def create_schedule(db: Session, schedule_data: ScheduleEntryCreate) -> ScheduleEntry:
    """
    Crea una nuova schedulazione nel database.
    
    Args:
        db: Sessione del database
        schedule_data: Dati per la creazione della schedulazione
        
    Returns:
        La nuova schedulazione creata
    """
    # Verifica che l'ODL e l'autoclave esistano
    odl = db.query(ODL).filter(ODL.id == schedule_data.odl_id).first()
    autoclave = db.query(Autoclave).filter(Autoclave.id == schedule_data.autoclave_id).first()
    
    if not odl or not autoclave:
        raise ValueError("ODL o autoclave non trovati")
    
    # Crea l'oggetto ScheduleEntry
    schedule_entry = ScheduleEntry(
        odl_id=schedule_data.odl_id,
        autoclave_id=schedule_data.autoclave_id,
        start_datetime=schedule_data.start_datetime,
        end_datetime=schedule_data.end_datetime,
        status=ScheduleEntryStatus.MANUAL if schedule_data.status == "manual" else ScheduleEntryStatus.SCHEDULED,
        created_by=schedule_data.created_by,
        priority_override=schedule_data.priority_override
    )
    
    # Salva nel database
    db.add(schedule_entry)
    db.commit()
    db.refresh(schedule_entry)
    
    # Aggiorna lo stato dell'ODL in "Attesa Cura"
    if odl.status != "Attesa Cura":
        odl.status = "Attesa Cura"
        db.add(odl)
        db.commit()
    
    return schedule_entry

def update_schedule(db: Session, schedule_id: int, schedule_data: ScheduleEntryUpdate) -> Optional[ScheduleEntry]:
    """
    Aggiorna una schedulazione esistente.
    
    Args:
        db: Sessione del database
        schedule_id: ID della schedulazione da aggiornare
        schedule_data: Dati per l'aggiornamento della schedulazione
        
    Returns:
        La schedulazione aggiornata o None se non trovata
    """
    # Recupera la schedulazione
    schedule_entry = db.query(ScheduleEntry).filter(ScheduleEntry.id == schedule_id).first()
    
    if not schedule_entry:
        return None
    
    # Aggiorna i campi se presenti nei dati di aggiornamento
    if schedule_data.odl_id is not None:
        schedule_entry.odl_id = schedule_data.odl_id
    
    if schedule_data.autoclave_id is not None:
        schedule_entry.autoclave_id = schedule_data.autoclave_id
    
    if schedule_data.start_datetime is not None:
        schedule_entry.start_datetime = schedule_data.start_datetime
    
    if schedule_data.end_datetime is not None:
        schedule_entry.end_datetime = schedule_data.end_datetime
    
    if schedule_data.status is not None:
        if schedule_data.status == "manual":
            schedule_entry.status = ScheduleEntryStatus.MANUAL
        elif schedule_data.status == "scheduled":
            schedule_entry.status = ScheduleEntryStatus.SCHEDULED
        elif schedule_data.status == "done":
            schedule_entry.status = ScheduleEntryStatus.DONE
    
    if schedule_data.priority_override is not None:
        schedule_entry.priority_override = schedule_data.priority_override
    
    if schedule_data.created_by is not None:
        schedule_entry.created_by = schedule_data.created_by
    
    # Salva le modifiche
    db.add(schedule_entry)
    db.commit()
    db.refresh(schedule_entry)
    
    return schedule_entry

def delete_schedule(db: Session, schedule_id: int) -> bool:
    """
    Elimina una schedulazione dal database.
    
    Args:
        db: Sessione del database
        schedule_id: ID della schedulazione da eliminare
        
    Returns:
        True se la schedulazione è stata eliminata, False altrimenti
    """
    # Recupera la schedulazione
    schedule_entry = db.query(ScheduleEntry).filter(ScheduleEntry.id == schedule_id).first()
    
    if not schedule_entry:
        return False
    
    # Elimina la schedulazione
    db.delete(schedule_entry)
    db.commit()
    
    return True

def auto_generate_schedules(db: Session, target_date: str) -> AutoScheduleResponse:
    """
    Genera automaticamente le schedulazioni per una data specifica.
    
    Args:
        db: Sessione del database
        target_date: Data in formato YYYY-MM-DD per cui generare le schedulazioni
        
    Returns:
        Oggetto AutoScheduleResponse con i risultati dell'operazione
    """
    # Converti la stringa della data in oggetto date
    try:
        parsed_date = datetime.strptime(target_date, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Formato data non valido. Usa YYYY-MM-DD")
    
    # Definisci l'inizio e la fine della giornata
    start_datetime = datetime.combine(parsed_date, datetime.min.time())
    end_datetime = datetime.combine(parsed_date, datetime.max.time())
    
    # Recupera le autoclavi disponibili
    autoclavi = db.query(Autoclave).filter(
        Autoclave.stato == StatoAutoclaveEnum.DISPONIBILE
    ).all()
    
    # Recupera gli ODL in attesa di cura
    odl_list = db.query(ODL).filter(ODL.status == "Attesa Cura").all()
    
    # Ottieni le schedulazioni manuali esistenti per il giorno specifico
    existing_manual_schedules = db.query(ScheduleEntry).filter(
        ScheduleEntry.status == ScheduleEntryStatus.MANUAL,
        ScheduleEntry.start_datetime >= start_datetime,
        ScheduleEntry.end_datetime <= end_datetime
    ).all()
    
    # Raccogli gli ID degli ODL già schedulati manualmente
    manual_odl_ids = [schedule.odl_id for schedule in existing_manual_schedules]
    
    # Raccogli gli ID delle autoclavi già utilizzate manualmente in quel giorno
    manual_autoclave_ids = [schedule.autoclave_id for schedule in existing_manual_schedules]
    
    # Filtra gli ODL che non sono già stati schedulati manualmente
    odl_list = [odl for odl in odl_list if odl.id not in manual_odl_ids]
    
    # Filtra le autoclavi che non sono già state utilizzate manualmente nel giorno specifico
    # (Questo è un semplice esempio; in realtà potremmo voler fare controlli più sofisticati sulla sovrapposizione degli slot temporali)
    autoclavi_disponibili = [autoclave for autoclave in autoclavi if autoclave.id not in manual_autoclave_ids]
    
    # Se non ci sono ODL o autoclavi disponibili, restituisci una risposta vuota
    if not odl_list or not autoclavi_disponibili:
        return AutoScheduleResponse(
            schedules=[],
            message="Nessun ODL in attesa o nessuna autoclave disponibile",
            count=0
        )
    
    # Esegui l'algoritmo di nesting
    nesting_result = compute_nesting(db, odl_list, autoclavi_disponibili)
    
    # Crea le schedulazioni
    created_schedules = []
    
    # Elabora i risultati del nesting
    for autoclave_id, odl_ids in nesting_result.assegnamenti.items():
        for odl_id in odl_ids:
            # Crea una schedulazione per ogni ODL assegnato
            schedule_entry = ScheduleEntry(
                odl_id=odl_id,
                autoclave_id=autoclave_id,
                start_datetime=start_datetime,
                end_datetime=end_datetime,  # Semplificazione: l'ODL occupa l'intera giornata
                status=ScheduleEntryStatus.SCHEDULED,
                created_by="auto-scheduler",
                priority_override=False
            )
            
            # Salva nel database
            db.add(schedule_entry)
            created_schedules.append(schedule_entry)
    
    # Commit delle modifiche al database
    db.commit()
    
    # Aggiorna gli oggetti dopo il commit
    for schedule in created_schedules:
        db.refresh(schedule)
    
    # Restituisci la risposta
    return AutoScheduleResponse(
        schedules=created_schedules,
        message=f"Generazione automatica completata: {len(created_schedules)} ODL schedulati",
        count=len(created_schedules)
    ) 