"""
Servizio per la gestione della schedulazione degli ODL nelle autoclavi.
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from models.schedule_entry import ScheduleEntry, ScheduleEntryStatus, ScheduleEntryType
from models.odl import ODL
from models.autoclave import Autoclave, StatoAutoclaveEnum
from models.parte import Parte
from models.catalogo import Catalogo
from models.tempo_produzione import TempoProduzione
# from nesting_optimizer.auto_nesting import compute_nesting  # Temporaneamente commentato
from schemas.schedule import (
    ScheduleEntryCreate, ScheduleEntryUpdate, AutoScheduleResponse,
    RecurringScheduleCreate, ScheduleOperatorAction
)
import calendar

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

def get_schedules_by_date_range(db: Session, start_date: date, end_date: date) -> List[ScheduleEntry]:
    """
    Recupera le schedulazioni in un intervallo di date.
    
    Args:
        db: Sessione del database
        start_date: Data di inizio
        end_date: Data di fine
        
    Returns:
        Lista di oggetti ScheduleEntry
    """
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    return db.query(ScheduleEntry).options(
        joinedload(ScheduleEntry.odl),
        joinedload(ScheduleEntry.autoclave)
    ).filter(
        ScheduleEntry.start_datetime >= start_datetime,
        ScheduleEntry.start_datetime <= end_datetime
    ).order_by(ScheduleEntry.start_datetime).all()

def calculate_estimated_end_time(db: Session, schedule_data: ScheduleEntryCreate) -> Optional[datetime]:
    """
    Calcola il tempo di fine stimato basato sui dati storici.
    
    Args:
        db: Sessione del database
        schedule_data: Dati della schedulazione
        
    Returns:
        Data e ora di fine stimata o None se non disponibile
    """
    part_number = None
    categoria = schedule_data.categoria
    sotto_categoria = schedule_data.sotto_categoria
    
    # Se è una schedulazione per ODL specifico, recupera i dati della parte
    if schedule_data.schedule_type == ScheduleEntryType.ODL_SPECIFICO and schedule_data.odl_id:
        odl = db.query(ODL).filter(ODL.id == schedule_data.odl_id).first()
        if odl and odl.parte:
            parte = odl.parte
            if parte.catalogo:
                part_number = parte.catalogo.part_number
                categoria = parte.catalogo.categoria
                sotto_categoria = parte.catalogo.sotto_categoria
    
    # Recupera il tempo stimato dai dati storici
    tempo_stimato = TempoProduzione.get_tempo_stimato(
        db, part_number=part_number, categoria=categoria, sotto_categoria=sotto_categoria
    )
    
    if tempo_stimato:
        return schedule_data.start_datetime + timedelta(minutes=tempo_stimato)
    
    return None

def create_schedule(db: Session, schedule_data: ScheduleEntryCreate) -> ScheduleEntry:
    """
    Crea una nuova schedulazione nel database.
    
    Args:
        db: Sessione del database
        schedule_data: Dati per la creazione della schedulazione
        
    Returns:
        La nuova schedulazione creata
    """
    # Verifica che l'autoclave esista
    autoclave = db.query(Autoclave).filter(Autoclave.id == schedule_data.autoclave_id).first()
    if not autoclave:
        raise ValueError("Autoclave non trovata")
    
    # Se è una schedulazione per ODL specifico, verifica che l'ODL esista
    if schedule_data.schedule_type == ScheduleEntryType.ODL_SPECIFICO:
        if not schedule_data.odl_id:
            raise ValueError("ODL ID è obbligatorio per schedulazioni di tipo ODL_SPECIFICO")
        
        odl = db.query(ODL).filter(ODL.id == schedule_data.odl_id).first()
        if not odl:
            raise ValueError("ODL non trovato")
    
    # Calcola il tempo di fine stimato se non fornito
    end_datetime = schedule_data.end_datetime
    estimated_duration = None
    
    if not end_datetime:
        estimated_end = calculate_estimated_end_time(db, schedule_data)
        if estimated_end:
            end_datetime = estimated_end
            estimated_duration = int((estimated_end - schedule_data.start_datetime).total_seconds() / 60)
    
    # Crea l'oggetto ScheduleEntry
    schedule_entry = ScheduleEntry(
        schedule_type=schedule_data.schedule_type,
        odl_id=schedule_data.odl_id,
        autoclave_id=schedule_data.autoclave_id,
        categoria=schedule_data.categoria,
        sotto_categoria=schedule_data.sotto_categoria,
        start_datetime=schedule_data.start_datetime,
        end_datetime=end_datetime,
        status=schedule_data.status,
        created_by=schedule_data.created_by,
        priority_override=schedule_data.priority_override,
        is_recurring=schedule_data.is_recurring,
        recurring_frequency=schedule_data.recurring_frequency,
        pieces_per_month=schedule_data.pieces_per_month,
        note=schedule_data.note,
        estimated_duration_minutes=estimated_duration
    )
    
    # Salva nel database
    db.add(schedule_entry)
    db.commit()
    db.refresh(schedule_entry)
    
    # Aggiorna lo stato dell'ODL se necessario
    if schedule_entry.odl_id and schedule_entry.odl:
        if schedule_entry.odl.status != "Attesa Cura":
            schedule_entry.odl.status = "Attesa Cura"
            db.add(schedule_entry.odl)
            db.commit()
    
    return schedule_entry

def create_recurring_schedules(db: Session, recurring_data: RecurringScheduleCreate) -> List[ScheduleEntry]:
    """
    Crea schedulazioni ricorrenti per un mese.
    
    Args:
        db: Sessione del database
        recurring_data: Dati per la creazione delle schedulazioni ricorrenti
        
    Returns:
        Lista delle schedulazioni create
    """
    start_date = datetime.strptime(recurring_data.start_date, "%Y-%m-%d").date()
    end_date = datetime.strptime(recurring_data.end_date, "%Y-%m-%d").date()
    
    # Calcola il numero di giorni lavorativi nel periodo
    current_date = start_date
    working_days = []
    
    while current_date <= end_date:
        # Considera solo i giorni feriali (lunedì-venerdì)
        if current_date.weekday() < 5:  # 0=lunedì, 6=domenica
            working_days.append(current_date)
        current_date += timedelta(days=1)
    
    if not working_days:
        raise ValueError("Nessun giorno lavorativo nel periodo specificato")
    
    # Distribuisci i pezzi sui giorni lavorativi
    pieces_per_day = recurring_data.pieces_per_month / len(working_days)
    schedules_created = []
    
    for work_day in working_days:
        # Crea una schedulazione per ogni giorno lavorativo
        schedule_data = ScheduleEntryCreate(
            schedule_type=recurring_data.schedule_type,
            autoclave_id=recurring_data.autoclave_id,
            categoria=recurring_data.categoria,
            sotto_categoria=recurring_data.sotto_categoria,
            start_datetime=datetime.combine(work_day, datetime.min.time().replace(hour=8)),
            status=ScheduleEntryStatus.PREVISIONALE,
            created_by=recurring_data.created_by,
            is_recurring=True,
            recurring_frequency="monthly",
            pieces_per_month=recurring_data.pieces_per_month,
            note=f"Schedulazione automatica ricorrente - {pieces_per_day:.1f} pezzi/giorno"
        )
        
        schedule = create_schedule(db, schedule_data)
        schedules_created.append(schedule)
    
    return schedules_created

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
    update_fields = [
        'schedule_type', 'odl_id', 'autoclave_id', 'categoria', 'sotto_categoria',
        'start_datetime', 'end_datetime', 'status', 'priority_override', 'created_by', 'note'
    ]
    
    for field in update_fields:
        value = getattr(schedule_data, field, None)
        if value is not None:
            setattr(schedule_entry, field, value)
    
    # Ricalcola il tempo di fine se necessario
    if schedule_data.start_datetime and not schedule_data.end_datetime:
        estimated_end = calculate_estimated_end_time(db, schedule_data)
        if estimated_end:
            schedule_entry.end_datetime = estimated_end
            schedule_entry.estimated_duration_minutes = int(
                (estimated_end - schedule_data.start_datetime).total_seconds() / 60
            )
    
    # Salva le modifiche
    db.add(schedule_entry)
    db.commit()
    db.refresh(schedule_entry)
    
    return schedule_entry

def handle_operator_action(db: Session, schedule_id: int, action_data: ScheduleOperatorAction) -> ScheduleEntry:
    """
    Gestisce le azioni dell'operatore su una schedulazione.
    
    Args:
        db: Sessione del database
        schedule_id: ID della schedulazione
        action_data: Dati dell'azione da eseguire
        
    Returns:
        La schedulazione aggiornata
    """
    schedule = get_schedule_by_id(db, schedule_id)
    if not schedule:
        raise ValueError("Schedulazione non trovata")
    
    if action_data.action == "avvia":
        schedule.status = ScheduleEntryStatus.IN_CORSO
        if schedule.odl:
            schedule.odl.status = "Cura"
            db.add(schedule.odl)
        
        # Esegui il nesting automatico se ci sono ODL compatibili
        if schedule.schedule_type in [ScheduleEntryType.CATEGORIA, ScheduleEntryType.SOTTO_CATEGORIA]:
            assign_compatible_odl(db, schedule)
    
    elif action_data.action == "posticipa":
        if not action_data.new_datetime:
            raise ValueError("new_datetime è obbligatorio per l'azione 'posticipa'")
        
        schedule.status = ScheduleEntryStatus.POSTICIPATO
        schedule.start_datetime = action_data.new_datetime
        
        # Ricalcola il tempo di fine
        if schedule.estimated_duration_minutes:
            schedule.end_datetime = action_data.new_datetime + timedelta(minutes=schedule.estimated_duration_minutes)
    
    elif action_data.action == "completa":
        schedule.status = ScheduleEntryStatus.DONE
        if schedule.odl:
            schedule.odl.status = "Finito"
            db.add(schedule.odl)
    
    else:
        raise ValueError(f"Azione non supportata: {action_data.action}")
    
    if action_data.note:
        schedule.note = action_data.note
    
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    
    return schedule

def assign_compatible_odl(db: Session, schedule: ScheduleEntry) -> List[int]:
    """
    Assegna automaticamente ODL compatibili a una schedulazione per categoria.
    
    Args:
        db: Sessione del database
        schedule: Schedulazione per categoria/sotto-categoria
        
    Returns:
        Lista degli ID degli ODL assegnati
    """
    if schedule.schedule_type not in [ScheduleEntryType.CATEGORIA, ScheduleEntryType.SOTTO_CATEGORIA]:
        return []
    
    # Trova ODL compatibili in "Attesa Cura"
    query = db.query(ODL).join(Parte).join(Catalogo).filter(
        ODL.status == "Attesa Cura"
    )
    
    if schedule.schedule_type == ScheduleEntryType.CATEGORIA:
        query = query.filter(Catalogo.categoria == schedule.categoria)
    elif schedule.schedule_type == ScheduleEntryType.SOTTO_CATEGORIA:
        query = query.filter(Catalogo.sotto_categoria == schedule.sotto_categoria)
    
    # Ordina per priorità
    compatible_odl = query.order_by(ODL.priorita.desc()).all()
    
    if not compatible_odl:
        return []
    
    # Esegui il nesting per determinare quali ODL possono essere inclusi
    try:
        nesting_result = compute_nesting(db, compatible_odl, [schedule.autoclave])
        assigned_odl_ids = nesting_result.assegnamenti.get(schedule.autoclave_id, [])
        
        # Crea schedulazioni specifiche per gli ODL assegnati
        for odl_id in assigned_odl_ids:
            odl_schedule = ScheduleEntry(
                schedule_type=ScheduleEntryType.ODL_SPECIFICO,
                odl_id=odl_id,
                autoclave_id=schedule.autoclave_id,
                start_datetime=schedule.start_datetime,
                end_datetime=schedule.end_datetime,
                status=ScheduleEntryStatus.SCHEDULED,
                created_by="auto-assignment",
                parent_schedule_id=schedule.id,
                note=f"Assegnato automaticamente da schedulazione {schedule.id}"
            )
            db.add(odl_schedule)
        
        db.commit()
        return assigned_odl_ids
        
    except Exception as e:
        print(f"Errore durante l'assegnazione automatica: {e}")
        return []

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
    
    # Recupera gli ODL in attesa di cura con priorità alta
    odl_list = db.query(ODL).filter(
        ODL.status == "Attesa Cura"
    ).order_by(ODL.priorita.desc()).all()
    
    # Ottieni le schedulazioni manuali esistenti per il giorno specifico
    existing_schedules = db.query(ScheduleEntry).filter(
        ScheduleEntry.start_datetime >= start_datetime,
        ScheduleEntry.start_datetime <= end_datetime
    ).all()
    
    # Raccogli gli ID degli ODL già schedulati
    scheduled_odl_ids = [s.odl_id for s in existing_schedules if s.odl_id]
    
    # Raccogli gli ID delle autoclavi già utilizzate
    used_autoclave_ids = [s.autoclave_id for s in existing_schedules]
    
    # Filtra gli ODL che non sono già stati schedulati
    available_odl = [odl for odl in odl_list if odl.id not in scheduled_odl_ids]
    
    # Filtra le autoclavi disponibili
    available_autoclavi = [a for a in autoclavi if a.id not in used_autoclave_ids]
    
    # Se non ci sono ODL o autoclavi disponibili, restituisci una risposta vuota
    if not available_odl or not available_autoclavi:
        return AutoScheduleResponse(
            schedules=[],
            message="Nessun ODL in attesa o nessuna autoclave disponibile",
            count=0
        )
    
    # Esegui l'algoritmo di nesting
    nesting_result = compute_nesting(db, available_odl, available_autoclavi)
    
    # Crea le schedulazioni
    created_schedules = []
    
    # Elabora i risultati del nesting
    for autoclave_id, odl_ids in nesting_result.assegnamenti.items():
        for odl_id in odl_ids:
            # Calcola il tempo di fine stimato
            odl = db.query(ODL).filter(ODL.id == odl_id).first()
            end_time = start_datetime.replace(hour=17)  # Default: fine giornata
            estimated_duration = None
            
            if odl and odl.parte and odl.parte.catalogo:
                catalogo = odl.parte.catalogo
                tempo_stimato = TempoProduzione.get_tempo_stimato(
                    db, 
                    part_number=catalogo.part_number,
                    categoria=catalogo.categoria,
                    sotto_categoria=catalogo.sotto_categoria
                )
                if tempo_stimato:
                    end_time = start_datetime.replace(hour=8) + timedelta(minutes=tempo_stimato)
                    estimated_duration = int(tempo_stimato)
            
            # Crea una schedulazione per ogni ODL assegnato
            schedule_entry = ScheduleEntry(
                schedule_type=ScheduleEntryType.ODL_SPECIFICO,
                odl_id=odl_id,
                autoclave_id=autoclave_id,
                start_datetime=start_datetime.replace(hour=8),  # Inizio giornata lavorativa
                end_datetime=end_time,
                status=ScheduleEntryStatus.SCHEDULED,
                created_by="auto-scheduler",
                priority_override=False,
                estimated_duration_minutes=estimated_duration,
                note="Generato automaticamente dal sistema di nesting"
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
        message=f"Generazione automatica completata: {len(created_schedules)} ODL schedulati con priorità",
        count=len(created_schedules)
    ) 