import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from api.database import get_db
from models.batch_nesting import BatchNesting, StatoBatchNestingEnum
from models.autoclave import Autoclave, StatoAutoclaveEnum
from models.odl import ODL
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
        
        # Recupera ODL in attesa di cura
        odl_in_attesa = db.query(ODL).filter(
            ODL.status == "Attesa cura"
        ).all()
        
        # Costruisce lista ODL con dettagli
        odl_list = []
        for odl in odl_in_attesa:
            # Lazy loading delle relazioni
            if odl.parte:
                parte_data = {
                    "id": odl.parte.id,
                    "part_number": odl.parte.part_number,
                    "descrizione_breve": odl.parte.descrizione_breve,
                    "num_valvole_richieste": odl.parte.num_valvole_richieste,
                    "ciclo_cura": {
                        "nome": odl.parte.ciclo_cura.nome if odl.parte.ciclo_cura else None,
                        "durata_stasi1": odl.parte.ciclo_cura.durata_stasi1 if odl.parte.ciclo_cura else None,
                        "temperatura_stasi1": odl.parte.ciclo_cura.temperatura_stasi1 if odl.parte.ciclo_cura else None,
                        "pressione_stasi1": odl.parte.ciclo_cura.pressione_stasi1 if odl.parte.ciclo_cura else None
                    } if odl.parte.ciclo_cura else None
                }
            else:
                parte_data = None
            
            if odl.tool:
                tool_data = {
                    "id": odl.tool.id,
                    "part_number_tool": odl.tool.part_number_tool,
                    "descrizione": odl.tool.descrizione,
                    "larghezza_piano": odl.tool.larghezza_piano,
                    "lunghezza_piano": odl.tool.lunghezza_piano,
                    "peso": odl.tool.peso,
                    "disponibile": odl.tool.disponibile
                }
            else:
                tool_data = None
            
            odl_list.append({
                "id": odl.id,
                "status": odl.status,
                "priorita": odl.priorita,
                "created_at": odl.created_at.isoformat() if odl.created_at else None,
                "note": odl.note,
                "parte": parte_data,
                "tool": tool_data
            })
        
        # Recupera autoclavi disponibili
        autoclavi_disponibili = db.query(Autoclave).filter(
            Autoclave.stato == StatoAutoclaveEnum.DISPONIBILE
        ).all()
        
        autoclavi_list = []
        for autoclave in autoclavi_disponibili:
            autoclavi_list.append({
                "id": autoclave.id,
                "nome": autoclave.nome,
                "codice": autoclave.codice,
                "stato": autoclave.stato,
                "lunghezza": autoclave.lunghezza,
                "larghezza_piano": autoclave.larghezza_piano,
                "temperatura_max": autoclave.temperatura_max,
                "pressione_max": autoclave.pressione_max,
                "max_load_kg": autoclave.max_load_kg,
                "num_linee_vuoto": autoclave.num_linee_vuoto,
                "use_secondary_plane": autoclave.use_secondary_plane,
                "produttore": autoclave.produttore,
                "anno_produzione": autoclave.anno_produzione
            })
        
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

@router.get("/{batch_id}", response_model=BatchNestingResponse, 
            summary="Ottiene un batch nesting specifico")
def read_batch_nesting(batch_id: str, db: Session = Depends(get_db)):
    """
    Recupera un batch nesting specifico tramite il suo UUID.
    Include tutte le informazioni dettagliate e le statistiche.
    """
    db_batch = db.query(BatchNesting).filter(BatchNesting.id == batch_id).first()
    if db_batch is None:
        logger.warning(f"Tentativo di accesso a batch nesting inesistente: {batch_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Batch nesting con ID {batch_id} non trovato"
        )
    
    # Aggiunge proprietà calcolate per la risposta
    response_data = db_batch.__dict__.copy()
    response_data['stato_descrizione'] = db_batch.stato_descrizione
    
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
    Conferma il batch nesting e avvia il ciclo di cura.
    
    Effettua le seguenti operazioni in transazione:
    1. Aggiorna il batch da "sospeso" a "confermato"  
    2. Aggiorna l'autoclave a non disponibile
    3. Aggiorna tutti gli ODL da "Attesa Cura" a "Cura"
    4. Registra timestamp di conferma
    
    **Prerequisiti:**
    - Il batch deve essere in stato "sospeso"
    - L'autoclave deve essere disponibile
    - Gli ODL devono essere in stato "Attesa Cura"
    """
    # Recupera il batch con le relazioni
    db_batch = db.query(BatchNesting).filter(BatchNesting.id == batch_id).first()
    if db_batch is None:
        logger.warning(f"Tentativo di conferma di batch inesistente: {batch_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch nesting con ID {batch_id} non trovato"
        )
    
    # Verifica che il batch sia in stato "sospeso"
    if db_batch.stato != StatoBatchNestingEnum.SOSPESO.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Il batch è in stato '{db_batch.stato}' e non può essere confermato. Solo i batch in stato 'sospeso' possono essere confermati."
        )
    
    # Recupera l'autoclave associata
    autoclave = db.query(Autoclave).filter(Autoclave.id == db_batch.autoclave_id).first()
    if not autoclave:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Autoclave con ID {db_batch.autoclave_id} non trovata"
        )
    
    # Verifica che l'autoclave sia disponibile
    if autoclave.stato != StatoAutoclaveEnum.DISPONIBILE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"L'autoclave '{autoclave.nome}' non è disponibile (stato: {autoclave.stato.value})"
        )
    
    # Recupera gli ODL associati al batch
    if not db_batch.odl_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Il batch non contiene ODL da processare"
        )
    
    odl_list = db.query(ODL).filter(ODL.id.in_(db_batch.odl_ids)).all()
    
    if len(odl_list) != len(db_batch.odl_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uno o più ODL del batch non esistono nel database"
        )
    
    # Verifica che tutti gli ODL siano in stato "Attesa Cura"
    odl_non_validi = [odl for odl in odl_list if odl.status != "Attesa Cura"]
    if odl_non_validi:
        stati_non_validi = [f"ODL {odl.id}: {odl.status}" for odl in odl_non_validi]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"I seguenti ODL non sono in stato 'Attesa Cura': {', '.join(stati_non_validi)}"
        )
    
    try:
        # Inizia la transazione
        ora_conferma = datetime.now()
        
        logger.info(f"🚀 Avvio conferma batch {batch_id} con {len(odl_list)} ODL")
        
        # 1. Aggiorna il batch nesting
        db_batch.stato = StatoBatchNestingEnum.CONFERMATO.value
        db_batch.confermato_da_utente = confermato_da_utente
        db_batch.confermato_da_ruolo = confermato_da_ruolo
        db_batch.data_conferma = ora_conferma
        
        logger.info(f"✅ Batch {batch_id} aggiornato a stato 'confermato'")
        
        # 2. Aggiorna l'autoclave (rende non disponibile)
        autoclave.stato = StatoAutoclaveEnum.IN_USO
        
        logger.info(f"✅ Autoclave {autoclave.id} ({autoclave.nome}) aggiornata a stato 'in_uso'")
        
        # 3. Aggiorna tutti gli ODL da "Attesa Cura" a "Cura"
        odl_aggiornati = []
        for odl in odl_list:
            stato_precedente = odl.status
            odl.status = "Cura"
            odl.previous_status = "Attesa Cura"  # Salva stato precedente per eventuale ripristino
            odl_aggiornati.append(odl.id)
            
            # ✅ AGGIUNGO: Log del cambio di stato
            StateTrackingService.registra_cambio_stato(
                db=db,
                odl_id=odl.id,
                stato_precedente=stato_precedente,
                stato_nuovo="Cura",
                responsabile=confermato_da_utente,
                ruolo_responsabile=confermato_da_ruolo,
                note=f"Conferma batch nesting {batch_id}"
            )
            
            # ✅ AGGIUNGO: Log nell'ODLLogService
            ODLLogService.log_cambio_stato(
                db=db,
                odl_id=odl.id,
                stato_precedente=stato_precedente,
                stato_nuovo="Cura",
                responsabile=confermato_da_utente,
                descrizione_aggiuntiva=f"Conferma batch nesting {batch_id}"
            )
        
        logger.info(f"✅ {len(odl_aggiornati)} ODL aggiornati a stato 'Cura': {odl_aggiornati}")
        
        # Commit della transazione
        db.commit()
        db.refresh(db_batch)
        
        logger.info(f"🎉 Conferma batch {batch_id} completata con successo!")
        logger.info(f"📊 Riepilogo:")
        logger.info(f"   - Batch: {db_batch.stato}")
        logger.info(f"   - Autoclave: {autoclave.stato.value}")
        logger.info(f"   - ODL processati: {len(odl_aggiornati)}")
        logger.info(f"   - Confermato da: {confermato_da_utente} ({confermato_da_ruolo})")
        
        return db_batch
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Errore durante la conferma del batch {batch_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Si è verificato un errore durante la conferma del batch: {str(e)}"
        )

@router.patch("/{batch_id}/chiudi", response_model=BatchNestingResponse,
              summary="Chiude il batch e completa il ciclo di cura")
def chiudi_batch_nesting(
    batch_id: str, 
    chiuso_da_utente: str = Query(..., description="ID dell'utente che chiude il batch"),
    chiuso_da_ruolo: str = Query(..., description="Ruolo dell'utente che chiude"),
    db: Session = Depends(get_db)
):
    """
    Chiude il batch nesting e completa il ciclo di cura.
    Aggiorna lo stato di tutti gli ODL da "In cura" a "Completato".
    """
    try:
        # Verifica che il batch esista e sia nello stato corretto
        db_batch = db.query(BatchNesting).filter(BatchNesting.id == batch_id).first()
        if not db_batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch nesting con ID {batch_id} non trovato"
            )
        
        if db_batch.stato != StatoBatchNestingEnum.IN_CURA:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Il batch deve essere in stato 'In cura' per essere chiuso. Stato attuale: {db_batch.stato}"
            )
        
        # Aggiorna il batch nesting
        db_batch.stato = StatoBatchNestingEnum.COMPLETATO
        db_batch.chiuso_da_utente = chiuso_da_utente
        db_batch.chiuso_da_ruolo = chiuso_da_ruolo
        db_batch.data_chiusura = datetime.now()
        db_batch.updated_at = datetime.now()
        
        # Aggiorna gli ODL associati
        state_service = StateTrackingService()
        odl_log_service = ODLLogService()
        
        # Gestisce tutti gli ODL nel batch
        for odl_id in db_batch.odl_ids:
            odl = db.query(ODL).filter(ODL.id == odl_id).first()
            if odl and odl.status == "In cura":
                # Aggiorna lo stato dell'ODL
                previous_status = odl.status
                odl.status = "Completato"
                odl.updated_at = datetime.now()
                
                # Registra il cambio di stato
                state_service.log_state_change(
                    db=db,
                    odl_id=odl_id,
                    stato_precedente=previous_status,
                    stato_nuovo="Completato",
                    responsabile=chiuso_da_utente,
                    ruolo_responsabile=chiuso_da_ruolo,
                    note=f"Completamento automatico tramite chiusura batch {batch_id}"
                )
                
                # Log dell'operazione
                odl_log_service.log_odl_event(
                    db=db,
                    odl_id=odl_id,
                    evento="batch_chiuso",
                    stato_precedente=previous_status,
                    stato_nuovo="Completato",
                    responsabile=chiuso_da_utente,
                    descrizione=f"ODL completato tramite chiusura batch nesting {batch_id}"
                )
        
        # Aggiorna eventuale autoclave
        if db_batch.autoclave_id:
            autoclave = db.query(Autoclave).filter(Autoclave.id == db_batch.autoclave_id).first()
            if autoclave and autoclave.stato == StatoAutoclaveEnum.OCCUPATA:
                autoclave.stato = StatoAutoclaveEnum.DISPONIBILE
                autoclave.updated_at = datetime.now()
        
        db.commit()
        db.refresh(db_batch)
        
        logger.info(f"Batch nesting {batch_id} chiuso con successo da {chiuso_da_utente}")
        return db_batch
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Errore durante la chiusura del batch nesting {batch_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Si è verificato un errore durante la chiusura del batch nesting: {str(e)}"
        ) 