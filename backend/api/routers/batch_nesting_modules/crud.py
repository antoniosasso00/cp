"""
Router CRUD base per batch nesting

Questo modulo contiene le operazioni CRUD fondamentali:
- Creazione batch
- Lettura lista batch
- Lettura singolo batch
- Aggiornamento batch
- Eliminazione batch
- Eliminazione multipla batch
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from api.database import get_db
from models.batch_nesting import BatchNesting, StatoBatchNestingEnum
from models.autoclave import Autoclave
from models.odl import ODL
from models.parte import Parte
from models.tool import Tool
from schemas.batch_nesting import (
    BatchNestingCreate, 
    BatchNestingResponse, 
    BatchNestingUpdate, 
    BatchNestingList,
    StatoBatchNestingEnum as StatoBatchNestingEnumSchema
)
from schemas.odl import ODLRead

logger = logging.getLogger(__name__)

# Router per operazioni CRUD
router = APIRouter(
    tags=["Batch Nesting - CRUD"],
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

@router.get("/{batch_id}", response_model=BatchNestingResponse, 
            summary="Ottiene un batch nesting specifico")
def read_batch_nesting(batch_id: str, db: Session = Depends(get_db)):
    """
    Recupera un singolo batch nesting per ID
    """
    batch = db.query(BatchNesting).filter(BatchNesting.id == batch_id).first()
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch nesting con ID {batch_id} non trovato"
        )
    return batch

@router.get("/{batch_id}/full", summary="Ottiene un batch nesting con tutte le informazioni")
def read_batch_nesting_full(batch_id: str, db: Session = Depends(get_db)):
    """
    Recupera un batch nesting con tutte le relazioni caricate (autoclave, ODL, etc.)
    """
    batch = db.query(BatchNesting).options(
        joinedload(BatchNesting.autoclave)
    ).filter(BatchNesting.id == batch_id).first()
    
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch nesting con ID {batch_id} non trovato"
        )
    
    # Carica ODL associati
    if batch.odl_ids:
        odls = db.query(ODL).filter(ODL.id.in_(batch.odl_ids)).all()
        batch_data = {
            "batch": batch,
            "autoclave": batch.autoclave,
            "odls": odls,
            "odl_count": len(odls),
            "total_weight": sum(odl.peso or 0 for odl in odls)
        }
        return batch_data
    
    return {
        "batch": batch,
        "autoclave": batch.autoclave,
        "odls": [],
        "odl_count": 0,
        "total_weight": 0
    }

@router.get("/result/{batch_id}", summary="🎯 Ottiene risultati di un batch nesting per la visualizzazione")
def get_batch_nesting_result(
    batch_id: str, 
    multi: bool = Query(False, description="Se True, cerca batch correlati nello stesso timeframe"),
    db: Session = Depends(get_db)
):
    """
    🎯 ENDPOINT RISULTATI BATCH NESTING
    ===================================
    
    Recupera i risultati completi di un batch nesting per la visualizzazione:
    - Configurazione del layout (posizioni tool)
    - Metriche di efficienza 
    - ODL esclusi e motivi
    - Informazioni autoclave
    - Multi-batch: cerca batch correlati se richiesto
    
    Utilizzato dal frontend per la pagina dei risultati.
    """
    try:
        # 🎯 SISTEMA UNIFICATO: Cerca solo nel database (include tutti gli stati)
        main_batch = db.query(BatchNesting).options(
            joinedload(BatchNesting.autoclave)
        ).filter(BatchNesting.id == batch_id).first()
        
        # Se non trovato, errore 404
        if not main_batch:
            logger.warning(f"❌ Batch {batch_id} non trovato nel database")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch nesting con ID {batch_id} non trovato"
            )
        
        # 🔧 FIX AUTOCLAVE: Se la relazione non è caricata, carica manualmente
        if main_batch.autoclave_id and not main_batch.autoclave:
            logger.warning(f"⚠️ Autoclave non caricata con joinedload per batch {batch_id}, caricamento manuale")
            main_batch.autoclave = db.query(Autoclave).filter(Autoclave.id == main_batch.autoclave_id).first()
            if not main_batch.autoclave:
                logger.error(f"❌ Autoclave ID {main_batch.autoclave_id} non trovata per batch {batch_id}")
        
        def enrich_tool_positions_with_odl_data(batch, odls_data):
            """
            🎯 ARRICCHIMENTO TOOL POSITIONS: Aggiungi part_number, descrizione_breve, numero_odl ai tool positions
            """
            configurazione = batch.configurazione_json or {}
            
            # Mappa ODL ID -> dati ODL per lookup veloce
            odl_lookup = {odl_data['id']: odl_data for odl_data in odls_data}
            
            # 🔧 ARRICCHIMENTO TOOL_POSITIONS (formato database)
            if 'tool_positions' in configurazione:
                enriched_positions = []
                for tool in configurazione['tool_positions']:
                    enriched_tool = tool.copy()
                    odl_id = tool.get('odl_id')
                    if odl_id and odl_id in odl_lookup:
                        odl_data = odl_lookup[odl_id]
                        # Aggiungi informazioni della parte
                        if odl_data.get('parte'):
                            enriched_tool['part_number'] = odl_data['parte']['part_number']
                            enriched_tool['descrizione_breve'] = odl_data['parte']['descrizione_breve']
                        # Aggiungi numero ODL (cerca nel database l'ODL reale)
                        odl_entity = db.query(ODL).filter(ODL.id == odl_id).first()
                        if odl_entity:
                            enriched_tool['numero_odl'] = odl_entity.numero_odl
                    enriched_positions.append(enriched_tool)
                configurazione['tool_positions'] = enriched_positions
            
            # 🔧 ARRICCHIMENTO POSITIONED_TOOLS (formato draft)
            if 'positioned_tools' in configurazione:
                enriched_positioned = []
                for tool in configurazione['positioned_tools']:
                    enriched_tool = tool.copy()
                    odl_id = tool.get('odl_id')
                    if odl_id and odl_id in odl_lookup:
                        odl_data = odl_lookup[odl_id]
                        # Aggiungi informazioni della parte
                        if odl_data.get('parte'):
                            enriched_tool['part_number'] = odl_data['parte']['part_number']
                            enriched_tool['descrizione_breve'] = odl_data['parte']['descrizione_breve']
                        # Aggiungi numero ODL (cerca nel database l'ODL reale)
                        odl_entity = db.query(ODL).filter(ODL.id == odl_id).first()
                        if odl_entity:
                            enriched_tool['numero_odl'] = odl_entity.numero_odl
                    enriched_positioned.append(enriched_tool)
                configurazione['positioned_tools'] = enriched_positioned
            
            return configurazione
        
        # Funzione helper per formattare un batch
        def format_batch_result(batch):
            # 🔧 FIX AUTOCLAVE: Caricamento manuale se necessario
            if batch.autoclave_id and not batch.autoclave:
                batch.autoclave = db.query(Autoclave).filter(Autoclave.id == batch.autoclave_id).first()
            
            # Carica ODL associati
            odls = []
            if batch.odl_ids:
                odls = db.query(ODL).options(
                    joinedload(ODL.parte),
                    joinedload(ODL.tool)
                ).filter(ODL.id.in_(batch.odl_ids)).all()
            
            # Prepara dati ODL per arricchimento
            odls_data = [
                {
                    "id": odl.id,
                    "parte": {
                        "part_number": odl.parte.part_number if odl.parte else None,
                        "descrizione_breve": odl.parte.descrizione_breve if odl.parte else None
                    } if odl.parte else None,
                    "tool": {
                        "part_number_tool": odl.tool.part_number_tool if odl.tool else None,
                        "larghezza_piano": odl.tool.larghezza_piano if odl.tool else 0,
                        "lunghezza_piano": odl.tool.lunghezza_piano if odl.tool else 0,
                        "peso": odl.tool.peso if odl.tool else 0
                    } if odl.tool else None
                } for odl in odls
            ]
            
            # 🎯 ARRICCHIMENTO: Aggiungi dati parte ai tool positions
            configurazione = enrich_tool_positions_with_odl_data(batch, odls_data)
            
            # Estrai metriche dalla configurazione
            metrics = configurazione.get('metrics', {})
            
            # 🔧 FIX AUTOCLAVE INFO: Gestisci caso in cui autoclave è None
            autoclave_info = None
            if batch.autoclave:
                autoclave_info = {
                    "id": batch.autoclave.id,
                    "nome": batch.autoclave.nome,
                    "larghezza_piano": batch.autoclave.larghezza_piano,
                    "lunghezza": batch.autoclave.lunghezza,
                    "max_load_kg": batch.autoclave.max_load_kg,
                    "num_linee_vuoto": batch.autoclave.num_linee_vuoto
                }
            elif batch.autoclave_id:
                # Fallback: carica autoclave senza relazione
                autoclave_db = db.query(Autoclave).filter(Autoclave.id == batch.autoclave_id).first()
                if autoclave_db:
                    autoclave_info = {
                        "id": autoclave_db.id,
                        "nome": autoclave_db.nome,
                        "larghezza_piano": autoclave_db.larghezza_piano,
                        "lunghezza": autoclave_db.lunghezza,
                        "max_load_kg": autoclave_db.max_load_kg,
                        "num_linee_vuoto": autoclave_db.num_linee_vuoto
                    }
                else:
                    logger.error(f"❌ Autoclave ID {batch.autoclave_id} non trovata per batch {batch.id}")
            
            return {
                "id": batch.id,
                "nome": batch.nome,
                "stato": batch.stato,
                "autoclave_id": batch.autoclave_id,
                "autoclave": autoclave_info,
                "odl_ids": batch.odl_ids or [],
                "configurazione_json": configurazione,  # 🎯 Ora arricchita con dati parte
                "parametri": batch.parametri,
                "created_at": batch.created_at.isoformat() if batch.created_at else None,
                "numero_nesting": batch.numero_nesting,
                "peso_totale_kg": batch.peso_totale_kg,
                "area_totale_utilizzata": batch.area_totale_utilizzata,
                "valvole_totali_utilizzate": batch.valvole_totali_utilizzate,
                "efficiency": batch.efficiency,
                "note": batch.note,
                "metrics": {
                    "efficiency_percentage": batch.efficiency,
                    "total_area_used_mm2": metrics.get('total_area_used_mm2', 0),
                    "total_weight_kg": batch.peso_totale_kg or 0,
                    "positioned_tools": len(configurazione.get('tool_positions', [])) or len(configurazione.get('positioned_tools', [])),
                    "excluded_tools": 0  # TODO: calcolare gli esclusi se disponibili
                },
                "odls_data": odls_data  # Mantenuto per compatibilità
            }
        
        # Risultato principale
        batch_results = [format_batch_result(main_batch)]
        
        # Se richiesto, cerca batch correlati (multi-batch)
        if multi:
            correlated_batches = []
            
            # 🎯 CORRELAZIONE DRAFT: Se il batch è DRAFT, usa il sistema di correlazione avanzata
            if hasattr(main_batch, 'stato') and main_batch.stato == StatoBatchNestingEnum.DRAFT.value:
                logger.info(f"🔗 Ricerca correlazioni DRAFT per batch {batch_id}")
                
                # 🚀 Usa il nesting service singleton per le correlazioni DRAFT
                from services.nesting_service import get_nesting_service
                nesting_service = get_nesting_service()
                
                # Usa il sistema di correlazione DRAFT avanzata
                draft_correlated_ids = nesting_service.get_correlated_draft_batches(db, batch_id)
                
                # Recupera i batch correlati dal database
                if draft_correlated_ids:
                    correlated_batches_query = db.query(BatchNesting).options(
                        joinedload(BatchNesting.autoclave)
                    ).filter(
                        BatchNesting.id.in_(draft_correlated_ids),
                        BatchNesting.id != batch_id  # Escludi il batch principale
                    ).all()
                    
                    correlated_batches.extend(correlated_batches_query)
                    
                logger.info(f"🔗 Trovati {len(correlated_batches)} batch DRAFT correlati per {batch_id}")
                
            # 🚀 CORRELAZIONE UNIFICATA: Per TUTTI i batch (inclusi DRAFT)
            if main_batch.created_at:
                from datetime import timedelta
                
                # 🎯 STRATEGIA TEMPORALE MIGLIORATA: 
                # 1. Finestra ±1 minuto per batch generati insieme
                # 2. Se non trova nulla, espande a ±5 minuti
                # 3. Filtra per autoclavi diverse (pattern multi-batch)
                
                time_windows = [
                    timedelta(minutes=5),   # Prima prova: finestra ampia per multi-batch lenti
                    timedelta(minutes=10),  # Seconda prova: finestra ultra-ampia per generazioni lunghe
                ]
                
                for time_window in time_windows:
                    start_time = main_batch.created_at - time_window
                    end_time = main_batch.created_at + time_window
                    
                    related_batches = db.query(BatchNesting).options(
                        joinedload(BatchNesting.autoclave)
                    ).filter(
                        BatchNesting.id != main_batch.id,
                        BatchNesting.created_at >= start_time,
                        BatchNesting.created_at <= end_time,
                        # 🚀 Includi anche DRAFT per correlazioni complete
                        BatchNesting.stato.in_(['draft', 'sospeso', 'confermato'])
                    ).limit(20).all()
                    
                    logger.info(f"🔍 Candidati correlazione (±{time_window.total_seconds()/60:.0f}min): {len(related_batches)} batch")
                    
                    # 🎯 FILTRO MULTI-BATCH: Solo batch con autoclavi diverse
                    multi_batch_candidates = []
                    for rb in related_batches:
                        if rb.autoclave_id != main_batch.autoclave_id:
                            multi_batch_candidates.append(rb)
                            logger.info(f"   ✅ Multi-batch candidato: {rb.id[:8]}... | Autoclave: {rb.autoclave.nome if rb.autoclave else rb.autoclave_id}")
                    
                    # Se troviamo correlazioni, usa queste e fermati SOLO se abbiamo un numero significativo
                    if multi_batch_candidates:
                        correlated_batches.extend(multi_batch_candidates)
                        logger.info(f"🎯 MULTI-BATCH TROVATO (±{time_window.total_seconds()/60:.0f}min): {len(multi_batch_candidates)} batch correlati")
                        
                        # Per multi-batch con molte autoclavi, continua a cercare se abbiamo pochi risultati
                        if len(multi_batch_candidates) >= 2 or time_window.total_seconds() >= 600:  # >= 2 batch o >= 10 min
                            break
                        else:
                            logger.info(f"🔍 Continuando ricerca: solo {len(multi_batch_candidates)} batch trovati, potrebbero essercene altri")
                        
                if not correlated_batches:
                    logger.info(f"📍 SINGLE-BATCH: Nessuna correlazione multi-batch trovata per {batch_id}")
                
                logger.info(f"🔗 Totale batch correlati: {len(correlated_batches)}")
            
            # Aggiungi i batch correlati ai risultati (rimuovi duplicati)
            added_batch_ids = {main_batch.id}  # Track per evitare duplicati
            for correlated_batch in correlated_batches:
                if correlated_batch.id not in added_batch_ids:
                    batch_results.append(format_batch_result(correlated_batch))
                    added_batch_ids.add(correlated_batch.id)
        
        # Ordina per autoclave_id per una visualizzazione coerente
        batch_results.sort(key=lambda x: x['autoclave_id'])
        
        # Risposta finale
        response = {
            "batch_results": batch_results,
            "total_batches": len(batch_results),
            "is_multi_batch": len(batch_results) > 1,
            "main_batch_id": batch_id,
            "execution_timestamp": main_batch.created_at.isoformat() if main_batch.created_at else None
        }
        
        logger.info(f"✅ Risultati batch {batch_id} recuperati: {len(batch_results)} batch totali")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Errore recupero risultati batch {batch_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante il recupero dei risultati: {str(e)}"
        )

@router.put("/{batch_id}", response_model=BatchNestingResponse, 
            summary="Aggiorna un batch nesting")
def update_batch_nesting(
    batch_id: str, 
    batch_update: BatchNestingUpdate, 
    db: Session = Depends(get_db)
):
    """
    Aggiorna un batch nesting esistente
    """
    try:
        batch = db.query(BatchNesting).filter(BatchNesting.id == batch_id).first()
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch nesting con ID {batch_id} non trovato"
            )
        
        # Verifica che il batch sia modificabile (non in stati finali)
        if batch.stato in ['TERMINATO', 'FALLITO']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Impossibile modificare un batch in stato {batch.stato}"
            )
        
        # Aggiorna solo i campi forniti
        update_data = batch_update.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(batch, field, value)
        
        # Aggiorna timestamp di modifica
        batch.updated_at = datetime.now()
        
        db.commit()
        db.refresh(batch)
        
        logger.info(f"Aggiornato batch nesting: {batch_id}")
        return batch
        
    except Exception as e:
        db.rollback()
        logger.error(f"Errore durante l'aggiornamento del batch nesting {batch_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Si è verificato un errore durante l'aggiornamento: {str(e)}"
        )

@router.delete("/{batch_id}", status_code=status.HTTP_204_NO_CONTENT, 
               summary="Elimina un batch nesting")
def delete_batch_nesting(batch_id: str, db: Session = Depends(get_db)):
    """
    Elimina un batch nesting
    """
    try:
        batch = db.query(BatchNesting).filter(BatchNesting.id == batch_id).first()
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch nesting con ID {batch_id} non trovato"
            )
        
        # Verifica che il batch sia eliminabile
        if batch.stato in ['CONFERMATO', 'LOADED', 'CURED']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Impossibile eliminare un batch in stato {batch.stato}"
            )
        
        db.delete(batch)
        db.commit()
        
        logger.info(f"Eliminato batch nesting: {batch_id}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Errore durante l'eliminazione del batch nesting {batch_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Si è verificato un errore durante l'eliminazione: {str(e)}"
        )

@router.delete("/bulk", status_code=status.HTTP_200_OK,
               summary="🗑️ Elimina multipli batch nesting con controlli di sicurezza")
def delete_multiple_batch_nesting(
    batch_ids: List[str] = Body(..., description="Lista degli ID dei batch da eliminare"),
    confirm: bool = Query(False, description="Conferma eliminazione (obbligatorio per batch confermati/attivi)"),
    db: Session = Depends(get_db)
):
    """
    🗑️ ELIMINAZIONE MULTIPLA BATCH NESTING
    =======================================
    
    Elimina più batch nesting contemporaneamente con controlli di sicurezza:
    - Batch SOSPESO/DRAFT: eliminazione diretta
    - Batch CONFERMATO/LOADED/CURED: richiede conferma esplicita
    - Batch TERMINATO: non eliminabili (solo archivio)
    """
    try:
        if not batch_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lista batch_ids vuota"
            )
        
        logger.info(f"🗑️ Richiesta eliminazione multipla: {len(batch_ids)} batch")
        
        # Recupera tutti i batch richiesti
        batches = db.query(BatchNesting).filter(BatchNesting.id.in_(batch_ids)).all()
        found_ids = [batch.id for batch in batches]
        missing_ids = [bid for bid in batch_ids if bid not in found_ids]
        
        if missing_ids:
            logger.warning(f"❌ Batch non trovati: {missing_ids}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch non trovati: {missing_ids}"
            )
        
        # Analizza stati e controlli di sicurezza
        safe_to_delete = []
        require_confirmation = []
        cannot_delete = []
        
        for batch in batches:
            if batch.stato in ['SOSPESO', 'DRAFT', 'FALLITO']:
                safe_to_delete.append(batch)
            elif batch.stato in ['CONFERMATO', 'LOADED', 'CURED']:
                require_confirmation.append(batch)
            elif batch.stato in ['TERMINATO']:
                cannot_delete.append(batch)
        
        # Controllo batch non eliminabili
        if cannot_delete:
            cannot_delete_info = [f"{b.id} ({b.stato})" for b in cannot_delete]
            logger.error(f"❌ Batch non eliminabili: {cannot_delete_info}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Batch in stato TERMINATO non eliminabili: {cannot_delete_info}"
            )
        
        # Controllo conferma per batch attivi
        if require_confirmation and not confirm:
            confirmation_info = [f"{b.id} ({b.stato})" for b in require_confirmation]
            logger.warning(f"⚠️ Richiesta conferma per: {confirmation_info}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Batch in stati attivi richiedono conferma esplicita (confirm=true): {confirmation_info}"
            )
        
        # Procedi con l'eliminazione
        deleted_count = 0
        deleted_ids = []
        
        all_to_delete = safe_to_delete + (require_confirmation if confirm else [])
        
        for batch in all_to_delete:
            try:
                logger.info(f"🗑️ Eliminando batch {batch.id} (stato: {batch.stato})")
                db.delete(batch)
                deleted_ids.append(batch.id)
                deleted_count += 1
            except Exception as e:
                logger.error(f"❌ Errore eliminazione batch {batch.id}: {e}")
                # Continua con gli altri batch
        
        db.commit()
        
        logger.info(f"✅ Eliminazione multipla completata: {deleted_count}/{len(batch_ids)} batch")
        
        return {
            "message": f"Eliminati {deleted_count} batch nesting",
            "deleted_count": deleted_count,
            "deleted_ids": deleted_ids,
            "total_requested": len(batch_ids),
            "required_confirmation": len(require_confirmation) if not confirm else 0,
            "cannot_delete": len(cannot_delete)
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Errore durante eliminazione multipla: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante eliminazione multipla: {str(e)}"
        ) 