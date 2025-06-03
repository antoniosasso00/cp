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
from services.nesting_robustness_improvement import RobustNestingService

class NestingParametri(BaseModel):
    padding_mm: int = 20
    min_distance_mm: int = 15

class NestingRequest(BaseModel):
    odl_ids: List[str]
    autoclave_ids: List[str]
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
    validation_report: Dict[str, Any] = None
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
            min_distance_mm=request.parametri.min_distance_mm,
            priorita_area=False  # ✅ FIX: Valore fisso dato che non è più configurabile dall'utente
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
    Aggiorna i dati di un batch nesting esistente.
    Solo i campi inclusi nella richiesta verranno aggiornati.
    
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

@router.patch("/{batch_id}/conferma", response_model=BatchNestingResponse,
              summary="Conferma il batch e avvia il ciclo di cura")
def conferma_batch_nesting(
    batch_id: str, 
    confermato_da_utente: str = Query(..., description="ID dell'utente che conferma il batch"),
    confermato_da_ruolo: str = Query(..., description="Ruolo dell'utente che conferma"),
    db: Session = Depends(get_db)
):
    """
    Conferma un batch nesting e lo prepara per l'avvio del ciclo di cura.
    
    Cambia lo stato del batch da "sospeso" a "confermato" e registra
    le informazioni dell'utente che ha effettuato la conferma.
    """
    db_batch = db.query(BatchNesting).filter(BatchNesting.id == batch_id).first()
    
    if db_batch is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Batch nesting con ID {batch_id} non trovato"
        )
    
    if db_batch.stato != StatoBatchNestingEnum.SOSPESO.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Il batch deve essere in stato 'sospeso' per essere confermato. Stato attuale: {db_batch.stato}"
        )
    
    try:
        db_batch.stato = StatoBatchNestingEnum.CONFERMATO.value
        db_batch.confermato_da_utente = confermato_da_utente
        db_batch.confermato_da_ruolo = confermato_da_ruolo
        db_batch.data_conferma = datetime.now()
        
        db.commit()
        db.refresh(db_batch)
        
        logger.info(f"Batch nesting {batch_id} confermato da {confermato_da_utente} ({confermato_da_ruolo})")
        return db_batch
        
    except Exception as e:
        db.rollback()
        logger.error(f"Errore durante la conferma del batch nesting {batch_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Si è verificato un errore durante la conferma del batch nesting: {str(e)}"
        )

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
            padding_mm=request.padding_mm,
            min_distance_mm=request.min_distance_mm,
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