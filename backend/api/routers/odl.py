import logging
from typing import List, Optional
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