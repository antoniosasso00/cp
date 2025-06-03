"""
Router nesting per endpoint v1.4.17-DEMO
Re-espone l'endpoint solve del batch_nesting con il path corretto
"""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from api.database import get_db

# Import della funzione solve dal router batch_nesting esistente
from api.routers.batch_nesting import solve_nesting_v1_4_12_demo
from schemas.batch_nesting import NestingSolveRequest, NestingSolveResponse

logger = logging.getLogger(__name__)

# Creazione router
router = APIRouter(
    prefix="/nesting",
    tags=["Nesting v1.4.17"],
    responses={404: {"description": "Risorsa non trovata"}}
)

@router.post("/solve", response_model=NestingSolveResponse,
             summary="🚀 Risolve nesting v1.4.17-DEMO con algoritmi avanzati")
def solve_nesting_v1_4_17_demo(
    request: NestingSolveRequest,
    db: Session = Depends(get_db)
):
    """
    🚀 ENDPOINT NESTING SOLVER v1.4.17-DEMO
    =====================================
    
    Alias per l'endpoint solve del batch_nesting con path aggiornato.
    Mantiene piena compatibilità con il sistema esistente.
    
    **Questo endpoint è identico a `/api/v1/batch_nesting/solve`**
    
    Per la documentazione completa, vedere l'endpoint originale.
    """
    logger.info(f"🔀 Forward richiesta nesting solve v1.4.17 per autoclave {request.autoclave_id}")
    
    # Forward della chiamata all'endpoint originale
    return solve_nesting_v1_4_12_demo(request, db) 