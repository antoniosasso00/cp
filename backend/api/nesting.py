"""
API per il sistema di nesting delle parti in autoclave.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
import sys
import os

# Import assoluti
from models.nesting_result import NestingResult
from models.nesting_params import NestingParams
from models.autoclave import Autoclave
from models.odl import ODL
from api.database import get_db
from nesting_optimizer import (
    NestingOptimizer,
    NestingRequest,
    NestingResponse,
    NestingParameters,
    NestingConfirmRequest,
    NestingResultResponse
)

router = APIRouter(prefix="/nesting", tags=["nesting"])
logger = logging.getLogger(__name__)

@router.post("/auto", response_model=NestingResponse)
def run_auto_nesting(
    request: NestingRequest,
    db: Session = Depends(get_db)
):
    """
    Esegue l'algoritmo di nesting automatico e restituisce il layout consigliato.
    Il nesting automatico considera tutti gli ODL in stato "Attesa Cura" e tutte
    le autoclavi disponibili, se non specificato diversamente nella richiesta.
    """
    try:
        optimizer = NestingOptimizer(db)
        response = optimizer.optimize_nesting(request)
        
        # Se il nesting ha avuto successo, salviamo i risultati nel database
        if response.success and response.layouts:
            for layout in response.layouts:
                nesting_id = optimizer.save_nesting_result(layout)
                # Aggiungiamo l'ID del risultato salvato nel layout
                layout.nesting_result_id = nesting_id
        
        return response
    except Exception as e:
        logger.exception("Errore durante l'esecuzione del nesting automatico")
        raise HTTPException(
            status_code=500,
            detail=f"Errore durante l'esecuzione del nesting: {str(e)}"
        )

@router.post("/manual", response_model=NestingResponse)
def run_manual_nesting(
    request: NestingRequest,
    db: Session = Depends(get_db)
):
    """
    Esegue il nesting manuale con gli ODL selezionati dall'utente.
    Richiede una lista di ID degli ODL nella richiesta.
    """
    if not request.odl_ids:
        raise HTTPException(
            status_code=400,
            detail="È necessario specificare almeno un ODL per il nesting manuale"
        )
    
    request.manual = True  # Imposta il flag per il nesting manuale
    
    try:
        optimizer = NestingOptimizer(db)
        response = optimizer.optimize_nesting(request)
        
        # Se il nesting ha avuto successo, salviamo i risultati nel database
        if response.success and response.layouts:
            for layout in response.layouts:
                nesting_id = optimizer.save_nesting_result(layout, manual=True)
                # Aggiungiamo l'ID del risultato salvato nel layout
                layout.nesting_id = nesting_id
        
        return response
    except Exception as e:
        logger.exception("Errore durante l'esecuzione del nesting manuale")
        raise HTTPException(
            status_code=500,
            detail=f"Errore durante l'esecuzione del nesting manuale: {str(e)}"
        )

@router.post("/confirm", status_code=200)
def confirm_nesting(
    request: NestingConfirmRequest,
    db: Session = Depends(get_db)
):
    """
    Conferma un risultato di nesting, aggiornando lo stato degli ODL a "Cura"
    e l'autoclave a "IN_USO".
    """
    try:
        optimizer = NestingOptimizer(db)
        success = optimizer.confirm_nesting(request.nesting_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Risultato di nesting con ID {request.nesting_id} non trovato"
            )
        
        return {"success": True, "message": "Nesting confermato con successo"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Errore durante la conferma del nesting")
        raise HTTPException(
            status_code=500,
            detail=f"Errore durante la conferma del nesting: {str(e)}"
        )

@router.get("/params", response_model=NestingParameters)
def get_nesting_parameters(
    db: Session = Depends(get_db)
):
    """
    Restituisce i parametri di ottimizzazione correnti.
    """
    try:
        optimizer = NestingOptimizer(db)
        return optimizer.get_active_parameters()
    except Exception as e:
        logger.exception("Errore durante il recupero dei parametri di nesting")
        raise HTTPException(
            status_code=500,
            detail=f"Errore durante il recupero dei parametri: {str(e)}"
        )

@router.put("/params", status_code=200)
def update_nesting_parameters(
    params: NestingParameters,
    db: Session = Depends(get_db)
):
    """
    Aggiorna i parametri di ottimizzazione per il nesting.
    """
    try:
        optimizer = NestingOptimizer(db)
        success = optimizer.update_parameters(params)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Impossibile aggiornare i parametri di nesting"
            )
        
        return {"success": True, "message": "Parametri aggiornati con successo"}
    except Exception as e:
        logger.exception("Errore durante l'aggiornamento dei parametri di nesting")
        raise HTTPException(
            status_code=500,
            detail=f"Errore durante l'aggiornamento dei parametri: {str(e)}"
        )

@router.get("/results", response_model=List[NestingResultResponse])
def get_nesting_results(
    limit: int = 10, 
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Restituisce i risultati di nesting salvati.
    """
    try:
        results = db.query(
            NestingResult.id,
            NestingResult.codice,
            Autoclave.nome.label("autoclave_nome"),
            NestingResult.confermato,
            NestingResult.data_conferma,
            NestingResult.efficienza_area,
            NestingResult.valvole_utilizzate,
            NestingResult.valvole_totali,
            NestingResult.generato_manualmente,
            NestingResult.created_at
        ).join(Autoclave).order_by(
            NestingResult.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        return results
    except Exception as e:
        logger.exception("Errore durante il recupero dei risultati di nesting")
        raise HTTPException(
            status_code=500,
            detail=f"Errore durante il recupero dei risultati: {str(e)}"
        )

@router.get("/results/{nesting_id}", response_model=dict)
def get_nesting_result_detail(
    nesting_id: int,
    db: Session = Depends(get_db)
):
    """
    Restituisce i dettagli di un risultato di nesting specifico.
    """
    try:
        result = db.query(NestingResult).filter(NestingResult.id == nesting_id).first()
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Risultato di nesting con ID {nesting_id} non trovato"
            )
        
        # Ottieni i dettagli dell'autoclave
        autoclave = db.query(Autoclave).filter(Autoclave.id == result.autoclave_id).first()
        
        # Ottieni i dettagli degli ODL
        odl_ids = result.odl_ids
        odls = db.query(ODL).filter(ODL.id.in_(odl_ids)).all()
        odl_map = {odl.id: odl for odl in odls}
        
        # Prepara la risposta
        response = {
            "id": result.id,
            "codice": result.codice,
            "autoclave": {
                "id": autoclave.id,
                "nome": autoclave.nome,
                "lunghezza": autoclave.lunghezza,
                "larghezza": autoclave.larghezza_piano,
                "num_linee_vuoto": autoclave.num_linee_vuoto
            },
            "confermato": result.confermato,
            "data_conferma": result.data_conferma,
            "area_totale_mm2": result.area_totale_mm2,
            "area_utilizzata_mm2": result.area_utilizzata_mm2,
            "efficienza_area": result.efficienza_area,
            "valvole_totali": result.valvole_totali,
            "valvole_utilizzate": result.valvole_utilizzate,
            "layout": result.layout,
            "odl_ids": result.odl_ids,
            "odl_stati": {odl_id: odl_map.get(odl_id).status if odl_id in odl_map else None for odl_id in odl_ids},
            "generato_manualmente": result.generato_manualmente,
            "created_at": result.created_at
        }
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Errore durante il recupero dei dettagli del risultato di nesting")
        raise HTTPException(
            status_code=500,
            detail=f"Errore durante il recupero dei dettagli: {str(e)}"
        ) 