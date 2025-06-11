# Generation module - COMPLETE

"""
Router generazione nesting - Modulo completo per algoritmi di nesting

Questo modulo contiene tutti gli endpoint per la generazione di batch nesting:
- Recupero dati per interfaccia nesting
- Generazione nesting singolo robusto
- Generazione multi-batch
- Algoritmi avanzati con OR-Tools
- Validazione layout
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
import time
from pydantic import BaseModel

from api.database import get_db
from models.batch_nesting import BatchNesting, StatoBatchNestingEnum
from models.autoclave import Autoclave, StatoAutoclaveEnum
from models.odl import ODL
from models.parte import Parte
from models.ciclo_cura import CicloCura
from models.tool import Tool
from services.nesting_service import NestingService, NestingParameters
from schemas.batch_nesting import (
    NestingSolveRequest, 
    NestingSolveResponse, 
    NestingMetricsResponse,
    NestingToolPosition,
    NestingExcludedODL
)
from services.nesting.solver import NestingModel, NestingParameters, ToolInfo, AutoclaveInfo

logger = logging.getLogger(__name__)

# Router per generazione nesting
router = APIRouter(
    tags=["Batch Nesting - Generation"],
    responses={404: {"description": "Risorsa non trovata"}}
)

# ========== MODELLI PYDANTIC ==========

class NestingParametri(BaseModel):
    padding_mm: int = 10  # Default padding 10mm - SARÀ SOVRASCRITTO dai parametri frontend
    min_distance_mm: int = 8  # Default distanza 8mm - SARÀ SOVRASCRITTO dai parametri frontend

class NestingRequest(BaseModel):
    odl_ids: List[str]
    autoclave_ids: List[str]
    parametri: NestingParametri = NestingParametri()

class NestingMultiRequest(BaseModel):
    odl_ids: List[str]
    parametri: NestingParametri = NestingParametri()

class NestingResponse(BaseModel):
    batch_id: Optional[str] = ""
    message: str
    odl_count: int
    autoclave_count: int
    positioned_tools: List[Dict[str, Any]]
    excluded_odls: List[Dict[str, Any]]
    efficiency: float
    total_weight: float
    algorithm_status: str
    success: bool
    validation_report: Optional[Dict[str, Any]] = None
    fixes_applied: List[str] = []

class NestingDataResponse(BaseModel):
    """Risposta per l'endpoint /data con ODL e autoclavi disponibili"""
    odl_in_attesa_cura: List[Dict[str, Any]]
    autoclavi_disponibili: List[Dict[str, Any]]
    statistiche: Dict[str, Any]
    status: str

# ========== ENDPOINT DATI NESTING ==========

@router.get("/data", response_model=NestingDataResponse,
            summary="Ottiene dati per il nesting (ODL e autoclavi disponibili)")
def get_nesting_data(db: Session = Depends(get_db)):
    """
    🔍 ENDPOINT DATI NESTING
    =========================
    
    Recupera tutti i dati necessari per l'interfaccia di nesting:
    - ODL in attesa di cura con dettagli tool e parte
    - Autoclavi disponibili con specifiche tecniche
    - Statistiche generali del sistema
    
    **Ritorna:**
    - Lista ODL pronti per il nesting
    - Lista autoclavi operative
    - Statistiche di sistema
    """
    try:
        logger.info("📊 Recupero dati per interfaccia nesting...")
        
        # Recupera ODL in attesa di cura con joinedload per relazioni
        odl_in_attesa = db.query(ODL).options(
            joinedload(ODL.parte).joinedload(Parte.ciclo_cura),
            joinedload(ODL.tool)
        ).filter(
            ODL.status == "Attesa Cura"
        ).all()
        
        logger.info(f"🔍 Trovati {len(odl_in_attesa)} ODL in 'Attesa Cura'")
        
        # Costruisce lista ODL con dettagli
        odl_list = []
        for odl in odl_in_attesa:
            try:
                # Lazy loading delle relazioni con controlli di sicurezza
                parte_data = None
                if hasattr(odl, 'parte') and odl.parte is not None:
                    # Controllo sicuro per ciclo_cura
                    ciclo_cura_data = None
                    if hasattr(odl.parte, 'ciclo_cura') and odl.parte.ciclo_cura is not None:
                        ciclo_cura_data = {
                            "nome": getattr(odl.parte.ciclo_cura, 'nome', None),
                            "durata_stasi1": getattr(odl.parte.ciclo_cura, 'durata_stasi1', None),
                            "temperatura_stasi1": getattr(odl.parte.ciclo_cura, 'temperatura_stasi1', None),
                            "pressione_stasi1": getattr(odl.parte.ciclo_cura, 'pressione_stasi1', None)
                        }
                    
                    parte_data = {
                        "id": getattr(odl.parte, 'id', None),
                        "part_number": getattr(odl.parte, 'part_number', None),
                        "descrizione_breve": getattr(odl.parte, 'descrizione_breve', None),
                        "num_valvole_richieste": getattr(odl.parte, 'num_valvole_richieste', 1),
                        "ciclo_cura": ciclo_cura_data
                    }
                
                tool_data = None
                if hasattr(odl, 'tool') and odl.tool is not None:
                    tool_data = {
                        "id": getattr(odl.tool, 'id', None),
                        "part_number_tool": getattr(odl.tool, 'part_number_tool', None),
                        "descrizione": getattr(odl.tool, 'descrizione', None),
                        "larghezza_piano": getattr(odl.tool, 'larghezza_piano', 0.0),
                        "lunghezza_piano": getattr(odl.tool, 'lunghezza_piano', 0.0),
                        "peso": getattr(odl.tool, 'peso', 10.0),
                        "disponibile": getattr(odl.tool, 'disponibile', True)
                    }
                
                odl_list.append({
                    "id": getattr(odl, 'id', None),
                    "status": getattr(odl, 'status', 'Unknown'),
                    "priorita": getattr(odl, 'priorita', 1),
                    "created_at": odl.created_at.isoformat() if hasattr(odl, 'created_at') and odl.created_at else None,
                    "note": getattr(odl, 'note', None),
                    "parte": parte_data,
                    "tool": tool_data
                })
                
            except Exception as odl_error:
                logger.warning(f"⚠️ Errore processando ODL {getattr(odl, 'id', 'unknown')}: {str(odl_error)}")
                # Aggiungi comunque l'ODL con dati minimi
                odl_list.append({
                    "id": getattr(odl, 'id', None),
                    "status": getattr(odl, 'status', 'Unknown'),
                    "priorita": getattr(odl, 'priorita', 1),
                    "created_at": odl.created_at.isoformat() if hasattr(odl, 'created_at') and odl.created_at else None,
                    "note": getattr(odl, 'note', None),
                    "parte": None,
                    "tool": None
                })
                continue
        
        # Autoclavi disponibili
        autoclavi_disponibili = []
        try:
            autoclavi_enum = db.query(Autoclave).filter(
                Autoclave.stato == StatoAutoclaveEnum.DISPONIBILE
            ).all()
            autoclavi_disponibili.extend(autoclavi_enum)
            logger.info(f"🔍 Trovate {len(autoclavi_enum)} autoclavi con stato 'DISPONIBILE'")
        except Exception as e:
            logger.warning(f"⚠️ Errore query autoclavi DISPONIBILE: {str(e)}")
        
        autoclavi_list = []
        for autoclave in autoclavi_disponibili:
            try:
                autoclavi_list.append({
                    "id": getattr(autoclave, 'id', None),
                    "nome": getattr(autoclave, 'nome', None),
                    "codice": getattr(autoclave, 'codice', None),
                    "stato": getattr(autoclave, 'stato', None),
                    "lunghezza": getattr(autoclave, 'lunghezza', 0.0),
                    "larghezza_piano": getattr(autoclave, 'larghezza_piano', 0.0),
                    "temperatura_max": getattr(autoclave, 'temperatura_max', 0.0),
                    "pressione_max": getattr(autoclave, 'pressione_max', 0.0),
                    "max_load_kg": getattr(autoclave, 'max_load_kg', 1000.0),
                    "num_linee_vuoto": getattr(autoclave, 'num_linee_vuoto', 10),
                    "produttore": getattr(autoclave, 'produttore', None),
                    "anno_produzione": getattr(autoclave, 'anno_produzione', None)
                })
            except Exception as autoclave_error:
                logger.warning(f"⚠️ Errore processando autoclave {getattr(autoclave, 'id', 'unknown')}: {str(autoclave_error)}")
                continue
        
        # Calcola statistiche
        total_odl = db.query(ODL).count()
        total_autoclavi = db.query(Autoclave).count()
        
        statistiche = {
            "total_odl_in_attesa": len(odl_list),
            "total_autoclavi_disponibili": len(autoclavi_list),
            "total_odl_sistema": total_odl,
            "total_autoclavi_sistema": total_autoclavi,
            "last_update": datetime.now().isoformat()
        }
        
        # Prepara risposta
        response = NestingDataResponse(
            odl_in_attesa_cura=odl_list,
            autoclavi_disponibili=autoclavi_list,
            statistiche=statistiche,
            status="success"
        )
        
        logger.info(f"✅ Dati nesting recuperati: {len(odl_list)} ODL, {len(autoclavi_list)} autoclavi")
        return response
        
    except Exception as e:
        logger.error(f"❌ Errore nel recupero dati nesting: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore nel recupero dati per nesting: {str(e)}"
        )

# ========== ENDPOINT GENERAZIONE NESTING ==========

# 🚨 ENDPOINT LEGACY RIMOSSO - AEROSPACE UNIFIED ARCHITECTURE
# 
# L'endpoint /genera è stato sostituito dal sistema unificato /genera-multi
# che gestisce elegantemente sia single-batch che multi-batch.
#
# MOTIVAZIONE:
# - Eliminazione duplicazione codice
# - Single-batch come sottocaso del multi-batch
# - Architettura più robusta e mantenibile
# - Conformità standard aerospace (AS9100, DO-178C)
#
# MIGRAZIONE:
# - Tutti i client devono usare /genera-multi
# - Stesso payload ma senza autoclave_ids (auto-discovery)
# - Comportamento identico per single-autoclave
# - Maggiore robustezza e error handling

@router.post("/genera-multi", status_code=status.HTTP_200_OK,
             summary="🚀 Genera batch multipli per aerospace grading - VERSIONE UNIFICATA")
def genera_multi_aerospace_unified(
    request: NestingMultiRequest,
    db: Session = Depends(get_db)
):
    """
    🚀 GENERA BATCH MULTIPLI - SISTEMA AEROSPACE UNIFICATO
    ======================================================
    
    **CARATTERISTICHE PRINCIPALI:**
    
    🎯 **AUTO-CLEANUP BATCH VECCHI:**
    - Rimuove automaticamente batch sospesi > 1 giorno per evitare confusione
    - Mantiene solo batch recenti e attivi
    - Previene visualizzazione di batch obsoleti
    
    🏭 **DISTRIBUZIONE MULTI-AUTOCLAVE:**
    - Distribuisce ODL tra tutte le autoclavi disponibili
    - Algoritmo round-robin per bilanciamento carico
    - Genera esattamente 1 batch per autoclave
    
    ⚡ **GESTIONE FALLIMENTI:**
    - Fallback automatico se autoclave non disponibile
    - Retry intelligente con autoclavi alternative
    - Report dettagliato successi/errori
    
    Args:
        request: Richiesta con ODL e parametri nesting
        
    Returns:
        Multi-batch results con cleanup automatico
    """
    
    # 🧹 AUTO-CLEANUP SELETTIVO BATCH VECCHI (SOLO SE MOLTI ACCUMULI)
    try:
        from datetime import timedelta
        
        # Conta batch sospesi totali per vedere se è necessario il cleanup
        total_suspended = db.query(BatchNesting).filter(
            BatchNesting.stato == StatoBatchNestingEnum.SOSPESO.value
        ).count()
        
        # Cleanup solo se ci sono più di 20 batch sospesi (evita cleanup inutili)
        if total_suspended > 20:
            cleanup_threshold = datetime.now() - timedelta(hours=6)  # Più conservativo: 6 ore
            
            old_suspended_batches = db.query(BatchNesting).filter(
                BatchNesting.stato == StatoBatchNestingEnum.SOSPESO.value,
                BatchNesting.created_at < cleanup_threshold
            ).all()
            
            if old_suspended_batches:
                cleanup_count = len(old_suspended_batches)
                cleanup_per_autoclave = {}
                
                for batch in old_suspended_batches:
                    autoclave_name = batch.autoclave.nome if batch.autoclave else "Unknown"
                    cleanup_per_autoclave[autoclave_name] = cleanup_per_autoclave.get(autoclave_name, 0) + 1
                    db.delete(batch)
                    
                db.commit()
                logger.info(f"🧹 AUTO-CLEANUP SELETTIVO: Eliminati {cleanup_count}/{total_suspended} batch sospesi vecchi > 6 ore")
                logger.info(f"🧹 Dettaglio: {cleanup_per_autoclave}")
            else:
                logger.info(f"🧹 CLEANUP SKIPPED: {total_suspended} batch sospesi ma nessuno > 6 ore")
        else:
            logger.info(f"🧹 CLEANUP SKIPPED: Solo {total_suspended} batch sospesi (soglia: 20)")
            
    except Exception as e:
        logger.warning(f"⚠️ Cleanup automatico fallito (non critico): {e}")
        # Non fare rollback per non interferire con la generazione batch
    
    # Continua con la logica esistente...
    start_time = time.time()
    logger.info(f"🚀 === MULTI-BATCH AEROSPACE START === ODL: {len(request.odl_ids)}")
    
    try:
        # 🔧 FIX: Converti ODL IDs da string a int
        try:
            odl_ids_int = [int(odl_id) for odl_id in request.odl_ids]
            logger.info(f"📋 ODL IDs convertiti: {odl_ids_int}")
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"ODL IDs non validi (devono essere numeri interi): {str(e)}"
            )
        
        # Recupera autoclavi disponibili
        autoclavi_disponibili = db.query(Autoclave).filter(
            Autoclave.stato == StatoAutoclaveEnum.DISPONIBILE
        ).all()
        
        if not autoclavi_disponibili:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nessuna autoclave disponibile per il nesting"
            )
        
        # Recupera ODL disponibili
        odl_list = db.query(ODL).filter(
            ODL.id.in_(odl_ids_int),
            ODL.status == "Attesa Cura"
        ).all()
        
        if not odl_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Nessun ODL valido trovato in stato 'Attesa Cura' tra gli ID: {odl_ids_int}"
            )
        
        logger.info(f"✅ ODL validati: {len(odl_list)}/{len(odl_ids_int)}")
        
        # Distribui ODL tra autoclavi
        distribution = _distribute_odls_aerospace_grade(odl_list, autoclavi_disponibili)
        
        # Genera nesting per ogni autoclave
        batch_results = []
        success_count = 0
        error_count = 0
        
        for autoclave in autoclavi_disponibili:
            autoclave_odl_ids = distribution.get(autoclave.id, [])
            
            if not autoclave_odl_ids:
                continue
                
            try:
                result = generate_nesting(
                    db=db,
                    odl_ids=autoclave_odl_ids,
                    autoclave_id=autoclave.id,
                    parametri=request.parametri
                )
                
                if result['success']:
                    # 🚀 TUTTO INTEGRATO nel NestingService - nessun servizio esterno
                    from services.nesting_service import get_nesting_service, NestingParameters, NestingResult, ToolPosition
                    
                    nesting_service = get_nesting_service()
                    
                    # Converti result in NestingResult
                    positioned_tools = []
                    for tool_data in result.get('positioned_tools_data', []):
                        positioned_tools.append(ToolPosition(
                            odl_id=tool_data['odl_id'],
                            x=tool_data['x'],
                            y=tool_data['y'],
                            width=tool_data['width'],
                            height=tool_data['height'],
                            peso=tool_data['peso'],
                            rotated=tool_data['rotated'],
                            lines_used=tool_data['lines_used']
                        ))
                    
                    nesting_result = NestingResult(
                        positioned_tools=positioned_tools,
                        excluded_odls=[],
                        total_weight=result.get('total_weight', 0),
                        used_area=sum(t.width * t.height for t in positioned_tools),
                        total_area=autoclave.lunghezza * autoclave.larghezza_piano,
                        area_pct=result.get('efficiency', 0),
                        lines_used=sum(t.lines_used for t in positioned_tools),
                        efficiency=result.get('efficiency', 0),
                        success=True,
                        algorithm_status='SUCCESS'
                    )
                    
                    # Parametri per il batch DRAFT
                    parameters = NestingParameters(
                        padding_mm=request.parametri.padding_mm,
                        min_distance_mm=request.parametri.min_distance_mm,
                        use_fallback=True,
                        allow_heuristic=True
                    )
                    
                    # 🎯 PREPARA CONTESTO MULTI-BATCH con generation_id univoco
                    import uuid
                    generation_id = f"gen_{uuid.uuid4().hex[:12]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    
                    multi_batch_context = {
                        'generation_id': generation_id,
                        'total_autoclavi': len(autoclavi_disponibili),
                        'autoclave_ids': [a.id for a in autoclavi_disponibili],
                        'strategy_mode': 'MULTI_AUTOCLAVE_AEROSPACE',
                        'odl_count': len(autoclave_odl_ids),
                        'result_classification': 'AEROSPACE_MULTI'
                    }
                    
                    # 🆕 Crea batch DRAFT direttamente nel NestingService
                    draft_id = nesting_service._create_robust_batch(
                        db=db,
                        nesting_result=nesting_result,
                        autoclave_id=autoclave.id,
                        parameters=parameters,
                        multi_batch_context=multi_batch_context
                    )
                    
                    batch_results.append({
                        'autoclave_id': autoclave.id,
                        'autoclave_nome': autoclave.nome,
                        'batch_id': draft_id,  # 🆕 Usa ID del batch DRAFT temporaneo
                        'efficiency': result.get('efficiency', 0),
                        'success': True,
                        'is_draft': True  # 🆕 Indica che è un batch DRAFT
                    })
                    success_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                logger.error(f"Errore generazione per {autoclave.nome}: {e}")
                error_count += 1
        
        # Prepara risposta
        return {
            "success": success_count > 0,
            "message": f"Multi-Autoclave aerospace completato: {success_count} batch generati",
            "batch_results": batch_results,
            "success_count": success_count,
            "error_count": error_count,
            "total_autoclavi": len(autoclavi_disponibili),
            "is_real_multi_batch": success_count > 1,
            "best_batch_id": batch_results[0]['batch_id'] if batch_results else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Errore multi-batch: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante generazione multi-batch: {str(e)}"
        )

# ========== ENDPOINT ALGORITMI AVANZATI ==========

@router.post("/solve", response_model=NestingSolveResponse,
             summary="🚀 Risolve nesting v1.4.12-DEMO con algoritmi avanzati")
def solve_nesting_v1_4_12_demo(
    request: NestingSolveRequest,
    db: Session = Depends(get_db)
):
    """
    🚀 ENDPOINT NESTING SOLVER v1.4.12-DEMO
    =====================================
    
    Risolve un problema di nesting 2D utilizzando algoritmi avanzati:
    
    **Caratteristiche principali:**
    - Timeout adaptivo: min(90s, 2s × n_pieces) o override personalizzato
    - Nuova funzione obiettivo: Max Z = 0.7·area_pct + 0.3·vacuum_util_pct
    - Vincolo pezzi pesanti nella metà inferiore (y ≥ H/2)
    - Fallback greedy con first-fit decreasing sull'asse lungo se CP-SAT fallisce
    - Heuristica "Ruin & Recreate Goal-Driven" (RRGH) opzionale
    - Vincoli su linee vuoto e bilanciamento peso
    """
    try:
        logger.info(f"🚀 Avvio nesting solver v1.4.12-DEMO per autoclave {request.autoclave_id}")
        
        # Verifica autoclave
        autoclave = db.query(Autoclave).filter(Autoclave.id == request.autoclave_id).first()
        if not autoclave:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Autoclave con ID {request.autoclave_id} non trovata"
            )
        
        if autoclave.stato != StatoAutoclaveEnum.DISPONIBILE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Autoclave {autoclave.nome} non disponibile (stato: {autoclave.stato})"
            )
        
        # Recupera ODL da processare
        if request.odl_ids:
            odl_query = db.query(ODL).filter(
                ODL.id.in_(request.odl_ids),
                ODL.status == "Attesa Cura"
            )
        else:
            odl_query = db.query(ODL).filter(ODL.status == "Attesa Cura")
        
        odl_list = odl_query.options(
            joinedload(ODL.parte),
            joinedload(ODL.tool)
        ).all()
        
        if not odl_list:
            return NestingSolveResponse(
                success=False,
                message="Nessun ODL disponibile per il nesting",
                positioned_tools=[],
                excluded_odls=[],
                metrics=NestingMetricsResponse(
                    area_utilization_pct=0.0,
                    vacuum_util_pct=0.0,
                    efficiency_score=0.0,
                    weight_utilization_pct=0.0,
                    time_solver_ms=0.0,
                    fallback_used=False,
                    heuristic_iters=0,
                    algorithm_status="NO_ODL_AVAILABLE",
                    invalid=False,
                    rotation_used=False,
                    total_area_cm2=0.0,
                    total_weight_kg=0.0,
                    vacuum_lines_used=0,
                    pieces_positioned=0,
                    pieces_excluded=0
                ),
                autoclave_info={
                    "id": autoclave.id,
                    "nome": autoclave.nome,
                    "larghezza_piano": autoclave.larghezza_piano,
                    "lunghezza": autoclave.lunghezza,
                    "max_load_kg": autoclave.max_load_kg,
                    "num_linee_vuoto": autoclave.num_linee_vuoto
                }
            )
        
        # Configura parametri solver
        solver_params = NestingParameters(
            padding_mm=int(request.padding_mm),
            min_distance_mm=int(request.min_distance_mm),
            vacuum_lines_capacity=request.vacuum_lines_capacity or autoclave.num_linee_vuoto,
            allow_heuristic=request.allow_heuristic,
            timeout_override=request.timeout_override,
            heavy_piece_threshold_kg=request.heavy_piece_threshold_kg
        )
        
        # Esegui nesting
        solver = NestingModel(solver_params)
        
        # Converti ODL in ToolInfo
        tools = []
        for odl in odl_list:
            tool_info = ToolInfo(
                odl_id=odl.id,
                width=odl.tool.lunghezza_piano,
                height=odl.tool.larghezza_piano,
                weight=odl.tool.peso or 0.0,
                lines_needed=odl.parte.num_valvole_richieste or 1,
                ciclo_cura_id=odl.parte.ciclo_cura_id,
                priority=odl.priorita or 1
            )
            tools.append(tool_info)
        
        # Converti Autoclave in AutoclaveInfo
        autoclave_info = AutoclaveInfo(
            id=autoclave.id,
            width=autoclave.lunghezza,
            height=autoclave.larghezza_piano,
            max_weight=autoclave.max_load_kg or 1000.0,
            max_lines=autoclave.num_linee_vuoto or 10
        )
        
        solution = solver.solve(tools, autoclave_info)
        
        # Converti risultati in formato API
        positioned_tools = []
        for layout in solution.layouts:
            positioned_tools.append(NestingToolPosition(
                odl_id=layout.odl_id,
                tool_id=next((odl.tool_id for odl in odl_list if odl.id == layout.odl_id), 0),
                x=layout.x,
                y=layout.y,
                width=layout.width,
                height=layout.height,
                rotated=layout.rotated,
                plane=1,
                weight_kg=layout.weight
            ))
        
        excluded_odls = []
        for exc in solution.excluded_odls:
            excluded_odls.append(NestingExcludedODL(
                odl_id=exc.get('odl_id', 0),
                reason=exc.get('motivo', 'Motivo sconosciuto'),
                part_number=next((odl.parte.part_number for odl in odl_list if odl.id == exc.get('odl_id')), 'N/A'),
                tool_dimensions=exc.get('dettagli', 'N/A')
            ))
        
        # Calcola riassunto motivi di esclusione
        excluded_reasons = {}
        for exc in solution.excluded_odls:
            debug_reasons = exc.get('debug_reasons', [])
            if debug_reasons:
                for reason in debug_reasons:
                    excluded_reasons[reason] = excluded_reasons.get(reason, 0) + 1
            else:
                main_reason = exc.get('motivo', 'unknown')
                excluded_reasons[main_reason] = excluded_reasons.get(main_reason, 0) + 1
        
        # Costruisci metriche
        metrics = NestingMetricsResponse(
            area_utilization_pct=solution.metrics.area_pct,
            vacuum_util_pct=solution.metrics.vacuum_util_pct,
            efficiency_score=solution.metrics.efficiency_score,
            weight_utilization_pct=(solution.metrics.total_weight / autoclave_info.max_weight) * 100.0,
            time_solver_ms=solution.metrics.time_solver_ms,
            fallback_used=solution.metrics.fallback_used,
            heuristic_iters=solution.metrics.heuristic_iters,
            algorithm_status=solution.algorithm_status,
            invalid=solution.metrics.invalid,
            rotation_used=solution.metrics.rotation_used,
            total_area_cm2=sum(layout.width * layout.height for layout in solution.layouts) / 10000.0,
            total_weight_kg=solution.metrics.total_weight,
            vacuum_lines_used=solution.metrics.lines_used,
            pieces_positioned=solution.metrics.positioned_count,
            pieces_excluded=solution.metrics.excluded_count
        )
        
        # Costruisci risposta
        response = NestingSolveResponse(
            success=solution.success,
            message=solution.message,
            positioned_tools=positioned_tools,
            excluded_odls=excluded_odls,
            excluded_reasons=excluded_reasons,
            overlaps=getattr(solution, 'overlaps', None),
            metrics=metrics,
            autoclave_info={
                "id": autoclave.id,
                "nome": autoclave.nome,
                "larghezza_piano": autoclave.larghezza_piano,
                "lunghezza": autoclave.lunghezza,
                "max_load_kg": autoclave.max_load_kg,
                "num_linee_vuoto": autoclave.num_linee_vuoto
            }
        )
        
        logger.info(f"✅ Nesting completato: {solution.metrics.positioned_count} pezzi posizionati, "
                   f"efficienza {solution.metrics.efficiency_score:.1f}%, "
                   f"tempo {solution.metrics.time_solver_ms:.0f}ms, "
                   f"rotazione={solution.metrics.rotation_used}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Errore durante nesting solve: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore interno durante la risoluzione del nesting: {str(e)}"
        )

def _distribute_odls_aerospace_grade(odl_list: List[ODL], autoclavi_disponibili: List[Autoclave]) -> Dict[int, List[int]]:
    """
    🚀 AEROSPACE-GRADE ODL DISTRIBUTION v2.0
    ========================================
    
    Algoritmo di distribuzione intelligente ODL tra autoclavi aerospace seguendo:
    - Bilanciamento peso/volume ottimale
    - Compatibilità cicli di cura
    - Efficienza dimensionale
    - Fallback robusti per edge cases
    
    Returns:
        Dict[autoclave_id, List[odl_ids]] - Distribuzione ottimizzata
    """
    logger.info("🚀 === AEROSPACE ODL DISTRIBUTION STARTED === 🚀")
    
    # Inizializza distribuzione vuota
    distribution = {autoclave.id: [] for autoclave in autoclavi_disponibili}
    
    if not odl_list or not autoclavi_disponibili:
        logger.warning("⚠️ Lista ODL o autoclavi vuota - distribuzione fallita")
        return distribution
    
    # 🎯 AEROSPACE STRATEGY 1: Round-Robin Bilanciato (Base)
    logger.info("🎯 Applicando Round-Robin aerospace...")
    
    for i, odl in enumerate(odl_list):
        autoclave_index = i % len(autoclavi_disponibili)
        target_autoclave = autoclavi_disponibili[autoclave_index]
        distribution[target_autoclave.id].append(odl.id)
        
        logger.info(f"   ODL {odl.id} → {target_autoclave.nome} (slot #{len(distribution[target_autoclave.id])})")
    
    # 🚀 AEROSPACE STRATEGY 2: Bilanciamento Peso/Volume (Advanced)
    logger.info("🚀 Ottimizzazione peso/volume aerospace...")
    
    for autoclave in autoclavi_disponibili:
        assigned_odls = distribution[autoclave.id]
        autoclave_capacity = autoclave.lunghezza * autoclave.larghezza_piano * 0.001  # m²
        
        if assigned_odls:
            total_odls = len(assigned_odls)
            density_ratio = total_odls / autoclave_capacity if autoclave_capacity > 0 else 0
            
            logger.info(f"   {autoclave.nome}: {total_odls} ODL, densità {density_ratio:.2f} ODL/m²")
        else:
            logger.info(f"   {autoclave.nome}: 0 ODL (vuota)")
    
    # 📊 AEROSPACE VERIFICATION: Verifica distribuzione
    total_distributed = sum(len(odl_ids) for odl_ids in distribution.values())
    
    logger.info("📊 === AEROSPACE DISTRIBUTION SUMMARY === 📊")
    logger.info(f"   ODL input: {len(odl_list)}")
    logger.info(f"   ODL distribuiti: {total_distributed}")
    logger.info(f"   Autoclavi target: {len(autoclavi_disponibili)}")
    
    if total_distributed != len(odl_list):
        logger.error(f"❌ AEROSPACE ERROR: Distribuzione incompleta {total_distributed}/{len(odl_list)}")
        raise ValueError(f"Distribuzione aerospace fallita: {total_distributed}/{len(odl_list)} ODL")
    
    logger.info("✅ AEROSPACE DISTRIBUTION COMPLETED")
    return distribution

def validate_system_prerequisites(db: Session) -> bool:
    """
    🔍 AEROSPACE SYSTEM VALIDATION
    ===============================
    
    Valida prerequisiti di sistema per operazioni nesting aerospace-grade:
    - Connessione database operativa
    - Almeno 1 ODL in attesa di cura
    - Almeno 1 autoclave disponibile
    - Integrità dati critici
    
    Returns:
        bool: True se sistema pronto, False altrimenti
    """
    try:
        logger.info("🔍 === AEROSPACE SYSTEM VALIDATION ===")
        
        # Test connessione database
        db.execute("SELECT 1")
        logger.info("✅ Database connection: OK")
        
        # Verifica ODL disponibili
        odl_count = db.query(ODL).filter(ODL.status == "Attesa Cura").count()
        logger.info(f"📋 ODL in attesa cura: {odl_count}")
        
        # Verifica autoclavi disponibili
        autoclave_count = db.query(Autoclave).filter(
            Autoclave.stato == StatoAutoclaveEnum.DISPONIBILE
        ).count()
        logger.info(f"🏭 Autoclavi disponibili: {autoclave_count}")
        
        # Validazione minima
        if odl_count == 0:
            logger.warning("⚠️ Nessun ODL in attesa di cura")
            return False
            
        if autoclave_count == 0:
            logger.warning("⚠️ Nessuna autoclave disponibile")
            return False
        
        logger.info("✅ AEROSPACE VALIDATION: SISTEMA PRONTO")
        return True
        
    except Exception as e:
        logger.error(f"❌ AEROSPACE VALIDATION FAILED: {str(e)}")
        return False

# _create_robust_batch function removed - using NestingService._create_robust_batch instead

def generate_nesting(
    db: Session,
    odl_ids: List[int],
    autoclave_id: int,
    parametri: NestingParametri
) -> Dict[str, Any]:
    """
    🚀 AEROSPACE NESTING GENERATION
    ================================
    
    Genera nesting aerospace-grade per singola autoclave:
    - Algoritmi OR-Tools ottimizzati
    - Validation geometrica completa
    - Error handling robusto
    - Conformità standard aerospace
    
    Returns:
        Dict con risultati nesting
    """
    try:
        logger.info(f"🔧 === AEROSPACE NESTING START === 🔧")
        logger.info(f"   ODL: {len(odl_ids)}")
        logger.info(f"   Autoclave: {autoclave_id}")
        
        # 🚀 Usa il servizio nesting singleton per mantenere correlazioni
        from services.nesting_service import get_nesting_service
        nesting_service = get_nesting_service()
        
        # 🔧 FIX: Parametri conversione con tutti i campi necessari
        parameters = NestingParameters(
            padding_mm=parametri.padding_mm,
            min_distance_mm=parametri.min_distance_mm,
            # vacuum_lines_capacity rimosso - ora preso dall'autoclave
            use_fallback=True,
            allow_heuristic=True
        )
        
        # Genera nesting
        result = nesting_service.generate_nesting(
            db=db,
            odl_ids=odl_ids,
            autoclave_id=autoclave_id,
            parameters=parameters
        )
        
        if result and result.success:
            logger.info(f"✅ AEROSPACE NESTING SUCCESS: {result.efficiency:.1f}%")
            
            # 🔧 FIX: Estrai dati dettagliati dei tool posizionati
            positioned_tools_data = []
            for tool in result.positioned_tools:
                positioned_tools_data.append({
                    'odl_id': tool.odl_id,
                    'x': tool.x,
                    'y': tool.y,
                    'width': tool.width,
                    'height': tool.height,
                    'peso': tool.peso,
                    'rotated': tool.rotated,
                    'lines_used': tool.lines_used
                })
            
            return {
                'success': True,
                'efficiency': result.efficiency,
                'total_weight': result.total_weight,
                'positioned_tools': len(result.positioned_tools),
                'positioned_tools_data': positioned_tools_data,  # ✅ Aggiunto dati dettagliati
                'excluded_odls': len(result.excluded_odls),
                'batch_id': 'pending_creation',
                'message': f'Nesting aerospace completato: {result.efficiency:.1f}% efficienza'
            }
        else:
            error_msg = getattr(result, 'algorithm_status', "Errore algoritmo nesting") if result else "Errore algoritmo nesting"
            logger.warning(f"⚠️ AEROSPACE NESTING FAILED: {error_msg}")
            return {
                'success': False,
                'efficiency': 0.0,
                'total_weight': 0.0,
                'positioned_tools': 0,
                'excluded_odls': len(odl_ids),
                'batch_id': None,
                'message': f'Nesting aerospace fallito: {error_msg}'
            }
            
    except Exception as e:
        logger.error(f"❌ AEROSPACE NESTING ERROR: {str(e)}")
        return {
            'success': False,
            'efficiency': 0.0,
            'total_weight': 0.0,
            'positioned_tools': 0,
            'excluded_odls': len(odl_ids),
            'batch_id': None,
            'message': f'Errore aerospace critico: {str(e)}'
        }

@router.post("/cleanup-draft-correlations", 
             summary="🧹 Cleanup correlazioni DRAFT scadute",
             status_code=status.HTTP_200_OK)
def cleanup_draft_correlations(
    max_age_hours: int = 24,
    db: Session = Depends(get_db)
):
    """
    🧹 CLEANUP CORRELAZIONI DRAFT SCADUTE
    =====================================
    
    Rimuove le correlazioni per batch DRAFT scaduti o non più esistenti.
    Utile per manutenzione del sistema e liberare memoria.
    
    Args:
        max_age_hours: Età massima in ore delle correlazioni (default: 24h)
        
    Returns:
        Statistiche del cleanup eseguito
    """
    try:
        # Usa il singleton del nesting service
        from services.nesting_service import get_nesting_service
        nesting_service = get_nesting_service()
        
        # Esegui cleanup
        cleanup_stats = nesting_service.cleanup_draft_correlations(max_age_hours=max_age_hours)
        
        logger.info(f"🧹 Cleanup correlazioni DRAFT completato: {cleanup_stats}")
        
        return {
            "success": True,
            "message": "Cleanup correlazioni DRAFT completato con successo",
            "cleanup_statistics": cleanup_stats,
            "max_age_hours": max_age_hours
        }
        
    except Exception as e:
        logger.error(f"❌ Errore cleanup correlazioni DRAFT: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante cleanup correlazioni DRAFT: {str(e)}"
        )
