import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from api.database import get_db
from models.autoclave import Autoclave
from schemas.autoclave import AutoclaveCreate, AutoclaveResponse, AutoclaveUpdate, StatoAutoclaveEnum

# Configurazione logger
logger = logging.getLogger(__name__)

# Creazione router
router = APIRouter(
    tags=["Autoclavi"],
    responses={404: {"description": "Autoclave non trovata"}}
)

@router.post("/", response_model=AutoclaveResponse, status_code=status.HTTP_201_CREATED,
             summary="Crea una nuova autoclave")
def create_autoclave(autoclave: AutoclaveCreate, db: Session = Depends(get_db)):
    """
    Crea una nuova autoclave con le seguenti informazioni:
    - **nome**: nome identificativo dell'autoclave
    - **codice**: codice univoco dell'autoclave
    - **lunghezza**: lunghezza interna in mm
    - **larghezza_piano**: larghezza utile del piano di carico
    - **num_linee_vuoto**: numero di linee vuoto disponibili
    - **temperatura_max**: temperatura massima in gradi Celsius
    - **pressione_max**: pressione massima in bar
    - **stato**: stato attuale dell'autoclave
    - **produttore**: nome del produttore (opzionale)
    - **anno_produzione**: anno di produzione (opzionale)
    - **note**: note aggiuntive (opzionale)
    """
    try:
        # Converte direttamente i dati senza conversione speciale per lo stato
        autoclave_data = autoclave.model_dump()
        db_autoclave = Autoclave(**autoclave_data)
        
        db.add(db_autoclave)
        db.commit()
        db.refresh(db_autoclave)
        return db_autoclave
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Errore durante la creazione dell'autoclave: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Il nome '{autoclave.nome}' o il codice '{autoclave.codice}' è già utilizzato da un'altra autoclave."
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Errore imprevisto durante la creazione dell'autoclave: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Si è verificato un errore durante la creazione dell'autoclave: {str(e)}"
        )

@router.get("/", response_model=List[AutoclaveResponse], 
            summary="Ottiene la lista delle autoclavi")
def read_autoclavi(
    skip: int = 0, 
    limit: int = 100,
    nome: Optional[str] = Query(None, description="Filtra per nome"),
    codice: Optional[str] = Query(None, description="Filtra per codice"),
    stato: Optional[StatoAutoclaveEnum] = Query(None, description="Filtra per stato"),
    db: Session = Depends(get_db)
):
    """
    Recupera una lista di autoclavi con supporto per paginazione e filtri:
    - **skip**: numero di elementi da saltare
    - **limit**: numero massimo di elementi da restituire
    - **nome**: filtro opzionale per nome
    - **codice**: filtro opzionale per codice
    - **stato**: filtro opzionale per stato
    """
    query = db.query(Autoclave)
    
    # Applicazione filtri
    if nome:
        query = query.filter(Autoclave.nome == nome)
    if codice:
        query = query.filter(Autoclave.codice == codice)
    if stato:
        query = query.filter(Autoclave.stato == stato)
    
    return query.offset(skip).limit(limit).all()

@router.get("/{autoclave_id}", response_model=AutoclaveResponse, 
            summary="Ottiene un'autoclave specifica")
def read_autoclave(autoclave_id: int, db: Session = Depends(get_db)):
    """
    Recupera un'autoclave specifica tramite il suo ID.
    """
    db_autoclave = db.query(Autoclave).filter(Autoclave.id == autoclave_id).first()
    if db_autoclave is None:
        logger.warning(f"Tentativo di accesso ad autoclave inesistente: {autoclave_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Autoclave con ID {autoclave_id} non trovata"
        )
    return db_autoclave

@router.get("/by-codice/{codice}", response_model=AutoclaveResponse, 
            summary="Ottiene un'autoclave tramite il codice")
def read_autoclave_by_codice(codice: str, db: Session = Depends(get_db)):
    """
    Recupera un'autoclave specifica tramite il suo codice univoco.
    """
    db_autoclave = db.query(Autoclave).filter(Autoclave.codice == codice).first()
    if db_autoclave is None:
        logger.warning(f"Tentativo di accesso ad autoclave con codice inesistente: {codice}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Autoclave con codice '{codice}' non trovata"
        )
    return db_autoclave

@router.put("/{autoclave_id}", response_model=AutoclaveResponse, 
            summary="Aggiorna un'autoclave")
def update_autoclave(autoclave_id: int, autoclave: AutoclaveUpdate, db: Session = Depends(get_db)):
    """
    Aggiorna i dati di un'autoclave esistente.
    Solo i campi inclusi nella richiesta verranno aggiornati.
    """
    from services.system_log_service import SystemLogService
    from models.system_log import UserRole
    import json
    
    db_autoclave = db.query(Autoclave).filter(Autoclave.id == autoclave_id).first()
    
    if db_autoclave is None:
        logger.warning(f"Tentativo di aggiornamento di autoclave inesistente: {autoclave_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Autoclave con ID {autoclave_id} non trovata"
        )
    
    # Salva i valori precedenti per il logging
    old_values = {
        "nome": db_autoclave.nome,
        "codice": db_autoclave.codice,
        "lunghezza": db_autoclave.lunghezza,
        "larghezza_piano": db_autoclave.larghezza_piano,
        "num_linee_vuoto": db_autoclave.num_linee_vuoto,
        "temperatura_max": db_autoclave.temperatura_max,
        "pressione_max": db_autoclave.pressione_max,
        "max_load_kg": db_autoclave.max_load_kg,
        "stato": db_autoclave.stato.value if db_autoclave.stato else None,
        "produttore": db_autoclave.produttore,
        "anno_produzione": db_autoclave.anno_produzione,
        "note": db_autoclave.note
    }
    
    try:
        # Aggiornamento dei campi presenti nella richiesta
        update_data = autoclave.model_dump(exclude_unset=True)
        modified_fields = []
        
        for key, value in update_data.items():
            old_value = getattr(db_autoclave, key)
            # Gestione speciale per enum
            if hasattr(old_value, 'value'):
                old_value = old_value.value
            
            if old_value != value:
                modified_fields.append(f"{key}: {old_value} → {value}")
                setattr(db_autoclave, key, value)
        
        db.commit()
        db.refresh(db_autoclave)
        
        # Log dell'evento se ci sono state modifiche
        if modified_fields:
            modification_details = f"Campi modificati: {', '.join(modified_fields)}"
            
            SystemLogService.log_autoclave_modify(
                db=db,
                autoclave_id=autoclave_id,
                modification_details=modification_details,
                user_role=UserRole.ADMIN,  # Assumiamo che solo admin possa modificare autoclavi
                old_value=json.dumps(old_values),
                new_value=json.dumps(update_data),
                user_id="admin"  # In futuro si potrà passare l'ID utente reale
            )
            
            logger.info(f"Autoclave {autoclave_id} aggiornata: {modification_details}")
        
        return db_autoclave
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Errore durante l'aggiornamento dell'autoclave {autoclave_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Il nome o il codice specificato è già utilizzato da un'altra autoclave."
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Errore durante l'aggiornamento dell'autoclave {autoclave_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Si è verificato un errore durante l'aggiornamento dell'autoclave: {str(e)}"
        )

@router.delete("/{autoclave_id}", status_code=status.HTTP_204_NO_CONTENT, 
               summary="Elimina un'autoclave")
def delete_autoclave(autoclave_id: int, db: Session = Depends(get_db)):
    """
    Elimina un'autoclave tramite il suo ID.
    """
    db_autoclave = db.query(Autoclave).filter(Autoclave.id == autoclave_id).first()
    
    if db_autoclave is None:
        logger.warning(f"Tentativo di cancellazione di autoclave inesistente: {autoclave_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Autoclave con ID {autoclave_id} non trovata"
        )
    
    try:
        db.delete(db_autoclave)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Errore durante l'eliminazione dell'autoclave {autoclave_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Si è verificato un errore durante l'eliminazione dell'autoclave."
        ) 