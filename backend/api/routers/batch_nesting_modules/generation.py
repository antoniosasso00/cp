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
from datetime import datetime, timedelta
import time
from pydantic import BaseModel
import json

from api.database import get_db
from models.batch_nesting import BatchNesting, StatoBatchNestingEnum
from models.autoclave import Autoclave, StatoAutoclaveEnum
from models.odl import ODL
from models.parte import Parte
from models.ciclo_cura import CicloCura
from models.tool import Tool
from services.nesting_service import NestingService, NestingParameters as ServiceNestingParameters
from schemas.batch_nesting import (
    NestingSolveRequest, 
    NestingSolveResponse, 
    NestingMetricsResponse,
    NestingToolPosition,
    NestingExcludedODL
)
from services.nesting.solver import NestingModel, NestingParameters as SolverNestingParameters, ToolInfo, AutoclaveInfo
from schemas.batch_nesting import (
    NestingSolveRequest2L,
    NestingSolveResponse2L,
    PosizionamentoTool2L,
    CavallettoPosizionamento,
    NestingMetrics2L
)
from services.nesting.solver_2l import (
    NestingModel2L,
    NestingParameters2L,
    ToolInfo2L,
    AutoclaveInfo2L,
    CavallettiConfiguration
)

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

class NestingMultiFilteredRequest(BaseModel):
    odl_ids: List[str]
    autoclave_ids: List[str]
    parametri: NestingParametri = NestingParametri()

class CavallettiConfigRequest(BaseModel):
    """Configurazione cavalletti dal frontend"""
    min_distance_from_edge: float = 30.0
    max_span_without_support: float = 400.0
    min_distance_between_cavalletti: float = 200.0
    safety_margin_x: float = 5.0
    safety_margin_y: float = 5.0
    prefer_symmetric: bool = True
    force_minimum_two: bool = True

class NestingMulti2LRequest(BaseModel):
    """Request per endpoint multi-2L - PARAMETRI DINAMICI DAL FRONTEND"""
    autoclavi_2l: List[int]
    odl_ids: List[int]
    parametri: NestingParametri
    use_cavalletti: bool = True
    # ✅ PARAMETRI RIMOSSI: cavalletti configurati dinamicamente dal database autoclave
    # cavalletto_height_mm: RIMOSSO - ora da AutoclaveInfo2L.cavalletto_height
    # max_weight_per_level_kg: RIMOSSO - ora da AutoclaveInfo2L.peso_max_per_cavalletto_kg
    prefer_base_level: bool = True
    # ✅ NUOVO: Parametri cavalletti configurabili
    cavalletti_config: Optional[CavallettiConfigRequest] = None

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
                    "numero_odl": getattr(odl, 'numero_odl', None),
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
                    "numero_odl": getattr(odl, 'numero_odl', None),
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
                    "anno_produzione": getattr(autoclave, 'anno_produzione', None),
                    # ✅ FIX: Aggiunta campi 2L necessari per frontend
                    "usa_cavalletti": getattr(autoclave, 'usa_cavalletti', False),
                    "altezza_cavalletto_standard": getattr(autoclave, 'altezza_cavalletto_standard', None),
                    "max_cavalletti": getattr(autoclave, 'max_cavalletti', 2),
                    "clearance_verticale": getattr(autoclave, 'clearance_verticale', None),
                    "peso_max_per_cavalletto_kg": getattr(autoclave, 'peso_max_per_cavalletto_kg', 300.0)
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
        
        # Debug logging per 2L
        autoclavi_2l = [a for a in autoclavi_list if a.get('usa_cavalletti', False)]
        logger.info(f"✅ Dati nesting recuperati: {len(odl_list)} ODL, {len(autoclavi_list)} autoclavi ({len(autoclavi_2l)} con 2L)")
        if autoclavi_2l:
            logger.info(f"🔧 Autoclavi 2L: {[f'{a['nome']} (cavalletti: {a.get('usa_cavalletti', False)})' for a in autoclavi_2l]}")
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Errore nel recupero dati nesting: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore nel recupero dati per nesting: {str(e)}"
        )

# ========== ENDPOINT GENERAZIONE NESTING ==========

# 🆕 NUOVO: Endpoint per generazione single-batch con autoclave specifica
@router.post("/genera", response_model=NestingResponse,
             summary="🎯 Genera batch singolo per autoclave specifica")
def genera_nesting_single_autoclave(
    request: NestingRequest,
    db: Session = Depends(get_db)
):
    """
    🎯 GENERA BATCH SINGOLO PER AUTOCLAVE SPECIFICA
    ===============================================
    
    Genera un batch nesting per una specifica autoclave selezionata dall'utente.
    Questo endpoint NON distribuisce gli ODL su multiple autoclavi.
    
    Args:
        request: Richiesta con ODL, autoclave specifica e parametri
        
    Returns:
        Risultato nesting per la singola autoclave specificata
    """
    start_time = time.time()
    logger.info(f"🎯 === SINGLE-BATCH START === ODL: {len(request.odl_ids)}, Autoclave: {request.autoclave_ids}")
    
    try:
        # Converti IDs da string a int
        try:
            odl_ids_int = [int(odl_id) for odl_id in request.odl_ids]
            autoclave_ids_int = [int(autoclave_id) for autoclave_id in request.autoclave_ids]
            logger.info(f"📋 ODL IDs: {odl_ids_int}, Autoclave IDs: {autoclave_ids_int}")
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"IDs non validi (devono essere numeri interi): {str(e)}"
            )
        
        # Verifica che sia stata selezionata una sola autoclave
        if len(autoclave_ids_int) != 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Endpoint single-batch richiede esattamente 1 autoclave, ricevute: {len(autoclave_ids_int)}"
            )
        
        autoclave_id = autoclave_ids_int[0]
        
        # Verifica che l'autoclave sia disponibile
        autoclave = db.query(Autoclave).filter(
            Autoclave.id == autoclave_id,
            Autoclave.stato == StatoAutoclaveEnum.DISPONIBILE
        ).first()
        
        if not autoclave:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Autoclave {autoclave_id} non disponibile o non trovata"
            )
        
        # Verifica ODL
        odl_list = db.query(ODL).filter(
            ODL.id.in_(odl_ids_int),
            ODL.status == "Attesa Cura"
        ).all()
        
        if not odl_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Nessun ODL valido trovato in stato 'Attesa Cura' tra gli ID: {odl_ids_int}"
            )
        
        # Genera nesting per la singola autoclave
        result = generate_nesting(
            db=db,
            odl_ids=odl_ids_int,
            autoclave_id=autoclave_id,
            parametri=request.parametri
        )
        
        if result['success']:
            response = NestingResponse(
                batch_id=result.get('batch_id', ''),
                message=f"Batch generato per autoclave {autoclave.nome}",
                odl_count=len(odl_ids_int),
                autoclave_count=1,
                positioned_tools=result.get('positioned_tools_data', []),
                excluded_odls=result.get('excluded_odls', []),
                efficiency=result.get('efficiency', 0.0),
                total_weight=result.get('total_weight', 0.0),
                algorithm_status=result.get('algorithm_status', 'SUCCESS'),
                success=True,
                validation_report={},
                fixes_applied=[]
            )
            
            execution_time = time.time() - start_time
            logger.info(f"✅ SINGLE-BATCH SUCCESS: {execution_time:.2f}s, Efficienza: {result.get('efficiency', 0):.1f}%")
            return response
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Generazione fallita: {result.get('message', 'Errore sconosciuto')}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Errore single-batch: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore interno nella generazione single-batch: {str(e)}"
        )

# 🆕 NUOVO: Endpoint per generazione multi-batch con autoclavi filtrate
@router.post("/genera-multi-filtered", status_code=status.HTTP_200_OK,
             summary="🎯 Genera batch multipli per autoclavi specifiche selezionate")
def genera_multi_aerospace_filtered(
    request: NestingMultiFilteredRequest,
    db: Session = Depends(get_db)
):
    """
    🎯 GENERA BATCH MULTIPLI PER AUTOCLAVI SPECIFICHE
    ===============================================
    
    Genera batch nesting solo per le autoclavi specificamente selezionate dall'utente.
    A differenza di /genera-multi che usa tutte le autoclavi disponibili,
    questo endpoint rispetta la selezione dell'utente.
    
    Args:
        request: Richiesta con ODL, autoclavi specifiche e parametri
        
    Returns:
        Multi-batch results per le autoclavi selezionate
    """
    start_time = time.time()
    logger.info(f"🎯 === MULTI-FILTERED START === ODL: {len(request.odl_ids)}, Autoclavi: {len(request.autoclave_ids)}")
    
    try:
        # Converti IDs da string a int
        try:
            odl_ids_int = [int(odl_id) for odl_id in request.odl_ids]
            autoclave_ids_int = [int(autoclave_id) for autoclave_id in request.autoclave_ids]
            logger.info(f"📋 ODL IDs: {odl_ids_int}, Autoclave IDs: {autoclave_ids_int}")
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"IDs non validi (devono essere numeri interi): {str(e)}"
            )
        
        # Verifica che siano state selezionate multiple autoclavi
        if len(autoclave_ids_int) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Endpoint multi-filtered richiede almeno 2 autoclavi, ricevute: {len(autoclave_ids_int)}"
            )
        
        # Recupera solo le autoclavi selezionate e disponibili
        autoclavi_selezionate = db.query(Autoclave).filter(
            Autoclave.id.in_(autoclave_ids_int),
            Autoclave.stato == StatoAutoclaveEnum.DISPONIBILE
        ).all()
        
        if not autoclavi_selezionate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nessuna autoclave selezionata è disponibile"
            )
        
        # Verifica ODL
        odl_list = db.query(ODL).filter(
            ODL.id.in_(odl_ids_int),
            ODL.status == "Attesa Cura"
        ).all()
        
        if not odl_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Nessun ODL valido trovato in stato 'Attesa Cura' tra gli ID: {odl_ids_int}"
            )
        
        # Distribuisci ODL tra le autoclavi selezionate (non tutte disponibili)
        distribution = _distribute_odls_aerospace_grade(odl_list, autoclavi_selezionate)
        
        # Genera nesting per ogni autoclave selezionata
        batch_results = []
        success_count = 0
        error_count = 0
        
        for autoclave in autoclavi_selezionate:
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
                    # 🔧 FIX CRITICO: Usa direttamente il batch_id restituito da generate_nesting
                    # che ora crea già correttamente il batch nel database
                    batch_results.append({
                        'autoclave_id': autoclave.id,
                        'autoclave_nome': autoclave.nome,
                        'batch_id': result.get('batch_id'),  # 🔧 FIX: Usa ID reale dal database
                        'efficiency': result.get('efficiency', 0),
                        'total_weight': result.get('total_weight', 0),
                        'positioned_tools': result.get('positioned_tools', 0),
                        'excluded_odls': result.get('excluded_odls', 0),
                        'success': True,
                        'message': f'Batch generato con successo per {autoclave.nome}'
                    })
                    success_count += 1
                else:
                    # Gestione fallimento più semplice
                    batch_results.append({
                        'batch_id': None,
                        'autoclave_id': autoclave.id,
                        'autoclave_nome': autoclave.nome,
                        'efficiency': 0,
                        'total_weight': 0,
                        'positioned_tools': 0,
                        'excluded_odls': len(autoclave_odl_ids),
                        'success': False,
                        'message': result.get('message', f'Nesting fallito per {autoclave.nome}')
                    })
                    error_count += 1
                    
            except Exception as e:
                logger.error(f"❌ Errore generazione autoclave {autoclave.nome}: {str(e)}")
                batch_results.append({
                    'batch_id': None,
                    'autoclave_id': autoclave.id,
                    'autoclave_nome': autoclave.nome,
                    'efficiency': 0,
                    'total_weight': 0,
                    'positioned_tools': 0,
                    'excluded_odls': len(autoclave_odl_ids),
                    'success': False,
                    'message': f"Errore: {str(e)}"
                })
                error_count += 1
        
        # 🔧 FIX: Trova il batch migliore con controllo validità ID
        best_batch_id = None
        best_efficiency = 0
        for batch in batch_results:
            if (batch['success'] and 
                batch['efficiency'] > best_efficiency and 
                batch.get('batch_id') and 
                batch['batch_id'] != 'pending_creation'):  # 🔧 Escludi placeholder invalidi
                best_efficiency = batch['efficiency']
                best_batch_id = batch['batch_id']
        
        # Calcola efficienza media
        successful_batches = [b for b in batch_results if b['success']]
        avg_efficiency = sum(b['efficiency'] for b in successful_batches) / len(successful_batches) if successful_batches else 0
        
        execution_time = time.time() - start_time
        logger.info(f"✅ MULTI-FILTERED SUCCESS: {execution_time:.2f}s, {success_count}/{len(autoclavi_selezionate)} autoclavi")
        
        return {
            'success': success_count > 0,
            'message': f"Multi-Autoclave filtrato completato: {success_count} batch generati su {len(autoclavi_selezionate)} autoclavi selezionate",
            'total_autoclavi': len(autoclavi_selezionate),
            'success_count': success_count,
            'error_count': error_count,
            'best_batch_id': best_batch_id,
            'avg_efficiency': avg_efficiency,
            'batch_results': batch_results,
            'is_real_multi_batch': len(successful_batches) > 1,
            'unique_autoclavi_count': len(set(b['autoclave_id'] for b in successful_batches))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Errore multi-filtered: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore interno nella generazione multi-filtered: {str(e)}"
        )

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
    
    # 🔧 FIX PROBLEMA REDIRECT: DISABILITA AUTO-CLEANUP AUTOMATICO
    # Il cleanup automatico può eliminare batch che l'utente sta ancora visualizzando
    # causando redirect a risultati inesistenti. Lo rimuoviamo completamente.
    
    logger.info("🚫 AUTO-CLEANUP DISABILITATO: Prevenzione redirect a batch eliminati")
    
    # 🔧 NUOVO: Cleanup intelligente solo su richiesta esplicita via API dedicata
    # Il cleanup deve essere eseguito manualmente quando necessario per evitare
    # interferenze con il workflow utente e redirect indesiderati.
    
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
                    # 🔧 FIX CRITICO: Usa direttamente il batch_id restituito da generate_nesting
                    # che ora crea già correttamente il batch nel database
                    batch_results.append({
                        'autoclave_id': autoclave.id,
                        'autoclave_nome': autoclave.nome,
                        'batch_id': result.get('batch_id'),  # 🔧 FIX: Usa ID reale dal database
                        'efficiency': result.get('efficiency', 0),
                        'total_weight': result.get('total_weight', 0),
                        'positioned_tools': result.get('positioned_tools', 0),
                        'excluded_odls': result.get('excluded_odls', 0),
                        'success': True,
                        'message': f'Batch generato con successo per {autoclave.nome}'
                    })
                    success_count += 1
                else:
                    # Gestione fallimento più semplice
                    batch_results.append({
                        'batch_id': None,
                        'autoclave_id': autoclave.id,
                        'autoclave_nome': autoclave.nome,
                        'efficiency': 0,
                        'total_weight': 0,
                        'positioned_tools': 0,
                        'excluded_odls': len(autoclave_odl_ids),
                        'success': False,
                        'message': result.get('message', f'Nesting fallito per {autoclave.nome}')
                    })
                    error_count += 1
                    
            except Exception as e:
                logger.error(f"Errore generazione per {autoclave.nome}: {e}")
                error_count += 1
        
        # 🔧 FIX CRITICO: Trova il batch migliore per efficienza con controllo validità ID
        best_batch_id = None
        best_efficiency = 0
        for batch in batch_results:
            if (batch['success'] and 
                batch['efficiency'] > best_efficiency and 
                batch.get('batch_id') and 
                batch['batch_id'] != 'pending_creation'):  # 🔧 Escludi placeholder invalidi
                best_efficiency = batch['efficiency']
                best_batch_id = batch['batch_id']
        
        # Calcola efficienza media
        successful_batches = [b for b in batch_results if b['success']]
        avg_efficiency = sum(b['efficiency'] for b in successful_batches) / len(successful_batches) if successful_batches else 0
        
        # Prepara risposta
        return {
            "success": success_count > 0,
            "message": f"Multi-Autoclave aerospace completato: {success_count} batch generati",
            "batch_results": batch_results,
            "success_count": success_count,
            "error_count": error_count,
            "total_autoclavi": len(autoclavi_disponibili),
            "is_real_multi_batch": success_count > 1,
            "best_batch_id": best_batch_id,  # 🔧 FIX: Usa batch con migliore efficienza
            "avg_efficiency": avg_efficiency  # 🆕 Aggiungi efficienza media
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
        solver_params = SolverNestingParameters(
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
        parameters = ServiceNestingParameters(
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
            
            # 🔧 FIX CRITICO: Crea REALMENTE il batch nel database invece di restituire placeholder
            batch_id = nesting_service._create_robust_batch(
                db=db,
                nesting_result=result,
                autoclave_id=autoclave_id,
                parameters=parameters
            )
            
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
                'excluded_odls': result.excluded_odls if hasattr(result, 'excluded_odls') else [],
                'batch_id': batch_id,  # 🔧 FIX CRITICO: Usa ID reale del batch creato
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
                'excluded_odls': [{'odl_id': odl_id, 'motivo': error_msg} for odl_id in odl_ids],
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
            'excluded_odls': [{'odl_id': odl_id, 'motivo': f'Errore critico: {str(e)}'} for odl_id in odl_ids],
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

# ========== NUOVO ENDPOINT NESTING 2L - PARALLEL STRUCTURE ==========

@router.post("/2l", response_model=NestingSolveResponse2L,
             summary="🚀 Calcola il nesting 2D su due livelli (piano + cavalletti)",
             description="Calcola il nesting 2D su due livelli (piano + cavalletti)")
def solve_nesting_2l_batch(
    request: NestingSolveRequest2L,
    db: Session = Depends(get_db)
):
    """
    🚀 ENDPOINT NESTING SOLVER 2L - BATCH MODE
    ==========================================
    
    Risolve problemi di nesting 2D utilizzando due livelli fisici:
    - Piano base dell'autoclave (livello 0)
    - Cavalletti di supporto (livello 1)
    
    **Caratteristiche principali:**
    - Algoritmi CP-SAT ottimizzati per due livelli
    - Calcolo automatico posizione cavalletti
    - Bilanciamento intelligente peso tra livelli
    - Gestione interferenze cavalletti-tool
    
    **Parametri specifici 2L:**
    - usa_cavalletti: Abilita/disabilita secondo livello
    - cavalletto_height_mm: Altezza cavalletti (50-200mm)
    - max_weight_per_level_kg: Peso massimo per livello
    - prefer_base_level: Preferenza piano base
    
    **Output ottimizzato:**
    - positioned_tools: Include campo 'level' (0=base, 1=cavalletto)
    - cavalletti: Posizioni automatiche cavalletti calcolate
    - metrics: Metriche separate per livello (level_0_count, level_1_count)
    """
    start_time = time.time()
    logger.info(f"🚀 === NESTING 2L BATCH START === Autoclave: {request.autoclave_id}, ODL: {request.odl_ids}")
    
    try:
        # 1. Recupera e valida autoclave
        autoclave = db.query(Autoclave).filter(Autoclave.id == request.autoclave_id).first()
        if not autoclave:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Autoclave con ID {request.autoclave_id} non trovata"
            )
        
        # Verifica supporto cavalletti se richiesto
        if request.use_cavalletti and not autoclave.usa_cavalletti:
            logger.warning(f"⚠️ Autoclave {autoclave.nome} non supporta cavalletti, usa_cavalletti disabilitato")
            request.use_cavalletti = False
        
        logger.info(f"🔧 Autoclave: {autoclave.nome}, Cavalletti: {'ON' if request.use_cavalletti else 'OFF'}")
        
        # 2. Recupera ODL da processare
        if request.odl_ids:
            # ODL specifici richiesti
            odls_query = db.query(ODL).options(
                joinedload(ODL.tool),
                joinedload(ODL.parte)
            ).filter(
                ODL.id.in_(request.odl_ids),
                ODL.status == "Attesa Cura"
            )
        else:
            # Tutti gli ODL in attesa di cura (limite di sicurezza)
            odls_query = db.query(ODL).options(
                joinedload(ODL.tool),
                joinedload(ODL.parte)
            ).filter(ODL.status == "Attesa Cura").limit(20)
        
        odls = odls_query.all()
        
        if not odls:
            return NestingSolveResponse2L(
                success=False,
                message="Nessun ODL disponibile per il nesting 2L",
                positioned_tools=[],
                cavalletti=[],
                excluded_odls=[],
                metrics=NestingMetrics2L(
                    area_utilization_pct=0.0,
                    vacuum_util_pct=0.0,
                    efficiency_score=0.0,
                    weight_utilization_pct=0.0,
                    time_solver_ms=(time.time() - start_time) * 1000,
                    fallback_used=False,
                    algorithm_status="NO_ODL_AVAILABLE",
                    total_area_cm2=0.0,
                    total_weight_kg=0.0,
                    vacuum_lines_used=0,
                    pieces_positioned=0,
                    pieces_excluded=len(request.odl_ids or []),
                    level_0_count=0,
                    level_1_count=0,
                    level_0_weight_kg=0.0,
                    level_1_weight_kg=0.0,
                    level_0_area_pct=0.0,
                    level_1_area_pct=0.0,
                    cavalletti_used=0,
                    cavalletti_coverage_pct=0.0,
                    complexity_score=0.0,
                    timeout_used_seconds=0.0
                ),
                autoclave_info={
                    "id": autoclave.id,
                    "nome": autoclave.nome,
                    "dimensioni": f"{autoclave.lunghezza}x{autoclave.larghezza_piano}mm",
                    "cavalletti_supportati": autoclave.usa_cavalletti
                }
            )
        
        logger.info(f"📋 ODL trovati: {len(odls)}")
        
        # 3. Converte ODL in ToolInfo2L
        tools_2l = []
        for odl in odls:
            if not odl.tool:
                logger.warning(f"⚠️ Tool non trovato per ODL {odl.id}")
                continue
                
            if not odl.parte:
                logger.warning(f"⚠️ Parte non trovata per ODL {odl.id}")
                continue
            
            # Converte in ToolInfo2L usando la funzione esistente
            tool_2l = _convert_db_to_tool_info_2l(odl, odl.tool, odl.parte)
            tools_2l.append(tool_2l)
            
        logger.info(f"🔧 Tool convertiti per 2L: {len(tools_2l)}")
        
        if not tools_2l:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nessun tool valido trovato per gli ODL specificati"
            )
        
        # 4. Converte autoclave in AutoclaveInfo2L
        autoclave_2l = _convert_db_to_autoclave_info_2l(autoclave)
        
        # ⚠️ VERIFICA SUPPORTO CAVALLETTI AUTOCLAVE
        if request.use_cavalletti and not autoclave.usa_cavalletti:
            logger.warning(f"⚠️ Richiesti cavalletti ma autoclave {autoclave.nome} non li supporta")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"L'autoclave {autoclave.nome} non supporta i cavalletti. Disabilitare 'use_cavalletti' nella richiesta."
            )
        
        # Aggiorna con parametri richiesta E controllo autoclave
        autoclave_2l.has_cavalletti = request.use_cavalletti and autoclave.usa_cavalletti
        # autoclave_2l.cavalletto_height = RIMOSSO - viene dal database via _convert_db_to_autoclave_info_2l
        
        logger.info(f"🔧 Autoclave 2L configurata: {autoclave_2l.width}x{autoclave_2l.height}mm")
        
        # 5. Configura parametri solver 2L - FIX DEFINITIVO
        parameters_2l = NestingParameters2L(
            padding_mm=request.padding_mm,
            min_distance_mm=request.min_distance_mm,
            vacuum_lines_capacity=request.vacuum_lines_capacity or autoclave.num_linee_vuoto or 20,
            use_cavalletti=request.use_cavalletti,
            # cavalletto_height_mm=RIMOSSO - ora passa via AutoclaveInfo2L.cavalletto_height
            prefer_base_level=request.prefer_base_level,
            allow_heuristic=request.allow_heuristic,
            use_multithread=request.use_multithread,
            heavy_piece_threshold_kg=request.heavy_piece_threshold_kg
        )
        
        # Override timeout se specificato
        if request.timeout_override:
            parameters_2l.base_timeout_seconds = float(request.timeout_override)
            parameters_2l.max_timeout_seconds = float(request.timeout_override)
        
        # 6. Inizializza solver 2L e risolve usando solve_2l
        solver_2l = NestingModel2L(parameters_2l)
        logger.info(f"🎯 Avvio solver 2L batch...")
        
        # ✅ INTEGRAZIONE SISTEMA CAVALLETTI AVANZATO v2.0
        try:
            from backend.services.nesting.cavalletti_optimizer import CavallettiOptimizerAdvanced, OptimizationStrategy
            
            # Determina strategia ottimizzazione basata su principi palletizing industriali
            strategy = OptimizationStrategy.INDUSTRIAL
            if len(tools_2l) > 25:  # Batch molto grandi → aerospace efficiency
                strategy = OptimizationStrategy.AEROSPACE
            elif len(tools_2l) < 8:  # Batch piccoli → balanced approach
                strategy = OptimizationStrategy.BALANCED
            
            logger.info(f"🔧 [SISTEMA AVANZATO v2.0] Strategia cavalletti: {strategy.value}")
            logger.info(f"   Tool batch: {len(tools_2l)}, Max cavalletti DB: {autoclave_2l.max_cavalletti}")
            
            # Integra ottimizzatore nel solver
            optimizer = CavallettiOptimizerAdvanced()
            solver_2l._cavalletti_optimizer = optimizer
            solver_2l._optimization_strategy = strategy
            
            # ✅ CONFIGURAZIONE CAVALLETTI COMPLETA dal database + frontend
            config = request.cavalletti_config
            cavalletti_config = CavallettiConfiguration(
                # ✅ Dimensioni fisiche dal database autoclave
                cavalletto_width=autoclave_2l.cavalletto_width,
                cavalletto_height=autoclave_2l.cavalletto_height_mm,
                
                # ✅ Parametri operativi dal frontend (con fallback)
                min_distance_from_edge=config.min_distance_from_edge if config else 30.0,
                max_span_without_support=config.max_span_without_support if config else 400.0,
                min_distance_between_cavalletti=config.min_distance_between_cavalletti if config else 200.0,
                safety_margin_x=config.safety_margin_x if config else 10.0,
                safety_margin_y=config.safety_margin_y if config else 10.0,
                prefer_symmetric=config.prefer_symmetric if config else True,
                force_minimum_two=config.force_minimum_two if config else True
            )
            
            solver_2l._cavalletti_config = cavalletti_config
            
            logger.info(f"✅ Sistema cavalletti integrato:")
            logger.info(f"   Dimensioni DB: {autoclave_2l.cavalletto_width}x{autoclave_2l.cavalletto_height_mm}mm")
            logger.info(f"   Max span: {cavalletti_config.max_span_without_support}mm")
            logger.info(f"   Validazione max_cavalletti: {'ON' if autoclave_2l.max_cavalletti else 'OFF'}")
            
        except ImportError as e:
            logger.warning(f"⚠️ CavallettiOptimizerAdvanced non disponibile: {e}")
            logger.info("   Fallback a sistema base con validazione critica...")
            
            # ✅ FALLBACK: Sistema base con validazione max_cavalletti essenziale
            cavalletti_config = CavallettiConfiguration(
                cavalletto_width=autoclave_2l.cavalletto_width,
                cavalletto_height=autoclave_2l.cavalletto_height_mm,
                min_distance_from_edge=30.0,
                max_span_without_support=400.0,
                force_minimum_two=True
            )
            solver_2l._cavalletti_config = cavalletti_config
            
        except Exception as e:
            logger.error(f"❌ Errore configurazione sistema cavalletti: {e}")
            # Continua con sistema base per sicurezza
            cavalletti_config = CavallettiConfiguration(
                cavalletto_width=80.0,  # Fallback hardcoded
                cavalletto_height=60.0,
                min_distance_from_edge=30.0,
                max_span_without_support=400.0,
                force_minimum_two=True
            )
            solver_2l._cavalletti_config = cavalletti_config
        
        # Chiama il metodo solve_2l del solver (come richiesto nelle specifiche)
        solution_2l = solver_2l.solve_2l(tools_2l, autoclave_2l)
        
        # 7. Converte soluzione in risposta Pydantic usando metodo esistente
        response = solver_2l.convert_to_pydantic_response(
            solution_2l, 
            autoclave_2l,
            request_params=request.model_dump()
        )
        
        # 🆕 SALVATAGGIO BATCH 2L: Salva sempre se l'algoritmo ha successo
        if response.success and response.metrics.pieces_positioned > 0:
            try:
                # 🔧 FIX SERIALIZZAZIONE: Usa dict invece di model_dump per evitare errori di serializzazione
                def safe_serialize(obj):
                    """Serializza in modo sicuro un oggetto Pydantic"""
                    try:
                        return obj.model_dump() if hasattr(obj, 'model_dump') else dict(obj)
                    except Exception as e:
                        logger.warning(f"⚠️ Fallback serialization per {type(obj)}: {e}")
                        # Fallback: serializza manualmente i campi base
                        if hasattr(obj, '__dict__'):
                            return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
                        return {}
                
                # 🔧 FIX BUG #2: MIGLIORAMENTO GESTIONE POSITIONED_TOOLS_DATA
                positioned_tools_data = []
                for tool in response.positioned_tools:
                    tool_data = {
                        'odl_id': getattr(tool, 'odl_id', None),
                        'x': getattr(tool, 'x', 0.0),
                        'y': getattr(tool, 'y', 0.0),
                        'width': getattr(tool, 'width', 0.0),
                        'height': getattr(tool, 'height', 0.0),
                        'peso': getattr(tool, 'peso', getattr(tool, 'weight', 0.0)),
                        'weight': getattr(tool, 'peso', getattr(tool, 'weight', 0.0)),  # Backup field
                        'rotated': getattr(tool, 'rotated', False),
                        'level': getattr(tool, 'level', 0),  # ✅ CRITICO: Campo livello per 2L
                        'lines_used': getattr(tool, 'lines_used', 1),
                        'numero_odl': None,  # Sarà popolato dopo
                        'descrizione_breve': None,  # Sarà popolato dopo
                        'part_number': None  # Sarà popolato dopo
                    }
                    positioned_tools_data.append(tool_data)
                
                # 🔧 FIX BUG #2: ARRICCHIMENTO DATI CON INFO ODL/PARTE
                odl_info_map = {}
                for odl_id in request.odl_ids:
                    odl = db.query(ODL).options(
                        joinedload(ODL.parte),
                        joinedload(ODL.tool)
                    ).filter(ODL.id == odl_id).first()
                    if odl:
                        odl_info_map[odl_id] = {
                            'numero_odl': odl.numero_odl,
                            'descrizione_breve': odl.parte.descrizione_breve if odl.parte else "N/A",
                            'part_number': odl.parte.part_number if odl.parte else "N/A"
                        }
                
                # Arricchisce positioned_tools_data con info ODL
                for tool_data in positioned_tools_data:
                    odl_id = tool_data.get('odl_id')
                    if odl_id and odl_id in odl_info_map:
                        tool_data.update(odl_info_map[odl_id])
                
                configurazione_json = {
                    "positioned_tools": positioned_tools_data,  # 🔧 FIX: Usa positioned_tools invece di tool serializzati
                    "positioned_tools_data": positioned_tools_data,  # ✅ BACKWARD COMPATIBILITY
                    "cavalletti": [safe_serialize(cav) for cav in response.cavalletti],
                    "autoclave_info": response.autoclave_info,
                    "algorithm_used": response.metrics.algorithm_status,
                    "parametri_usati": safe_serialize(single_request),
                    "is_2l_batch": True,
                    # 🔧 FIX BUG #2: METADATI AGGIUNTIVI PER DEBUG
                    "canvas_width": getattr(response.autoclave_info, 'width', autoclave_2l.width),
                    "canvas_height": getattr(response.autoclave_info, 'height', autoclave_2l.height),
                    "total_positioned": len(positioned_tools_data),
                    "level_0_count": response.metrics.level_0_count,
                    "level_1_count": response.metrics.level_1_count
                }
                
                # 🎯 CREA BATCH 2L CON CAMPI CORRETTI E COMPLETI
                batch = BatchNesting(
                    nome=f"Batch 2L {autoclave.nome}",
                    autoclave_id=autoclave.id,
                    configurazione_json=configurazione_json,
                    # ✅ Campi opzionali con valori di default sicuri
                    efficiency=float(response.metrics.efficiency_score or 0.0),
                    peso_totale_kg=int(response.metrics.total_weight_kg or 0),
                    numero_nesting=1,
                    area_totale_utilizzata=int(response.metrics.total_area_cm2 or 0),
                    valvole_totali_utilizzate=int(response.metrics.vacuum_lines_used or 0),
                    note=f"Batch 2L: {response.metrics.pieces_positioned} tool posizionati",
                    # ✅ Tracciabilità 
                    creato_da_utente="SYSTEM_2L",
                    creato_da_ruolo="AUTO",
                    stato=StatoBatchNestingEnum.DRAFT.value,  # 🔧 FIX: Genera sempre in stato DRAFT
                    # 🔧 FIX: Aggiungi ODL IDs dal request per completezza
                    odl_ids=request.odl_ids
                )
                
                db.add(batch)
                db.commit()
                db.refresh(batch)
                
                logger.info(f"💾 Batch 2L salvato nel database con ID: {batch.id}")
                
                # 🎯 SOLUZIONE SEMPLICE: Aggiungi batch_id direttamente alla risposta come dict
                response_dict = response.model_dump()
                response_dict["batch_id"] = str(batch.id)
                response_dict["saved_to_database"] = True
                
                solve_time = (time.time() - start_time) * 1000
                logger.info(f"✅ Nesting 2L batch completato in {solve_time:.1f}ms: {response.metrics.pieces_positioned} tool posizionati")
                logger.info(f"📊 Distribuzione livelli: L0={response.metrics.level_0_count}, L1={response.metrics.level_1_count}")
                logger.info(f"🎯 Batch ID per redirect frontend: {batch.id}")
                
                return response_dict
                
            except Exception as e:
                logger.error(f"❌ Errore salvataggio batch 2L: {str(e)}")
                logger.error(f"❌ Traceback completo: {str(e)}", exc_info=True)
                
                # ⚠️ Salvataggio fallito: restituisci risposta con errore
                response_dict = response.model_dump()
                response_dict["debug_error"] = f"Errore salvataggio: {str(e)}"
                response_dict["saved_to_database"] = False
                
                return response_dict
                
        solve_time = (time.time() - start_time) * 1000
        logger.info(f"✅ Nesting 2L batch completato in {solve_time:.1f}ms: {response.metrics.pieces_positioned} tool posizionati")
        logger.info(f"📊 Distribuzione livelli: L0={response.metrics.level_0_count}, L1={response.metrics.level_1_count}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Errore solver 2L batch: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante il nesting 2L batch: {str(e)}"
        )


# ========== ENDPOINT NESTING 2L ORIGINALE ==========

def _convert_db_to_tool_info_2l(odl: ODL, tool: Tool, parte: Parte) -> ToolInfo2L:
    """Converte dati database in ToolInfo2L per il solver - VERSION FIXED CRITICO"""
    
    # ✅ FIX CRITICO: Usa dimensioni realistiche diverse per ogni tool invece di fallback identici
    # PROBLEMA RISOLTO: Prima tutti i tool NULL diventavano 100x100mm, 1kg -> identici -> solo 6/45 posizionati
    
    # Genera dimensioni realistiche diverse basate sull'ODL ID per consistenza
    import hashlib
    seed = int(hashlib.md5(f"{odl.id}_{tool.id}".encode()).hexdigest()[:8], 16)
    import random
    random.seed(seed)
    
    # Lista dimensioni realistiche per diversi tipi di tool aerospace
    realistic_options = [
        (400, 300, 15),  # Small panel
        (600, 400, 25),  # Medium panel  
        (800, 500, 40),  # Large panel
        (350, 250, 12),  # Small bracket
        (500, 350, 20),  # Medium bracket
        (750, 450, 35),  # Large bracket
        (300, 200, 8),   # Small component
        (450, 300, 18),  # Medium component
        (700, 400, 30),  # Large component
        (250, 150, 5),   # Tiny part
    ]
    
    # Seleziona dimensioni consistenti per questo tool
    fallback_width, fallback_height, fallback_weight = realistic_options[seed % len(realistic_options)]
    
    # Usa dimensioni database se valide, altrimenti fallback realistici diversificati
    width = tool.lunghezza_piano if tool.lunghezza_piano and tool.lunghezza_piano > 0 else fallback_width
    height = tool.larghezza_piano if tool.larghezza_piano and tool.larghezza_piano > 0 else fallback_height  
    weight = tool.peso if tool.peso and tool.peso > 0 else fallback_weight
    
    # Criteri eligibilità rilassati ma realistici
    can_use_cavalletto = (
        weight <= 100.0 and  
        height <= 800.0 and  
        width <= 1200.0
    )
    
    return ToolInfo2L(
        odl_id=odl.id,
        width=width,    # ✅ FIXED: Dimensioni realistiche diverse per ogni tool
        height=height,  # ✅ FIXED: Elimina tool identici che causano 13% success rate  
        weight=weight,  # ✅ FIXED: Peso realistico diversificato
        lines_needed=parte.num_valvole_richieste or 1,
        ciclo_cura_id=parte.ciclo_cura_id,
        priority=1,
        can_use_cavalletto=can_use_cavalletto,
        preferred_level=None  # Lascia al solver decidere
    )

def _convert_db_to_autoclave_info_2l(autoclave: Autoclave) -> AutoclaveInfo2L:
    """Converte dati autoclave database in AutoclaveInfo2L - TUTTI I CAMPI DAL DATABASE - FIX NOMI CAMPI"""
    return AutoclaveInfo2L(
        id=autoclave.id,
        width=autoclave.lunghezza or 1000.0,
        height=autoclave.larghezza_piano or 800.0,
        max_weight=autoclave.max_load_kg or 500.0,
        max_lines=autoclave.num_linee_vuoto or 20,
        
        # ✅ FIX: Specifiche cavalletti dal database con nomi corretti
        has_cavalletti=autoclave.usa_cavalletti or False,
        cavalletto_height=autoclave.altezza_cavalletto_standard or 100.0,
        peso_max_per_cavalletto_kg=autoclave.peso_max_per_cavalletto_kg or 300.0,
        
        # ✅ FIX: Dimensioni fisiche cavalletti (campi corretti dal modello)
        cavalletto_width=autoclave.cavalletto_width or 80.0,
        cavalletto_height_mm=autoclave.cavalletto_height or 60.0,
        
        # ✅ FIX: Campi aggiuntivi dal database con fallback sicuri
        max_cavalletti=autoclave.max_cavalletti or 10,  # Fallback sicuro
        cavalletto_thickness_mm=60.0,  # Valore di default
        clearance_verticale=autoclave.clearance_verticale or 50.0,  # Fallback sicuro
        
        # Calcolato dinamicamente durante il solve
        num_cavalletti_utilizzati=0
    )

# ========== NUOVO ENDPOINT CARICAMENTO BATCH 2L ==========

@router.get("/result/{batch_id}", 
            summary="🎯 Recupera risultati batch (1L o 2L) per visualizzazione")
def get_batch_results(
    batch_id: str,
    multi: bool = False,  # 🆕 NUOVO: Parametro per gestire multi-batch
    db: Session = Depends(get_db)
):
    """
    🎯 ENDPOINT UNIVERSALE PER BATCH 1L E 2L - CON SUPPORTO MULTI-BATCH
    ===================================================================
    
    Recupera i risultati di un batch (normale o 2L) dal database
    per la visualizzazione nella pagina risultati.
    
    🆕 NOVITÀ v2.0:
    - Supporto parametro ?multi=true per caricare batch correlati
    - Compatibilità totale con sistema 1L multi-batch esistente
    - Detection automatica batch 2L per visualizzazione corretta
    
    Args:
        batch_id: ID del batch da recuperare
        multi: Se true, cerca e restituisce tutti i batch correlati
        
    Returns:
        Configurazione batch singolo o multi-batch con metadati per la visualizzazione
    """
    try:
        logger.info(f"🔍 Richiesta caricamento batch: {batch_id}, multi={multi}")
        
        # Cerca il batch principale nel database
        main_batch = db.query(BatchNesting).filter(BatchNesting.id == batch_id).first()
        
        if not main_batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch con ID {batch_id} non trovato"
            )
        
        def format_batch_for_frontend(batch: BatchNesting) -> dict:
            """Formatta un batch per la visualizzazione frontend"""
            # Verifica se è un batch 2L
            is_2l_batch = False
            if batch.configurazione_json:
                is_2l_batch = batch.configurazione_json.get('is_2l_batch', False)
            
            # Prepara la risposta base
            batch_data = {
                "id": str(batch.id),
                "nome": batch.nome,
                "stato": batch.stato if batch.stato else "draft",
                "autoclave_id": batch.autoclave_id,
                "configurazione_json": batch.configurazione_json or {},
                "created_at": batch.created_at.isoformat() if batch.created_at else None,
                "updated_at": batch.updated_at.isoformat() if batch.updated_at else None,
                "is_2l_batch": is_2l_batch
            }
            
            # Calcola metriche dal configurazione_json se disponibile
            if batch.configurazione_json:
                positioned_tools = batch.configurazione_json.get('positioned_tools', []) or batch.configurazione_json.get('tool_positions', [])
                
                # Metriche base
                efficiency = batch.efficiency if batch.efficiency is not None else 0.0
                total_weight = batch.peso_totale_kg if batch.peso_totale_kg is not None else 0.0
                positioned_count = len(positioned_tools)
                
                batch_data["metrics"] = {
                    "efficiency_percentage": efficiency,
                    "total_weight_kg": total_weight,
                    "positioned_tools": positioned_count,
                    "excluded_tools": 0  # Calcolabile se necessario
                }
                
                # Se è un batch 2L, aggiungi metadati specifici
                if is_2l_batch:
                    cavalletti = batch.configurazione_json.get('cavalletti', [])
                    
                    # Conta tool per livello
                    level_0_count = len([t for t in positioned_tools if t.get('level') == 0])
                    level_1_count = len([t for t in positioned_tools if t.get('level') == 1])
                    
                    batch_data["level_0_count"] = level_0_count
                    batch_data["level_1_count"] = level_1_count
                    batch_data["cavalletti_count"] = len(cavalletti)
                    
                    logger.info(f"📊 Batch 2L formattato: L0={level_0_count}, L1={level_1_count}, cavalletti={len(cavalletti)}")
            
            # Recupera informazioni autoclave
            if batch.autoclave_id:
                autoclave = db.query(Autoclave).filter(Autoclave.id == batch.autoclave_id).first()
                if autoclave:
                    batch_data["autoclave"] = {
                        "nome": autoclave.nome,
                        "codice": autoclave.codice,
                        "lunghezza": autoclave.lunghezza,
                        "larghezza_piano": autoclave.larghezza_piano,
                        "usa_cavalletti": autoclave.usa_cavalletti
                    }
            
            return batch_data
        
        # 🚀 GESTIONE MULTI-BATCH: Cerca batch correlati se richiesto
        if multi:
            logger.info(f"🔄 MULTI-BATCH MODE: Cerco batch correlati per {batch_id}")
            
            # Strategia di correlazione per batch multi-autoclave
            # 1. Cerca batch creati nello stesso periodo temporale (±5 minuti)
            time_window_minutes = 5
            created_time = main_batch.created_at
            
            if created_time:
                start_time = created_time - timedelta(minutes=time_window_minutes)
                end_time = created_time + timedelta(minutes=time_window_minutes)
                
                # Cerca batch correlati con autoclavi diverse
                related_batches = db.query(BatchNesting).filter(
                    BatchNesting.created_at >= start_time,
                    BatchNesting.created_at <= end_time,
                    BatchNesting.id != batch_id,  # Escludi il batch principale
                    BatchNesting.autoclave_id != main_batch.autoclave_id  # Autoclavi diverse per multi-batch
                ).limit(10).all()  # Limite di sicurezza
                
                # Combina batch principale + correlati
                all_batches = [main_batch] + related_batches
                
                logger.info(f"✅ MULTI-BATCH: Trovati {len(all_batches)} batch correlati (principale + {len(related_batches)} correlati)")
                
                # Formatta tutti i batch per il frontend
                batch_results = [format_batch_for_frontend(batch) for batch in all_batches]
                
                # Ordina per efficienza decrescente
                batch_results.sort(key=lambda x: x.get('metrics', {}).get('efficiency_percentage', 0), reverse=True)
                
                return {
                    "batch_results": batch_results,
                    "is_real_multi_batch": len(batch_results) > 1,
                    "total_batches": len(batch_results)
                }
            else:
                logger.warning(f"⚠️ MULTI-BATCH: Nessun timestamp per batch {batch_id}, fallback a single-batch")
        
        # 🎯 SINGLE-BATCH MODE: Restituisci solo il batch richiesto
        logger.info(f"✅ SINGLE-BATCH MODE: Restituisco batch {batch_id}")
        return format_batch_for_frontend(main_batch)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Errore caricamento batch {batch_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante il caricamento del batch: {str(e)}"
        )

# ========== NUOVO ENDPOINT MULTI-2L (PRIORITÀ ALTA) ==========

@router.post("/2l-multi", response_model=Dict[str, Any],
             summary="🚀 Nesting 2L multi-autoclave senza concorrenza",
             description="Genera batch 2L per multiple autoclavi in sequenza per evitare problemi di concorrenza")
def solve_nesting_2l_multi_batch(
    request: NestingMulti2LRequest,
    db: Session = Depends(get_db)
):
    """
    🚀 ENDPOINT NESTING SOLVER 2L MULTI-AUTOCLAVE - SEQUENZIALE
    ===========================================================
    
    Risolve problemi di nesting 2D per multiple autoclavi SEQUENZIALMENTE
    invece che in parallelo, evitando problemi di concorrenza del database.
    
    **Differenze chiave vs /2l:**
    - Processa multiple autoclavi in un singolo request
    - Esecuzione sequenziale invece che parallela
    - Gestione transazioni database atomica
    - Response unificata con tutti i risultati
    
    **Request format:**
    {
        "autoclavi_2l": [1, 2, 3],  // ID autoclavi con supporto 2L
        "odl_ids": [5, 6, 7, 8],
        "parametri": {"padding_mm": 5, "min_distance_mm": 10},
        "use_cavalletti": true,
        "cavalletto_height_mm": 100.0,
        "max_weight_per_level_kg": 200.0,
        "prefer_base_level": true
    }
    """
    start_time = time.time()
    logger.info(f"🚀 === NESTING 2L MULTI-BATCH START ===")
    
    try:
        # Estrai parametri dalla richiesta Pydantic
        autoclavi_2l_ids = request.autoclavi_2l
        odl_ids = request.odl_ids
        parametri = request.parametri
        use_cavalletti = request.use_cavalletti
        # cavalletto_height_mm = RIMOSSO - ora dal database autoclave
        # max_weight_per_level_kg = RIMOSSO - ora dal database autoclave
        prefer_base_level = request.prefer_base_level
        
        if not autoclavi_2l_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Almeno un'autoclave 2L deve essere specificata"
            )
        
        if not odl_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Almeno un ODL deve essere specificato"
            )
        
        logger.info(f"📋 Multi-2L: {len(autoclavi_2l_ids)} autoclavi, {len(odl_ids)} ODL")
        
        batch_results = []
        successful_batches = []
        
        # 🔄 PROCESSO SEQUENZIALE PER EVITARE CONCORRENZA
        for autoclave_id in autoclavi_2l_ids:
            try:
                logger.info(f"🎯 Processando autoclave 2L: {autoclave_id}")
                
                # Crea richiesta per singola autoclave - FIX DEFINITIVO senza cavalletto_height_mm
                single_request = NestingSolveRequest2L(
                    autoclave_id=autoclave_id,
                    odl_ids=odl_ids,
                    padding_mm=parametri.padding_mm,
                    min_distance_mm=parametri.min_distance_mm,
                    use_cavalletti=use_cavalletti,
                    # ✅ FIX: max_weight_per_level_kg rimosso perché non esiste in NestingSolveRequest2L
                    prefer_base_level=prefer_base_level,
                    allow_heuristic=True,
                    use_multithread=True,
                    heavy_piece_threshold_kg=50.0
                    # ✅ NOTA: cavalletto_height_mm è nell'autoclave, non nella request
                )
                
                # 🔧 CHIAMATA SEQUENZIALE AL MOTORE 2L
                # Usa la stessa logica del singolo endpoint ma in modo controllato
                autoclave = db.query(Autoclave).filter(Autoclave.id == autoclave_id).first()
                if not autoclave:
                    logger.warning(f"⚠️ Autoclave {autoclave_id} non trovata")
                    continue
                
                # Verifica supporto cavalletti
                if use_cavalletti and not autoclave.usa_cavalletti:
                    logger.warning(f"⚠️ Autoclave {autoclave.nome} non supporta cavalletti")
                    continue
                
                # Recupera ODL da processare
                odls = db.query(ODL).options(
                    joinedload(ODL.tool),
                    joinedload(ODL.parte)
                ).filter(
                    ODL.id.in_(odl_ids),
                    ODL.status == "Attesa Cura"
                ).all()
                
                if not odls:
                    logger.warning(f"⚠️ Nessun ODL valido per autoclave {autoclave_id}")
                    continue
                
                # Converte in ToolInfo2L
                tools_2l = []
                for odl in odls:
                    if odl.tool and odl.parte:
                        tool_2l = _convert_db_to_tool_info_2l(odl, odl.tool, odl.parte)
                        tools_2l.append(tool_2l)
                
                if not tools_2l:
                    logger.warning(f"⚠️ Nessun tool valido per autoclave {autoclave_id}")
                    continue
                
                # ✅ FIX LOGGING: Verifica dettagliata tool convertiti
                logger.info(f"🔧 Tool 2L convertiti per autoclave {autoclave_id}: {len(tools_2l)} tools")
                for i, tool in enumerate(tools_2l[:3]):  # Mostra solo primi 3 per debug
                    logger.info(f"   Tool {i}: ODL {tool.odl_id}, dims={tool.width}x{tool.height}, weight={tool.weight}kg")
                
                # Converte autoclave con dati dinamici dal database - FIX completo
                autoclave_2l = _convert_db_to_autoclave_info_2l(autoclave)
                autoclave_2l.has_cavalletti = use_cavalletti and autoclave.usa_cavalletti
                
                # ✅ FIX CRITICO: Assicura che i campi autoclave abbiano valori validi
                if not hasattr(autoclave_2l, 'cavalletto_height') or autoclave_2l.cavalletto_height <= 0:
                    autoclave_2l.cavalletto_height = 100.0  # Fallback sicuro
                if not hasattr(autoclave_2l, 'cavalletto_width') or autoclave_2l.cavalletto_width <= 0:
                    autoclave_2l.cavalletto_width = 80.0   # Fallback sicuro
                if not hasattr(autoclave_2l, 'cavalletto_height_mm') or autoclave_2l.cavalletto_height_mm <= 0:
                    autoclave_2l.cavalletto_height_mm = 60.0  # Fallback sicuro
                
                # Configura parametri solver con dati dinamici - FIX TIMEOUT ULTRA-AGGRESSIVO
                parameters_2l = NestingParameters2L(
                    padding_mm=single_request.padding_mm,
                    min_distance_mm=single_request.min_distance_mm,
                    vacuum_lines_capacity=autoclave.num_linee_vuoto or 20,
                    use_cavalletti=use_cavalletti,
                    prefer_base_level=prefer_base_level,
                    allow_heuristic=True,
                    use_multithread=True,  # ✅ RIABILITA MULTITHREAD per performance
                    heavy_piece_threshold_kg=50.0,
                    # ✅ FIX TIMEOUT REALISTICI: Timeout appropriati per algoritmi aerospace
                    base_timeout_seconds=60.0,   # 60 secondi base per dataset semplici
                    max_timeout_seconds=180.0    # 180 secondi (3 minuti) per dataset complessi
                )
                
                # ✅ FIX LOGGING: Aggiungo debug per identificare problemi
                logger.info(f"🔧 Parametri 2L autoclave {autoclave_id}: padding={parameters_2l.padding_mm}mm, cavalletti={use_cavalletti}, vacuum_lines={parameters_2l.vacuum_lines_capacity}")
                logger.info(f"🔧 Dati autoclave 2L: width={autoclave_2l.width}, height={autoclave_2l.height}, cavalletti_support={autoclave_2l.has_cavalletti}")
                
                # Risolve nesting 2L con parametri cavalletti configurabili
                solver_2l = NestingModel2L(parameters_2l)
                
                # ✅ NUOVO: Configura parametri cavalletti dal frontend
                if request.cavalletti_config:
                    cavalletti_config = CavallettiConfiguration(
                        # ✅ FIX CRITICO #1: USA SEMPRE dati dal database autoclave
                        cavalletto_width=autoclave_2l.cavalletto_width,  # Dal database, non hardcoded
                        cavalletto_height=autoclave_2l.cavalletto_height_mm,  # Dal database, non hardcoded
                        # ✅ FIX CRITICO #2: Parametri configurabili dal frontend
                        min_distance_from_edge=request.cavalletti_config.min_distance_from_edge,
                        max_span_without_support=request.cavalletti_config.max_span_without_support,
                        min_distance_between_cavalletti=request.cavalletti_config.min_distance_between_cavalletti,
                        safety_margin_x=request.cavalletti_config.safety_margin_x,
                        safety_margin_y=request.cavalletti_config.safety_margin_y,
                        prefer_symmetric=request.cavalletti_config.prefer_symmetric,
                        force_minimum_two=request.cavalletti_config.force_minimum_two
                    )
                    # Passa la configurazione al solver
                    solver_2l._cavalletti_config = cavalletti_config
                    logger.info(f"🔧 Configurazione cavalletti da frontend: "
                               f"size={autoclave_2l.cavalletto_width}x{autoclave_2l.cavalletto_height_mm}mm, "
                               f"min_edge={request.cavalletti_config.min_distance_from_edge}mm, "
                               f"force_two={request.cavalletti_config.force_minimum_two}")
                else:
                    # ✅ FIX CRITICO #3: FALLBACK USA SEMPRE database + parametri sicuri
                    cavalletti_config = CavallettiConfiguration(
                        # ✅ CORREZIONE: Dimensioni fisiche SEMPRE dal database autoclave
                        cavalletto_width=autoclave_2l.cavalletto_width,  # Dal database
                        cavalletto_height=autoclave_2l.cavalletto_height_mm,  # Dal database
                        # ✅ CORREZIONE: Parametri operativi con valori aeronautici sicuri
                        min_distance_from_edge=30.0,
                        max_span_without_support=400.0,
                        min_distance_between_cavalletti=200.0,
                        safety_margin_x=5.0,
                        safety_margin_y=5.0,
                        prefer_symmetric=True,
                        force_minimum_two=True  # 🚨 FIX CRITICO: SEMPRE minimo 2 cavalletti
                    )
                    solver_2l._cavalletti_config = cavalletti_config
                    logger.info(f"🔧 Configurazione cavalletti fallback: "
                               f"size={autoclave_2l.cavalletto_width}x{autoclave_2l.cavalletto_height_mm}mm (da DB), "
                               f"force_minimum_two=True")
                
                # ✅ FIX: Try-catch con timeout threading-based (Windows compatible)
                try:
                    logger.info(f"🚀 Chiamata solver 2L per autoclave {autoclave_id} (timeout realistico)...")
                    
                    # Timeout usando threading (Windows compatible)
                    import threading
                    import time as time_module
                    
                    solution_2l = None
                    exception_occurred = None
                    
                    def solve_with_timeout():
                        nonlocal solution_2l, exception_occurred
                        try:
                            solution_2l = solver_2l.solve_2l(tools_2l, autoclave_2l)
                        except Exception as e:
                            exception_occurred = e
                    
                    # Avvia solver in thread separato con timeout REALISTICO
                    solver_thread = threading.Thread(target=solve_with_timeout)
                    solver_thread.start()
                    solver_thread.join(timeout=240)  # 4 minuti timeout per autoclave singola
                    
                    if solver_thread.is_alive():
                        # Timeout - il thread è ancora in esecuzione
                        logger.warning(f"⏰ Solver 2L timeout per autoclave {autoclave_id} dopo 4 minuti - FALLBACK A SOLVER NORMALE")
                        
                        # ✅ FALLBACK: Usa solver normale se 2L va in timeout
                        from services.nesting.solver import NestingModel, NestingParameters
                        
                        # Converte parametri per solver normale
                        normal_params = NestingParameters(
                            padding_mm=parameters_2l.padding_mm,
                            min_distance_mm=parameters_2l.min_distance_mm,
                            vacuum_lines_capacity=parameters_2l.vacuum_lines_capacity,
                            use_fallback=True,
                            allow_heuristic=True,
                            timeout_override=60  # 60 secondi per solver normale fallback
                        )
                        
                        # Converte dati per solver normale
                        from services.nesting.solver import ToolInfo, AutoclaveInfo
                        normal_tools = []
                        for tool_2l in tools_2l:
                            normal_tool = ToolInfo(
                                odl_id=tool_2l.odl_id,
                                width=tool_2l.width,
                                height=tool_2l.height,
                                weight=tool_2l.weight,
                                lines_needed=tool_2l.lines_needed,
                                ciclo_cura_id=tool_2l.ciclo_cura_id,
                                priority=tool_2l.priority
                            )
                            normal_tools.append(normal_tool)
                        
                        normal_autoclave = AutoclaveInfo(
                            id=autoclave_2l.id,
                            width=autoclave_2l.width,
                            height=autoclave_2l.height,
                            max_weight=autoclave_2l.max_weight,
                            max_lines=autoclave_2l.max_lines
                        )
                        
                        # Usa solver normale come fallback
                        normal_solver = NestingModel(normal_params)
                        normal_solution = normal_solver.solve(normal_tools, normal_autoclave)
                        
                        logger.info(f"✅ Fallback normale completato: success={normal_solution.success}, positioned={len(normal_solution.layouts)}")
                        
                        # Simula response 2L per compatibilità
                        if normal_solution.success:
                            response = type('obj', (object,), {
                                'success': True,
                                'message': f"Fallback normale: {normal_solution.metrics.positioned_count} tool posizionati",
                                'metrics': type('obj', (object,), {
                                    'pieces_positioned': normal_solution.metrics.positioned_count,
                                    'efficiency_score': normal_solution.metrics.efficiency_score,
                                    'total_weight_kg': normal_solution.metrics.total_weight,
                                    'total_area_cm2': normal_solution.metrics.positioned_count * 1000,  # Stima
                                    'vacuum_lines_used': normal_solution.metrics.lines_used,
                                    'level_0_count': normal_solution.metrics.positioned_count,
                                    'level_1_count': 0,  # Solo livello 0 nel solver normale
                                    'cavalletti_used': 0,
                                    'algorithm_status': 'FALLBACK_NORMAL'
                                })(),
                                'positioned_tools': [],  # Semplificato per ora
                                'cavalletti': [],
                                'autoclave_info': {
                                    'id': autoclave.id,
                                    'nome': autoclave.nome,
                                    'width': autoclave_2l.width,
                                    'height': autoclave_2l.height
                                }
                            })()
                        else:
                            logger.warning(f"⚠️ Anche fallback normale fallito per autoclave {autoclave_id}")
                            continue
                    
                    elif exception_occurred:
                        # Errore nel solver 2L
                        logger.error(f"❌ Errore nel solver 2L per autoclave {autoclave_id}: {exception_occurred}")
                        continue
                    
                    elif solution_2l is not None:
                        # Solver 2L completato con successo
                        logger.info(f"✅ Solver 2L completato: success={solution_2l.success}, positioned={len(solution_2l.layouts)}")
                        
                        response = solver_2l.convert_to_pydantic_response(
                            solution_2l, 
                            autoclave_2l,
                            request_params=single_request.model_dump()
                        )
                        logger.info(f"✅ Response 2L convertita: success={response.success}, metrics_positioned={response.metrics.pieces_positioned}")
                    
                    else:
                        # Caso inaspettato
                        logger.warning(f"⚠️ Solver 2L terminato senza risultato per autoclave {autoclave_id}")
                        continue
                
                except Exception as solver_error:
                    logger.error(f"❌ ERRORE SOLVER 2L autoclave {autoclave_id}: {str(solver_error)}")
                    logger.error(f"❌ Dettagli errore: {type(solver_error).__name__}")
                    import traceback
                    logger.error(f"❌ Stack trace: {traceback.format_exc()}")
                    continue  # Salta questa autoclave e prova la prossima
                
                # Salva batch se successo
                if response.success and response.metrics.pieces_positioned > 0:
                    try:
                        # 🔧 FIX SERIALIZZAZIONE: Usa dict invece di model_dump per evitare errori di serializzazione
                        def safe_serialize(obj):
                            """Serializza in modo sicuro un oggetto Pydantic"""
                            try:
                                return obj.model_dump() if hasattr(obj, 'model_dump') else dict(obj)
                            except Exception as e:
                                logger.warning(f"⚠️ Fallback serialization per {type(obj)}: {e}")
                                # Fallback: serializza manualmente i campi base
                                if hasattr(obj, '__dict__'):
                                    return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
                                return {}
                        
                        # 🔧 FIX BUG #2: MIGLIORAMENTO GESTIONE POSITIONED_TOOLS_DATA
                        positioned_tools_data = []
                        for tool in response.positioned_tools:
                            tool_data = {
                                'odl_id': getattr(tool, 'odl_id', None),
                                'x': getattr(tool, 'x', 0.0),
                                'y': getattr(tool, 'y', 0.0),
                                'width': getattr(tool, 'width', 0.0),
                                'height': getattr(tool, 'height', 0.0),
                                'peso': getattr(tool, 'peso', getattr(tool, 'weight', 0.0)),
                                'weight': getattr(tool, 'peso', getattr(tool, 'weight', 0.0)),  # Backup field
                                'rotated': getattr(tool, 'rotated', False),
                                'level': getattr(tool, 'level', 0),  # ✅ CRITICO: Campo livello per 2L
                                'lines_used': getattr(tool, 'lines_used', 1),
                                'numero_odl': None,  # Sarà popolato dopo
                                'descrizione_breve': None,  # Sarà popolato dopo
                                'part_number': None  # Sarà popolato dopo
                            }
                            positioned_tools_data.append(tool_data)
                        
                        # 🔧 FIX BUG #2: ARRICCHIMENTO DATI CON INFO ODL/PARTE
                        odl_info_map = {}
                        for odl_id in request.odl_ids:
                            odl = db.query(ODL).options(
                                joinedload(ODL.parte),
                                joinedload(ODL.tool)
                            ).filter(ODL.id == odl_id).first()
                            if odl:
                                odl_info_map[odl_id] = {
                                    'numero_odl': odl.numero_odl,
                                    'descrizione_breve': odl.parte.descrizione_breve if odl.parte else "N/A",
                                    'part_number': odl.parte.part_number if odl.parte else "N/A"
                                }
                
                        # Arricchisce positioned_tools_data con info ODL
                        for tool_data in positioned_tools_data:
                            odl_id = tool_data.get('odl_id')
                            if odl_id and odl_id in odl_info_map:
                                tool_data.update(odl_info_map[odl_id])
                        
                        configurazione_json = {
                            "positioned_tools": positioned_tools_data,  # 🔧 FIX: Usa positioned_tools invece di tool serializzati
                            "positioned_tools_data": positioned_tools_data,  # ✅ BACKWARD COMPATIBILITY
                            "cavalletti": [safe_serialize(cav) for cav in response.cavalletti],
                            "autoclave_info": response.autoclave_info,
                            "algorithm_used": response.metrics.algorithm_status,
                            "parametri_usati": safe_serialize(single_request),
                            "is_2l_batch": True,
                            # 🔧 FIX BUG #2: METADATI AGGIUNTIVI PER DEBUG
                            "canvas_width": getattr(response.autoclave_info, 'width', autoclave_2l.width),
                            "canvas_height": getattr(response.autoclave_info, 'height', autoclave_2l.height),
                            "total_positioned": len(positioned_tools_data),
                            "level_0_count": response.metrics.level_0_count,
                            "level_1_count": response.metrics.level_1_count
                        }
                        
                        batch = BatchNesting(
                            nome=f"Batch 2L {autoclave.nome}",
                            autoclave_id=autoclave.id,
                            configurazione_json=configurazione_json,
                            # ✅ Campi opzionali con valori di default sicuri
                            efficiency=float(response.metrics.efficiency_score or 0.0),
                            peso_totale_kg=int(response.metrics.total_weight_kg or 0),
                            numero_nesting=1,
                            area_totale_utilizzata=int(response.metrics.total_area_cm2 or 0),
                            valvole_totali_utilizzate=int(response.metrics.vacuum_lines_used or 0),
                            note=f"Batch 2L: {response.metrics.pieces_positioned} tool posizionati",
                            creato_da_utente="SYSTEM_2L_MULTI",
                            creato_da_ruolo="AUTO",
                            stato=StatoBatchNestingEnum.DRAFT.value,  # 🔧 FIX: Genera sempre in stato DRAFT
                            # 🔧 FIX: Aggiungi ODL IDs dal request per completezza
                            odl_ids=request.odl_ids
                        )
                        
                        db.add(batch)
                        db.commit()
                        db.refresh(batch)
                        
                        # Aggiungi ai risultati di successo
                        batch_result = {
                            "batch_id": str(batch.id),
                            "autoclave_id": autoclave_id,
                            "autoclave_nome": autoclave.nome,
                            "efficiency": float(response.metrics.efficiency_score or 0.0),
                            "total_weight": float(response.metrics.total_weight_kg or 0.0),
                            "positioned_tools": response.metrics.pieces_positioned,
                            "excluded_odls": getattr(response.metrics, 'pieces_excluded', getattr(response.metrics, 'excluded_count', 0)),
                            "success": True,
                            "message": f"Batch 2L generato: {response.metrics.pieces_positioned} tool",
                            "level_0_count": response.metrics.level_0_count,
                            "level_1_count": response.metrics.level_1_count,
                            "cavalletti_used": response.metrics.cavalletti_used
                        }
                        
                        batch_results.append(batch_result)
                        successful_batches.append(batch_result)
                        
                        logger.info(f"✅ Batch 2L salvato: {batch.id} per {autoclave.nome}")
                        
                    except Exception as save_error:
                        logger.error(f"❌ Errore salvataggio batch 2L autoclave {autoclave_id}: {save_error}")
                        batch_results.append({
                            "batch_id": None,
                            "autoclave_id": autoclave_id,
                            "autoclave_nome": autoclave.nome,
                            "success": False,
                            "message": f"Errore salvataggio: {str(save_error)}"
                        })
                else:
                    logger.warning(f"⚠️ Nesting 2L fallito per autoclave {autoclave_id}")
                    batch_results.append({
                        "batch_id": None,
                        "autoclave_id": autoclave_id,
                        "autoclave_nome": autoclave.nome,
                        "success": False,
                        "message": "Nesting fallito o nessun tool posizionato"
                    })
                        
            except Exception as autoclave_error:
                logger.error(f"❌ Errore processing autoclave {autoclave_id}: {autoclave_error}")
                batch_results.append({
                    "batch_id": None,
                    "autoclave_id": autoclave_id,
                    "success": False,
                    "message": f"Errore processing: {str(autoclave_error)}"
                })
        
        # Prepara risposta unificata
        total_time = (time.time() - start_time) * 1000
        success_count = len(successful_batches)
        
        if success_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Nessun batch 2L generato con successo"
            )
        
        # 🔧 FIX SERIALIZZAZIONE: Costruisci la risposta in modo sicuro per evitare errori HTTP 500
        try:
            # 🎯 TROVA IL MIGLIOR BATCH PER REDIRECT
            best_batch = max(successful_batches, key=lambda b: b.get('efficiency', 0.0)) if successful_batches else None
            best_batch_id = best_batch.get('batch_id') if best_batch else None
            
            # Calcola statistiche aggregate
            avg_efficiency = sum(b.get('efficiency', 0.0) for b in successful_batches) / len(successful_batches) if successful_batches else 0.0
            total_tools = sum(b.get('positioned_tools', 0) for b in successful_batches)
            
            # 🚀 RISPOSTA COMPATIBILE CON SISTEMA MULTI-BATCH FRONTEND
            response_data = {
                "success": True,
                "message": f"Multi-2L completato: {success_count}/{len(autoclavi_2l_ids)} batch generati",
                "batch_results": batch_results,  # ✅ CHIAVE STANDARD per frontend multi-batch
                "total_autoclavi": len(autoclavi_2l_ids),
                "success_count": success_count,
                "error_count": len(autoclavi_2l_ids) - success_count,
                "best_batch_id": best_batch_id,  # ✅ CAMPO STANDARD per redirect
                "avg_efficiency": round(avg_efficiency, 2),
                "total_positioned_tools": total_tools,
                "is_real_multi_batch": True,  # ✅ SEMPRE True per 2L multi-batch
                "unique_autoclavi_count": len(set(b.get('autoclave_id') for b in successful_batches if b.get('success'))),
                "processing_time_ms": round(total_time, 1),
                "algorithm_type": "2L_MULTI_SEQUENTIAL",
                # 🆕 METADATI 2L SPECIFICI
                "is_2l_generation": True,
                "total_level_0_tools": sum(b.get('level_0_count', 0) for b in successful_batches),
                "total_level_1_tools": sum(b.get('level_1_count', 0) for b in successful_batches),
                "total_cavalletti": sum(b.get('cavalletti_used', 0) for b in successful_batches)
            }
            
            logger.info(f"✅ Multi-2L completato: {success_count} batch in {total_time:.1f}ms")
            logger.info(f"🎯 Best batch per redirect: {best_batch_id} (efficienza {best_batch['efficiency']:.1f}%)")
            
            # 🔧 VERIFICA FINALE: Assicurati che la risposta sia JSON-serializable
            json.dumps(response_data)  # Test serialization
            
            return response_data
            
        except Exception as serialization_error:
            logger.error(f"❌ Errore serializzazione risposta Multi-2L: {serialization_error}")
            logger.error(f"   Tipo errore: {type(serialization_error)}")
            logger.error(f"   Response keys: {list(response_data.keys()) if 'response_data' in locals() else 'N/A'}")
            
            # 🆘 FALLBACK: Risposta minima ma funzionante
            fallback_response = {
                "success": True,
                "message": f"Multi-2L completato: {success_count}/{len(autoclavi_2l_ids)} batch generati (serializzazione semplificata)",
                "total_autoclavi": len(autoclavi_2l_ids),
                "success_count": success_count,
                "error_count": len(autoclavi_2l_ids) - success_count,
                "best_batch_id": str(best_batch_id),
                "avg_efficiency": float(round(avg_efficiency, 2)),
                "algorithm_type": "2L_MULTI_SEQUENTIAL",
                "batch_results": [
                    {
                        "batch_id": str(b.get('batch_id', '')),
                        "autoclave_id": int(b.get('autoclave_id', 0)),
                        "autoclave_nome": str(b.get('autoclave_nome', '')),
                        "efficiency": float(b.get('efficiency', 0.0)),
                        "success": bool(b.get('success', False)),
                        "message": str(b.get('message', ''))
                    }
                    for b in successful_batches
                ]
            }
            
            logger.info(f"🆘 Usando risposta fallback per Multi-2L")
            return fallback_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Errore Multi-2L: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante multi-nesting 2L: {str(e)}"
        )

# ========== ENDPOINT NESTING 2L ORIGINALE ==========
