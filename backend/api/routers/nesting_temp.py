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
from services.nesting_robustness_improvement import RobustNestingService
from models.nesting_result import NestingResult
from models.odl import ODL
from models.autoclave import Autoclave, StatoAutoclaveEnum

# Configurazione logger
logger = logging.getLogger(__name__)

# Creazione router
router = APIRouter(
    prefix="/nesting",
    tags=["Nesting con OR-Tools Robusto"],
    responses={404: {"description": "Endpoint non trovato"}}
)

class NestingParametri(BaseModel):
    padding_mm: int = 20
    min_distance_mm: int = 15
    priorita_area: bool = True

class NestingRequest(BaseModel):
    odl_ids: List[str]
    autoclave_ids: List[str]
    parametri: NestingParametri = NestingParametri()

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
    # Nuovi campi per robustezza
    validation_report: Dict[str, Any] = None
    fixes_applied: List[str] = []

class NestingDataResponse(BaseModel):
    """Risposta per l'endpoint /data con ODL e autoclavi disponibili"""
    odl_in_attesa_cura: List[Dict[str, Any]]
    autoclavi_disponibili: List[Dict[str, Any]]
    statistiche: Dict[str, Any]
    status: str

@router.post("/genera", response_model=NestingResponse,
             summary="Genera un nuovo nesting robusto utilizzando OR-Tools")
def genera_nesting_robusto(
    request: NestingRequest, 
    db: Session = Depends(get_db)
):
    """
    🔧 ENDPOINT NESTING ROBUSTO CON OR-TOOLS
    ========================================
    
    Genera un nesting ottimizzato con gestione errori avanzata e strategie di fallback:
    
    - **Validazione automatica** dei prerequisiti di sistema
    - **Auto-correzione** dei problemi comuni (es. stato autoclavi)
    - **Algoritmo di fallback** per situazioni critiche
    - **Gestione errori robusta** con messaggi dettagliati
    - **Creazione batch garantita** anche in caso di problemi parziali
    
    **Parametri:**
    - odl_ids: Lista degli ID degli ODL da processare
    - autoclave_ids: Lista degli ID delle autoclavi da utilizzare
    - parametri: Configurazione algoritmo nesting
    
    **Ritorna:**
    - Batch ID principale generato
    - Lista tool posizionati e ODL esclusi
    - Report di validazione e fix applicati
    - Statistiche di efficienza e peso
    """
    
    try:
        logger.info(f"🚀 Avvio nesting robusto: {len(request.odl_ids)} ODL, {len(request.autoclave_ids)} autoclavi")
        
        # Validazione input base
        if not request.odl_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lista ODL non può essere vuota"
            )
        
        if not request.autoclave_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lista autoclavi non può essere vuota"
            )
        
        # Conversione IDs da string a int
        try:
            odl_ids = [int(id_str) for id_str in request.odl_ids]
            autoclave_ids = [int(id_str) for id_str in request.autoclave_ids]
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"IDs non validi forniti: {str(e)}"
            )
        
        # Parametri nesting
        parameters = NestingParameters(
            padding_mm=request.parametri.padding_mm,
            min_distance_mm=request.parametri.min_distance_mm,
            priorita_area=request.parametri.priorita_area
        )
        
        # Inizializza servizio robusto
        robust_service = RobustNestingService()
        
        # Genera nesting con robustezza
        result = robust_service.generate_robust_nesting(
            db=db,
            odl_ids=odl_ids,
            autoclave_ids=autoclave_ids,
            parameters=parameters
        )
        
        # Log del risultato
        if result['success']:
            logger.info(f"✅ Nesting robusto completato: batch {result['batch_id']}")
        else:
            logger.warning(f"⚠️ Nesting con problemi: {result['message']}")
        
        # Prepara risposta
        return NestingResponse(
            batch_id=result.get('batch_id', ''),
            message=result['message'],
            odl_count=len(request.odl_ids),
            autoclave_count=len(request.autoclave_ids),
            positioned_tools=result['positioned_tools'],
            excluded_odls=result['excluded_odls'],
            efficiency=result['efficiency'],
            total_weight=result['total_weight'],
            algorithm_status=result['algorithm_status'],
            success=result['success'],
            validation_report=result.get('validation_report'),
            fixes_applied=result.get('fixes_applied', [])
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
        logger.error(f"❌ Errore imprevisto nella generazione nesting robusto: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore interno del server: {str(e)}"
        )

@router.get("/health", summary="Verifica stato salute modulo nesting")
def check_nesting_health(db: Session = Depends(get_db)):
    """
    🔍 ENDPOINT HEALTH CHECK NESTING
    =================================
    
    Verifica lo stato di salute del modulo nesting e fornisce:
    - Statistiche ODL e autoclavi disponibili
    - Validazione prerequisiti sistema
    - Report problemi identificati
    - Suggerimenti per risoluzione
    """
    try:
        logger.info("🔍 Health check modulo nesting...")
        
        robust_service = RobustNestingService()
        validation = robust_service.validate_system_prerequisites(db)
        
        health_status = {
            "status": "HEALTHY" if validation['valid'] else "UNHEALTHY",
            "timestamp": datetime.now().isoformat(),
            "statistics": validation['statistics'],
            "issues": validation['issues'],
            "warnings": validation['warnings'],
            "recommendations": []
        }
        
        # Aggiungi raccomandazioni
        if not validation['valid']:
            for issue in validation['issues']:
                if issue['type'] == 'NO_ODL_AVAILABLE':
                    health_status['recommendations'].append(
                        "Creare nuovi ODL in stato 'Attesa Cura' per abilitare il nesting"
                    )
                elif issue['type'] == 'NO_AUTOCLAVE_AVAILABLE':
                    health_status['recommendations'].append(
                        "Verificare stato autoclavi e renderle disponibili"
                    )
        
        if validation['warnings']:
            health_status['recommendations'].append(
                "Verificare integrità dati e completare informazioni mancanti"
            )
        
        logger.info(f"Health check completato: {health_status['status']}")
        return health_status
        
    except Exception as e:
        logger.error(f"❌ Errore durante health check: {str(e)}")
        return {
            "status": "ERROR",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "recommendations": ["Verificare connessione database e integrità sistema"]
        }

@router.post("/auto-fix", summary="Applica correzioni automatiche al sistema")
def apply_auto_fixes(db: Session = Depends(get_db)):
    """
    🔧 ENDPOINT AUTO-FIX SISTEMA NESTING
    ====================================
    
    Applica automaticamente le correzioni disponibili per i problemi del sistema:
    - Aggiorna stato autoclavi non disponibili
    - Corregge dati incompleti quando possibile
    - Ripristina configurazioni di default
    """
    try:
        logger.info("🔧 Applicazione auto-fix sistema nesting...")
        
        robust_service = RobustNestingService()
        
        # Validazione preliminare
        validation = robust_service.validate_system_prerequisites(db)
        
        if validation['valid']:
            return {
                "success": True,
                "message": "Sistema già in stato ottimale - nessun fix necessario",
                "fixes_applied": [],
                "validation_report": validation
            }
        
        # Applica correzioni
        fixes_applied = robust_service.fix_system_issues(db, validation)
        
        # Re-validazione post fix
        new_validation = robust_service.validate_system_prerequisites(db)
        
        result = {
            "success": fixes_applied,
            "message": "Correzioni applicate con successo" if fixes_applied else "Nessuna correzione automatica disponibile",
            "fixes_applied": ["Auto-fix autoclavi"] if fixes_applied else [],
            "validation_before": validation,
            "validation_after": new_validation
        }
        
        logger.info(f"Auto-fix completato: {result['success']}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Errore durante auto-fix: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante applicazione correzioni: {str(e)}"
        )

@router.get("/data", response_model=NestingDataResponse,
            summary="Ottiene dati per il nesting (ODL e autoclavi disponibili)")
def get_nesting_data(db: Session = Depends(get_db)):
    """
    📊 ENDPOINT DATI NESTING
    ========================
    
    Fornisce tutti i dati necessari per il frontend del nesting:
    - ODL in attesa di cura con dettagli parte e tool
    - Autoclavi disponibili con specifiche tecniche
    - Statistiche di sistema
    - Stato generale del sistema
    
    **Ritorna:**
    - Lista ODL pronti per il nesting
    - Lista autoclavi utilizzabili
    - Contatori e statistiche
    - Stato salute sistema
    """
    try:
        logger.info("📊 Richiesta dati nesting da frontend...")
        
        # Query ODL in attesa di cura con relazioni
        odl_query = db.query(ODL).filter(ODL.status == "Attesa Cura")
        odl_list = odl_query.all()
        
        # Query autoclavi disponibili
        autoclavi_query = db.query(Autoclave).filter(Autoclave.stato == StatoAutoclaveEnum.DISPONIBILE)
        autoclavi_list = autoclavi_query.all()
        
        # Prepara dati ODL con dettagli
        odl_data = []
        for odl in odl_list:
            try:
                odl_info = {
                    "id": odl.id,
                    "status": odl.status,
                    "priorita": odl.priorita,
                    "note": odl.note,
                    "created_at": odl.created_at.isoformat() if odl.created_at else None,
                    "parte": {
                        "id": odl.parte.id if odl.parte else None,
                        "part_number": odl.parte.part_number if odl.parte else None,
                        "descrizione_breve": odl.parte.descrizione_breve if odl.parte else "N/A",
                        "num_valvole_richieste": odl.parte.num_valvole_richieste if odl.parte else 1,
                        "ciclo_cura": {
                            "id": odl.parte.ciclo_cura.id if odl.parte and odl.parte.ciclo_cura else None,
                            "nome": odl.parte.ciclo_cura.nome if odl.parte and odl.parte.ciclo_cura else "N/A",
                            "temperatura_stasi1": odl.parte.ciclo_cura.temperatura_stasi1 if odl.parte and odl.parte.ciclo_cura else None,
                            "pressione_stasi1": odl.parte.ciclo_cura.pressione_stasi1 if odl.parte and odl.parte.ciclo_cura else None,
                            "durata_stasi1": odl.parte.ciclo_cura.durata_stasi1 if odl.parte and odl.parte.ciclo_cura else None
                        } if odl.parte and odl.parte.ciclo_cura else None
                    } if odl.parte else None,
                    "tool": {
                        "id": odl.tool.id if odl.tool else None,
                        "part_number_tool": odl.tool.part_number_tool if odl.tool else "N/A",
                        "descrizione": odl.tool.descrizione if odl.tool else None,
                        "larghezza_piano": odl.tool.larghezza_piano if odl.tool else 0,
                        "lunghezza_piano": odl.tool.lunghezza_piano if odl.tool else 0,
                        "peso": odl.tool.peso if odl.tool else 0
                    } if odl.tool else None
                }
                odl_data.append(odl_info)
            except Exception as e:
                logger.warning(f"Errore nel processare ODL {odl.id}: {e}")
                continue
        
        # Prepara dati autoclavi
        autoclavi_data = []
        for autoclave in autoclavi_list:
            try:
                autoclave_info = {
                    "id": autoclave.id,
                    "nome": autoclave.nome,
                    "codice": autoclave.codice,
                    "stato": autoclave.stato.value if autoclave.stato else "N/A",
                    "lunghezza": autoclave.lunghezza,
                    "larghezza_piano": autoclave.larghezza_piano,
                    "temperatura_max": autoclave.temperatura_max,
                    "pressione_max": autoclave.pressione_max,
                    "max_load_kg": autoclave.max_load_kg,
                    "num_linee_vuoto": autoclave.num_linee_vuoto,
                    "use_secondary_plane": autoclave.use_secondary_plane,
                    "produttore": autoclave.produttore
                }
                autoclavi_data.append(autoclave_info)
            except Exception as e:
                logger.warning(f"Errore nel processare Autoclave {autoclave.id}: {e}")
                continue
        
        # Calcola statistiche
        statistiche = {
            "odl_totali": len(odl_data),
            "autoclavi_totali": len(autoclavi_data),
            "peso_totale_stimato": sum(odl.get("tool", {}).get("peso", 0) for odl in odl_data),
            "valvole_totali_richieste": sum(odl.get("parte", {}).get("num_valvole_richieste", 0) for odl in odl_data),
            "priorita_media": sum(odl.get("priorita", 1) for odl in odl_data) / len(odl_data) if odl_data else 0
        }
        
        # Determina stato sistema
        if len(odl_data) == 0:
            status_sistema = "NO_ODL_AVAILABLE"
        elif len(autoclavi_data) == 0:
            status_sistema = "NO_AUTOCLAVE_AVAILABLE"
        else:
            status_sistema = "READY"
        
        response = NestingDataResponse(
            odl_in_attesa_cura=odl_data,
            autoclavi_disponibili=autoclavi_data,
            statistiche=statistiche,
            status=status_sistema
        )
        
        logger.info(f"✅ Dati nesting preparati: {len(odl_data)} ODL, {len(autoclavi_data)} autoclavi")
        return response
        
    except Exception as e:
        logger.error(f"❌ Errore nel recupero dati nesting: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore nel recupero dati: {str(e)}"
        ) 