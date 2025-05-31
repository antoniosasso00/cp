import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from api.database import get_db
from api.routers.batch_nesting import create_batch_nesting
from schemas.batch_nesting import BatchNestingCreate

# Configurazione logger
logger = logging.getLogger(__name__)

# Creazione router
router = APIRouter(
    prefix="/nesting",
    tags=["Nesting Temporaneo"],
    responses={404: {"description": "Endpoint non trovato"}}
)

class NestingParametri(BaseModel):
    padding_mm: int = 20
    min_distance_mm: int = 15
    priorita_area: bool = True
    accorpamento_odl: bool = False

class NestingRequest(BaseModel):
    odl_ids: List[str]
    autoclave_ids: List[str]
    parametri: NestingParametri

class NestingResponse(BaseModel):
    batch_id: str
    message: str
    odl_count: int
    autoclave_count: int

@router.post("/genera", response_model=NestingResponse,
             summary="Genera un nuovo nesting (endpoint temporaneo)")
def genera_nesting_temporaneo(
    request: NestingRequest, 
    db: Session = Depends(get_db)
):
    """
    Endpoint temporaneo per generare un nesting.
    
    Questo endpoint converte la richiesta di nesting in un BatchNesting
    e lo crea usando l'infrastruttura esistente.
    
    Una volta implementato l'algoritmo di nesting vero, questo endpoint
    verrà sostituito con la logica completa.
    """
    try:
        logger.info(f"Richiesta nesting ricevuta: {len(request.odl_ids)} ODL, {len(request.autoclave_ids)} autoclavi")
        
        # Valida che ci siano ODL e autoclavi
        if not request.odl_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Almeno un ODL deve essere selezionato"
            )
        
        if not request.autoclave_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Almeno un'autoclave deve essere selezionata"
            )
        
        # Per ora usiamo solo la prima autoclave selezionata
        autoclave_id = int(request.autoclave_ids[0])
        odl_ids = [int(odl_id) for odl_id in request.odl_ids]
        
        # Converte i parametri in dict
        parametri_dict = {
            "padding_mm": request.parametri.padding_mm,
            "min_distance_mm": request.parametri.min_distance_mm,
            "priorita_area": request.parametri.priorita_area,
            "accorpamento_odl": request.parametri.accorpamento_odl
        }
        
        # Crea il BatchNesting usando l'endpoint esistente
        batch_create = BatchNestingCreate(
            nome=None,  # Sarà generato automaticamente
            autoclave_id=autoclave_id,
            odl_ids=odl_ids,
            parametri=parametri_dict,
            configurazione_json={
                "version": "1.0",
                "generated_by": "nesting_temp_endpoint",
                "timestamp": None  # Sarà impostato automaticamente
            },
            note=f"Batch generato automaticamente con {len(odl_ids)} ODL per autoclave {autoclave_id}",
            creato_da_utente="system",
            creato_da_ruolo="Curing"
        )
        
        # Crea il batch
        batch = create_batch_nesting(batch_create, db)
        
        logger.info(f"Batch nesting creato con successo: {batch.id}")
        
        return NestingResponse(
            batch_id=batch.id,
            message="Nesting generato con successo",
            odl_count=len(odl_ids),
            autoclave_count=len(request.autoclave_ids)
        )
        
    except HTTPException:
        # Re-raise HTTPException as is
        raise
    except ValueError as e:
        logger.error(f"Errore di validazione dati: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dati non validi: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Errore imprevisto nella generazione nesting: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore interno del server: {str(e)}"
        ) 