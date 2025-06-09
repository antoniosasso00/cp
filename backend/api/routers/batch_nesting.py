import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from api.database import get_db
from models.batch_nesting import BatchNesting, StatoBatchNestingEnum
from models.autoclave import Autoclave, StatoAutoclaveEnum
from models.odl import ODL
from models.parte import Parte
from models.ciclo_cura import CicloCura
from models.tool import Tool
from models.nesting_result import NestingResult
from schemas.batch_nesting import (
    BatchNestingCreate, 
    BatchNestingResponse, 
    BatchNestingUpdate, 
    BatchNestingList,
    StatoBatchNestingEnum as StatoBatchNestingEnumSchema
)
from services.state_tracking_service import StateTrackingService
from services.odl_log_service import ODLLogService
from services.batch.log import BatchLogService

# Configurazione logger
logger = logging.getLogger(__name__)

# Creazione router
router = APIRouter(
    prefix="/batch_nesting",
    tags=["Batch Nesting"],
    responses={404: {"description": "Batch nesting non trovato"}}
)

@router.post("/", response_model=BatchNestingResponse, status_code=status.HTTP_201_CREATED,
             summary="Crea un nuovo batch nesting")
def create_batch_nesting(batch_data: BatchNestingCreate, db: Session = Depends(get_db)):
    """
    Crea un nuovo batch nesting con le seguenti informazioni:
    
    - **nome**: nome opzionale del batch (se non specificato viene generato automaticamente)
    - **autoclave_id**: ID dell'autoclave per cui è destinato il batch
    - **odl_ids**: lista degli ID degli ODL da includere nel batch
    - **parametri**: parametri utilizzati per la generazione del nesting
    - **configurazione_json**: configurazione del layout generata dal frontend
    - **note**: note aggiuntive opzionali
    - **creato_da_utente**: ID dell'utente che crea il batch
    - **creato_da_ruolo**: ruolo dell'utente che crea il batch
    """
    try:
        # Verifica che l'autoclave esista
        autoclave = db.query(Autoclave).filter(Autoclave.id == batch_data.autoclave_id).first()
        if not autoclave:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Autoclave con ID {batch_data.autoclave_id} non trovata"
            )
        
        # Verifica che tutti gli ODL esistano
        if batch_data.odl_ids:
            existing_odl_count = db.query(ODL).filter(ODL.id.in_(batch_data.odl_ids)).count()
            if existing_odl_count != len(batch_data.odl_ids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Uno o più ODL specificati non esistono"
                )
        
        # Genera nome automatico se non specificato
        if not batch_data.nome:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            batch_data.nome = f"Batch_{autoclave.nome}_{timestamp}"
        
        # Converte i dati per il database
        batch_dict = batch_data.model_dump()
        
        # Converte i parametri e configurazione in dict se sono oggetti Pydantic
        if batch_dict.get('parametri'):
            if hasattr(batch_dict['parametri'], 'model_dump'):
                batch_dict['parametri'] = batch_dict['parametri'].model_dump()
        
        if batch_dict.get('configurazione_json'):
            if hasattr(batch_dict['configurazione_json'], 'model_dump'):
                batch_dict['configurazione_json'] = batch_dict['configurazione_json'].model_dump()
        
        # Calcola statistiche iniziali
        batch_dict['numero_nesting'] = 1 if batch_data.odl_ids else 0
        
        db_batch = BatchNesting(**batch_dict)
        
        db.add(db_batch)
        db.commit()
        db.refresh(db_batch)
        
        logger.info(f"Creato nuovo batch nesting: {db_batch.id} per autoclave {batch_data.autoclave_id}")
        return db_batch
        
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Errore di integrità durante la creazione del batch nesting: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Errore di integrità dei dati. Verificare che tutti i riferimenti siano validi."
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Errore imprevisto durante la creazione del batch nesting: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Si è verificato un errore durante la creazione del batch nesting: {str(e)}"
        )

@router.get("/", response_model=List[BatchNestingList], 
            summary="Ottiene la lista dei batch nesting")
def read_batch_nesting_list(
    skip: int = Query(0, ge=0, description="Numero di elementi da saltare"),
    limit: int = Query(100, ge=1, le=1000, description="Numero massimo di elementi da restituire"),
    autoclave_id: Optional[int] = Query(None, description="Filtra per ID autoclave"),
    stato: Optional[StatoBatchNestingEnumSchema] = Query(None, description="Filtra per stato"),
    nome: Optional[str] = Query(None, description="Filtra per nome (ricerca parziale)"),
    db: Session = Depends(get_db)
):
    """
    Recupera una lista di batch nesting con supporto per paginazione e filtri:
    
    - **skip**: numero di elementi da saltare per la paginazione
    - **limit**: numero massimo di elementi da restituire
    - **autoclave_id**: filtro opzionale per ID autoclave
    - **stato**: filtro opzionale per stato del batch
    - **nome**: filtro opzionale per nome (ricerca parziale case-insensitive)
    """
    query = db.query(BatchNesting)
    
    # Applicazione filtri
    if autoclave_id:
        query = query.filter(BatchNesting.autoclave_id == autoclave_id)
    if stato:
        query = query.filter(BatchNesting.stato == stato.value)
    if nome:
        query = query.filter(BatchNesting.nome.ilike(f"%{nome}%"))
    
    # Ordinamento per data di creazione (più recenti prima)
    query = query.order_by(BatchNesting.created_at.desc())
    
    return query.offset(skip).limit(limit).all()

# ========== ENDPOINT LEGACY DA NESTING_TEMP ==========
# Aggiunti per compatibilità con il frontend esistente

from typing import Dict, Any
from pydantic import BaseModel
from services.nesting_service import NestingService, NestingParameters

class NestingParametri(BaseModel):
    padding_mm: int = 1  # 🚀 OTTIMIZZAZIONE: Padding ultra-ottimizzato 1mm
    min_distance_mm: int = 1  # 🚀 OTTIMIZZAZIONE: Distanza ultra-ottimizzata 1mm

class NestingRequest(BaseModel):
    odl_ids: List[str]
    autoclave_ids: List[str]
    parametri: NestingParametri = NestingParametri()

# 🆕 NUOVO: Modello specifico per multi-batch che non richiede autoclave_ids
class NestingMultiRequest(BaseModel):
    odl_ids: List[str]
    parametri: NestingParametri = NestingParametri()

class NestingResponse(BaseModel):
    batch_id: Optional[str] = ""  # ✅ FIX: Permette None e fornisce default vuoto
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
            ODL.status == "Attesa Cura"  # Corretto: maiuscolo come nel database
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
                        "peso": getattr(odl.tool, 'peso', 10.0),  # Default se peso non esiste
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
        
        # ✅ Autoclavi disponibili: utilizzo solo DISPONIBILE (enum corretto)
        autoclavi_disponibili = []
        try:
            autoclavi_enum = db.query(Autoclave).filter(
                Autoclave.stato == StatoAutoclaveEnum.DISPONIBILE
            ).all()
            autoclavi_disponibili.extend(autoclavi_enum)
            logger.info(f"🔍 Trovate {len(autoclavi_enum)} autoclavi con stato 'DISPONIBILE'")
        except Exception as e:
            logger.warning(f"⚠️ Errore query autoclavi DISPONIBILE: {str(e)}")
        
        logger.info(f"🔍 Totale autoclavi disponibili: {len(autoclavi_disponibili)}")
        
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

@router.get("/data-test", response_model=NestingDataResponse,
            summary="🔍 TEST: Ottiene dati per il nesting (con qualsiasi status ODL)")
def get_nesting_data_test(db: Session = Depends(get_db)):
    """
    🔍 ENDPOINT TEST DATI NESTING
    =============================
    
    Versione di test che recupera ODL con qualsiasi status per verificare il funzionamento
    """
    try:
        logger.info("🧪 TEST: Recupero dati per interfaccia nesting...")
        
        # Test semplificato - solo conteggi
        total_odl = db.query(ODL).count()
        total_autoclavi = db.query(Autoclave).count()
        
        logger.info(f"🧪 Conteggi: {total_odl} ODL, {total_autoclavi} autoclavi")
        
        # Lista vuota per ora
        odl_list = []
        autoclavi_list = []
        
        statistiche = {
            "total_odl_in_attesa": 0,
            "total_autoclavi_disponibili": 0,
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
        
        logger.info(f"🧪 TEST: Risposta preparata con successo")
        return response
        
    except Exception as e:
        logger.error(f"❌ Errore nel test recupero dati nesting: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore nel test recupero dati per nesting: {str(e)}"
        )

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
            min_distance_mm=request.parametri.min_distance_mm
        )
        
        # Inizializza servizio robusto
        nesting_service = NestingService()
        
        # Genera nesting con robustezza
        result = nesting_service.generate_robust_nesting(
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
            batch_id=result.get('batch_id') or '',
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

@router.get("/{batch_id}", response_model=BatchNestingResponse, 
            summary="Ottiene un batch nesting specifico")
def read_batch_nesting(batch_id: str, db: Session = Depends(get_db)):
    """
    Recupera un batch nesting specifico tramite il suo UUID.
    Include tutte le informazioni dettagliate e le statistiche.
    """
    db_batch = db.query(BatchNesting).options(
        joinedload(BatchNesting.autoclave)
    ).filter(BatchNesting.id == batch_id).first()
    
    if db_batch is None:
        logger.warning(f"Tentativo di accesso a batch nesting inesistente: {batch_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Batch nesting con ID {batch_id} non trovato"
        )
    
    # ✅ Aggiorna l'efficienza prima di restituire la risposta
    db_batch.update_efficiency()
    db.commit()
    
    # Aggiunge proprietà calcolate per la risposta
    response_data = db_batch.__dict__.copy()
    response_data['stato_descrizione'] = db_batch.stato_descrizione
    response_data['area_pct'] = db_batch.area_pct
    response_data['vacuum_util_pct'] = db_batch.vacuum_util_pct  
    response_data['efficiency_score'] = db_batch.efficiency_score
    response_data['efficiency_level'] = db_batch.efficiency_level
    response_data['efficiency_color_class'] = db_batch.efficiency_color_class
    
    return db_batch

@router.get("/result/{batch_id}", summary="Ottiene risultati batch nesting, supporta multi-batch")
def get_batch_result(
    batch_id: str, 
    multi: bool = False,
    db: Session = Depends(get_db)
):
    """
    Endpoint per risultati batch nesting con supporto multi-batch.
    
    Args:
        batch_id: ID del batch principale
        multi: Se True, ritorna tutti i batch correlati nell'esecuzione
        
    Returns:
        MultiBatchResponse se multi=True, altrimenti BatchNestingResult singolo
    """
    logger.info(f"📊 Richiesta risultati batch: {batch_id}, multi={multi}")
    
    # Carica il batch principale
    main_batch = db.query(BatchNesting).options(
        joinedload(BatchNesting.autoclave)
    ).filter(BatchNesting.id == batch_id).first()
    
    if not main_batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch nesting con ID {batch_id} non trovato"
        )
    
    def format_batch_result(batch: BatchNesting) -> dict:
        """Formatta un batch per la risposta API"""
        # Calcola metriche se necessarie
        if batch.configurazione_json and 'tool_positions' in batch.configurazione_json:
            tool_positions = batch.configurazione_json['tool_positions']
            total_area_used = sum(
                tool.get('width', 0) * tool.get('height', 0) 
                for tool in tool_positions
            )
            total_weight = sum(tool.get('peso', 0) for tool in tool_positions)
            
            # Area autoclave in mm²
            autoclave_area = 0
            if batch.autoclave:
                autoclave_area = batch.autoclave.lunghezza * batch.autoclave.larghezza_piano
                
            efficiency_percentage = (
                (total_area_used / autoclave_area * 100) if autoclave_area > 0 else 0
            )
        else:
            total_area_used = 0
            total_weight = 0  
            efficiency_percentage = 0
        
        return {
            "id": batch.id,
            "nome": batch.nome,
            "stato": batch.stato,
            "autoclave_id": batch.autoclave_id,
            "autoclave": {
                "id": batch.autoclave.id,
                "nome": batch.autoclave.nome,
                "lunghezza": batch.autoclave.lunghezza,
                "larghezza_piano": batch.autoclave.larghezza_piano,
                "codice": batch.autoclave.codice,
                "produttore": getattr(batch.autoclave, 'produttore', None)
            } if batch.autoclave else None,
            "odl_ids": batch.odl_ids or [],
            "configurazione_json": batch.configurazione_json,
            "parametri": batch.parametri,
            "created_at": batch.created_at.isoformat() if batch.created_at else None,
            "updated_at": batch.updated_at.isoformat() if batch.updated_at else None,
            "numero_nesting": batch.numero_nesting,
            "peso_totale_kg": batch.peso_totale_kg,
            "area_totale_utilizzata": batch.area_totale_utilizzata,
            "valvole_totali_utilizzate": batch.valvole_totali_utilizzate,
            "note": batch.note,
            "metrics": {
                "efficiency_percentage": efficiency_percentage,
                "total_area_used_mm2": total_area_used,
                "total_weight_kg": total_weight
            }
        }
    
    if multi:
        # Modalità multi-batch: trova tutti i batch correlati
        batch_results = [format_batch_result(main_batch)]
        
        # 🔧 FIX MULTI-BATCH v2: Ricerca batch correlati con finestra progressiva
        if main_batch.created_at:
            from datetime import timedelta
            
            # Prima prova: finestra stretta per multi-batch (±1 minuto)
            time_window = timedelta(minutes=1)
            start_time = main_batch.created_at - time_window
            end_time = main_batch.created_at + time_window
            
            logger.info(f"🔍 Ricerca batch correlati per {main_batch.id} nel periodo {start_time} - {end_time}")
            
            related_batches = db.query(BatchNesting).options(
                joinedload(BatchNesting.autoclave)
            ).filter(
                BatchNesting.id != main_batch.id,  # Escludi il batch principale
                BatchNesting.created_at >= start_time,
                BatchNesting.created_at <= end_time,
                BatchNesting.stato.in_(['sospeso', 'confermato'])  # Solo batch validi
            ).all()
            
            logger.info(f"🔗 Trovati {len(related_batches)} batch correlati (±1min) per {main_batch.id}")
            
            # Log dettagliato dei batch trovati
            for rb in related_batches:
                logger.info(f"   - Batch {rb.id[:8]}... | Autoclave: {rb.autoclave_id} | ODL: {rb.odl_ids}")
            
            # Se non troviamo batch nella finestra stretta, espandi progressivamente
            if not related_batches:
                logger.info("🔍 Espansione ricerca a ±5 minuti")
                expanded_window = timedelta(minutes=5)
                start_time = main_batch.created_at - expanded_window
                end_time = main_batch.created_at + expanded_window
                
                related_batches = db.query(BatchNesting).options(
                    joinedload(BatchNesting.autoclave)
                ).filter(
                    BatchNesting.id != main_batch.id,
                    BatchNesting.created_at >= start_time,
                    BatchNesting.created_at <= end_time,
                    BatchNesting.stato.in_(['sospeso', 'confermato'])
                ).limit(20).all()  # Limite ragionevole
                
                logger.info(f"🔗 Trovati {len(related_batches)} batch correlati (±5min) per {main_batch.id}")
            
            # Verifica che i batch abbiano autoclavi diverse (caratteristica del multi-batch)
            if related_batches:
                main_autoclave_id = main_batch.autoclave_id
                truly_related = []
                
                for rb in related_batches:
                    # Se le autoclavi sono diverse, potrebbero essere batch multi-autoclave
                    if rb.autoclave_id != main_autoclave_id:
                        truly_related.append(rb)
                
                related_batches = truly_related
                logger.info(f"🎯 Filtrati {len(related_batches)} batch con autoclavi diverse (multi-batch)")
            
            # Aggiungi i batch correlati
            for related_batch in related_batches:
                batch_results.append(format_batch_result(related_batch))
        
        # Ordina per autoclave_id per una visualizzazione coerente
        batch_results.sort(key=lambda x: x['autoclave_id'])
        
        return {
            "batch_results": batch_results,
            "total_batches": len(batch_results),
            "execution_id": f"exec_{main_batch.created_at.strftime('%Y%m%d_%H%M%S')}" if main_batch.created_at else None
        }
    else:
        # Modalità singolo batch
        return format_batch_result(main_batch)

@router.get("/{batch_id}/full", summary="Ottiene un batch nesting con tutte le informazioni")
def read_batch_nesting_full(batch_id: str, db: Session = Depends(get_db)):
    """
    Recupera un batch nesting con tutte le informazioni dettagliate,
    inclusi autoclave, ODL esclusi e motivi di esclusione.
    """
    # Recupera il batch con le relazioni
    db_batch = db.query(BatchNesting)\
        .filter(BatchNesting.id == batch_id)\
        .first()
    
    if db_batch is None:
        logger.warning(f"Tentativo di accesso a batch nesting inesistente: {batch_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Batch nesting con ID {batch_id} non trovato"
        )
    
    # Recupera l'autoclave associata
    autoclave = db.query(Autoclave).filter(Autoclave.id == db_batch.autoclave_id).first()
    
    # Recupera il NestingResult associato (se esiste) per gli ODL esclusi
    nesting_result = db.query(NestingResult).filter(NestingResult.batch_id == batch_id).first()
    
    # Prepara la risposta completa
    response = {
        "id": db_batch.id,
        "nome": db_batch.nome,
        "stato": db_batch.stato,
        "autoclave_id": db_batch.autoclave_id,
        "odl_ids": db_batch.odl_ids,
        "configurazione_json": db_batch.configurazione_json,
        "parametri": db_batch.parametri,
        "numero_nesting": db_batch.numero_nesting,
        "peso_totale_kg": db_batch.peso_totale_kg,
        "area_totale_utilizzata": db_batch.area_totale_utilizzata,
        "valvole_totali_utilizzate": db_batch.valvole_totali_utilizzate,
        "note": db_batch.note,
        "creato_da_utente": db_batch.creato_da_utente,
        "creato_da_ruolo": db_batch.creato_da_ruolo,
        "confermato_da_utente": db_batch.confermato_da_utente,
        "confermato_da_ruolo": db_batch.confermato_da_ruolo,
        "data_conferma": db_batch.data_conferma,
        "created_at": db_batch.created_at,
        "updated_at": db_batch.updated_at,
        "stato_descrizione": db_batch.stato_descrizione,
        
        # Informazioni autoclave
        "autoclave": {
            "id": autoclave.id if autoclave else None,
            "nome": autoclave.nome if autoclave else None,
            "larghezza_piano": autoclave.larghezza_piano if autoclave else None,
            "lunghezza": autoclave.lunghezza if autoclave else None,
            "codice": autoclave.codice if autoclave else None,
            "produttore": autoclave.produttore if autoclave else None,
        } if autoclave else None,
        
        # ODL esclusi dal nesting (se disponibili)
        "odl_esclusi": nesting_result.motivi_esclusione if nesting_result and nesting_result.motivi_esclusione else []
    }
    
    return response

@router.put("/{batch_id}", response_model=BatchNestingResponse, 
            summary="Aggiorna un batch nesting")
def update_batch_nesting(
    batch_id: str, 
    batch_update: BatchNestingUpdate, 
    db: Session = Depends(get_db)
):
    """
    🔒 AGGIORNA BATCH NESTING
    =========================
    
    Aggiorna i dati di un batch nesting esistente.
    Solo i campi inclusi nella richiesta verranno aggiornati.
    
    **PROTEZIONE:**
    - Solo batch in stato SOSPESO possono essere aggiornati
    - Batch confermati, caricati o in corso non possono essere modificati
    
    Permette di aggiornare:
    - Nome del batch
    - Stato del batch  
    - Lista degli ODL
    - Parametri di nesting
    - Configurazione del layout
    - Note
    - Informazioni di conferma
    """
    db_batch = db.query(BatchNesting).filter(BatchNesting.id == batch_id).first()
    
    if db_batch is None:
        logger.warning(f"Tentativo di aggiornamento di batch nesting inesistente: {batch_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Batch nesting con ID {batch_id} non trovato"
        )
    
    # 🔒 PROTEZIONE: Solo batch SOSPESO possono essere aggiornati
    if db_batch.stato != StatoBatchNestingEnum.SOSPESO.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Impossibile aggiornare batch: solo batch in stato 'sospeso' possono essere modificati. Stato attuale: {db_batch.stato}"
        )
    
    try:
        # Salva i valori precedenti per il logging
        old_state = db_batch.stato
        
        # Aggiornamento dei campi presenti nella richiesta
        update_data = batch_update.model_dump(exclude_unset=True)
        modified_fields = []
        
        for key, value in update_data.items():
            old_value = getattr(db_batch, key)
            
            # Gestione speciale per oggetti Pydantic nei campi JSON
            if key in ['parametri', 'configurazione_json'] and value is not None:
                if hasattr(value, 'model_dump'):
                    value = value.model_dump()
            
            if old_value != value:
                modified_fields.append(f"{key}: {old_value} → {value}")
                setattr(db_batch, key, value)
        
        # Gestione speciale per il cambio di stato a "CONFERMATO"
        if (batch_update.stato == StatoBatchNestingEnumSchema.CONFERMATO and 
            old_state != StatoBatchNestingEnumSchema.CONFERMATO.value):
            db_batch.data_conferma = datetime.now()
            if batch_update.confermato_da_utente:
                db_batch.confermato_da_utente = batch_update.confermato_da_utente
            if batch_update.confermato_da_ruolo:
                db_batch.confermato_da_ruolo = batch_update.confermato_da_ruolo
        
        db.commit()
        db.refresh(db_batch)
        
        # Log dell'evento se ci sono state modifiche
        if modified_fields:
            modification_details = f"Campi modificati: {', '.join(modified_fields)}"
            logger.info(f"Batch nesting {batch_id} aggiornato: {modification_details}")
        
        return db_batch
        
    except Exception as e:
        db.rollback()
        logger.error(f"Errore durante l'aggiornamento del batch nesting {batch_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Si è verificato un errore durante l'aggiornamento del batch nesting: {str(e)}"
        )

@router.delete("/{batch_id}", status_code=status.HTTP_204_NO_CONTENT, 
               summary="Elimina un batch nesting")
def delete_batch_nesting(batch_id: str, db: Session = Depends(get_db)):
    """
    Elimina un batch nesting esistente.
    
    ⚠️ **Attenzione**: Questa operazione è irreversibile.
    Il batch può essere eliminato solo se è in stato "SOSPESO".
    """
    db_batch = db.query(BatchNesting).filter(BatchNesting.id == batch_id).first()
    
    if db_batch is None:
        logger.warning(f"Tentativo di eliminazione di batch nesting inesistente: {batch_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Batch nesting con ID {batch_id} non trovato"
        )
    
    # Verifica che il batch sia in stato modificabile
    if db_batch.stato != StatoBatchNestingEnum.SOSPESO.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Impossibile eliminare il batch nesting in stato '{db_batch.stato}'. "
                   f"Solo i batch in stato 'sospeso' possono essere eliminati."
        )
    
    try:
        db.delete(db_batch)
        db.commit()
        logger.info(f"Batch nesting {batch_id} eliminato con successo")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Errore durante l'eliminazione del batch nesting {batch_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Si è verificato un errore durante l'eliminazione del batch nesting: {str(e)}"
        )

@router.get("/{batch_id}/statistics", summary="Ottiene statistiche dettagliate del batch")
def get_batch_statistics(batch_id: str, db: Session = Depends(get_db)):
    """
    Recupera statistiche dettagliate per un batch nesting specifico.
    Include informazioni sui nesting results collegati e metriche di efficienza.
    """
    db_batch = db.query(BatchNesting).filter(BatchNesting.id == batch_id).first()
    
    if db_batch is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Batch nesting con ID {batch_id} non trovato"
        )
    
    # Calcola statistiche aggiuntive
    statistics = {
        "batch_id": batch_id,
        "nome": db_batch.nome,
        "stato": db_batch.stato,
        "autoclave_id": db_batch.autoclave_id,
        "numero_odl": len(db_batch.odl_ids) if db_batch.odl_ids else 0,
        "numero_nesting": db_batch.numero_nesting,
        "peso_totale_kg": db_batch.peso_totale_kg,
        "area_totale_utilizzata": db_batch.area_totale_utilizzata,
        "valvole_totali_utilizzate": db_batch.valvole_totali_utilizzate,
        "efficienza_media": db_batch.efficienza_media,
        "created_at": db_batch.created_at,
        "updated_at": db_batch.updated_at,
        "data_conferma": db_batch.data_conferma
    }
    
    return statistics

@router.patch("/{batch_id}/confirm", response_model=BatchNestingResponse,
              summary="🔄 Conferma batch - Transizione SOSPESO → CONFERMATO")
def confirm_batch_nesting(
    batch_id: str, 
    confermato_da_utente: str = Query(..., description="ID dell'utente che conferma il batch"),
    confermato_da_ruolo: str = Query(..., description="Ruolo dell'utente che conferma (Responsabile o Autoclavista)"),
    db: Session = Depends(get_db)
):
    """
    🔄 CONFERMA BATCH NESTING
    =========================
    
    Transizione: SOSPESO → CONFERMATO
    
    **Protezioni:**
    - Solo batch in stato SOSPESO possono essere confermati
    - Solo utenti con ruolo 'Responsabile' o 'Autoclavista' possono confermare
    
    **Aggiornamenti:**
    - Stato → CONFERMATO
    - data_conferma → timestamp attuale
    - confermato_da_utente → ID utente
    - confermato_da_ruolo → ruolo utente
    """
    # Validazione ruolo
    if confermato_da_ruolo not in ["Responsabile", "Autoclavista", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Accesso negato: solo utenti 'Responsabile' o 'Autoclavista' possono confermare batch. Ruolo attuale: {confermato_da_ruolo}"
        )
    
    # Recupera batch
    db_batch = db.query(BatchNesting).filter(BatchNesting.id == batch_id).first()
    
    if db_batch is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Batch nesting con ID {batch_id} non trovato"
        )
    
    # Validazione transizione di stato
    if db_batch.stato != StatoBatchNestingEnum.SOSPESO.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transizione non valida: batch deve essere in stato 'sospeso' per essere confermato. Stato attuale: {db_batch.stato}"
        )
    
    try:
        # Aggiornamento stato e metadati batch
        db_batch.stato = StatoBatchNestingEnum.CONFERMATO.value
        db_batch.confermato_da_utente = confermato_da_utente
        db_batch.confermato_da_ruolo = confermato_da_ruolo
        db_batch.data_conferma = datetime.now()
        
        # 🆕 AGGIORNAMENTO AUTOMATICO STATO ODL: CONFERMATO → CURA
        from models.odl import ODL
        from models.autoclave import Autoclave, StatoAutoclaveEnum
        
        if db_batch.odl_ids:
            updated_odl_count = 0
            for odl_id in db_batch.odl_ids:
                db_odl = db.query(ODL).filter(ODL.id == odl_id).first()
                if db_odl and db_odl.status == "Attesa Cura":
                    db_odl.status = "Cura"
                    updated_odl_count += 1
            
            logger.info(f"📋 Aggiornati {updated_odl_count} ODL da 'Attesa Cura' a 'Cura' per batch {batch_id}")
        
        # 🆕 AGGIORNAMENTO AUTOMATICO STATO AUTOCLAVE: DISPONIBILE → IN_USO
        db_autoclave = db.query(Autoclave).filter(Autoclave.id == db_batch.autoclave_id).first()
        if db_autoclave and db_autoclave.stato == StatoAutoclaveEnum.DISPONIBILE:
            db_autoclave.stato = StatoAutoclaveEnum.IN_USO
            logger.info(f"🏭 Autoclave {db_autoclave.nome} (ID: {db_autoclave.id}) aggiornata da 'DISPONIBILE' a 'IN_USO' per batch {batch_id}")
        
        db.commit()
        db.refresh(db_batch)
        
        logger.info(f"✅ Batch {batch_id} confermato da {confermato_da_utente} ({confermato_da_ruolo})")
        return db_batch
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Errore durante conferma batch {batch_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante la conferma del batch: {str(e)}"
        )

@router.patch("/{batch_id}/conferma", response_model=BatchNestingResponse,
              summary="⚠️ DEPRECATO: usa /confirm - Conferma batch (legacy)")
def conferma_batch_nesting_legacy(
    batch_id: str,
    confermato_da_utente: str = Query(..., description="ID dell'utente che conferma il batch"),
    confermato_da_ruolo: str = Query(..., description="Ruolo dell'utente che conferma"),
    db: Session = Depends(get_db)
):
    """
    ⚠️ ENDPOINT LEGACY - USA /confirm
    =================================
    
    Questo endpoint è deprecato. Usa invece: PATCH /{batch_id}/confirm
    Mantiene compatibilità con il frontend esistente.
    """
    logger.warning(f"⚠️ Uso endpoint legacy /conferma per batch {batch_id} - migrare a /confirm")
    
    # Forward alla nuova implementazione
    return confirm_batch_nesting(batch_id, confermato_da_utente, confermato_da_ruolo, db)

@router.patch("/{batch_id}/load", response_model=BatchNestingResponse,
              summary="🔄 Carica batch - Transizione CONFERMATO → LOADED")
def load_batch_nesting(
    batch_id: str,
    caricato_da_utente: str = Query(..., description="ID dell'utente che carica il batch"),
    caricato_da_ruolo: str = Query(..., description="Ruolo dell'utente che carica (Responsabile o Autoclavista)"),
    db: Session = Depends(get_db)
):
    """
    🔄 CARICA BATCH IN AUTOCLAVE
    =============================
    
    Transizione: CONFERMATO → LOADED
    
    **Protezioni:**
    - Solo batch in stato CONFERMATO possono essere caricati
    - Solo utenti con ruolo 'Responsabile' o 'Autoclavista' possono caricare
    
    **Aggiornamenti:**
    - Stato → LOADED
    - updated_at → timestamp attuale
    - Metadati utente aggiornati
    """
    # Validazione ruolo
    if caricato_da_ruolo not in ["Responsabile", "Autoclavista", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Accesso negato: solo utenti 'Responsabile' o 'Autoclavista' possono caricare batch. Ruolo attuale: {caricato_da_ruolo}"
        )
    
    # Recupera batch
    db_batch = db.query(BatchNesting).filter(BatchNesting.id == batch_id).first()
    
    if db_batch is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch nesting con ID {batch_id} non trovato"
        )
    
    # Validazione transizione di stato
    if db_batch.stato != StatoBatchNestingEnum.CONFERMATO.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transizione non valida: batch deve essere in stato 'confermato' per essere caricato. Stato attuale: {db_batch.stato}"
        )
    
    try:
        # Aggiornamento stato
        db_batch.stato = StatoBatchNestingEnum.LOADED.value
        
        db.commit()
        db.refresh(db_batch)
        
        logger.info(f"✅ Batch {batch_id} caricato da {caricato_da_utente} ({caricato_da_ruolo})")
        return db_batch
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Errore durante caricamento batch {batch_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante il caricamento del batch: {str(e)}"
        )

@router.patch("/{batch_id}/cure", response_model=BatchNestingResponse,
              summary="🔄 Avvia cura - Transizione LOADED → CURED")  
def cure_batch_nesting(
    batch_id: str,
    avviato_da_utente: str = Query(..., description="ID dell'utente che avvia la cura"),
    avviato_da_ruolo: str = Query(..., description="Ruolo dell'utente che avvia la cura (Responsabile o Autoclavista)"),
    db: Session = Depends(get_db)
):
    """
    🔄 AVVIA CICLO DI CURA
    ======================
    
    Transizione: LOADED → CURED
    
    **Protezioni:**
    - Solo batch in stato LOADED possono avviare la cura
    - Solo utenti con ruolo 'Responsabile' o 'Autoclavista' possono avviare
    
    **Aggiornamenti:**
    - Stato → CURED
    - updated_at → timestamp attuale
    - Metadati utente aggiornati
    """
    # Validazione ruolo
    if avviato_da_ruolo not in ["Responsabile", "Autoclavista", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Accesso negato: solo utenti 'Responsabile' o 'Autoclavista' possono avviare la cura. Ruolo attuale: {avviato_da_ruolo}"
        )
    
    # Recupera batch
    db_batch = db.query(BatchNesting).filter(BatchNesting.id == batch_id).first()
    
    if db_batch is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch nesting con ID {batch_id} non trovato"
        )
    
    # Validazione transizione di stato
    if db_batch.stato != StatoBatchNestingEnum.LOADED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transizione non valida: batch deve essere in stato 'loaded' per avviare la cura. Stato attuale: {db_batch.stato}"
        )
    
    try:
        # Aggiornamento stato
        db_batch.stato = StatoBatchNestingEnum.CURED.value
        
        db.commit()
        db.refresh(db_batch)
        
        logger.info(f"✅ Cura avviata per batch {batch_id} da {avviato_da_utente} ({avviato_da_ruolo})")
        return db_batch
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Errore durante avvio cura batch {batch_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante l'avvio della cura: {str(e)}"
        )

@router.patch("/{batch_id}/terminate", response_model=BatchNestingResponse,
              summary="🔄 Termina batch - Transizione CURED → TERMINATO")
def terminate_batch_nesting(
    batch_id: str,
    terminato_da_utente: str = Query(..., description="ID dell'utente che termina il batch"),
    terminato_da_ruolo: str = Query(..., description="Ruolo dell'utente che termina (Responsabile o Autoclavista)"),
    db: Session = Depends(get_db)
):
    """
    🔄 TERMINA BATCH NESTING
    ========================
    
    Transizione: CURED → TERMINATO
    
    **Protezioni:**
    - Solo batch in stato CURED possono essere terminati
    - Solo utenti con ruolo 'Responsabile' o 'Autoclavista' possono terminare
    
    **Aggiornamenti:**
    - Stato → TERMINATO
    - data_completamento → timestamp attuale
    - durata_ciclo_minuti → calcolata dalla data_conferma
    - updated_at → timestamp attuale
    """
    # Validazione ruolo
    if terminato_da_ruolo not in ["Responsabile", "Autoclavista", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Accesso negato: solo utenti 'Responsabile' o 'Autoclavista' possono terminare batch. Ruolo attuale: {terminato_da_ruolo}"
        )
    
    # Recupera batch
    db_batch = db.query(BatchNesting).filter(BatchNesting.id == batch_id).first()
    
    if db_batch is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch nesting con ID {batch_id} non trovato"
        )
    
    # Validazione transizione di stato
    if db_batch.stato != StatoBatchNestingEnum.CURED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transizione non valida: batch deve essere in stato 'cured' per essere terminato. Stato attuale: {db_batch.stato}"
        )
    
    try:
        # Aggiornamento stato e completamento batch
        db_batch.stato = StatoBatchNestingEnum.TERMINATO.value
        db_batch.data_completamento = datetime.now()
        
        # Calcola durata ciclo se abbiamo data_conferma
        if db_batch.data_conferma:
            durata = db_batch.data_completamento - db_batch.data_conferma
            db_batch.durata_ciclo_minuti = int(durata.total_seconds() / 60)
        
        # 🆕 AGGIORNAMENTO AUTOMATICO STATO ODL: TERMINATO → FINITO
        from models.odl import ODL
        from models.autoclave import Autoclave, StatoAutoclaveEnum
        
        if db_batch.odl_ids:
            updated_odl_count = 0
            for odl_id in db_batch.odl_ids:
                db_odl = db.query(ODL).filter(ODL.id == odl_id).first()
                if db_odl and db_odl.status == "Cura":
                    db_odl.status = "Finito"
                    updated_odl_count += 1
            
            logger.info(f"📋 Aggiornati {updated_odl_count} ODL da 'Cura' a 'Finito' per batch {batch_id}")
        
        # 🆕 AGGIORNAMENTO AUTOMATICO STATO AUTOCLAVE: IN_USO → DISPONIBILE
        db_autoclave = db.query(Autoclave).filter(Autoclave.id == db_batch.autoclave_id).first()
        if db_autoclave and db_autoclave.stato == StatoAutoclaveEnum.IN_USO:
            db_autoclave.stato = StatoAutoclaveEnum.DISPONIBILE
            logger.info(f"🏭 Autoclave {db_autoclave.nome} (ID: {db_autoclave.id}) aggiornata da 'IN_USO' a 'DISPONIBILE' per batch {batch_id}")
        
        db.commit()
        db.refresh(db_batch)
        
        logger.info(f"✅ Batch {batch_id} terminato da {terminato_da_utente} ({terminato_da_ruolo})")
        return db_batch
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Errore durante terminazione batch {batch_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante la terminazione del batch: {str(e)}"
        )

# ========== FINE NUOVI ENDPOINT ==========

# ========== ENDPOINT SOLVE v1.4.12-DEMO ==========

from schemas.batch_nesting import (
    NestingSolveRequest, 
    NestingSolveResponse, 
    NestingMetricsResponse,
    NestingToolPosition,
    NestingExcludedODL
)
from services.nesting.solver import NestingModel, NestingParameters, ToolInfo, AutoclaveInfo

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
    
    **Parametri:**
    - **autoclave_id**: ID dell'autoclave da utilizzare  
    - **odl_ids**: Lista degli ID degli ODL da processare (se None, usa tutti quelli disponibili)
    - **padding_mm**: Padding tra i tool (5-50mm, default: 20)
    - **min_distance_mm**: Distanza minima dai bordi (5-30mm, default: 15)
    - **vacuum_lines_capacity**: Capacità massima linee vuoto (1-50, default: 10)
    - **allow_heuristic**: Abilita heuristica RRGH (default: False)
    - **timeout_override**: Override timeout in secondi (30-300s, default: adaptivo)
    - **heavy_piece_threshold_kg**: Soglia peso per constraint posizionamento (default: 50kg)
    
    **Ritorna:**
    - Layout JSON con posizioni precise dei tool
    - Metriche dettagliate inclusi efficiency_score, time_solver_ms, fallback_used, heuristic_iters
    - Lista ODL esclusi con motivi specifici
    - Stato algoritmo utilizzato (CP-SAT_OPTIMAL, FALLBACK_GREEDY, etc.)
    
    **Algoritmi:**
    1. **CP-SAT principale**: Ottimizzazione constraint programming con nuovo obiettivo multi-termine
    2. **Heuristica RRGH**: Ruin & Recreate Goal-Driven per miglioramento (se abilitata)
    3. **Fallback greedy**: First-fit decreasing se CP-SAT fallisce/timeout
    4. **Pre-filtraggio**: Esclusione automatica ODL incompatibili
    """
    try:
        logger.info(f"🚀 Avvio nesting solver v1.4.12-DEMO per autoclave {request.autoclave_id}")
        
        # 1. Verifica autoclave
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
        
        # 2. Recupera ODL da processare
        if request.odl_ids:
            # ODL specifici richiesti - ma solo se in stato corretto
            odl_query = db.query(ODL).filter(
                ODL.id.in_(request.odl_ids),
                ODL.status == "Attesa Cura"  # ✅ FIX: Aggiungo filtro status anche per ODL specifici
            )
        else:
            # Tutti gli ODL in attesa di cura
            odl_query = db.query(ODL).filter(ODL.status == "Attesa Cura")  # ✅ FIX: Cambio da "Preparazione" a "Attesa Cura"
        
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
                    invalid=False,  # 🎯 NUOVO v1.4.16-DEMO
                    rotation_used=False,  # 🔄 NUOVO v1.4.17-DEMO
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
        
        # 3. Configura parametri solver
        solver_params = NestingParameters(
            padding_mm=int(request.padding_mm),  # 🔧 FIX: Converte float to int
            min_distance_mm=int(request.min_distance_mm),  # 🔧 FIX: Converte float to int
            vacuum_lines_capacity=request.vacuum_lines_capacity or autoclave.num_linee_vuoto,
            allow_heuristic=request.allow_heuristic,
            timeout_override=request.timeout_override,
            heavy_piece_threshold_kg=request.heavy_piece_threshold_kg
        )
        
        # 4. Esegui nesting
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
        
        # 5. Converti risultati in formato API
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
                plane=1,  # Piano principale
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
        
        # 🔍 NUOVO v1.4.14: Calcola riassunto motivi di esclusione
        excluded_reasons = {}
        for exc in solution.excluded_odls:
            debug_reasons = exc.get('debug_reasons', [])
            if debug_reasons:
                for reason in debug_reasons:
                    excluded_reasons[reason] = excluded_reasons.get(reason, 0) + 1
            else:
                # Fallback su motivo principale se non ci sono debug_reasons
                main_reason = exc.get('motivo', 'unknown')
                excluded_reasons[main_reason] = excluded_reasons.get(main_reason, 0) + 1
        
        # 6. Costruisci metriche
        metrics = NestingMetricsResponse(
            area_utilization_pct=solution.metrics.area_pct,
            vacuum_util_pct=solution.metrics.vacuum_util_pct,
            efficiency_score=solution.metrics.efficiency_score,
            weight_utilization_pct=(solution.metrics.total_weight / autoclave_info.max_weight) * 100.0,
            time_solver_ms=solution.metrics.time_solver_ms,
            fallback_used=solution.metrics.fallback_used,
            heuristic_iters=solution.metrics.heuristic_iters,
            algorithm_status=solution.algorithm_status,
            invalid=solution.metrics.invalid,  # 🎯 NUOVO v1.4.16-DEMO: Campo invalid per overlap
            rotation_used=solution.metrics.rotation_used,  # 🔄 NUOVO v1.4.17-DEMO: Campo rotation_used
            total_area_cm2=sum(layout.width * layout.height for layout in solution.layouts) / 10000.0,
            total_weight_kg=solution.metrics.total_weight,
            vacuum_lines_used=solution.metrics.lines_used,
            pieces_positioned=solution.metrics.positioned_count,
            pieces_excluded=solution.metrics.excluded_count
        )
        
        # 🎯 NUOVO v1.4.16-DEMO: Estrai informazioni overlap se presenti
        overlaps_info = None
        if hasattr(solution, 'overlaps') and solution.overlaps:
            overlaps_info = solution.overlaps
        
        # 7. Costruisci risposta
        response = NestingSolveResponse(
            success=solution.success,
            message=solution.message,
            positioned_tools=positioned_tools,
            excluded_odls=excluded_odls,
            excluded_reasons=excluded_reasons,
            overlaps=overlaps_info,  # 🎯 NUOVO v1.4.16-DEMO: Informazioni overlap
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
                   f"rotazione={solution.metrics.rotation_used}")  # 🔄 NUOVO v1.4.17-DEMO
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"❌ Errore durante nesting solve: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore interno durante la risoluzione del nesting: {str(e)}"
        )

# ========== NUOVO ENDPOINT VALIDAZIONE v1.4.18-DEMO ==========

@router.get("/{batch_id}/validate", 
            summary="🔍 Valida layout nesting v1.4.18-DEMO")
def validate_nesting_layout(
    batch_id: str,
    db: Session = Depends(get_db)
):
    """
    🔍 ENDPOINT VALIDAZIONE LAYOUT v1.4.18-DEMO
    ==========================================
    
    Valida un layout di nesting esistente controllando:
    - **in_bounds**: Tutti i pezzi sono dentro i limiti dell'autoclave
    - **no_overlap**: Nessuna sovrapposizione tra i pezzi  
    - **overlaps**: Lista delle coppie di pezzi che si sovrappongono
    - **scale_ok**: Le proporzioni sono ragionevoli rispetto all'autoclave
    
    **Parametri:**
    - batch_id: ID del batch nesting da validare
    
    **Ritorna:**
    - in_bounds: boolean - tutti i pezzi dentro i limiti
    - no_overlap: boolean - nessuna sovrapposizione
    - overlaps: lista di tuple (idA, idB) con sovrapposizioni
    - scale_ok: boolean - scala ragionevole
    - details: dettagli aggiuntivi della validazione
    """
    try:
        logger.info(f"🔍 Validazione layout per batch {batch_id}")
        
        # Recupera il batch
        batch = db.query(BatchNesting).filter(BatchNesting.id == batch_id).first()
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch {batch_id} non trovato"
            )
        
        # Recupera configurazione JSON
        config_json = batch.configurazione_json
        if not config_json or not config_json.get('tool_positions'):
            return {
                "in_bounds": True,
                "no_overlap": True, 
                "overlaps": [],
                "scale_ok": True,
                "details": "Nessun layout da validare"
            }
        
        # Recupera autoclave
        autoclave = db.query(Autoclave).filter(Autoclave.id == batch.autoclave_id).first()
        if not autoclave:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Autoclave {batch.autoclave_id} non trovata"
            )
        
        tool_positions = config_json['tool_positions']
        autoclave_width = autoclave.larghezza_piano or autoclave.lunghezza or 2000
        autoclave_height = autoclave.larghezza_piano or 1200
        
        # 1. Controllo bounds
        in_bounds = True
        out_of_bounds = []
        
        for tool in tool_positions:
            x, y, w, h = float(tool['x']), float(tool['y']), float(tool['width']), float(tool['height'])
            
            if x < 0 or y < 0 or x + w > autoclave_width or y + h > autoclave_height:
                in_bounds = False
                out_of_bounds.append({
                    'odl_id': tool['odl_id'],
                    'bounds': f"({x},{y}) {w}×{h}",
                    'autoclave_limits': f"{autoclave_width}×{autoclave_height}"
                })
        
        # 2. Controllo overlap
        overlaps = []
        for i, tool_a in enumerate(tool_positions):
            for j, tool_b in enumerate(tool_positions[i+1:], i+1):
                x1, y1, w1, h1 = float(tool_a['x']), float(tool_a['y']), float(tool_a['width']), float(tool_a['height'])
                x2, y2, w2, h2 = float(tool_b['x']), float(tool_b['y']), float(tool_b['width']), float(tool_b['height'])
                
                # Controllo sovrapposizione
                if not (x1 + w1 <= x2 or x2 + w2 <= x1 or y1 + h1 <= y2 or y2 + h2 <= y1):
                    overlaps.append([tool_a['odl_id'], tool_b['odl_id']])
        
        no_overlap = len(overlaps) == 0
        
        # 3. Controllo scala
        total_tool_area = sum(float(tool['width']) * float(tool['height']) for tool in tool_positions)
        autoclave_area = autoclave_width * autoclave_height
        area_ratio = total_tool_area / autoclave_area if autoclave_area > 0 else 0
        
        # Scala OK se i tool occupano tra 1% e 95% dell'autoclave
        scale_ok = 0.01 <= area_ratio <= 0.95
        
        result = {
            "in_bounds": in_bounds,
            "no_overlap": no_overlap,
            "overlaps": overlaps,
            "scale_ok": scale_ok,
            "details": {
                "total_pieces": len(tool_positions),
                "out_of_bounds_pieces": len(out_of_bounds),
                "overlapping_pairs": len(overlaps),
                "area_ratio_pct": area_ratio * 100,
                "autoclave_dimensions": f"{autoclave_width}×{autoclave_height}mm",
                "out_of_bounds_details": out_of_bounds
            }
        }
        
        logger.info(f"✅ Validazione completata: bounds={in_bounds}, overlaps={no_overlap}, scala={scale_ok}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Errore validazione layout {batch_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante la validazione: {str(e)}"
        )

@router.post("/genera-multi", response_model=Dict[str, Any],
             summary="🚀 Genera batch multipli automaticamente per tutte le autoclavi disponibili")
def genera_nesting_multi_batch(
    request: NestingMultiRequest, 
    db: Session = Depends(get_db)
):
    """
    🔧 ENDPOINT MULTI-BATCH AUTOMATICO
    ==================================
    
    Genera automaticamente batch nesting per tutte le autoclavi disponibili:
    
    - **Auto-selezione autoclavi**: Utilizza tutte le autoclavi disponibili nel sistema
    - **Generazione parallela**: Crea un batch per ogni autoclave con gli stessi ODL
    - **Ordinamento per efficienza**: Ordina i risultati per efficienza decrescente
    - **Gestione errori robusta**: Continua anche se qualche autoclave fallisce
    - **Response unified**: Ritorna tutti i batch generati con statistiche aggregate
    
    **Parametri:**
    - odl_ids: Lista degli ID degli ODL da processare
    - parametri: Configurazione algoritmo nesting (usata per tutte le autoclavi)
    
    **Ritorna:**
    - Lista di tutti i batch generati
    - Statistiche aggregate di efficienza
    - Best batch ID (quello con efficienza maggiore)
    - Report di successo/fallimento per ogni autoclave
    """
    
    try:
        logger.info(f"🚀 Avvio generazione multi-batch: {len(request.odl_ids)} ODL")
        
        # 🔍 DEBUG: Log dettagliato input
        logger.info(f"🔍 DEBUG INPUT: ODL IDs: {request.odl_ids}")
        logger.info(f"🔍 DEBUG INPUT: Parametri: padding={request.parametri.padding_mm}mm, min_distance={request.parametri.min_distance_mm}mm")
        
        # Validazione input base
        if not request.odl_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lista ODL non può essere vuota"
            )
        
        # Conversione IDs da string a int
        try:
            odl_ids = [int(id_str) for id_str in request.odl_ids]
            logger.info(f"🔍 DEBUG: ODL IDs convertiti: {odl_ids}")
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"IDs ODL non validi: {str(e)}"
            )
        
        # Recupera tutte le autoclavi disponibili
        from models.autoclave import Autoclave
        logger.info("🔍 DEBUG: Recupero autoclavi disponibili...")
        autoclavi_disponibili = db.query(Autoclave).filter(
            Autoclave.stato == StatoAutoclaveEnum.DISPONIBILE
        ).all()
        
        logger.info(f"🔍 DEBUG: Trovate {len(autoclavi_disponibili)} autoclavi: {[(a.id, a.nome) for a in autoclavi_disponibili]}")
        
        if not autoclavi_disponibili:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nessuna autoclave disponibile per la generazione multi-batch"
            )
        
        logger.info(f"🏭 Trovate {len(autoclavi_disponibili)} autoclavi disponibili")
        
        # Parametri nesting
        parameters = NestingParameters(
            padding_mm=request.parametri.padding_mm,
            min_distance_mm=request.parametri.min_distance_mm
        )
        logger.info(f"🔍 DEBUG: Parametri nesting: {parameters}")
        
        # 🚀 ALGORITMO DISTRIBUZIONE v2.0: Distribuzione ciclica intelligente degli ODL
        logger.info(f"📊 Distribuzione {len(odl_ids)} ODL tra {len(autoclavi_disponibili)} autoclavi")
        
        # Crea distribuzione ciclica: ODL i → autoclave (i % num_autoclavi)
        autoclave_assignments = {}
        for i, odl_id in enumerate(odl_ids):
            autoclave_index = i % len(autoclavi_disponibili)
            target_autoclave_id = autoclavi_disponibili[autoclave_index].id
            
            if target_autoclave_id not in autoclave_assignments:
                autoclave_assignments[target_autoclave_id] = []
            autoclave_assignments[target_autoclave_id].append(odl_id)
        
        # Log della distribuzione
        logger.info("🔍 DEBUG: DISTRIBUZIONE FINALE:")
        for autoclave_id, assigned_odls in autoclave_assignments.items():
            autoclave_nome = next(a.nome for a in autoclavi_disponibili if a.id == autoclave_id)
            logger.info(f"🏭 {autoclave_nome} (ID:{autoclave_id}): ODL {assigned_odls} ({len(assigned_odls)} pezzi)")
        
        # Inizializza servizio
        logger.info("🔍 DEBUG: Inizializzazione servizio nesting...")
        nesting_service = NestingService()
        
        # Genera batch per ogni autoclave
        logger.info("🔍 DEBUG: Avvio generazione batch per ogni autoclave...")
        batch_results = []
        success_count = 0
        error_count = 0
        
        for i, autoclave in enumerate(autoclavi_disponibili):
            try:
                logger.info(f"🔍 DEBUG: Processo autoclave {i+1}/{len(autoclavi_disponibili)}: {autoclave.nome}")
                
                # 🎯 DISTRIBUZIONE INTELLIGENTE: Usa solo gli ODL assegnati a questa autoclave
                assigned_odl_ids = autoclave_assignments.get(autoclave.id, [])
                
                if not assigned_odl_ids:
                    logger.info(f"⚠️ Nessun ODL assegnato a {autoclave.nome}, saltando...")
                    batch_results.append({
                        'batch_id': None,
                        'autoclave_id': autoclave.id,
                        'autoclave_nome': autoclave.nome,
                        'efficiency': 0,
                        'total_weight': 0,
                        'positioned_tools': 0,
                        'excluded_odls': 0,
                        'success': False,
                        'message': f'Nessun ODL assegnato a {autoclave.nome}'
                    })
                    error_count += 1
                    continue
                
                logger.info(f"🔄 Generazione batch per {autoclave.nome}: {len(assigned_odl_ids)} ODL assegnati {assigned_odl_ids}")
                
                # 🔧 FIX ALGORITMO: Genera nesting DIRETTAMENTE per questa autoclave specifica
                # Con SOLO gli ODL assegnati alla distribuzione ciclica
                logger.info(f"🔍 DEBUG: Chiamata generate_nesting per autoclave {autoclave.id} con ODL {assigned_odl_ids}")
                
                nesting_result = nesting_service.generate_nesting(
                    db=db,
                    odl_ids=assigned_odl_ids,  # ✅ USA SOLO GLI ODL ASSEGNATI
                    autoclave_id=autoclave.id,
                    parameters=parameters
                )
                
                logger.info(f"🔍 DEBUG: Risultato nesting per {autoclave.nome}: success={nesting_result.success if nesting_result else None}")
                
                # Converti il risultato nel formato atteso
                if nesting_result and nesting_result.success:
                    logger.info(f"🔍 DEBUG: Creazione batch per {autoclave.nome}...")
                    # Crea batch nel database per questa autoclave
                    batch_id = nesting_service._create_robust_batch(db, nesting_result, autoclave.id, parameters)
                    logger.info(f"🔍 DEBUG: Batch creato con ID: {batch_id}")
                    
                    result = {
                        'success': True,
                        'batch_id': batch_id,
                        'efficiency': nesting_result.efficiency,
                        'total_weight': nesting_result.total_weight,
                        'positioned_tools': [
                            {
                                'odl_id': tool.odl_id,
                                'x': tool.x,
                                'y': tool.y,
                                'width': tool.width,
                                'height': tool.height,
                                'peso': tool.peso,
                                'rotated': tool.rotated,
                                'lines_used': tool.lines_used
                            } for tool in nesting_result.positioned_tools
                        ],
                        'excluded_odls': nesting_result.excluded_odls,
                        'message': f'Nesting completato per autoclave {autoclave.nome}'
                    }
                else:
                    logger.warning(f"🔍 DEBUG: Nesting fallito per {autoclave.nome}")
                    result = {
                        'success': False,
                        'batch_id': None,
                        'efficiency': 0,
                        'total_weight': 0,
                        'positioned_tools': [],
                        'excluded_odls': nesting_result.excluded_odls if nesting_result else [],
                        'message': f'Nesting fallito per autoclave {autoclave.nome}: {nesting_result.algorithm_status if nesting_result else "Errore sconosciuto"}'
                    }
                
                if result['success'] and result.get('batch_id'):
                    # Recupera il batch completo per le statistiche
                    logger.info(f"🔍 DEBUG: Recupero batch {result['batch_id']} dal database...")
                    batch = db.query(BatchNesting).filter(
                        BatchNesting.id == result['batch_id']
                    ).first()
                    
                    if batch:
                        batch_info = {
                            'batch_id': result['batch_id'],
                            'autoclave_id': autoclave.id,
                            'autoclave_nome': autoclave.nome,
                            'efficiency': result['efficiency'],
                            'total_weight': result['total_weight'],
                            'positioned_tools': len(result['positioned_tools']),
                            'excluded_odls': len(result['excluded_odls']),
                            'success': True,
                            'message': result['message']
                        }
                        batch_results.append(batch_info)
                        success_count += 1
                        logger.info(f"✅ Batch generato per {autoclave.nome}: {result['batch_id']} (efficienza: {result['efficiency']:.1f}%)")
                    else:
                        logger.warning(f"⚠️ Batch ID {result['batch_id']} non trovato nel database")
                        error_count += 1
                else:
                    logger.warning(f"⚠️ Generazione fallita per {autoclave.nome}: {result['message']}")
                    batch_results.append({
                        'batch_id': None,
                        'autoclave_id': autoclave.id,
                        'autoclave_nome': autoclave.nome,
                        'efficiency': 0,
                        'total_weight': 0,
                        'positioned_tools': 0,
                        'excluded_odls': len(assigned_odl_ids),
                        'success': False,
                        'message': result['message']
                    })
                    error_count += 1
                    
            except Exception as autoclave_error:
                logger.error(f"❌ Errore durante generazione per {autoclave.nome}: {str(autoclave_error)}")
                import traceback
                logger.error(f"❌ Stack trace: {traceback.format_exc()}")
                batch_results.append({
                    'batch_id': None,
                    'autoclave_id': autoclave.id,
                    'autoclave_nome': autoclave.nome,
                    'efficiency': 0,
                    'total_weight': 0,
                    'positioned_tools': 0,
                    'excluded_odls': len(autoclave_assignments.get(autoclave.id, [])),
                    'success': False,
                    'message': f"Errore durante generazione: {str(autoclave_error)}"
                })
                error_count += 1
        
        logger.info(f"🔍 DEBUG: Completamento generazione multi-batch: {success_count} successi, {error_count} errori")
        
        # Ordina i risultati per efficienza decrescente
        batch_results.sort(key=lambda x: x['efficiency'], reverse=True)
        
        # Determina il best batch (quello con efficienza maggiore)
        successful_batches = [b for b in batch_results if b['success']]
        best_batch_id = successful_batches[0]['batch_id'] if successful_batches else None
        
        # Statistiche aggregate
        total_efficiency = sum(b['efficiency'] for b in successful_batches)
        avg_efficiency = total_efficiency / len(successful_batches) if successful_batches else 0
        
        # Log del risultato finale
        logger.info(f"🎯 Multi-batch completato: {success_count} successi, {error_count} errori")
        if best_batch_id:
            logger.info(f"🏆 Best batch: {best_batch_id} con efficienza {successful_batches[0]['efficiency']:.1f}%")
        
        # 🔍 DEBUG: Log dettagliato di tutti i batch generati
        logger.info(f"📊 RIEPILOGO BATCH GENERATI:")
        for br in batch_results:
            autoclave_nome = br.get('autoclave_nome', 'N/A')
            batch_id = br.get('batch_id', 'N/A')
            efficiency = br.get('efficiency', 0)
            success = br.get('success', False)
            logger.info(f"   - {autoclave_nome}: {batch_id} | Efficienza: {efficiency:.1f}% | {'✅' if success else '❌'}")
        
        # Prepara risposta
        return {
            'success': success_count > 0,
            'message': f"Generazione multi-batch completata: {success_count} batch creati, {error_count} errori",
            'total_autoclavi': len(autoclavi_disponibili),
            'success_count': success_count,
            'error_count': error_count,
            'best_batch_id': best_batch_id,
            'avg_efficiency': round(avg_efficiency, 2),
            'batch_results': batch_results,
            'execution_id': f"multi_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
        
    except HTTPException:
        # Re-raise HTTPException as is
        raise
    except Exception as e:
        logger.error(f"❌ Errore imprevisto nella generazione multi-batch: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore interno del server: {str(e)}"
        )