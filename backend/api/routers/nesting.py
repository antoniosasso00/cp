"""
Router per le operazioni di nesting automatico degli ODL nelle autoclavi.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from pydantic import BaseModel
from models.db import get_db
from models.nesting_result import NestingResult
from schemas.nesting import NestingResultSchema, NestingResultRead, NestingPreviewSchema, ManualNestingRequest
from services.nesting_service import run_automatic_nesting, get_all_nesting_results, get_nesting_preview, update_nesting_status, save_nesting_draft, load_nesting_draft, run_manual_nesting, extract_ciclo_cura_from_note
from models.autoclave import Autoclave, StatoAutoclaveEnum
from models.odl import ODL

# Schema per l'aggiornamento dello stato del nesting
class NestingStatusUpdate(BaseModel):
    stato: str
    note: str = None
    ruolo_utente: str = None

# Schema per l'assegnazione di un nesting a un'autoclave
class NestingAssignmentRequest(BaseModel):
    nesting_id: int
    autoclave_id: int
    note: str = None

def serialize_nesting_result(nesting: NestingResult) -> dict:
    """
    Serializza un risultato di nesting includendo le informazioni sui cicli di cura
    """
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
    summary="Anteprima del nesting senza salvare",
    description="""
    Mostra un'anteprima del nesting che verrebbe generato senza salvarlo nel database.
    Utile per visualizzare il layout e verificare i risultati prima di confermare.
    """
)
async def preview_nesting(db: Session = Depends(get_db)):
    """
    Endpoint per ottenere un'anteprima del nesting senza salvarlo.
    
    Args:
        db: Sessione del database
        
    Returns:
        Un oggetto NestingPreviewSchema con l'anteprima del nesting
    """
    try:
        # Ottieni l'anteprima del nesting
        result = await get_nesting_preview(db)
        return result
    except Exception as e:
        # In caso di errore, solleva una HTTPException
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante la generazione dell'anteprima del nesting: {str(e)}"
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
    # Query base
    query = db.query(NestingResult).options(
        joinedload(NestingResult.autoclave),
        joinedload(NestingResult.odl_list).joinedload(ODL.parte),
        joinedload(NestingResult.odl_list).joinedload(ODL.tool)
    )
    
    # Filtro per ruolo
    if ruolo_utente == "AUTOCLAVISTA":
        # L'autoclavista vede solo nesting in sospeso
        query = query.filter(NestingResult.stato == "In sospeso")
    elif ruolo_utente == "RESPONSABILE":
        # Il responsabile vede tutti i nesting
        pass
    
    # Filtro per stato specifico
    if stato_filtro:
        query = query.filter(NestingResult.stato == stato_filtro)
    
    # Ottieni i risultati e serializzali con le informazioni sui cicli di cura
    nesting_results = query.order_by(NestingResult.created_at.desc()).all()
    return [serialize_nesting_result(nesting) for nesting in nesting_results]

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