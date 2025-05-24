"""
Router per le operazioni di nesting automatico degli ODL nelle autoclavi.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from models.db import get_db
from models.nesting_result import NestingResult
from schemas.nesting import NestingResultSchema, NestingResultRead, NestingPreviewSchema
from services.nesting_service import run_automatic_nesting, get_all_nesting_results, get_nesting_preview, update_nesting_status

# Schema per l'aggiornamento dello stato del nesting
class NestingStatusUpdate(BaseModel):
    stato: str
    note: str = None

# Crea un router per la gestione del nesting
router = APIRouter(
    tags=["nesting"],
    responses={404: {"description": "Non trovato"}},
)

@router.post(
    "/auto",
    response_model=NestingResultSchema,
    status_code=status.HTTP_200_OK,
    summary="Esegue il nesting automatico degli ODL nelle autoclavi",
    description="""
    Ottimizza automaticamente il posizionamento degli ODL nelle autoclavi disponibili.
    Considera vincoli di area, numero di valvole e priorità degli ODL.
    Aggiorna lo stato degli ODL nel database in base al risultato.
    """
)
async def auto_nesting(db: Session = Depends(get_db)):
    """
    Endpoint per eseguire il nesting automatico degli ODL nelle autoclavi.
    
    Args:
        db: Sessione del database
        
    Returns:
        Un oggetto NestingResult con i risultati dell'ottimizzazione
    """
    try:
        # Esegui l'algoritmo di nesting
        result = await run_automatic_nesting(db)
        return result
    except Exception as e:
        # In caso di errore, solleva una HTTPException
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante l'esecuzione del nesting automatico: {str(e)}"
        )

@router.get(
    "/preview",
    response_model=NestingPreviewSchema,
    summary="Anteprima del nesting senza salvare",
    description="""
    Mostra un'anteprima del nesting che verrebbe generato senza salvarlo nel database.
    Utile per visualizzare il layout e verificare i risultati prima di confermare.
    """
)
async def preview_nesting(db: Session = Depends(get_db)):
    """
    Endpoint per ottenere un'anteprima del nesting senza salvarlo.
    
    Args:
        db: Sessione del database
        
    Returns:
        Un oggetto NestingPreviewSchema con l'anteprima del nesting
    """
    try:
        # Ottieni l'anteprima del nesting
        result = await get_nesting_preview(db)
        return result
    except Exception as e:
        # In caso di errore, solleva una HTTPException
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante la generazione dell'anteprima del nesting: {str(e)}"
        )

@router.put(
    "/{nesting_id}/status",
    response_model=NestingResultRead,
    summary="Aggiorna lo stato di un nesting",
    description="""
    Aggiorna lo stato di un nesting esistente. Quando viene schedulato,
    tutti gli ODL associati passano automaticamente allo stato "In Autoclave".
    """
)
async def update_nesting_status_endpoint(
    nesting_id: int,
    status_update: NestingStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Endpoint per aggiornare lo stato di un nesting.
    
    Args:
        nesting_id: ID del nesting da aggiornare
        status_update: Nuovo stato e note opzionali
        db: Sessione del database
        
    Returns:
        Il nesting aggiornato
    """
    try:
        # Aggiorna lo stato del nesting
        result = await update_nesting_status(db, nesting_id, status_update.stato, status_update.note)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante l'aggiornamento dello stato del nesting: {str(e)}"
        )

@router.get(
    "/",
    response_model=List[NestingResultRead],
    summary="Restituisce la lista dei nesting generati",
    description="Restituisce la lista dei nesting generati con tutte le informazioni relative agli ODL e all'autoclave",
)
def list_nesting(db: Session = Depends(get_db)):
    """
    Recupera tutti i risultati di nesting dal database con relazioni
    
    Args:
        db: Sessione del database
        
    Returns:
        Lista di oggetti NestingResultRead
    """
    return get_all_nesting_results(db) 