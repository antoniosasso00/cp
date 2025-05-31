import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from api.database import get_db
from api.routers.batch_nesting import create_batch_nesting
from schemas.batch_nesting import BatchNestingCreate
from services.nesting_service import NestingService, NestingParameters
from models.nesting_result import NestingResult

# Configurazione logger
logger = logging.getLogger(__name__)

# Creazione router
router = APIRouter(
    prefix="/nesting",
    tags=["Nesting con OR-Tools"],
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
    positioned_tools: List[Dict[str, Any]]
    excluded_odls: List[Dict[str, Any]]
    efficiency: float
    total_weight: float
    algorithm_status: str
    success: bool

@router.post("/genera", response_model=NestingResponse,
             summary="Genera un nuovo nesting utilizzando OR-Tools")
def genera_nesting_ortools(
    request: NestingRequest, 
    db: Session = Depends(get_db)
):
    """
    Genera un nesting ottimizzato utilizzando l'algoritmo OR-Tools CP-SAT.
    
    L'algoritmo considera:
    - Vincoli fisici (dimensioni, peso, non sovrapposizione)
    - Vincoli di processo (compatibilità cicli di cura)
    - Ottimizzazione dell'area utilizzata o massimizzazione ODL
    
    Il risultato viene salvato come BatchNesting con le posizioni 2D dei tool.
    """
    try:
        logger.info(f"🧠 Avvio nesting OR-Tools: {len(request.odl_ids)} ODL, {len(request.autoclave_ids)} autoclavi")
        
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
        
        # Converte i parametri per il servizio
        parameters = NestingParameters(
            padding_mm=request.parametri.padding_mm,
            min_distance_mm=request.parametri.min_distance_mm,
            priorita_area=request.parametri.priorita_area,
            accorpamento_odl=request.parametri.accorpamento_odl
        )
        
        # Esegui l'algoritmo di nesting
        nesting_service = NestingService()
        nesting_result = nesting_service.generate_nesting(
            db=db,
            odl_ids=odl_ids,
            autoclave_id=autoclave_id,
            parameters=parameters
        )
        
        # Recupera le dimensioni reali dell'autoclave per la configurazione
        autoclave_data = nesting_service.get_autoclave_data(db, autoclave_id)
        
        # Converte i risultati per il database
        positioned_tools_json = [
            {
                'odl_id': tool.odl_id,
                'piano': 1,  # Per ora utilizziamo solo il piano 1
                'x': tool.x,
                'y': tool.y,
                'width': tool.width,
                'height': tool.height,
                'peso': tool.peso
            }
            for tool in nesting_result.positioned_tools
        ]
        
        # Parametri completi per il database
        parametri_completi = {
            "algoritmo": "OR-Tools CP-SAT",
            "version": "1.0",
            "padding_mm": request.parametri.padding_mm,
            "min_distance_mm": request.parametri.min_distance_mm,
            "priorita_area": request.parametri.priorita_area,
            "accorpamento_odl": request.parametri.accorpamento_odl,
            "timeout_secondi": 30,
            "algoritmo_status": nesting_result.algorithm_status,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        # Configurazione JSON completa
        configurazione_json = {
            "canvas_width": autoclave_data['larghezza_piano'],
            "canvas_height": autoclave_data['lunghezza'],
            "scale_factor": 1.0,
            "tool_positions": positioned_tools_json,
            "plane_assignments": {str(tool.odl_id): 1 for tool in nesting_result.positioned_tools}
        }
        
        # Crea il BatchNesting
        batch_create = BatchNestingCreate(
            nome=f"Nesting OR-Tools {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            autoclave_id=autoclave_id,
            odl_ids=[tool.odl_id for tool in nesting_result.positioned_tools],  # Solo ODL posizionati
            parametri=parametri_completi,
            configurazione_json=configurazione_json,
            note=f"Batch generato con algoritmo OR-Tools: {len(nesting_result.positioned_tools)} ODL posizionati, {len(nesting_result.excluded_odls)} esclusi. Efficienza: {nesting_result.efficiency:.1f}%",
            creato_da_utente="system_ortools",
            creato_da_ruolo="Curing"
        )
        
        # Crea il batch nel database
        batch = create_batch_nesting(batch_create, db)
        
        # Crea anche un NestingResult nel database se ci sono tool posizionati
        if nesting_result.positioned_tools:
            from models.nesting_result import NestingResult as DBNestingResult
            
            db_nesting_result = DBNestingResult(
                autoclave_id=autoclave_id,
                batch_id=batch.id,
                odl_ids=[tool.odl_id for tool in nesting_result.positioned_tools],
                odl_esclusi_ids=[exc['odl_id'] for exc in nesting_result.excluded_odls if 'odl_id' in exc],
                motivi_esclusione=nesting_result.excluded_odls,
                stato="Generato automaticamente",
                peso_totale_kg=nesting_result.total_weight,
                area_piano_1=nesting_result.used_area,
                area_piano_2=0.0,  # Non utilizzato per ora
                area_totale=nesting_result.total_area,
                area_utilizzata=nesting_result.used_area,
                posizioni_tool=positioned_tools_json,
                note=f"Nesting generato automaticamente con algoritmo OR-Tools. Status: {nesting_result.algorithm_status}"
            )
            
            db.add(db_nesting_result)
            db.commit()
            db.refresh(db_nesting_result)
            
            logger.info(f"✅ NestingResult salvato nel database con ID {db_nesting_result.id}")
        
        logger.info(f"✅ Batch nesting creato con successo: {batch.id}")
        logger.info(f"📊 Risultati: {len(nesting_result.positioned_tools)} posizionati, {len(nesting_result.excluded_odls)} esclusi, efficienza {nesting_result.efficiency:.1f}%")
        
        # Prepara la risposta
        positioned_tools_response = [
            {
                'odl_id': tool.odl_id,
                'x': tool.x,
                'y': tool.y,
                'width': tool.width,
                'height': tool.height,
                'peso': tool.peso
            }
            for tool in nesting_result.positioned_tools
        ]
        
        return NestingResponse(
            batch_id=batch.id,
            message=f"Nesting OR-Tools completato con successo. {len(nesting_result.positioned_tools)} ODL posizionati su {len(odl_ids)}",
            odl_count=len(odl_ids),
            autoclave_count=len(request.autoclave_ids),
            positioned_tools=positioned_tools_response,
            excluded_odls=nesting_result.excluded_odls,
            efficiency=nesting_result.efficiency,
            total_weight=nesting_result.total_weight,
            algorithm_status=nesting_result.algorithm_status,
            success=nesting_result.success
        )
        
    except HTTPException:
        # Re-raise HTTPException as is
        raise
    except ValueError as e:
        logger.error(f"❌ Errore di validazione dati: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dati non validi: {str(e)}"
        )
    except Exception as e:
        logger.error(f"❌ Errore imprevisto nella generazione nesting: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore interno del server: {str(e)}"
        ) 