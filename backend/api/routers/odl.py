import logging
from typing import List, Optional, Literal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import desc
from datetime import datetime

from api.database import get_db
from models.odl import ODL
from models.parte import Parte
from models.tool import Tool
from models.tempo_fase import TempoFase
from schemas.odl import ODLCreate, ODLRead, ODLUpdate
from services.odl_queue_service import ODLQueueService
from services.nesting_service import get_odl_attesa_cura_filtered
from services.system_log_service import SystemLogService
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

@router.get("/pending-nesting", response_model=List[ODLRead], 
            summary="Ottiene gli ODL in attesa di essere nidificati")
async def get_odl_pending_nesting(db: Session = Depends(get_db)):
    """
    Recupera tutti gli ODL che sono pronti per essere inclusi nel nesting.
    
    Un ODL è considerato pronto per il nesting se:
    - Ha stato "Attesa Cura"
    - Non è già incluso in un nesting attivo
    - Ha tutti i dati necessari (parte, catalogo, area, valvole)
    
    Returns:
        Lista di ODL pronti per il nesting, ordinati per priorità decrescente
    """
    try:
        # Utilizza la logica esistente del servizio nesting per filtrare gli ODL
        odl_validi = await get_odl_attesa_cura_filtered(db)
        
        logger.info(f"Trovati {len(odl_validi)} ODL pronti per il nesting")
        
        return odl_validi
        
    except Exception as e:
        logger.error(f"Errore durante il recupero degli ODL in attesa di nesting: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Si è verificato un errore durante il recupero degli ODL in attesa di nesting."
        )

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
            logger.info(f"Cambio stato ODL {odl_id}: da '{stato_precedente}' a '{stato_nuovo}'")
            
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

@router.patch("/{odl_id}/laminatore-status", 
              response_model=ODLRead,
              summary="Aggiorna stato ODL per Laminatore")
def update_odl_status_laminatore(
    odl_id: int, 
    new_status: Literal["Laminazione", "Attesa Cura"] = Query(..., description="Nuovo stato ODL"),
    db: Session = Depends(get_db)
):
    """
    Endpoint specifico per il ruolo LAMINATORE.
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
    
    # Controlli specifici per il laminatore
    current_status = db_odl.status
    
    # Verifica transizioni consentite per il laminatore
    allowed_transitions = {
        "Preparazione": ["Laminazione"],
        "Laminazione": ["Attesa Cura"]
    }
    
    if current_status not in allowed_transitions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"ODL in stato '{current_status}' non può essere gestito dal laminatore"
        )
    
    if new_status not in allowed_transitions[current_status]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transizione da '{current_status}' a '{new_status}' non consentita per il laminatore"
        )
    
    try:
        # Salva lo stato precedente per verifica cambiamento
        stato_precedente = db_odl.status
        ora_corrente = datetime.now()
        
        # Aggiorna lo stato
        db_odl.status = new_status
        
        logger.info(f"Laminatore - Cambio stato ODL {odl_id}: da '{stato_precedente}' a '{new_status}'")
        
        # Log dell'evento nel sistema
        SystemLogService.log_odl_state_change(
            db=db,
            odl_id=odl_id,
            old_state=stato_precedente,
            new_state=new_status,
            user_role=UserRole.LAMINATORE,
            user_id="laminatore"  # In futuro si potrà passare l'ID utente reale
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
                fase_attiva.note = f"{fase_attiva.note or ''} - Fase completata da laminatore con cambio stato a '{new_status}'"
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
                    note=f"Fase {tipo_fase_nuova} iniziata da laminatore con cambio stato da '{stato_precedente}'"
                )
                db.add(nuova_fase)
                logger.info(f"Aperta nuova fase '{tipo_fase_nuova}' per ODL {odl_id}")
        
        db.commit()
        db.refresh(db_odl)
        return db_odl
        
    except Exception as e:
        db.rollback()
        logger.error(f"Errore durante l'aggiornamento stato ODL {odl_id} da laminatore: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Si è verificato un errore durante l'aggiornamento dello stato ODL."
        )

@router.patch("/{odl_id}/autoclavista-status", 
              response_model=ODLRead,
              summary="Aggiorna stato ODL per Autoclavista")
def update_odl_status_autoclavista(
    odl_id: int, 
    new_status: Literal["Cura", "Finito"] = Query(..., description="Nuovo stato ODL"),
    db: Session = Depends(get_db)
):
    """
    Endpoint specifico per il ruolo AUTOCLAVISTA.
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
    
    # Controlli specifici per l'autoclavista
    current_status = db_odl.status
    
    # Verifica transizioni consentite per l'autoclavista
    allowed_transitions = {
        "Attesa Cura": ["Cura"],
        "Cura": ["Finito"]
    }
    
    if current_status not in allowed_transitions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"ODL in stato '{current_status}' non può essere gestito dall'autoclavista"
        )
    
    if new_status not in allowed_transitions[current_status]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transizione da '{current_status}' a '{new_status}' non consentita per l'autoclavista"
        )
    
    try:
        # Salva lo stato precedente per verifica cambiamento
        stato_precedente = db_odl.status
        ora_corrente = datetime.now()
        
        # Aggiorna lo stato
        db_odl.status = new_status
        
        logger.info(f"Autoclavista - Cambio stato ODL {odl_id}: da '{stato_precedente}' a '{new_status}'")
        
        # Log dell'evento nel sistema
        SystemLogService.log_odl_state_change(
            db=db,
            odl_id=odl_id,
            old_state=stato_precedente,
            new_state=new_status,
            user_role=UserRole.AUTOCLAVISTA,
            user_id="autoclavista"  # In futuro si potrà passare l'ID utente reale
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
                fase_attiva.note = f"{fase_attiva.note or ''} - Fase completata da autoclavista con cambio stato a '{new_status}'"
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
                    note=f"Fase {tipo_fase_nuova} iniziata da autoclavista con cambio stato da '{stato_precedente}'"
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
        logger.error(f"Errore durante l'aggiornamento stato ODL {odl_id} da autoclavista: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Si è verificato un errore durante l'aggiornamento dello stato ODL."
        )

