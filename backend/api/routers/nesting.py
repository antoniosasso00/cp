"""
Router per le operazioni di nesting automatico degli ODL nelle autoclavi.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional
from pydantic import BaseModel
from models.db import get_db
from models.nesting_result import NestingResult, StatoNestingEnum
from schemas.nesting import (
    NestingResultSchema, NestingResultRead, NestingPreviewSchema, ManualNestingRequest, NestingParameters,
    BatchNestingRequest, BatchNestingResponse, NestingResponse, NestingCreate, NestingUpdate, StatoNestingEnum as SchemaStatoNestingEnum
)
from services.nesting_service import (
    run_automatic_nesting, get_all_nesting_results, get_nesting_preview, update_nesting_status, 
    save_nesting_draft, load_nesting_draft, run_manual_nesting, extract_ciclo_cura_from_note, 
    select_odl_and_autoclave_automatically, run_batch_nesting
)
from models.autoclave import Autoclave, StatoAutoclaveEnum
from models.odl import ODL
# ✅ NUOVO: Import per nesting su due piani
from services.nesting_service import run_two_level_nesting
from services.system_log_service import SystemLogService
from models.system_log import UserRole
import logging
# ✅ NUOVO: Import per automazione nesting multiplo
from services.nesting_service import generate_multi_nesting

# Configurazione logger
logger = logging.getLogger(__name__)

# Schema per l'aggiornamento dello stato del nesting
class NestingStatusUpdate(BaseModel):
    stato: SchemaStatoNestingEnum
    note: str = None
    ruolo_utente: str = None

# Schema per l'assegnazione di un nesting a un'autoclave
class NestingAssignmentRequest(BaseModel):
    nesting_id: int
    autoclave_id: int
    note: str = None

# ✅ NUOVO: Schema per il nesting su due piani
class TwoLevelNestingRequest(BaseModel):
    autoclave_id: int
    odl_ids: List[int] = None  # Se None, usa tutti gli ODL in attesa
    superficie_piano_2_max_cm2: float = None  # Superficie massima del piano 2
    note: str = None

def serialize_nesting_result(nesting: NestingResult) -> dict:
    """
    Serializza un risultato di nesting includendo le informazioni sui cicli di cura
    """
    try:
        # Estrai le informazioni del ciclo di cura dalle note
        ciclo_cura_id, ciclo_cura_nome = extract_ciclo_cura_from_note(nesting.note)
        
        # Serializza il risultato base
        result = {
            "id": nesting.id,
            "autoclave": {
                "id": nesting.autoclave.id,
                "nome": nesting.autoclave.nome,
                "codice": nesting.autoclave.codice,
                "num_linee_vuoto": nesting.autoclave.num_linee_vuoto,
                "lunghezza": nesting.autoclave.lunghezza,
                "larghezza_piano": nesting.autoclave.larghezza_piano,
            },
            "odl_list": [
                {
                    "id": odl.id,
                    "parte": {
                        "id": odl.parte.id,
                        "part_number": odl.parte.part_number,
                        "descrizione_breve": odl.parte.descrizione_breve,
                        "num_valvole_richieste": odl.parte.num_valvole_richieste,
                    },
                    "tool": {
                        "id": odl.tool.id,
                        "part_number_tool": odl.tool.part_number_tool,
                        "descrizione": odl.tool.descrizione,
                        "lunghezza_piano": odl.tool.lunghezza_piano,
                        "larghezza_piano": odl.tool.larghezza_piano,
                    },
                    "priorita": odl.priorita,
                }
                for odl in nesting.odl_list
            ],
            "area_utilizzata": nesting.area_utilizzata,
            "area_totale": nesting.area_totale,
            "valvole_utilizzate": nesting.valvole_utilizzate,
            "valvole_totali": nesting.valvole_totali,
            "stato": nesting.stato,
            "confermato_da_ruolo": nesting.confermato_da_ruolo,
            "odl_esclusi_ids": nesting.odl_esclusi_ids or [],
            "motivi_esclusione": nesting.motivi_esclusione or [],
            "created_at": nesting.created_at.isoformat(),
            "updated_at": nesting.updated_at.isoformat() if nesting.updated_at else None,
            "note": nesting.note,
            "ciclo_cura_id": ciclo_cura_id,
            "ciclo_cura_nome": ciclo_cura_nome,
            "posizioni_tool": nesting.posizioni_tool or [],  # ✅ NUOVO: Posizioni 2D dei tool
        }
        
        return result
    except Exception as e:
        logger.error(f"Errore nella serializzazione del nesting {nesting.id}: {str(e)}")
        # Restituisci una versione semplificata in caso di errore
        return {
            "id": nesting.id,
            "autoclave": {
                "id": nesting.autoclave.id if nesting.autoclave else None,
                "nome": nesting.autoclave.nome if nesting.autoclave else "N/A",
                "codice": nesting.autoclave.codice if nesting.autoclave else "N/A",
                "num_linee_vuoto": nesting.autoclave.num_linee_vuoto if nesting.autoclave else 0,
                "lunghezza": nesting.autoclave.lunghezza if nesting.autoclave else 0,
                "larghezza_piano": nesting.autoclave.larghezza_piano if nesting.autoclave else 0,
            },
            "odl_list": [],
            "area_utilizzata": nesting.area_utilizzata or 0,
            "area_totale": nesting.area_totale or 0,
            "valvole_utilizzate": nesting.valvole_utilizzate or 0,
            "valvole_totali": nesting.valvole_totali or 0,
            "stato": nesting.stato or "Errore",
            "confermato_da_ruolo": nesting.confermato_da_ruolo,
            "odl_esclusi_ids": [],
            "motivi_esclusione": [],
            "created_at": nesting.created_at.isoformat() if nesting.created_at else None,
            "updated_at": nesting.updated_at.isoformat() if nesting.updated_at else None,
            "note": f"Errore serializzazione: {str(e)}",
            "ciclo_cura_id": None,
            "ciclo_cura_nome": None,
            "posizioni_tool": [],
        }

# Crea un router per la gestione del nesting
router = APIRouter(
    tags=["nesting"],
    responses={404: {"description": "Non trovato"}},
)

@router.post(
    "/auto",
    response_model=NestingResultSchema,
    status_code=status.HTTP_200_OK,
    summary="Esegue il nesting automatico degli ODL nelle autoclavi",
    description="""
    Ottimizza automaticamente il posizionamento degli ODL nelle autoclavi disponibili.
    Considera vincoli di area, numero di valvole e priorità degli ODL.
    Aggiorna lo stato degli ODL nel database in base al risultato.
    """
)
async def auto_nesting(db: Session = Depends(get_db)):
    """
    Endpoint per eseguire il nesting automatico degli ODL nelle autoclavi.
    
    Args:
        db: Sessione del database
        
    Returns:
        Un oggetto NestingResult con i risultati dell'ottimizzazione
    """
    try:
        # Esegui l'algoritmo di nesting
        result = await run_automatic_nesting(db)
        return result
    except Exception as e:
        # In caso di errore, solleva una HTTPException
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante l'esecuzione del nesting automatico: {str(e)}"
        )

@router.get(
    "/preview",
    response_model=NestingPreviewSchema,
    summary="Anteprima del nesting senza salvare con parametri personalizzabili",
    description="""
    Mostra un'anteprima del nesting che verrebbe generato senza salvarlo nel database.
    Supporta parametri personalizzabili per testare diverse configurazioni di nesting.
    
    Parametri disponibili:
    - distanza_perimetrale_cm: Distanza dal bordo dell'autoclave (0.0-10.0 cm, default 1.0)
    - spaziatura_tra_tool_cm: Spazio tra i tool (0.0-5.0 cm, default 0.5)
    - rotazione_tool_abilitata: Abilita rotazione automatica dei tool (default True)
    - priorita_ottimizzazione: Criterio di priorità (PESO/AREA/EQUILIBRATO, default EQUILIBRATO)
    """
)
async def preview_nesting(
    db: Session = Depends(get_db),
    distanza_perimetrale_cm: Optional[float] = Query(None, ge=0.0, le=10.0, description="Distanza perimetrale in cm"),
    spaziatura_tra_tool_cm: Optional[float] = Query(None, ge=0.0, le=5.0, description="Spaziatura tra tool in cm"),
    rotazione_tool_abilitata: Optional[bool] = Query(None, description="Abilita rotazione automatica dei tool"),
    priorita_ottimizzazione: Optional[str] = Query(None, description="Priorità ottimizzazione: PESO, AREA, EQUILIBRATO")
):
    """
    Endpoint per ottenere un'anteprima del nesting senza salvarlo.
    
    Args:
        db: Sessione del database
        distanza_perimetrale_cm: Distanza dal perimetro dell'autoclave
        spaziatura_tra_tool_cm: Spazio minimo tra i tool
        rotazione_tool_abilitata: Se abilitare la rotazione automatica
        priorita_ottimizzazione: Criterio di priorità per l'ottimizzazione
        
    Returns:
        Un oggetto NestingPreviewSchema con l'anteprima del nesting
    """
    try:
        # Crea oggetto parametri se almeno uno è specificato
        parametri = None
        if any([
            distanza_perimetrale_cm is not None,
            spaziatura_tra_tool_cm is not None,
            rotazione_tool_abilitata is not None,
            priorita_ottimizzazione is not None
        ]):
            # Costruisci il dizionario dei parametri con valori non-None
            parametri_dict = {}
            if distanza_perimetrale_cm is not None:
                parametri_dict["distanza_perimetrale_cm"] = distanza_perimetrale_cm
            if spaziatura_tra_tool_cm is not None:
                parametri_dict["spaziatura_tra_tool_cm"] = spaziatura_tra_tool_cm
            if rotazione_tool_abilitata is not None:
                parametri_dict["rotazione_tool_abilitata"] = rotazione_tool_abilitata
            if priorita_ottimizzazione is not None:
                parametri_dict["priorita_ottimizzazione"] = priorita_ottimizzazione
            
            # Crea l'oggetto NestingParameters
            parametri = NestingParameters(**parametri_dict)
        
        # Ottieni l'anteprima del nesting con parametri personalizzati
        result = await get_nesting_preview(db, parametri=parametri)
        return result
    except Exception as e:
        # In caso di errore, solleva una HTTPException
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante la generazione dell'anteprima del nesting: {str(e)}"
        )

@router.get(
    "/auto-select",
    summary="Selezione automatica ODL e autoclave",
    description="""
    ✅ LOGICA SELEZIONE AUTOMATICA ODL + AUTOCLAVE
    
    Implementa la logica che seleziona automaticamente:
    - Gli ODL idonei da inserire nel nesting (stato ATTESA CURA)
    - L'autoclave più adatta per il carico
    
    Basandosi su:
    - Stato ODL: solo quelli in ATTESA CURA
    - Ciclo di cura compatibile
    - Capacità disponibile (area, peso)
    - Stato autoclave (DISPONIBILE)
    - Campo use_secondary_plane per aumentare capacità
    
    Restituisce una selezione ottimizzata senza salvare nel database.
    """
)
async def auto_select_odl_and_autoclave(db: Session = Depends(get_db)):
    """
    Endpoint per la selezione automatica di ODL e autoclave.
    
    Args:
        db: Sessione del database
        
    Returns:
        Dict con:
        - success: bool
        - message: str
        - odl_groups: List[Dict] - Gruppi di ODL per ciclo di cura
        - selected_autoclave: Dict - Autoclave selezionata
        - selection_criteria: Dict - Criteri di selezione utilizzati
    """
    try:
        # Esegui la selezione automatica
        result = await select_odl_and_autoclave_automatically(db)
        return result
    except Exception as e:
        # In caso di errore, solleva una HTTPException
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante la selezione automatica: {str(e)}"
        )

@router.put(
    "/{nesting_id}/status",
    summary="Aggiorna lo stato di un nesting",
    description="""
    Aggiorna lo stato di un nesting esistente. Quando viene schedulato,
    tutti gli ODL associati passano automaticamente allo stato "In Autoclave".
    """
)
async def update_nesting_status_endpoint(
    nesting_id: int,
    status_update: NestingStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Endpoint per aggiornare lo stato di un nesting.
    
    Args:
        nesting_id: ID del nesting da aggiornare
        status_update: Nuovo stato e note opzionali
        db: Sessione del database
        
    Returns:
        Il nesting aggiornato con informazioni sui cicli di cura
    """
    try:
        # Aggiorna lo stato del nesting
        result = await update_nesting_status(db, nesting_id, status_update.stato, status_update.note, status_update.ruolo_utente)
        
        # Log dell'evento nel sistema
        if status_update.stato == "Confermato":
            user_role = UserRole.MANAGEMENT if status_update.ruolo_utente == "Management" else UserRole.CURING
            SystemLogService.log_nesting_confirm(
                db=db,
                nesting_id=nesting_id,
                autoclave_id=result.autoclave_id,
                user_role=user_role,
                user_id=status_update.ruolo_utente
            )
        else:
            user_role = UserRole.MANAGEMENT if status_update.ruolo_utente == "Management" else UserRole.CURING
            SystemLogService.log_nesting_modify(
                db=db,
                nesting_id=nesting_id,
                modification_type=f"Stato cambiato a {status_update.stato}",
                user_role=user_role,
                user_id=status_update.ruolo_utente
            )
        
        return serialize_nesting_result(result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante l'aggiornamento dello stato del nesting: {str(e)}"
        )

@router.get(
    "/",
    summary="Restituisce la lista dei nesting generati",
    description="Restituisce la lista dei nesting generati con tutte le informazioni relative agli ODL e all'autoclave",
)
def list_nesting(
    ruolo_utente: str = None,
    stato_filtro: str = None,
    db: Session = Depends(get_db)
):
    """
    Recupera tutti i risultati di nesting dal database con relazioni
    
    Args:
        ruolo_utente: Ruolo dell'utente per filtrare i nesting appropriati
        stato_filtro: Filtro opzionale per stato specifico
        db: Sessione del database
        
    Returns:
        Lista di oggetti NestingResultRead con informazioni sui cicli di cura
    """
    try:
        logger.info(f"🔍 Richiesta lista nesting - Ruolo: {ruolo_utente}, Filtro stato: {stato_filtro}")
        
        # Query base con eager loading per evitare N+1 queries
        query = db.query(NestingResult).options(
            joinedload(NestingResult.autoclave),
            joinedload(NestingResult.odl_list).joinedload(ODL.parte),
            joinedload(NestingResult.odl_list).joinedload(ODL.tool)
        )
        
        # Filtro per ruolo
        if ruolo_utente == "Curing":
            # Il Curing vede solo nesting in sospeso
            query = query.filter(NestingResult.stato == "In sospeso")
            logger.info("🔧 Filtro applicato: solo nesting 'In sospeso' per Curing")
        elif ruolo_utente == "Management":
            # Il Management vede tutti i nesting
            logger.info("👔 Management: visualizzazione di tutti i nesting")
            pass
        
        # Filtro per stato specifico
        if stato_filtro:
            query = query.filter(NestingResult.stato == stato_filtro)
            logger.info(f"📊 Filtro stato applicato: {stato_filtro}")
        
        # Ottieni i risultati e serializzali con le informazioni sui cicli di cura
        nesting_results = query.order_by(NestingResult.created_at.desc()).all()
        logger.info(f"✅ Trovati {len(nesting_results)} nesting nel database")
        
        # Serializza i risultati con gestione errori per ogni elemento
        serialized_results = []
        for nesting in nesting_results:
            try:
                serialized = serialize_nesting_result(nesting)
                serialized_results.append(serialized)
            except Exception as e:
                logger.error(f"❌ Errore serializzazione nesting {nesting.id}: {str(e)}")
                # Continua con gli altri nesting invece di fallire completamente
                continue
        
        logger.info(f"✅ Serializzati {len(serialized_results)} nesting con successo")
        return serialized_results
        
    except Exception as e:
        logger.error(f"❌ Errore durante il recupero dei nesting: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante il recupero dei nesting: {str(e)}"
        )

@router.post(
    "/draft/save",
    summary="Salva una bozza di nesting",
    description="""
    Salva una bozza di nesting senza modificare lo stato degli ODL.
    Utile per salvare configurazioni temporanee durante la manipolazione manuale.
    """
)
async def save_draft(nesting_data: dict, db: Session = Depends(get_db)):
    """
    Endpoint per salvare una bozza di nesting.
    
    Args:
        nesting_data: Dati del nesting da salvare come bozza
        db: Sessione del database
        
    Returns:
        Risultato del salvataggio della bozza
    """
    try:
        result = await save_nesting_draft(db, nesting_data)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante il salvataggio della bozza: {str(e)}"
        )

@router.get(
    "/draft/{draft_id}",
    summary="Carica una bozza di nesting",
    description="""
    Carica una bozza di nesting salvata precedentemente.
    """
)
async def load_draft(draft_id: int, db: Session = Depends(get_db)):
    """
    Endpoint per caricare una bozza di nesting.
    
    Args:
        draft_id: ID della bozza da caricare
        db: Sessione del database
        
    Returns:
        Dati della bozza caricata
    """
    try:
        result = await load_nesting_draft(db, draft_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["message"]
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante il caricamento della bozza: {str(e)}"
        )

@router.get(
    "/drafts",
    summary="Lista delle bozze salvate",
    description="""
    Restituisce la lista di tutte le bozze di nesting salvate.
    """
)
async def list_drafts(db: Session = Depends(get_db)):
    """
    Endpoint per ottenere la lista delle bozze salvate.
    
    Args:
        db: Sessione del database
        
    Returns:
        Lista delle bozze disponibili
    """
    try:
        drafts = db.query(NestingResult).options(
            joinedload(NestingResult.autoclave)
        ).filter(
            NestingResult.stato == "Bozza"
        ).order_by(NestingResult.created_at.desc()).all()
        
        drafts_list = []
        for draft in drafts:
            drafts_list.append({
                "id": draft.id,
                "created_at": draft.created_at.isoformat(),
                "autoclave_nome": draft.autoclave.nome,
                "autoclave_codice": draft.autoclave.codice,
                "num_odl": len(draft.odl_ids) if draft.odl_ids else 0,
                "area_utilizzata": draft.area_utilizzata,
                "area_totale": draft.area_totale,
                "note": draft.note
            })
        
        return {
            "success": True,
            "drafts": drafts_list,
            "count": len(drafts_list)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante il recupero delle bozze: {str(e)}"
        )

@router.post(
    "/manual",
    response_model=NestingResultSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Crea un nesting manuale con ODL selezionati",
    description="""
    Crea un nesting manuale utilizzando gli ODL specificati.
    Valida che tutti gli ODL siano in stato "Attesa Cura" e non già assegnati.
    Ottimizza il posizionamento negli autoclavi disponibili.
    """
)
async def manual_nesting(request: ManualNestingRequest, db: Session = Depends(get_db)):
    """
    Endpoint per creare un nesting manuale con ODL selezionati.
    
    Args:
        request: Richiesta contenente gli ID degli ODL e note opzionali
        db: Sessione del database
        
    Returns:
        Un oggetto NestingResultSchema con i risultati dell'ottimizzazione
        
    Raises:
        HTTPException: 
            - 422 se gli ODL non sono validi o già assegnati
            - 400 se non è possibile creare il nesting
            - 500 per errori interni del server
    """
    try:
        # Valida che la lista non sia vuota
        if not request.odl_ids:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Deve essere selezionato almeno un ODL per creare il nesting"
            )
        
        # Esegui l'algoritmo di nesting manuale
        result = await run_manual_nesting(db, request.odl_ids, request.note)
        return result
        
    except ValueError as e:
        # Errori di validazione (ODL non validi, già assegnati, ecc.)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        # Errori generici del server
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante la creazione del nesting manuale: {str(e)}"
        )

@router.post(
    "/assign",
    response_model=NestingResultRead,
    status_code=status.HTTP_200_OK,
    summary="Assegna un nesting confermato a un'autoclave",
    description="""
    Assegna un nesting in stato "Confermato" a un'autoclave specifica.
    L'autoclave deve essere disponibile e il nesting deve essere confermato.
    """
)
async def assign_nesting_to_autoclave(
    assignment: NestingAssignmentRequest,
    db: Session = Depends(get_db)
):
    """
    Endpoint per assegnare un nesting confermato a un'autoclave.
    
    Args:
        assignment: Dati dell'assegnazione (nesting_id, autoclave_id, note)
        db: Sessione del database
        
    Returns:
        Il nesting aggiornato con l'assegnazione
    """
    try:
        # Verifica che il nesting esista e sia confermato
        nesting = db.query(NestingResult).filter(NestingResult.id == assignment.nesting_id).first()
        if not nesting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Nesting con ID {assignment.nesting_id} non trovato"
            )
        
        if nesting.stato != "Confermato":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo i nesting confermati possono essere assegnati alle autoclavi"
            )
        
        # Verifica che l'autoclave esista e sia disponibile
        autoclave = db.query(Autoclave).filter(Autoclave.id == assignment.autoclave_id).first()
        if not autoclave:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Autoclave con ID {assignment.autoclave_id} non trovata"
            )
        
        if autoclave.stato != StatoAutoclaveEnum.DISPONIBILE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"L'autoclave {autoclave.nome} non è disponibile (stato: {autoclave.stato})"
            )
        
        # Aggiorna l'assegnazione del nesting
        nesting.autoclave_id = assignment.autoclave_id
        if assignment.note:
            current_note = nesting.note or ""
            nesting.note = f"{current_note}\nAssegnato a {autoclave.nome}: {assignment.note}".strip()
        
        # Cambia lo stato dell'autoclave a "IN_USO"
        autoclave.stato = StatoAutoclaveEnum.IN_USO
        
        # Salva le modifiche
        db.add(nesting)
        db.add(autoclave)
        db.commit()
        db.refresh(nesting)
        
        return nesting
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante l'assegnazione del nesting: {str(e)}"
        )

@router.get(
    "/{nesting_id}",
    summary="Ottiene i dettagli di un nesting specifico",
    description="Restituisce i dettagli completi di un nesting specifico"
)
def get_nesting_detail(nesting_id: int, db: Session = Depends(get_db)):
    """
    Endpoint per ottenere i dettagli di un nesting specifico.
    
    Args:
        nesting_id: ID del nesting da recuperare
        db: Sessione del database
        
    Returns:
        Dettagli completi del nesting
    """
    try:
        # Recupera il nesting con tutte le relazioni
        nesting = db.query(NestingResult).options(
            joinedload(NestingResult.autoclave),
            joinedload(NestingResult.odl_list)
        ).filter(NestingResult.id == nesting_id).first()
        
        if not nesting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Nesting con ID {nesting_id} non trovato"
            )
        
        # Serializza il risultato
        result = serialize_nesting_result(nesting)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante il recupero del nesting: {str(e)}"
        )

@router.get(
    "/available-for-assignment",
    response_model=List[NestingResultRead],
    summary="Restituisce i nesting disponibili per l'assegnazione",
    description="Restituisce la lista dei nesting in stato 'Confermato' che possono essere assegnati alle autoclavi"
)
def get_available_nestings_for_assignment(db: Session = Depends(get_db)):
    """
    Recupera tutti i nesting confermati disponibili per l'assegnazione
    
    Args:
        db: Sessione del database
        
    Returns:
        Lista di nesting disponibili per l'assegnazione
    """
    try:
        return db.query(NestingResult).options(
            joinedload(NestingResult.autoclave),
            joinedload(NestingResult.odl_list).joinedload(ODL.parte),
            joinedload(NestingResult.odl_list).joinedload(ODL.tool)
        ).filter(
            NestingResult.stato == "Confermato"
        ).order_by(NestingResult.created_at.desc()).all()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante il recupero dei nesting disponibili: {str(e)}"
        )

@router.get(
    "/{nesting_id}/report",
    summary="Scarica il report PDF associato al nesting",
    description="""
    Scarica il report PDF generato automaticamente per questo nesting.
    Se il report non esiste, restituisce informazioni su come generarlo.
    """
)
async def download_nesting_report(
    nesting_id: int,
    db: Session = Depends(get_db)
):
    """
    Endpoint per scaricare il report PDF di un nesting.
    
    Args:
        nesting_id: ID del nesting
        db: Sessione del database
        
    Returns:
        FileResponse con il PDF del report o informazioni sul report
    """
    try:
        from fastapi.responses import FileResponse
        from models.report import Report
        import os
        
        # Trova il nesting
        nesting = db.query(NestingResult).filter(NestingResult.id == nesting_id).first()
        if not nesting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Nesting con ID {nesting_id} non trovato"
            )
        
        # Controlla se esiste un report associato
        if not nesting.report_id:
            return {
                "message": "Nessun report disponibile per questo nesting",
                "nesting_id": nesting_id,
                "has_report": False,
                "suggestion": "Usa l'endpoint /api/nesting/{nesting_id}/generate-report per generare un report"
            }
        
        # Trova il report nel database
        report = db.query(Report).filter(Report.id == nesting.report_id).first()
        if not report:
            return {
                "message": "Report collegato non trovato nel database",
                "nesting_id": nesting_id,
                "report_id": nesting.report_id,
                "has_report": False
            }
        
        # Verifica che il file esista fisicamente
        if not os.path.exists(report.file_path):
            return {
                "message": "File PDF del report non trovato su disco",
                "nesting_id": nesting_id,
                "report_id": report.id,
                "expected_path": report.file_path,
                "has_report": False
            }
        
        # Restituisce il file PDF
        return FileResponse(
            path=report.file_path,
            filename=report.filename,
            media_type="application/pdf"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante il download del report per nesting: {str(e)}"
        )

@router.post(
    "/{nesting_id}/generate-report",
    summary="Genera un report PDF per il nesting",
    description="""
    Genera un report PDF per un nesting specifico. Se esiste già un report,
    può essere rigenerato usando il parametro force_regenerate.
    """
)
async def generate_nesting_report(
    nesting_id: int,
    force_regenerate: bool = False,
    db: Session = Depends(get_db)
):
    """
    Endpoint per generare un report PDF per un nesting.
    
    Args:
        nesting_id: ID del nesting
        force_regenerate: Se True, rigenera il report anche se esiste già
        db: Sessione del database
        
    Returns:
        Informazioni sul report generato
    """
    try:
        # Importa qui per evitare dipendenze circolari
        from services.auto_report_service import AutoReportService
        from models.schedule_entry import ScheduleEntry, ScheduleEntryStatus
        from datetime import datetime
        
        # Trova il nesting
        nesting = db.query(NestingResult).filter(NestingResult.id == nesting_id).first()
        if not nesting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Nesting con ID {nesting_id} non trovato"
            )
        
        # Controlla se esiste già un report
        if nesting.report_id and not force_regenerate:
            from models.report import Report
            existing_report = db.query(Report).filter(Report.id == nesting.report_id).first()
            if existing_report:
                return {
                    "message": "Report già esistente per questo nesting",
                    "nesting_id": nesting_id,
                    "existing_report": {
                        "id": existing_report.id,
                        "filename": existing_report.filename,
                        "created_at": existing_report.created_at,
                        "file_path": existing_report.file_path
                    },
                    "suggestion": "Usa force_regenerate=true per rigenerare il report"
                }
        
        # Trova una schedule entry associata o crea una fittizia
        schedule = db.query(ScheduleEntry).filter(
            ScheduleEntry.autoclave_id == nesting.autoclave_id
        ).order_by(ScheduleEntry.updated_at.desc()).first()
        
        if not schedule:
            # Crea una schedule entry fittizia per il report
            schedule = ScheduleEntry(
                autoclave_id=nesting.autoclave_id,
                start_datetime=nesting.created_at,
                end_datetime=datetime.now(),
                status=ScheduleEntryStatus.DONE.value
            )
        
        # Inizializza il servizio di auto-report
        auto_report_service = AutoReportService(db)
        
        # Prepara le informazioni del ciclo
        cycle_info = {
            'schedule_id': schedule.id if schedule.id else 0,
            'nesting_id': nesting.id,
            'autoclave_id': nesting.autoclave_id,
            'odl_id': None,
            'completed_at': datetime.now(),
            'nesting': nesting,
            'schedule': schedule
        }
        
        # Genera il report
        report = await auto_report_service.generate_cycle_completion_report(cycle_info)
        
        if report:
            return {
                "message": "Report generato con successo per il nesting",
                "nesting_id": nesting_id,
                "report": {
                    "id": report.id,
                    "filename": report.filename,
                    "file_path": report.file_path,
                    "created_at": report.created_at
                },
                "download_url": f"/api/nesting/{nesting_id}/report"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Errore durante la generazione del report"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante la generazione del report per nesting: {str(e)}"
        )

# ✅ NUOVO: Endpoint per nesting su due piani
@router.post(
    "/seed",
    summary="Popola il database con dati di esempio per il nesting",
    description="Crea dati di esempio per testare il sistema di nesting"
)
async def seed_nesting_data(db: Session = Depends(get_db)):
    """
    Endpoint per popolare il database con dati di esempio per il nesting.
    
    Returns:
        Messaggio di conferma con statistiche sui dati creati
    """
    try:
        from models.odl import ODL
        from models.nesting_result import NestingResult
        
        # Conta i dati esistenti
        existing_odl = db.query(ODL).count()
        existing_nesting = db.query(NestingResult).count()
        
        return {
            "message": "Dati di seed già presenti nel database",
            "existing_data": {
                "odl_count": existing_odl,
                "nesting_count": existing_nesting
            },
            "note": "Il sistema è già popolato con dati di test"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante il seeding dei dati: {str(e)}"
        )

@router.post(
    "/two-level",
    status_code=status.HTTP_201_CREATED,
    summary="Esegue il nesting ottimizzato su due piani",
    description="""
    Esegue un nesting ottimizzato su due piani per un'autoclave specifica.
    Posiziona i pezzi più pesanti e grandi nel piano inferiore,
    i pezzi più leggeri e piccoli nel piano superiore.
    Rispetta il limite di carico massimo dell'autoclave.
    """
)
async def two_level_nesting(
    request: TwoLevelNestingRequest,
    db: Session = Depends(get_db)
):
    """
    Endpoint per eseguire il nesting su due piani ottimizzato per peso e dimensione.
    
    Args:
        request: Parametri per il nesting su due piani
        db: Sessione del database
        
    Returns:
        Risultato dettagliato del nesting su due piani
    """
    try:
        # Esegui l'algoritmo di nesting su due piani
        result = await run_two_level_nesting(
            db=db,
            autoclave_id=request.autoclave_id,
            odl_ids=request.odl_ids,
            superficie_piano_2_max_cm2=request.superficie_piano_2_max_cm2,
            note=request.note
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante l'esecuzione del nesting su due piani: {str(e)}"
        )

@router.post(
    "/auto-multiple",
    status_code=status.HTTP_201_CREATED,
    summary="Genera nesting automatico su autoclavi disponibili",
    description="""
    ✅ PROMPT 14.3B.2 - AUTOMAZIONE NESTING SU AUTOCLAVI DISPONIBILI
    
    Implementa una funzione backend che, partendo dagli ODL in `ATTESA CURA`, 
    generi automaticamente uno o più nesting associati alle autoclavi disponibili, 
    ottimizzando l'utilizzo delle risorse (area, peso, valvole).
    
    LOGICA:
    1. Recupera tutti gli ODL in stato `ATTESA CURA` validi
    2. Recupera tutte le autoclavi in stato `DISPONIBILE`
    3. Per ogni autoclave disponibile:
       - Seleziona gruppo compatibile di ODL (area, peso, valvole)
       - Se `use_secondary_plane` è attivo, sfrutta anche il secondo piano
       - Assegna ODL al nesting
       - Crea oggetto `NestingResult` con stato `SOSPESO`
       - Aggiorna autoclave a `IN_USO`
       - Mantiene ODL in `ATTESA CURA` (cambieranno solo alla conferma)
    
    Returns:
        Dizionario con i risultati dell'automazione multi-nesting
    """
)
async def auto_multiple_nesting(db: Session = Depends(get_db)):
    """
    Endpoint per eseguire l'automazione nesting su autoclavi disponibili.
    
    Args:
        db: Sessione del database
        
    Returns:
        Dizionario con i risultati dell'automazione multi-nesting
    """
    try:
        # Log dell'operazione
        logger.info("🚀 Richiesta automazione nesting su autoclavi disponibili")
        
        # Esegui l'algoritmo di automazione nesting
        result = await generate_multi_nesting(db)
        
        # Log del sistema per audit
        SystemLogService.log_nesting_operation(
            db=db,
            operation_type="AUTO_MULTIPLE_NESTING",
            user_role=UserRole.SISTEMA,
            details={
                "nesting_creati": len(result.get("nesting_creati", [])),
                "odl_pianificati": len(result.get("odl_pianificati", [])),
                "autoclavi_utilizzate": len(result.get("autoclavi_utilizzate", [])),
                "success": result.get("success", False)
            },
            result="SUCCESS" if result.get("success", False) else "FAILED"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Errore durante automazione nesting multiplo: {str(e)}")
        
        # Log dell'errore
        SystemLogService.log_nesting_operation(
            db=db,
            operation_type="AUTO_MULTIPLE_NESTING",
            user_role=UserRole.SISTEMA,
            details={"error": str(e)},
            result="ERROR"
        )
        
        # In caso di errore, solleva una HTTPException
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante l'automazione nesting su autoclavi disponibili: {str(e)}"
        )

# ✅ PROMPT 14.3B.3 - GESTIONE NESTING IN SOSPESO: CONFERMA E RIMOZIONE

@router.post(
    "/{nesting_id}/confirm",
    status_code=status.HTTP_200_OK,
    summary="Conferma un nesting in sospeso",
    description="""
    Conferma un nesting in stato SOSPESO e attiva il processo di cura.
    
    OPERAZIONI:
    - Cambia stato nesting da SOSPESO a ATTIVO
    - Aggiorna tutti gli ODL associati da ATTESA CURA a CURA
    - Mantiene l'autoclave in stato IN_USO
    - Registra l'operazione nei log di sistema
    
    VALIDAZIONI:
    - Il nesting deve essere in stato SOSPESO
    - L'autoclave non deve essere GUASTA o SPENTA
    - Gli ODL non devono essere già in cura
    """
)
async def confirm_nesting(
    nesting_id: int,
    ruolo_utente: str = "curing",
    db: Session = Depends(get_db)
):
    """
    Conferma un nesting in sospeso e attiva il processo di cura.
    
    Args:
        nesting_id: ID del nesting da confermare
        ruolo_utente: Ruolo dell'utente che conferma (default: curing)
        db: Sessione del database
        
    Returns:
        Dettagli del nesting confermato e ODL aggiornati
    """
    try:
        # Recupera il nesting con le relazioni
        nesting = db.query(NestingResult).options(
            joinedload(NestingResult.autoclave),
            joinedload(NestingResult.odl_list)
        ).filter(NestingResult.id == nesting_id).first()
        
        if not nesting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Nesting con ID {nesting_id} non trovato"
            )
        
        # Validazione: deve essere in stato SOSPESO o "In sospeso"
        if nesting.stato not in ["SOSPESO", "In sospeso"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Il nesting deve essere in stato SOSPESO. Stato attuale: {nesting.stato}"
            )
        
        # Validazione: autoclave non deve essere guasta o spenta
        if nesting.autoclave.stato in [StatoAutoclaveEnum.GUASTO, StatoAutoclaveEnum.SPENTA]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Impossibile confermare: autoclave {nesting.autoclave.nome} è in stato {nesting.autoclave.stato.value}"
            )
        
        # Validazione: verifica che gli ODL siano ancora in ATTESA CURA
        odl_non_validi = []
        for odl in nesting.odl_list:
            if odl.status != "Attesa Cura":
                odl_non_validi.append(f"ODL {odl.id} è in stato {odl.status}")
        
        if odl_non_validi:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Alcuni ODL non sono più validi per la conferma: {'; '.join(odl_non_validi)}"
            )
        
        # Aggiorna stato nesting
        nesting.stato = "ATTIVO"
        nesting.confermato_da_ruolo = ruolo_utente
        nesting.updated_at = func.now()
        
        # Aggiorna stato ODL a CURA
        odl_aggiornati = []
        for odl in nesting.odl_list:
            odl.status = "Cura"
            odl.updated_at = func.now()
            odl_aggiornati.append({
                "id": odl.id,
                "parte_id": odl.parte_id,
                "tool_id": odl.tool_id,
                "nuovo_stato": "Cura"
            })
        
        # L'autoclave rimane IN_USO (già impostata quando il nesting è stato creato)
        
        # Salva le modifiche
        db.commit()
        
        # Log dell'operazione per audit
        user_role_enum = UserRole.CURING if ruolo_utente == "curing" else UserRole.MANAGEMENT
        SystemLogService.log_nesting_confirm(
            db=db,
            nesting_id=nesting_id,
            autoclave_id=nesting.autoclave_id,
            user_role=user_role_enum,
            user_id=ruolo_utente
        )
        
        logger.info(f"✅ Nesting {nesting_id} confermato da {ruolo_utente}. {len(odl_aggiornati)} ODL passati in CURA")
        
        return {
            "message": "Nesting confermato con successo",
            "nesting": {
                "id": nesting.id,
                "stato": nesting.stato,
                "confermato_da_ruolo": nesting.confermato_da_ruolo,
                "autoclave": {
                    "id": nesting.autoclave.id,
                    "nome": nesting.autoclave.nome,
                    "stato": nesting.autoclave.stato.value
                }
            },
            "odl_aggiornati": odl_aggiornati,
            "statistiche": {
                "odl_in_cura": len(odl_aggiornati),
                "area_utilizzata": nesting.area_utilizzata,
                "peso_totale_kg": nesting.peso_totale_kg
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Errore durante conferma nesting {nesting_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante la conferma del nesting: {str(e)}"
        )

@router.delete(
    "/{nesting_id}",
    status_code=status.HTTP_200_OK,
    summary="Elimina un nesting in sospeso",
    description="""
    Elimina un nesting in stato SOSPESO e rilascia le risorse.
    
    OPERAZIONI:
    - Elimina il nesting dal database
    - Rilascia gli ODL associati (tornano in ATTESA CURA)
    - Aggiorna l'autoclave a DISPONIBILE se nessun altro nesting è attivo
    - Registra l'operazione nei log di sistema
    
    VALIDAZIONI:
    - Il nesting deve essere in stato SOSPESO
    - Solo nesting non confermati possono essere eliminati
    """
)
async def delete_nesting(
    nesting_id: int,
    ruolo_utente: str = "curing",
    db: Session = Depends(get_db)
):
    """
    Elimina un nesting in sospeso e rilascia le risorse.
    
    Args:
        nesting_id: ID del nesting da eliminare
        ruolo_utente: Ruolo dell'utente che elimina (default: curing)
        db: Sessione del database
        
    Returns:
        Conferma dell'eliminazione e statistiche
    """
    try:
        # Recupera il nesting con le relazioni
        nesting = db.query(NestingResult).options(
            joinedload(NestingResult.autoclave),
            joinedload(NestingResult.odl_list)
        ).filter(NestingResult.id == nesting_id).first()
        
        if not nesting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Nesting con ID {nesting_id} non trovato"
            )
        
        # Validazione: deve essere in stato SOSPESO o "In sospeso"
        if nesting.stato not in ["SOSPESO", "In sospeso"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Solo i nesting in stato SOSPESO possono essere eliminati. Stato attuale: {nesting.stato}"
            )
        
        # Salva informazioni per il log prima dell'eliminazione
        autoclave_id = nesting.autoclave_id
        autoclave_nome = nesting.autoclave.nome
        odl_ids = [odl.id for odl in nesting.odl_list]
        odl_count = len(nesting.odl_list)
        
        # Rilascia gli ODL (tornano in ATTESA CURA se erano in quello stato)
        odl_rilasciati = []
        for odl in nesting.odl_list:
            # Gli ODL in nesting sospeso dovrebbero essere ancora in ATTESA CURA
            if odl.status == "Attesa Cura":
                odl_rilasciati.append({
                    "id": odl.id,
                    "parte_id": odl.parte_id,
                    "tool_id": odl.tool_id,
                    "stato": odl.status
                })
        
        # Verifica se ci sono altri nesting attivi per questa autoclave
        altri_nesting_attivi = db.query(NestingResult).filter(
            NestingResult.autoclave_id == autoclave_id,
            NestingResult.id != nesting_id,
            NestingResult.stato.in_(["ATTIVO", "CONFERMATO"])
        ).count()
        
        # Aggiorna stato autoclave solo se non ci sono altri nesting attivi
        autoclave_aggiornata = False
        if altri_nesting_attivi == 0:
            nesting.autoclave.stato = StatoAutoclaveEnum.DISPONIBILE
            autoclave_aggiornata = True
        
        # Elimina il nesting (le associazioni ODL vengono eliminate automaticamente)
        db.delete(nesting)
        
        # Salva le modifiche
        db.commit()
        
        # Log dell'operazione per audit
        user_role_enum = UserRole.CURING if ruolo_utente == "curing" else UserRole.MANAGEMENT
        SystemLogService.log_nesting_operation(
            db=db,
            operation_type="NESTING_DELETE",
            user_role=user_role_enum,
            details={
                "nesting_id": nesting_id,
                "autoclave_id": autoclave_id,
                "autoclave_nome": autoclave_nome,
                "odl_ids": odl_ids,
                "odl_count": odl_count,
                "autoclave_liberata": autoclave_aggiornata,
                "altri_nesting_attivi": altri_nesting_attivi
            },
            result="SUCCESS",
            user_id=ruolo_utente
        )
        
        logger.info(f"✅ Nesting {nesting_id} eliminato da {ruolo_utente}. {odl_count} ODL rilasciati, autoclave {'liberata' if autoclave_aggiornata else 'ancora occupata'}")
        
        return {
            "message": "Nesting eliminato con successo",
            "nesting_eliminato": {
                "id": nesting_id,
                "autoclave_nome": autoclave_nome
            },
            "odl_rilasciati": odl_rilasciati,
            "autoclave": {
                "id": autoclave_id,
                "nome": autoclave_nome,
                "stato_aggiornato": "DISPONIBILE" if autoclave_aggiornata else "IN_USO",
                "altri_nesting_attivi": altri_nesting_attivi
            },
            "statistiche": {
                "odl_rilasciati": len(odl_rilasciati),
                "autoclave_liberata": autoclave_aggiornata
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Errore durante eliminazione nesting {nesting_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante l'eliminazione del nesting: {str(e)}"
        )

# ✅ NUOVO ENDPOINT: Batch nesting intelligente multi-autoclave
@router.post(
    "/batch",
    response_model=BatchNestingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Esegue batch nesting intelligente multi-autoclave",
    description="""
    🚀 BATCH NESTING INTELLIGENTE MULTI-AUTOCLAVE
    
    Implementa l'algoritmo batch che:
    1. Valuta tutti gli ODL in attesa e tutte le autoclavi disponibili
    2. Genera uno o più nesting contemporaneamente, ottimizzando superficie e valvole
    3. Distribuisce ODL in modo bilanciato per ridurre il numero totale di nesting
    4. Crea nesting in stato BOZZA (non blocca autoclavi fino alla conferma)
    
    VANTAGGI:
    - Ottimizzazione globale invece che sequenziale
    - Utilizzo bilanciato delle risorse
    - Parametri personalizzabili per ogni batch
    - Stato BOZZA permette revisione prima della conferma
    
    PARAMETRI PERSONALIZZABILI:
    - padding_mm: Spaziatura tra tool (default: 10mm)
    - borda_mm: Bordo minimo dall'autoclave (default: 20mm)
    - max_valvole_per_autoclave: Limite valvole (opzionale)
    - rotazione_abilitata: Rotazione automatica tool (default: true)
    - priorita_ottimizzazione: PESO/AREA/EQUILIBRATO (default: EQUILIBRATO)
    """
)
async def batch_nesting(
    request: BatchNestingRequest,
    db: Session = Depends(get_db)
):
    """
    Endpoint per eseguire il batch nesting intelligente multi-autoclave.
    
    Args:
        request: Richiesta con parametri personalizzabili
        db: Sessione del database
        
    Returns:
        BatchNestingResponse con i nesting creati e statistiche
    """
    try:
        logger.info("🚀 Avvio batch nesting intelligente multi-autoclave")
        
        # Esegui il batch nesting
        result = await run_batch_nesting(db, request)
        
        # Log del risultato
        if result.success:
            logger.info(f"✅ Batch completato: {len(result.nesting_creati)} nesting creati")
        else:
            logger.warning(f"⚠️ Batch fallito: {result.message}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Errore nel batch nesting: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante il batch nesting: {str(e)}"
        )

# ✅ NUOVO ENDPOINT: Conferma nesting da BOZZA a IN_SOSPESO
@router.post(
    "/{nesting_id}/promote",
    response_model=NestingResponse,
    status_code=status.HTTP_200_OK,
    summary="Promuove un nesting da BOZZA a IN_SOSPESO",
    description="""
    🔄 PROMOZIONE NESTING: BOZZA → IN_SOSPESO
    
    Promuove un nesting dallo stato BOZZA allo stato IN_SOSPESO:
    - Blocca l'autoclave (stato → IN_USO)
    - Mantiene ODL in ATTESA CURA
    - Permette successiva conferma da parte del Curing
    
    VALIDAZIONI:
    - Il nesting deve essere in stato BOZZA
    - L'autoclave deve essere DISPONIBILE
    - Gli ODL devono essere ancora in ATTESA CURA
    """
)
async def promote_nesting(
    nesting_id: int,
    ruolo_utente: str = "management",
    db: Session = Depends(get_db)
):
    """
    Endpoint per promuovere un nesting da BOZZA a IN_SOSPESO.
    
    Args:
        nesting_id: ID del nesting da promuovere
        ruolo_utente: Ruolo dell'utente che effettua l'operazione
        db: Sessione del database
        
    Returns:
        NestingResponse aggiornato
    """
    try:
        logger.info(f"🔄 Promozione nesting {nesting_id} da BOZZA a IN_SOSPESO")
        
        # Aggiorna lo stato del nesting
        nesting = await update_nesting_status(
            db, 
            nesting_id, 
            StatoNestingEnum.IN_SOSPESO, 
            note="Nesting promosso da bozza a in sospeso",
            ruolo_utente=ruolo_utente
        )
        
        # Blocca l'autoclave
        if nesting.autoclave:
            nesting.autoclave.stato = StatoAutoclaveEnum.IN_USO
            db.add(nesting.autoclave)
        
        db.commit()
        
        logger.info(f"✅ Nesting {nesting_id} promosso con successo")
        
        # Converti in risposta
        from services.nesting_service import nesting_to_response
        return nesting_to_response(nesting)
        
    except ValueError as e:
        logger.error(f"❌ Errore di validazione nella promozione nesting {nesting_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"❌ Errore nella promozione nesting {nesting_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante la promozione del nesting: {str(e)}"
        ) 