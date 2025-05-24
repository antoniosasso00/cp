import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from api.database import get_db
from models.ciclo_cura import CicloCura
from schemas.ciclo_cura import CicloCuraCreate, CicloCuraResponse, CicloCuraUpdate

# Configurazione logger
logger = logging.getLogger(__name__)

# Creazione router
router = APIRouter(
    tags=["Cicli Cura"],
    responses={404: {"description": "Ciclo di cura non trovato"}}
)

@router.post("/", response_model=CicloCuraResponse, status_code=status.HTTP_201_CREATED,
             summary="Crea un nuovo ciclo di cura")
def create_ciclo_cura(ciclo_cura: CicloCuraCreate, db: Session = Depends(get_db)):
    """
    Crea un nuovo ciclo di cura con le seguenti informazioni:
    - **nome**: nome identificativo del ciclo di cura
    - **temperatura_max**: temperatura massima in gradi Celsius
    - **pressione_max**: pressione massima in bar
    - **temperatura_stasi1**: temperatura della prima stasi
    - **pressione_stasi1**: pressione della prima stasi
    - **durata_stasi1**: durata della prima stasi in minuti
    - **attiva_stasi2**: indica se è presente la seconda stasi
    - **temperatura_stasi2**: temperatura della seconda stasi (opzionale)
    - **pressione_stasi2**: pressione della seconda stasi (opzionale)
    - **durata_stasi2**: durata della seconda stasi in minuti (opzionale)
    - **descrizione**: descrizione dettagliata (opzionale)
    """
    db_ciclo_cura = CicloCura(**ciclo_cura.model_dump())
    
    try:
        db.add(db_ciclo_cura)
        db.commit()
        db.refresh(db_ciclo_cura)
        return db_ciclo_cura
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Errore durante la creazione del ciclo di cura: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Il nome '{ciclo_cura.nome}' è già utilizzato da un altro ciclo di cura."
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Errore imprevisto durante la creazione del ciclo di cura: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Si è verificato un errore durante la creazione del ciclo di cura."
        )

@router.get("/", response_model=List[CicloCuraResponse], 
            summary="Ottiene la lista dei cicli di cura")
def read_cicli_cura(
    skip: int = 0, 
    limit: int = 100,
    nome: Optional[str] = Query(None, description="Filtra per nome"),
    temperatura_max_min: Optional[float] = Query(None, description="Filtra per temperatura massima minima"),
    temperatura_max_max: Optional[float] = Query(None, description="Filtra per temperatura massima massima"),
    attiva_stasi2: Optional[bool] = Query(None, description="Filtra per presenza seconda stasi"),
    db: Session = Depends(get_db)
):
    """
    Recupera una lista di cicli di cura con supporto per paginazione e filtri:
    - **skip**: numero di elementi da saltare
    - **limit**: numero massimo di elementi da restituire
    - **nome**: filtro opzionale per nome
    - **temperatura_max_min**: filtro opzionale per temperatura massima minima
    - **temperatura_max_max**: filtro opzionale per temperatura massima massima
    - **attiva_stasi2**: filtro opzionale per presenza seconda stasi
    """
    query = db.query(CicloCura)
    
    # Applicazione filtri
    if nome:
        query = query.filter(CicloCura.nome == nome)
    if temperatura_max_min is not None:
        query = query.filter(CicloCura.temperatura_max >= temperatura_max_min)
    if temperatura_max_max is not None:
        query = query.filter(CicloCura.temperatura_max <= temperatura_max_max)
    if attiva_stasi2 is not None:
        query = query.filter(CicloCura.attiva_stasi2 == attiva_stasi2)
    
    return query.offset(skip).limit(limit).all()

@router.get("/{ciclo_cura_id}", response_model=CicloCuraResponse, 
            summary="Ottiene un ciclo di cura specifico")
def read_ciclo_cura(ciclo_cura_id: int, db: Session = Depends(get_db)):
    """
    Recupera un ciclo di cura specifico tramite il suo ID.
    """
    db_ciclo_cura = db.query(CicloCura).filter(CicloCura.id == ciclo_cura_id).first()
    if db_ciclo_cura is None:
        logger.warning(f"Tentativo di accesso a ciclo di cura inesistente: {ciclo_cura_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Ciclo di cura con ID {ciclo_cura_id} non trovato"
        )
    return db_ciclo_cura

@router.get("/by-nome/{nome}", response_model=CicloCuraResponse, 
            summary="Ottiene un ciclo di cura tramite il nome")
def read_ciclo_cura_by_nome(nome: str, db: Session = Depends(get_db)):
    """
    Recupera un ciclo di cura specifico tramite il suo nome.
    """
    db_ciclo_cura = db.query(CicloCura).filter(CicloCura.nome == nome).first()
    if db_ciclo_cura is None:
        logger.warning(f"Tentativo di accesso a ciclo di cura con nome inesistente: {nome}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Ciclo di cura con nome '{nome}' non trovato"
        )
    return db_ciclo_cura

@router.put("/{ciclo_cura_id}", response_model=CicloCuraResponse, 
            summary="Aggiorna un ciclo di cura")
def update_ciclo_cura(ciclo_cura_id: int, ciclo_cura: CicloCuraUpdate, db: Session = Depends(get_db)):
    """
    Aggiorna i dati di un ciclo di cura esistente.
    Solo i campi inclusi nella richiesta verranno aggiornati.
    """
    db_ciclo_cura = db.query(CicloCura).filter(CicloCura.id == ciclo_cura_id).first()
    
    if db_ciclo_cura is None:
        logger.warning(f"Tentativo di aggiornamento di ciclo di cura inesistente: {ciclo_cura_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Ciclo di cura con ID {ciclo_cura_id} non trovato"
        )
    
    # Ottieni i dati da aggiornare
    update_data = ciclo_cura.model_dump(exclude_unset=True)
    
    # Gestione logica della stasi 2
    if "attiva_stasi2" in update_data:
        if update_data["attiva_stasi2"] == True:
            # Se si sta attivando la stasi2, verifica che i parametri necessari siano presenti
            # sia nei dati di aggiornamento che nel database esistente
            temperatura_stasi2 = update_data.get("temperatura_stasi2") or db_ciclo_cura.temperatura_stasi2
            pressione_stasi2 = update_data.get("pressione_stasi2") or db_ciclo_cura.pressione_stasi2
            durata_stasi2 = update_data.get("durata_stasi2") or db_ciclo_cura.durata_stasi2
            
            if temperatura_stasi2 is None or temperatura_stasi2 <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="Se attiva_stasi2 è True, temperatura_stasi2 deve essere specificata e maggiore di 0"
                )
            if pressione_stasi2 is None or pressione_stasi2 < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="Se attiva_stasi2 è True, pressione_stasi2 deve essere specificata e maggiore o uguale a 0"
                )
            if durata_stasi2 is None or durata_stasi2 <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="Se attiva_stasi2 è True, durata_stasi2 deve essere specificata e maggiore di 0"
                )
        else:
            # Se si sta disattivando la stasi2, imposta i campi a None
            update_data["temperatura_stasi2"] = None
            update_data["pressione_stasi2"] = None
            update_data["durata_stasi2"] = None
    
    # Aggiorna solo i campi specificati nell'update
    for key, value in update_data.items():
        if hasattr(db_ciclo_cura, key):
            setattr(db_ciclo_cura, key, value)
    
    try:
        db.commit()
        db.refresh(db_ciclo_cura)
        logger.info(f"Ciclo di cura {ciclo_cura_id} aggiornato con successo")
        return db_ciclo_cura
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Errore durante l'aggiornamento del ciclo di cura {ciclo_cura_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Il nome specificato è già utilizzato da un altro ciclo di cura."
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Errore durante l'aggiornamento del ciclo di cura {ciclo_cura_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Si è verificato un errore durante l'aggiornamento del ciclo di cura."
        )

@router.delete("/{ciclo_cura_id}", status_code=status.HTTP_204_NO_CONTENT, 
               summary="Elimina un ciclo di cura")
def delete_ciclo_cura(ciclo_cura_id: int, db: Session = Depends(get_db)):
    """
    Elimina un ciclo di cura tramite il suo ID.
    """
    db_ciclo_cura = db.query(CicloCura).filter(CicloCura.id == ciclo_cura_id).first()
    
    if db_ciclo_cura is None:
        logger.warning(f"Tentativo di cancellazione di ciclo di cura inesistente: {ciclo_cura_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Ciclo di cura con ID {ciclo_cura_id} non trovato"
        )
    
    try:
        db.delete(db_ciclo_cura)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Errore durante l'eliminazione del ciclo di cura {ciclo_cura_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Si è verificato un errore durante l'eliminazione del ciclo di cura."
        ) 