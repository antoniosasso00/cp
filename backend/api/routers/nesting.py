"""
Router per le operazioni di nesting automatico degli ODL nelle autoclavi.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from models.db import get_db
from models.nesting_result import NestingResult
from schemas.nesting import NestingResultSchema, NestingResultRead
from services.nesting_service import run_automatic_nesting, get_all_nesting_results

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