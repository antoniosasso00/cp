import logging
from typing import List, Optional, Literal
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session, joinedload, joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import desc, text
from datetime import datetime

from api.database import get_db
from models.odl import ODL
from models.parte import Parte
from models.tool import Tool
from models.tempo_fase import TempoFase
from schemas.odl import ODLCreate, ODLRead, ODLUpdate
from services.odl_queue_service import ODLQueueService
# from services.nesting_service import get_odl_attesa_cura_filtered  # Temporaneamente commentato - sarà implementato nel prossimo step
from services.system_log_service import SystemLogService
from services.state_tracking_service import StateTrackingService
from models.system_log import UserRole

# Configurazione logger
logger = logging.getLogger(__name__)

# Mappa per convertire stato ODL a tipo fase
STATO_A_FASE = {
    "Laminazione": "laminazione",
    "Attesa Cura": "attesa_cura",
    "Cura": "cura"
}

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
        
        # Se l'ODL viene creato già in uno stato di produzione, crea anche il primo TempoFase
        if db_odl.status in STATO_A_FASE:
            tipo_fase = STATO_A_FASE[db_odl.status]
            tempo_fase = TempoFase(
                odl_id=db_odl.id,
                fase=tipo_fase,
                inizio_fase=datetime.now(),
                note=f"Fase {tipo_fase} iniziata automaticamente alla creazione dell'ODL"
            )
            db.add(tempo_fase)
            db.commit()
            logger.info(f"Creato record TempoFase per nuovo ODL {db_odl.id} in stato {db_odl.status}")
        
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

# TEMPORANEAMENTE COMMENTATO - Sarà implementato nel prossimo step quando creeremo il nesting_service
# @router.get("/pending-nesting", response_model=List[ODLRead], 
#             summary="Ottiene gli ODL in attesa di essere nidificati")
# async def get_odl_pending_nesting(db: Session = Depends(get_db)):
#     """
#     Recupera tutti gli ODL che sono pronti per essere inclusi nel nesting.
#     
#     Un ODL è considerato pronto per il nesting se:
#     - Ha stato "Attesa Cura"
#     - Non è già incluso in un nesting attivo
#     - Ha tutti i dati necessari (parte, catalogo, area, valvole)
#     
#     Returns:
#         Lista di ODL pronti per il nesting, ordinati per priorità decrescente
#     """
#     try:
#         # Utilizza la logica esistente del servizio nesting per filtrare gli ODL
#         odl_validi = await get_odl_attesa_cura_filtered(db)
#         
#         logger.info(f"Trovati {len(odl_validi)} ODL pronti per il nesting")
#         
#         return odl_validi
#         
#     except Exception as e:
#         logger.error(f"Errore durante il recupero degli ODL in attesa di nesting: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Si è verificato un errore durante il recupero degli ODL in attesa di nesting."
#         )

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
        
        # Salva lo stato precedente per verifica cambiamento
        stato_precedente = db_odl.status
        
        # Aggiorna i campi
        update_data = odl.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_odl, key, value)
        
        # Verifica se lo stato è cambiato
        stato_nuovo = db_odl.status
        ora_corrente = datetime.now()
        
        if "status" in update_data and stato_precedente != stato_nuovo:
            # ✅ NUOVO: Salva lo stato precedente per la funzione ripristino
            db_odl.previous_status = stato_precedente
            logger.info(f"Cambio stato ODL {odl_id}: da '{stato_precedente}' a '{stato_nuovo}'")
            
            # ✅ NUOVO: Registra il cambio di stato con timestamp preciso
            StateTrackingService.registra_cambio_stato(
                db=db,
                odl_id=odl_id,
                stato_precedente=stato_precedente,
                stato_nuovo=stato_nuovo,
                responsabile="sistema",
                ruolo_responsabile="ADMIN",
                note="Aggiornamento generico via API"
            )
            
            # Chiudi la fase precedente se era in uno stato monitorato
            if stato_precedente in STATO_A_FASE:
                tipo_fase_precedente = STATO_A_FASE[stato_precedente]
                fase_attiva = db.query(TempoFase).filter(
                    TempoFase.odl_id == odl_id,
                    TempoFase.fase == tipo_fase_precedente,
                    TempoFase.fine_fase == None
                ).first()
                
                if fase_attiva:
                    # Calcola la durata in minuti
                    durata = int((ora_corrente - fase_attiva.inizio_fase).total_seconds() / 60)
                    
                    # Aggiorna il record esistente
                    fase_attiva.fine_fase = ora_corrente
                    fase_attiva.durata_minuti = durata 
                    fase_attiva.note = f"{fase_attiva.note or ''} - Fase completata automaticamente con cambio stato a '{stato_nuovo}'"
                    logger.info(f"Chiusa fase '{tipo_fase_precedente}' per ODL {odl_id} con durata {durata} minuti")
            
            # Apri una nuova fase se il nuovo stato è monitorato
            if stato_nuovo in STATO_A_FASE:
                tipo_fase_nuova = STATO_A_FASE[stato_nuovo]
                
                # Verifica se esiste già una fase attiva dello stesso tipo
                fase_esistente = db.query(TempoFase).filter(
                    TempoFase.odl_id == odl_id,
                    TempoFase.fase == tipo_fase_nuova,
                    TempoFase.fine_fase == None
                ).first()
                
                if not fase_esistente:
                    # Crea una nuova fase
                    nuova_fase = TempoFase(
                        odl_id=odl_id,
                        fase=tipo_fase_nuova,
                        inizio_fase=ora_corrente,
                        note=f"Fase {tipo_fase_nuova} iniziata automaticamente con cambio stato da '{stato_precedente}'"
                    )
                    db.add(nuova_fase)
                    logger.info(f"Aperta nuova fase '{tipo_fase_nuova}' per ODL {odl_id}")
        
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
def delete_odl(
    odl_id: int, 
    confirm: bool = Query(False, description="Conferma eliminazione (obbligatorio per ODL finiti)"),
    db: Session = Depends(get_db)
):
    """
    Elimina un ordine di lavoro tramite il suo ID.
    
    Per ODL in stato "Finito", è richiesta la conferma esplicita tramite il parametro 'confirm=true'.
    """
    from sqlalchemy import text
    
    logger.info(f"🔍 ELIMINAZIONE ODL {odl_id} - confirm: {confirm}")
    
    # Verifica che l'ODL esista usando query SQL diretta per evitare 
    # il caricamento automatico delle relazioni schedule_entries
    try:
        result = db.execute(text("SELECT id, status FROM odl WHERE id = :odl_id"), {"odl_id": odl_id})
        odl_data = result.fetchone()
        
        if odl_data is None:
            logger.warning(f"❌ ODL {odl_id} non trovato")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"ODL con ID {odl_id} non trovato"
            )
        
        odl_status = odl_data[1]  # status è la seconda colonna
        logger.info(f"✅ ODL {odl_id} trovato - Stato: {odl_status}")
        
        # Protezione per ODL finiti
        if odl_status == "Finito" and not confirm:
            logger.warning(f"⚠️ ODL finito {odl_id} richiede conferma")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Per eliminare un ODL in stato 'Finito' è richiesta la conferma esplicita. Aggiungi il parametro 'confirm=true' alla richiesta."
            )
        
    except HTTPException:
        # Re-raise HTTPException as-is
        raise
    except Exception as e:
        logger.error(f"❌ Errore verifica ODL {odl_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante la verifica dell'ODL {odl_id}"
        )
    
    try:
        logger.info(f"🚀 Eliminazione ODL {odl_id} in corso...")
        
        # Elimina relazioni in ordine sicuro usando SOLO query SQL dirette
        # per evitare problemi di schema con i modelli SQLAlchemy
        
        # 1. Elimina nesting_result_odl (many-to-many)
        try:
            result = db.execute(text("DELETE FROM nesting_result_odl WHERE odl_id = :odl_id"), {"odl_id": odl_id})
            logger.info(f"✅ nesting_result_odl: {result.rowcount} eliminati")
        except Exception as e:
            logger.warning(f"⚠️ Errore nesting_result_odl: {e}")
        
        # 2. Elimina schedule_entries (SOLO query SQL diretta)
        try:
            result = db.execute(text("DELETE FROM schedule_entries WHERE odl_id = :odl_id"), {"odl_id": odl_id})
            logger.info(f"✅ schedule_entries: {result.rowcount} eliminati")
        except Exception as e:
            logger.warning(f"⚠️ Errore schedule_entries: {e}")
        
        # 3. Elimina tempo_fasi
        try:
            result = db.execute(text("DELETE FROM tempo_fasi WHERE odl_id = :odl_id"), {"odl_id": odl_id})
            logger.info(f"✅ tempo_fasi: {result.rowcount} eliminati")
        except Exception as e:
            logger.warning(f"⚠️ Errore tempo_fasi: {e}")
        
        # 4. Elimina odl_logs
        try:
            result = db.execute(text("DELETE FROM odl_logs WHERE odl_id = :odl_id"), {"odl_id": odl_id})
            logger.info(f"✅ odl_logs: {result.rowcount} eliminati")
        except Exception as e:
            logger.warning(f"⚠️ Errore odl_logs: {e}")
        
        # 5. Elimina state_logs
        try:
            result = db.execute(text("DELETE FROM state_logs WHERE odl_id = :odl_id"), {"odl_id": odl_id})
            logger.info(f"✅ state_logs: {result.rowcount} eliminati")
        except Exception as e:
            logger.warning(f"⚠️ Errore state_logs: {e}")
        
        # 6. Elimina l'ODL principale usando query SQL diretta
        logger.info(f"🎯 Eliminazione ODL principale {odl_id}...")
        result = db.execute(text("DELETE FROM odl WHERE id = :odl_id"), {"odl_id": odl_id})
        if result.rowcount == 0:
            logger.error(f"❌ ODL {odl_id} non eliminato - possibile problema di concorrenza")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"ODL {odl_id} non è stato eliminato"
            )
        
        # 7. Commit finale
        db.commit()
        logger.info(f"🎉 ODL {odl_id} eliminato con successo!")
        
    except HTTPException:
        # Re-raise HTTPException as-is
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ ERRORE eliminazione ODL {odl_id}: {type(e).__name__} - {str(e)}")
        
        # Messaggio di errore semplificato
        error_message = str(e).lower()
        
        if "foreign key constraint" in error_message:
            detail = f"Impossibile eliminare l'ODL {odl_id}: è ancora referenziato da altre entità del sistema."
        elif "no such column" in error_message or "no such table" in error_message:
            detail = f"Errore di schema database durante l'eliminazione dell'ODL {odl_id}."
        else:
            detail = f"Errore durante l'eliminazione dell'ODL {odl_id}: {str(e)}"
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )

@router.post("/check-queue", 
             summary="Controlla e aggiorna automaticamente la coda degli ODL")
def check_odl_queue(db: Session = Depends(get_db)):
    """
    Controlla tutti gli ODL e aggiorna automaticamente lo stato in coda
    quando tutti i tool associati a una parte sono occupati.
    
    Restituisce la lista degli ODL che sono stati aggiornati.
    """
    try:
        updated_odls = ODLQueueService.check_and_update_odl_queue(db)
        
        return {
            "message": f"Controllo coda completato. {len(updated_odls)} ODL aggiornati.",
            "updated_odls": updated_odls
        }
    except Exception as e:
        logger.error(f"Errore durante il controllo della coda ODL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Si è verificato un errore durante il controllo della coda ODL."
        )

@router.post("/{odl_id}/check-status", 
             summary="Controlla lo stato di un singolo ODL")
def check_single_odl_status(odl_id: int, db: Session = Depends(get_db)):
    """
    Forza il controllo dello stato di un singolo ODL per verificare
    se deve essere messo in coda o rimosso dalla coda.
    """
    try:
        result = ODLQueueService.force_check_odl_status(db, odl_id)
        
        if result:
            return {
                "message": f"ODL {odl_id} aggiornato da '{result['old_status']}' a '{result['new_status']}'",
                "update_info": result
            }
        else:
            return {
                "message": f"ODL {odl_id} non necessita aggiornamenti",
                "update_info": None
            }
    except Exception as e:
        logger.error(f"Errore durante il controllo dello stato ODL {odl_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Si è verificato un errore durante il controllo dello stato ODL."
        )

@router.patch("/{odl_id}/clean-room-status", 
              response_model=ODLRead,
              summary="Aggiorna stato ODL per Clean Room")
def update_odl_status_clean_room(
    odl_id: int, 
    new_status: Literal["Laminazione", "Attesa Cura"] = Query(..., description="Nuovo stato ODL"),
    db: Session = Depends(get_db)
):
    """
    Endpoint specifico per il ruolo CLEAN ROOM.
    Permette di far avanzare gli ODL solo negli stati consentiti:
    - Preparazione → Laminazione
    - Laminazione → Attesa Cura
    """
    db_odl = db.query(ODL).filter(ODL.id == odl_id).first()
    
    if db_odl is None:
        logger.warning(f"Tentativo di aggiornamento di ODL inesistente: {odl_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"ODL con ID {odl_id} non trovato"
        )
    
    # Controlli specifici per il Clean Room
    current_status = db_odl.status
    
    # Verifica transizioni consentite per il Clean Room
    allowed_transitions = {
        "Preparazione": ["Laminazione"],
        "Laminazione": ["Attesa Cura"]
    }
    
    if current_status not in allowed_transitions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"ODL in stato '{current_status}' non può essere gestito dal Clean Room"
        )
    
    if new_status not in allowed_transitions[current_status]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transizione da '{current_status}' a '{new_status}' non consentita per il Clean Room"
        )
    
    try:
        # Salva lo stato precedente per verifica cambiamento
        stato_precedente = db_odl.status
        ora_corrente = datetime.now()
        
        # Aggiorna lo stato
        db_odl.status = new_status
        # ✅ NUOVO: Salva lo stato precedente per la funzione ripristino
        db_odl.previous_status = stato_precedente
        
        logger.info(f"Clean Room - Cambio stato ODL {odl_id}: da '{stato_precedente}' a '{new_status}'")
        
        # ✅ NUOVO: Registra il cambio di stato con timestamp preciso
        StateTrackingService.registra_cambio_stato(
            db=db,
            odl_id=odl_id,
            stato_precedente=stato_precedente,
            stato_nuovo=new_status,
            responsabile="clean_room",
            ruolo_responsabile="clean_room",
            note="Cambio stato da interfaccia Clean Room"
        )
        
        # Log dell'evento nel sistema
        SystemLogService.log_odl_state_change(
            db=db,
            odl_id=odl_id,
            old_state=stato_precedente,
            new_state=new_status,
            user_role=UserRole.CLEAN_ROOM,
            user_id="clean_room"  # In futuro si potrà passare l'ID utente reale
        )
        
        # Chiudi la fase precedente se era in uno stato monitorato
        if stato_precedente in STATO_A_FASE:
            tipo_fase_precedente = STATO_A_FASE[stato_precedente]
            fase_attiva = db.query(TempoFase).filter(
                TempoFase.odl_id == odl_id,
                TempoFase.fase == tipo_fase_precedente,
                TempoFase.fine_fase == None
            ).first()
            
            if fase_attiva:
                # Calcola la durata in minuti
                durata = int((ora_corrente - fase_attiva.inizio_fase).total_seconds() / 60)
                
                # Aggiorna il record esistente
                fase_attiva.fine_fase = ora_corrente
                fase_attiva.durata_minuti = durata 
                fase_attiva.note = f"{fase_attiva.note or ''} - Fase completata da Clean Room con cambio stato a '{new_status}'"
                logger.info(f"Chiusa fase '{tipo_fase_precedente}' per ODL {odl_id} con durata {durata} minuti")
        
        # Apri una nuova fase se il nuovo stato è monitorato
        if new_status in STATO_A_FASE:
            tipo_fase_nuova = STATO_A_FASE[new_status]
            
            # Verifica se esiste già una fase attiva dello stesso tipo
            fase_esistente = db.query(TempoFase).filter(
                TempoFase.odl_id == odl_id,
                TempoFase.fase == tipo_fase_nuova,
                TempoFase.fine_fase == None
            ).first()
            
            if not fase_esistente:
                # Crea una nuova fase
                nuova_fase = TempoFase(
                    odl_id=odl_id,
                    fase=tipo_fase_nuova,
                    inizio_fase=ora_corrente,
                    note=f"Fase {tipo_fase_nuova} iniziata da Clean Room con cambio stato da '{stato_precedente}'"
                )
                db.add(nuova_fase)
                logger.info(f"Aperta nuova fase '{tipo_fase_nuova}' per ODL {odl_id}")
        
        db.commit()
        db.refresh(db_odl)
        return db_odl
        
    except Exception as e:
        db.rollback()
        logger.error(f"Errore durante l'aggiornamento stato ODL {odl_id} da Clean Room: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Si è verificato un errore durante l'aggiornamento dello stato ODL."
        )

@router.patch("/{odl_id}/curing-status", 
              response_model=ODLRead,
              summary="Aggiorna stato ODL per Curing")
def update_odl_status_curing(
    odl_id: int, 
    new_status: Literal["Cura", "Finito"] = Query(..., description="Nuovo stato ODL"),
    db: Session = Depends(get_db)
):
    """
    Endpoint specifico per il ruolo CURING.
    Permette di far avanzare gli ODL solo negli stati consentiti:
    - Attesa Cura → Cura (dopo conferma nesting)
    - Cura → Finito (dopo completamento cura)
    """
    db_odl = db.query(ODL).filter(ODL.id == odl_id).first()
    
    if db_odl is None:
        logger.warning(f"Tentativo di aggiornamento di ODL inesistente: {odl_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"ODL con ID {odl_id} non trovato"
        )
    
    # Controlli specifici per il Curing
    current_status = db_odl.status
    
    # Verifica transizioni consentite per il Curing
    allowed_transitions = {
        "Attesa Cura": ["Cura"],
        "Cura": ["Finito"]
    }
    
    if current_status not in allowed_transitions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"ODL in stato '{current_status}' non può essere gestito dal Curing"
        )
    
    if new_status not in allowed_transitions[current_status]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transizione da '{current_status}' a '{new_status}' non consentita per il Curing"
        )
    
    try:
        # Salva lo stato precedente per verifica cambiamento
        stato_precedente = db_odl.status
        ora_corrente = datetime.now()
        
        # Aggiorna lo stato
        db_odl.status = new_status
        # ✅ NUOVO: Salva lo stato precedente per la funzione ripristino
        db_odl.previous_status = stato_precedente
        
        logger.info(f"Curing - Cambio stato ODL {odl_id}: da '{stato_precedente}' a '{new_status}'")
        
        # ✅ NUOVO: Registra il cambio di stato con timestamp preciso
        StateTrackingService.registra_cambio_stato(
            db=db,
            odl_id=odl_id,
            stato_precedente=stato_precedente,
            stato_nuovo=new_status,
            responsabile="curing",
            ruolo_responsabile="curing",
            note="Cambio stato da interfaccia Curing"
        )
        
        # Log dell'evento nel sistema
        SystemLogService.log_odl_state_change(
            db=db,
            odl_id=odl_id,
            old_state=stato_precedente,
            new_state=new_status,
            user_role=UserRole.CURING,
            user_id="curing"  # In futuro si potrà passare l'ID utente reale
        )
        
        # Chiudi la fase precedente se era in uno stato monitorato
        if stato_precedente in STATO_A_FASE:
            tipo_fase_precedente = STATO_A_FASE[stato_precedente]
            fase_attiva = db.query(TempoFase).filter(
                TempoFase.odl_id == odl_id,
                TempoFase.fase == tipo_fase_precedente,
                TempoFase.fine_fase == None
            ).first()
            
            if fase_attiva:
                # Calcola la durata in minuti
                durata = int((ora_corrente - fase_attiva.inizio_fase).total_seconds() / 60)
                
                # Aggiorna il record esistente
                fase_attiva.fine_fase = ora_corrente
                fase_attiva.durata_minuti = durata 
                fase_attiva.note = f"{fase_attiva.note or ''} - Fase completata da Curing con cambio stato a '{new_status}'"
                logger.info(f"Chiusa fase '{tipo_fase_precedente}' per ODL {odl_id} con durata {durata} minuti")
        
        # Apri una nuova fase se il nuovo stato è monitorato
        if new_status in STATO_A_FASE:
            tipo_fase_nuova = STATO_A_FASE[new_status]
            
            # Verifica se esiste già una fase attiva dello stesso tipo
            fase_esistente = db.query(TempoFase).filter(
                TempoFase.odl_id == odl_id,
                TempoFase.fase == tipo_fase_nuova,
                TempoFase.fine_fase == None
            ).first()
            
            if not fase_esistente:
                # Crea una nuova fase
                nuova_fase = TempoFase(
                    odl_id=odl_id,
                    fase=tipo_fase_nuova,
                    inizio_fase=ora_corrente,
                    note=f"Fase {tipo_fase_nuova} iniziata da Curing con cambio stato da '{stato_precedente}'"
                )
                db.add(nuova_fase)
                logger.info(f"Aperta nuova fase '{tipo_fase_nuova}' per ODL {odl_id}")
        
        # 🚀 TRIGGER AUTOMATICO GENERAZIONE REPORT
        # Quando un ODL passa a "Finito", genera automaticamente il report per il nesting associato
        if new_status == "Finito" and stato_precedente == "Cura":
            try:
                from services.auto_report_service import AutoReportService
                from models.nesting_result import NestingResult
                
                # Trova il nesting che contiene questo ODL
                nesting = db.query(NestingResult).filter(
                    NestingResult.odl_ids.contains([odl_id])
                ).order_by(NestingResult.created_at.desc()).first()
                
                if nesting and not nesting.report_id:
                    logger.info(f"🎯 Trigger automatico: generazione report per nesting {nesting.id} (ODL {odl_id} completato)")
                    
                    # Controlla se tutti gli ODL del nesting sono completati
                    odl_nesting_ids = nesting.odl_ids
                    odl_completati = db.query(ODL).filter(
                        ODL.id.in_(odl_nesting_ids),
                        ODL.status == "Finito"
                    ).count()
                    
                    # Se tutti gli ODL del nesting sono completati, genera il report
                    if odl_completati == len(odl_nesting_ids):
                        logger.info(f"✅ Tutti gli ODL del nesting {nesting.id} sono completati - generazione report automatica")
                        
                        # Inizializza il servizio di auto-report
                        auto_report_service = AutoReportService(db)
                        
                        # Prepara le informazioni del ciclo completato
                        cycle_info = {
                            'schedule_id': 0,  # Fittizio per compatibilità
                            'nesting_id': nesting.id,
                            'autoclave_id': nesting.autoclave_id,
                            'odl_id': odl_id,
                            'completed_at': ora_corrente,
                            'nesting': nesting,
                            'schedule': None  # Sarà gestito dal servizio
                        }
                        
                        # Genera il report in modo asincrono (non bloccare la risposta)
                        import asyncio
                        try:
                            # Crea un nuovo loop se necessario
                            loop = asyncio.get_event_loop()
                        except RuntimeError:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                        
                        # Esegui la generazione del report
                        report = loop.run_until_complete(
                            auto_report_service.generate_cycle_completion_report(cycle_info)
                        )
                        
                        if report:
                            logger.info(f"🎉 Report generato automaticamente: {report.filename}")
                        else:
                            logger.warning(f"⚠️ Errore nella generazione automatica del report per nesting {nesting.id}")
                    else:
                        logger.info(f"⏳ Nesting {nesting.id}: {odl_completati}/{len(odl_nesting_ids)} ODL completati - report in attesa")
                elif nesting and nesting.report_id:
                    logger.info(f"ℹ️ Nesting {nesting.id} ha già un report associato (ID: {nesting.report_id})")
                else:
                    logger.warning(f"⚠️ Nessun nesting trovato per ODL {odl_id} o nesting non valido")
                    
            except Exception as e:
                # Non bloccare l'aggiornamento dell'ODL se la generazione del report fallisce
                logger.error(f"❌ Errore durante la generazione automatica del report per ODL {odl_id}: {e}")
        
        db.commit()
        db.refresh(db_odl)
        return db_odl
        
    except Exception as e:
        db.rollback()
        logger.error(f"Errore durante l'aggiornamento stato ODL {odl_id} da Curing: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Si è verificato un errore durante l'aggiornamento dello stato ODL."
        )

@router.patch("/{odl_id}/admin-status", 
              response_model=ODLRead,
              summary="Aggiorna stato ODL per Admin (qualsiasi transizione)")
def update_odl_status_admin(
    odl_id: int, 
    new_status: Literal["Preparazione", "Laminazione", "In Coda", "Attesa Cura", "Cura", "Finito"] = Query(..., description="Nuovo stato ODL"),
    db: Session = Depends(get_db)
):
    """
    Endpoint specifico per il ruolo ADMIN.
    Permette di cambiare lo stato dell'ODL a qualsiasi valore valido,
    senza restrizioni sulle transizioni.
    """
    db_odl = db.query(ODL).filter(ODL.id == odl_id).first()
    
    if db_odl is None:
        logger.warning(f"Tentativo di aggiornamento di ODL inesistente: {odl_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"ODL con ID {odl_id} non trovato"
        )
    
    try:
        # Salva lo stato precedente per verifica cambiamento
        stato_precedente = db_odl.status
        ora_corrente = datetime.now()
        
        # Aggiorna lo stato (admin può fare qualsiasi transizione)
        db_odl.status = new_status
        # ✅ NUOVO: Salva lo stato precedente per la funzione ripristino
        db_odl.previous_status = stato_precedente
        
        logger.info(f"Admin - Cambio stato ODL {odl_id}: da '{stato_precedente}' a '{new_status}'")
        
        # ✅ NUOVO: Registra il cambio di stato con timestamp preciso
        StateTrackingService.registra_cambio_stato(
            db=db,
            odl_id=odl_id,
            stato_precedente=stato_precedente,
            stato_nuovo=new_status,
            responsabile="admin",
            ruolo_responsabile="ADMIN",
            note="Cambio stato da interfaccia admin"
        )
        
        # Log dell'evento nel sistema
        SystemLogService.log_odl_state_change(
            db=db,
            odl_id=odl_id,
            old_state=stato_precedente,
            new_state=new_status,
            user_role=UserRole.ADMIN,
            user_id="admin"  # In futuro si potrà passare l'ID utente reale
        )
        
        # Chiudi la fase precedente se era in uno stato monitorato
        if stato_precedente in STATO_A_FASE:
            tipo_fase_precedente = STATO_A_FASE[stato_precedente]
            fase_attiva = db.query(TempoFase).filter(
                TempoFase.odl_id == odl_id,
                TempoFase.fase == tipo_fase_precedente,
                TempoFase.fine_fase == None
            ).first()
            
            if fase_attiva:
                # Calcola la durata in minuti
                durata = int((ora_corrente - fase_attiva.inizio_fase).total_seconds() / 60)
                
                # Aggiorna il record esistente
                fase_attiva.fine_fase = ora_corrente
                fase_attiva.durata_minuti = durata 
                fase_attiva.note = f"{fase_attiva.note or ''} - Fase completata da admin con cambio stato a '{new_status}'"
                logger.info(f"Chiusa fase '{tipo_fase_precedente}' per ODL {odl_id} con durata {durata} minuti")
        
        # Apri una nuova fase se il nuovo stato è monitorato
        if new_status in STATO_A_FASE:
            tipo_fase_nuova = STATO_A_FASE[new_status]
            
            # Verifica se esiste già una fase attiva dello stesso tipo
            fase_esistente = db.query(TempoFase).filter(
                TempoFase.odl_id == odl_id,
                TempoFase.fase == tipo_fase_nuova,
                TempoFase.fine_fase == None
            ).first()
            
            if not fase_esistente:
                # Crea una nuova fase
                nuova_fase = TempoFase(
                    odl_id=odl_id,
                    fase=tipo_fase_nuova,
                    inizio_fase=ora_corrente,
                    note=f"Fase {tipo_fase_nuova} iniziata da admin con cambio stato da '{stato_precedente}'"
                )
                db.add(nuova_fase)
                logger.info(f"Aperta nuova fase '{tipo_fase_nuova}' per ODL {odl_id}")
        
        db.commit()
        db.refresh(db_odl)
        return db_odl
        
    except Exception as e:
        db.rollback()
        logger.error(f"Errore durante l'aggiornamento stato ODL {odl_id} da admin: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Si è verificato un errore durante l'aggiornamento dello stato ODL."
        )

@router.patch("/{odl_id}/status", 
              response_model=ODLRead,
              summary="Aggiorna stato ODL (endpoint generico)")
def update_odl_status_generic(
    odl_id: int, 
    request: dict = Body(..., example={"new_status": "Attesa Cura"}),
    db: Session = Depends(get_db)
):
    """
    Endpoint generico per l'aggiornamento dello stato ODL.
    Accetta un JSON con il campo 'new_status'.
    
    Supporta conversione automatica da stringhe maiuscole/minuscole.
    
    Esempio di richiesta:
    {
        "new_status": "LAMINAZIONE"  // Viene convertito automaticamente in "Laminazione"
    }
    """
    # Estrai il nuovo stato dalla richiesta
    new_status = request.get("new_status")
    
    if not new_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campo 'new_status' richiesto nel body della richiesta"
        )
    
    # Normalizza il formato dello stato (converte da maiuscolo/minuscolo a formato corretto)
    status_mapping = {
        "PREPARAZIONE": "Preparazione",
        "preparazione": "Preparazione",
        "LAMINAZIONE": "Laminazione", 
        "laminazione": "Laminazione",
        "IN CODA": "In Coda",
        "in coda": "In Coda",
        "IN_CODA": "In Coda",
        "in_coda": "In Coda",
        "ATTESA CURA": "Attesa Cura",
        "attesa cura": "Attesa Cura",
        "ATTESA_CURA": "Attesa Cura",
        "attesa_cura": "Attesa Cura",
        "CURA": "Cura",
        "cura": "Cura",
        "FINITO": "Finito",
        "finito": "Finito"
    }
    
    # Prova prima la conversione diretta, poi la mappatura
    normalized_status = status_mapping.get(new_status, new_status)
    
    # Valida che il nuovo stato sia valido
    valid_statuses = ["Preparazione", "Laminazione", "In Coda", "Attesa Cura", "Cura", "Finito"]
    if normalized_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stato '{new_status}' non valido. Stati validi: {', '.join(valid_statuses)}"
        )
    
    # Usa lo stato normalizzato
    new_status = normalized_status
    
    db_odl = db.query(ODL).filter(ODL.id == odl_id).first()
    
    if db_odl is None:
        logger.warning(f"Tentativo di aggiornamento di ODL inesistente: {odl_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"ODL con ID {odl_id} non trovato"
        )
    
    try:
        # Salva lo stato precedente per verifica cambiamento
        stato_precedente = db_odl.status
        ora_corrente = datetime.now()
        
        logger.info(f"🔄 Inizio aggiornamento ODL {odl_id}: '{stato_precedente}' → '{new_status}'")
        
        # Aggiorna SOLO i campi essenziali
        db_odl.status = new_status
        db_odl.previous_status = stato_precedente
        
        # ✅ NUOVO: Gestione tempo fasi - Chiudi la fase precedente se era in uno stato monitorato
        if stato_precedente in STATO_A_FASE:
            tipo_fase_precedente = STATO_A_FASE[stato_precedente]
            fase_attiva = db.query(TempoFase).filter(
                TempoFase.odl_id == odl_id,
                TempoFase.fase == tipo_fase_precedente,
                TempoFase.fine_fase == None
            ).first()
            
            if fase_attiva:
                # Calcola la durata in minuti
                durata = int((ora_corrente - fase_attiva.inizio_fase).total_seconds() / 60)
                
                # Aggiorna il record esistente
                fase_attiva.fine_fase = ora_corrente
                fase_attiva.durata_minuti = durata 
                fase_attiva.note = f"{fase_attiva.note or ''} - Fase completata con cambio stato a '{new_status}'"
                logger.info(f"Chiusa fase '{tipo_fase_precedente}' per ODL {odl_id} con durata {durata} minuti")
        
        # ✅ NUOVO: Gestione tempo fasi - Apri una nuova fase se il nuovo stato è monitorato
        if new_status in STATO_A_FASE:
            tipo_fase_nuova = STATO_A_FASE[new_status]
            
            # Verifica se esiste già una fase attiva dello stesso tipo
            fase_esistente = db.query(TempoFase).filter(
                TempoFase.odl_id == odl_id,
                TempoFase.fase == tipo_fase_nuova,
                TempoFase.fine_fase == None
            ).first()
            
            if not fase_esistente:
                # Crea una nuova fase
                nuova_fase = TempoFase(
                    odl_id=odl_id,
                    fase=tipo_fase_nuova,
                    inizio_fase=ora_corrente,
                    note=f"Fase {tipo_fase_nuova} iniziata con cambio stato da '{stato_precedente}'"
                )
                db.add(nuova_fase)
                logger.info(f"Aperta nuova fase '{tipo_fase_nuova}' per ODL {odl_id}")
        
        # Commit immediato per l'aggiornamento principale
        db.commit()
        db.refresh(db_odl)
        
        logger.info(f"✅ Aggiornamento stato ODL {odl_id} completato con successo: '{stato_precedente}' → '{db_odl.status}'")
        
        # Ora gestisci i log in modo separato (non critico)
        try:
            StateTrackingService.registra_cambio_stato(
                db=db,
                odl_id=odl_id,
                stato_precedente=stato_precedente,
                stato_nuovo=new_status,
                responsabile="generic",
                ruolo_responsabile="ADMIN",
                note="Cambio stato da endpoint generico"
            )
            db.commit()  # Commit separato per i log
            logger.info(f"✅ StateTrackingService completato per ODL {odl_id}")
        except Exception as e:
            logger.error(f"❌ Errore StateTrackingService per ODL {odl_id}: {str(e)}")
            db.rollback()  # Rollback solo per i log, non per l'ODL
        
        try:
            SystemLogService.log_odl_state_change(
                db=db,
                odl_id=odl_id,
                old_state=stato_precedente,
                new_state=new_status,
                user_role=UserRole.ADMIN,
                user_id="generic"
            )
            db.commit()  # Commit separato per i log
            logger.info(f"✅ SystemLogService completato per ODL {odl_id}")
        except Exception as e:
            logger.error(f"❌ Errore SystemLogService per ODL {odl_id}: {str(e)}")
            db.rollback()  # Rollback solo per i log, non per l'ODL
        
        return db_odl
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Errore durante l'aggiornamento stato ODL {odl_id}: {str(e)}")
        logger.error(f"❌ Tipo errore: {type(e).__name__}")
        import traceback
        logger.error(f"❌ Stack trace: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Si è verificato un errore durante l'aggiornamento dello stato ODL: {str(e)}"
        )

@router.post("/{odl_id}/restore-status", 
             response_model=ODLRead,
             summary="Ripristina lo stato precedente di un ODL")
def restore_previous_status(odl_id: int, db: Session = Depends(get_db)):
    """
    Ripristina lo stato precedente di un ODL utilizzando il campo previous_status.
    
    Questa funzione:
    - Verifica che l'ODL esista
    - Controlla che ci sia uno stato precedente salvato
    - Ripristina lo stato precedente
    - Aggiorna il previous_status con lo stato corrente
    - Registra il cambio nei log
    
    Args:
        odl_id: ID dell'ODL da ripristinare
        db: Sessione del database
        
    Returns:
        ODL aggiornato con lo stato ripristinato
        
    Raises:
        404: Se l'ODL non viene trovato
        400: Se non c'è uno stato precedente da ripristinare
        500: Per errori del server
    """
    # Trova l'ODL
    db_odl = db.query(ODL).filter(ODL.id == odl_id).first()
    
    if db_odl is None:
        logger.warning(f"Tentativo di ripristino di ODL inesistente: {odl_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"ODL con ID {odl_id} non trovato"
        )
    
    # Verifica che ci sia uno stato precedente
    if not db_odl.previous_status:
        logger.warning(f"Tentativo di ripristino ODL {odl_id} senza stato precedente")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"ODL {odl_id} non ha uno stato precedente da ripristinare"
        )
    
    try:
        # Salva gli stati per il log
        stato_corrente = db_odl.status
        stato_da_ripristinare = db_odl.previous_status
        ora_corrente = datetime.now()
        
        # Effettua il ripristino
        db_odl.status = stato_da_ripristinare
        db_odl.previous_status = stato_corrente  # Il vecchio stato corrente diventa il nuovo previous
        
        logger.info(f"🔄 Ripristino stato ODL {odl_id}: da '{stato_corrente}' a '{stato_da_ripristinare}'")
        
        # ✅ Registra il ripristino nei log
        StateTrackingService.registra_cambio_stato(
            db=db,
            odl_id=odl_id,
            stato_precedente=stato_corrente,
            stato_nuovo=stato_da_ripristinare,
            responsabile="sistema",
            ruolo_responsabile="ADMIN",
            note=f"Ripristino stato precedente da '{stato_corrente}' a '{stato_da_ripristinare}'"
        )
        
        # Log dell'evento nel sistema
        SystemLogService.log_odl_state_change(
            db=db,
            odl_id=odl_id,
            old_state=stato_corrente,
            new_state=stato_da_ripristinare,
            user_role=UserRole.ADMIN,
            user_id="restore_function"
        )
        
        # Gestione delle fasi di monitoraggio
        # Chiudi la fase corrente se era in uno stato monitorato
        if stato_corrente in STATO_A_FASE:
            tipo_fase_corrente = STATO_A_FASE[stato_corrente]
            fase_attiva = db.query(TempoFase).filter(
                TempoFase.odl_id == odl_id,
                TempoFase.fase == tipo_fase_corrente,
                TempoFase.fine_fase == None
            ).first()
            
            if fase_attiva:
                # Calcola la durata in minuti
                durata = int((ora_corrente - fase_attiva.inizio_fase).total_seconds() / 60)
                
                # Aggiorna il record esistente
                fase_attiva.fine_fase = ora_corrente
                fase_attiva.durata_minuti = durata 
                fase_attiva.note = f"{fase_attiva.note or ''} - Fase chiusa per ripristino stato a '{stato_da_ripristinare}'"
                logger.info(f"Chiusa fase '{tipo_fase_corrente}' per ODL {odl_id} con durata {durata} minuti (ripristino)")
        
        # Apri una nuova fase se lo stato ripristinato è monitorato
        if stato_da_ripristinare in STATO_A_FASE:
            tipo_fase_ripristinata = STATO_A_FASE[stato_da_ripristinare]
            
            # Verifica se esiste già una fase attiva dello stesso tipo
            fase_esistente = db.query(TempoFase).filter(
                TempoFase.odl_id == odl_id,
                TempoFase.fase == tipo_fase_ripristinata,
                TempoFase.fine_fase == None
            ).first()
            
            if not fase_esistente:
                # Crea una nuova fase
                nuova_fase = TempoFase(
                    odl_id=odl_id,
                    fase=tipo_fase_ripristinata,
                    inizio_fase=ora_corrente,
                    note=f"Fase {tipo_fase_ripristinata} riaperta per ripristino stato da '{stato_corrente}'"
                )
                db.add(nuova_fase)
                logger.info(f"Riaperta fase '{tipo_fase_ripristinata}' per ODL {odl_id} (ripristino)")
        
        db.commit()
        db.refresh(db_odl)
        
        logger.info(f"✅ Ripristino completato per ODL {odl_id}: stato '{stato_da_ripristinare}' ripristinato")
        return db_odl
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Errore durante il ripristino stato ODL {odl_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Si è verificato un errore durante il ripristino dello stato ODL."
        )

@router.get("/{odl_id}/timeline", 
            summary="Ottiene la timeline completa dei cambi di stato di un ODL")
def get_odl_state_timeline(odl_id: int, db: Session = Depends(get_db)):
    """
    Ottiene la timeline completa dei cambi di stato per un ODL specifico.
    
    Restituisce:
    - Tutti i cambi di stato con timestamp precisi
    - Durata di permanenza in ogni stato
    - Responsabile di ogni cambio
    - Statistiche temporali complete
    """
    # Verifica che l'ODL esista
    db_odl = db.query(ODL).filter(ODL.id == odl_id).first()
    if not db_odl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ODL con ID {odl_id} non trovato"
        )
    
    try:
        # Ottieni la timeline completa
        timeline = StateTrackingService.ottieni_timeline_stati(db, odl_id)
        
        # Ottieni statistiche per ogni stato
        statistiche = StateTrackingService.ottieni_statistiche_stati(db, odl_id)
        
        # Calcola tempo nello stato corrente
        tempo_stato_corrente = StateTrackingService.calcola_tempo_in_stato_corrente(db, odl_id)
        
        # Calcola tempo totale di produzione (se completato)
        tempo_totale = StateTrackingService.calcola_tempo_totale_produzione(db, odl_id)
        
        return {
            "odl_id": odl_id,
            "stato_corrente": db_odl.status,
            "timeline": timeline,
            "statistiche_per_stato": statistiche,
            "tempo_in_stato_corrente_minuti": tempo_stato_corrente,
            "tempo_totale_produzione_minuti": tempo_totale,
            "completato": db_odl.status == "Finito"
        }
        
    except Exception as e:
        logger.error(f"❌ Errore durante il recupero timeline ODL {odl_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Si è verificato un errore durante il recupero della timeline."
        )

@router.get("/{odl_id}/validation", 
            summary="Valida i dati di un ODL per il nesting")
def validate_odl_for_nesting(odl_id: int, db: Session = Depends(get_db)):
    """
    Valida che un ODL abbia tutti i dati necessari per essere incluso nel nesting.
    
    Controlla:
    - Tool assegnato
    - Superficie definita
    - Peso definito
    - Numero valvole definito
    - Ciclo di cura assegnato
    - Stato appropriato (Attesa Cura)
    """
    # Verifica che l'ODL esista
    db_odl = db.query(ODL).options(
        joinedload(ODL.parte).joinedload(Parte.catalogo),
        joinedload(ODL.tool)
    ).filter(ODL.id == odl_id).first()
    
    if not db_odl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ODL con ID {odl_id} non trovato"
        )
    
    try:
        # Lista degli errori di validazione
        errori = []
        warnings = []
        
        # Verifica stato
        if db_odl.status != "Attesa Cura":
            errori.append(f"Stato non valido: '{db_odl.status}' (richiesto: 'Attesa Cura')")
        
        # Verifica tool assegnato
        if not db_odl.tool:
            errori.append("Tool non assegnato")
        else:
            if not db_odl.tool.disponibile:
                warnings.append("Tool attualmente non disponibile")
        
        # Verifica parte e catalogo
        if not db_odl.parte:
            errori.append("Parte non definita")
        elif not db_odl.parte.catalogo:
            errori.append("Catalogo parte non definito")
        else:
            # Verifica superficie
            if not db_odl.parte.catalogo.area_cm2 or db_odl.parte.catalogo.area_cm2 <= 0:
                errori.append("Superficie non definita o zero")
            
            # Verifica peso
            if not hasattr(db_odl.parte.catalogo, 'peso_kg') or not db_odl.parte.catalogo.peso_kg:
                warnings.append("Peso non definito (verrà usato valore di default)")
        
        # Verifica valvole
        if not db_odl.parte or not db_odl.parte.num_valvole_richieste or db_odl.parte.num_valvole_richieste <= 0:
            errori.append("Numero valvole non definito")
        
        # Verifica ciclo di cura
        if not db_odl.parte or not hasattr(db_odl.parte, 'ciclo_cura') or not db_odl.parte.ciclo_cura:
            errori.append("Ciclo di cura non assegnato")
        
        # Verifica se già in un nesting attivo
        from models.nesting_result import NestingResult
        existing_nesting = db.query(NestingResult).filter(
            NestingResult.odl_ids.contains([odl_id]),
            NestingResult.stato.in_(["In attesa schedulazione", "Schedulato", "In corso"])
        ).first()
        
        if existing_nesting:
            errori.append(f"Già assegnato al nesting #{existing_nesting.id}")
        
        # Determina se l'ODL è valido per il nesting
        valido = len(errori) == 0
        
        return {
            "odl_id": odl_id,
            "valido_per_nesting": valido,
            "errori": errori,
            "warnings": warnings,
            "dati_odl": {
                "stato": db_odl.status,
                "tool_assegnato": db_odl.tool.part_number_tool if db_odl.tool else None,
                "superficie_cm2": db_odl.parte.catalogo.area_cm2 if db_odl.parte and db_odl.parte.catalogo else None,
                "peso_kg": getattr(db_odl.parte.catalogo, 'peso_kg', None) if db_odl.parte and db_odl.parte.catalogo else None,
                "num_valvole": db_odl.parte.num_valvole_richieste if db_odl.parte else None,
                "ciclo_cura": db_odl.parte.ciclo_cura.nome if db_odl.parte and hasattr(db_odl.parte, 'ciclo_cura') and db_odl.parte.ciclo_cura else None
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Errore durante la validazione ODL {odl_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Si è verificato un errore durante la validazione dell'ODL."
        )

