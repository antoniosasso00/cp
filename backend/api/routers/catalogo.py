import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from api.database import get_db
from models.catalogo import Catalogo
from schemas.catalogo import CatalogoCreate, CatalogoResponse, CatalogoUpdate

# Configurazione logger
logger = logging.getLogger(__name__)

# Creazione router
router = APIRouter(
    tags=["Catalogo"],
    responses={404: {"description": "Catalogo non trovato"}}
)

@router.post("/", response_model=CatalogoResponse, status_code=status.HTTP_201_CREATED, 
             summary="Crea un nuovo elemento nel catalogo")
def create_catalogo(catalogo: CatalogoCreate, db: Session = Depends(get_db)):
    """
    Crea un nuovo elemento nel catalogo con le seguenti informazioni:
    - **part_number**: codice univoco del prodotto
    - **descrizione**: descrizione dettagliata
    - **categoria**: categoria del prodotto (opzionale)
    - **attivo**: se il prodotto è attualmente attivo
    - **note**: note aggiuntive (opzionale)
    """
    db_catalogo = Catalogo(**catalogo.model_dump())
    
    try:
        db.add(db_catalogo)
        db.commit()
        db.refresh(db_catalogo)
        return db_catalogo
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Errore durante la creazione del catalogo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Part number '{catalogo.part_number}' già esistente."
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Errore imprevisto durante la creazione del catalogo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Si è verificato un errore durante la creazione del catalogo."
        )

@router.get("/", response_model=List[CatalogoResponse], 
            summary="Ottiene la lista degli elementi del catalogo")
def read_cataloghi(
    skip: int = 0, 
    limit: int = 100, 
    categoria: Optional[str] = Query(None, description="Filtra per categoria"),
    sotto_categoria: Optional[str] = Query(None, description="Filtra per sotto-categoria"),
    attivo: Optional[bool] = Query(None, description="Filtra per stato attivo/inattivo"),
    search: Optional[str] = Query(None, description="Ricerca nel part number, descrizione, categoria o sotto-categoria"),
    db: Session = Depends(get_db)
):
    """
    Recupera una lista di elementi del catalogo con supporto per paginazione e filtri:
    - **skip**: numero di elementi da saltare
    - **limit**: numero massimo di elementi da restituire
    - **categoria**: filtro opzionale per categoria
    - **sotto_categoria**: filtro opzionale per sotto-categoria
    - **attivo**: filtro opzionale per attivo/non attivo
    - **search**: ricerca per testo nei campi principali
    """
    query = db.query(Catalogo)
    
    # Applicazione filtri
    if categoria:
        query = query.filter(Catalogo.categoria == categoria)
    if sotto_categoria:
        query = query.filter(Catalogo.sotto_categoria == sotto_categoria)
    if attivo is not None:
        query = query.filter(Catalogo.attivo == attivo)
    
    # Ricerca testuale
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Catalogo.part_number.ilike(search_term)) |
            (Catalogo.descrizione.ilike(search_term)) |
            (Catalogo.categoria.ilike(search_term)) |
            (Catalogo.sotto_categoria.ilike(search_term))
        )
    
    return query.offset(skip).limit(limit).all()

@router.get("/{part_number}", response_model=CatalogoResponse, 
            summary="Ottiene un elemento specifico del catalogo")
def read_catalogo(part_number: str, db: Session = Depends(get_db)):
    """
    Recupera un elemento specifico del catalogo tramite il suo part_number.
    """
    db_catalogo = db.query(Catalogo).filter(Catalogo.part_number == part_number).first()
    if db_catalogo is None:
        logger.warning(f"Tentativo di accesso a part number inesistente: {part_number}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Catalogo con part number '{part_number}' non trovato"
        )
    return db_catalogo

@router.put("/{part_number}", response_model=CatalogoResponse, 
            summary="Aggiorna un elemento del catalogo")
def update_catalogo(part_number: str, catalogo: CatalogoUpdate, db: Session = Depends(get_db)):
    """
    Aggiorna i dati di un elemento del catalogo esistente.
    Solo i campi inclusi nella richiesta verranno aggiornati.
    """
    db_catalogo = db.query(Catalogo).filter(Catalogo.part_number == part_number).first()
    
    if db_catalogo is None:
        logger.warning(f"Tentativo di aggiornamento di part number inesistente: {part_number}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Catalogo con part number '{part_number}' non trovato"
        )
    
    # Aggiornamento dei campi presenti nella richiesta
    update_data = catalogo.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_catalogo, key, value)
    
    try:
        db.commit()
        db.refresh(db_catalogo)
        return db_catalogo
    except Exception as e:
        db.rollback()
        logger.error(f"Errore durante l'aggiornamento del catalogo {part_number}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Si è verificato un errore durante l'aggiornamento del catalogo."
        )

@router.delete("/{part_number}", status_code=status.HTTP_204_NO_CONTENT, 
               summary="Elimina un elemento del catalogo")
def delete_catalogo(part_number: str, db: Session = Depends(get_db)):
    """
    Elimina un elemento del catalogo tramite il suo part_number.
    """
    db_catalogo = db.query(Catalogo).filter(Catalogo.part_number == part_number).first()
    
    if db_catalogo is None:
        logger.warning(f"Tentativo di cancellazione di part number inesistente: {part_number}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Catalogo con part number '{part_number}' non trovato"
        )
    
    try:
        db.delete(db_catalogo)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Errore durante l'eliminazione del catalogo {part_number}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Si è verificato un errore durante l'eliminazione del catalogo."
        ) 