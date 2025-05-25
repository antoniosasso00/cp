"""
Router per le operazioni di nesting automatico degli ODL nelle autoclavi.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from pydantic import BaseModel
from models.db import get_db
from models.nesting_result import NestingResult
from schemas.nesting import NestingResultSchema, NestingResultRead, NestingPreviewSchema
from services.nesting_service import run_automatic_nesting, get_all_nesting_results, get_nesting_preview, update_nesting_status, save_nesting_draft, load_nesting_draft

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

@router.post(
    "/draft/save",
    summary="Salva una bozza di nesting",
    description="""
    Salva una bozza di nesting senza modificare lo stato degli ODL.
    Utile per salvare configurazioni temporanee durante la manipolazione manuale.
    """
)
async def save_draft(nesting_data: dict, db: Session = Depends(get_db)):
    """
    Endpoint per salvare una bozza di nesting.
    
    Args:
        nesting_data: Dati del nesting da salvare come bozza
        db: Sessione del database
        
    Returns:
        Risultato del salvataggio della bozza
    """
    try:
        result = await save_nesting_draft(db, nesting_data)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante il salvataggio della bozza: {str(e)}"
        )

@router.get(
    "/draft/{draft_id}",
    summary="Carica una bozza di nesting",
    description="""
    Carica una bozza di nesting salvata precedentemente.
    """
)
async def load_draft(draft_id: int, db: Session = Depends(get_db)):
    """
    Endpoint per caricare una bozza di nesting.
    
    Args:
        draft_id: ID della bozza da caricare
        db: Sessione del database
        
    Returns:
        Dati della bozza caricata
    """
    try:
        result = await load_nesting_draft(db, draft_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["message"]
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante il caricamento della bozza: {str(e)}"
        )

@router.get(
    "/drafts",
    summary="Lista delle bozze salvate",
    description="""
    Restituisce la lista di tutte le bozze di nesting salvate.
    """
)
async def list_drafts(db: Session = Depends(get_db)):
    """
    Endpoint per ottenere la lista delle bozze salvate.
    
    Args:
        db: Sessione del database
        
    Returns:
        Lista delle bozze disponibili
    """
    try:
        drafts = db.query(NestingResult).options(
            joinedload(NestingResult.autoclave)
        ).filter(
            NestingResult.stato == "Bozza"
        ).order_by(NestingResult.created_at.desc()).all()
        
        drafts_list = []
        for draft in drafts:
            drafts_list.append({
                "id": draft.id,
                "created_at": draft.created_at.isoformat(),
                "autoclave_nome": draft.autoclave.nome,
                "autoclave_codice": draft.autoclave.codice,
                "num_odl": len(draft.odl_ids) if draft.odl_ids else 0,
                "area_utilizzata": draft.area_utilizzata,
                "area_totale": draft.area_totale,
                "note": draft.note
            })
        
        return {
            "success": True,
            "drafts": drafts_list,
            "count": len(drafts_list)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante il recupero delle bozze: {str(e)}"
        ) 