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
            odl.status = "Cura"
            odl.previous_status = "Attesa Cura"  # Salva stato precedente per eventuale ripristino
            odl_aggiornati.append(odl.id)
        
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
    
    Effettua le seguenti operazioni in transazione:
    1. Aggiorna il batch da "confermato" a "terminato"  
    2. Aggiorna l'autoclave a disponibile
    3. Aggiorna tutti gli ODL da "Cura" a "Terminato"
    4. Registra timestamp di completamento
    
    **Prerequisiti:**
    - Il batch deve essere in stato "confermato"
    - L'autoclave deve essere in uso
    - Gli ODL devono essere in stato "Cura"
    """
    # Recupera il batch con le relazioni
    db_batch = db.query(BatchNesting).filter(BatchNesting.id == batch_id).first()
    if db_batch is None:
        logger.warning(f"Tentativo di chiusura di batch inesistente: {batch_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch nesting con ID {batch_id} non trovato"
        )
    
    # Verifica che il batch sia in stato "confermato"
    if db_batch.stato != StatoBatchNestingEnum.CONFERMATO.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Il batch è in stato '{db_batch.stato}' e non può essere chiuso. Solo i batch in stato 'confermato' possono essere chiusi."
        )
    
    # Recupera l'autoclave associata
    autoclave = db.query(Autoclave).filter(Autoclave.id == db_batch.autoclave_id).first()
    if not autoclave:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Autoclave con ID {db_batch.autoclave_id} non trovata"
        )
    
    # Verifica che l'autoclave sia in uso
    if autoclave.stato != StatoAutoclaveEnum.IN_USO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"L'autoclave '{autoclave.nome}' non è in uso (stato: {autoclave.stato.value}). Non può essere liberata."
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
    
    # Verifica che tutti gli ODL siano in stato "Cura"
    odl_non_validi = [odl for odl in odl_list if odl.status != "Cura"]
    if odl_non_validi:
        stati_non_validi = [f"ODL {odl.id}: {odl.status}" for odl in odl_non_validi]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"I seguenti ODL non sono in stato 'Cura': {', '.join(stati_non_validi)}"
        )
    
    try:
        # Inizia la transazione
        ora_chiusura = datetime.now()
        
        logger.info(f"🏁 Avvio chiusura batch {batch_id} con {len(odl_list)} ODL")
        
        # 1. Aggiorna il batch nesting
        db_batch.stato = StatoBatchNestingEnum.TERMINATO.value
        # Aggiungi campo ended_at se non esiste (compatibilità)
        if hasattr(db_batch, 'ended_at'):
            db_batch.ended_at = ora_chiusura
        
        # Salva data di completamento e calcola durata
        db_batch.data_completamento = ora_chiusura
        durata_cura_minuti = None
        if db_batch.data_conferma:
            durata_cura = ora_chiusura - db_batch.data_conferma
            durata_cura_minuti = int(durata_cura.total_seconds() / 60)
            db_batch.durata_ciclo_minuti = durata_cura_minuti
        
        logger.info(f"✅ Batch {batch_id} aggiornato a stato 'terminato'")
        if durata_cura_minuti:
            logger.info(f"📊 Durata ciclo di cura: {durata_cura_minuti} minuti")
        
        # 2. Aggiorna l'autoclave (rende disponibile)
        autoclave.stato = StatoAutoclaveEnum.DISPONIBILE
        
        logger.info(f"✅ Autoclave {autoclave.id} ({autoclave.nome}) aggiornata a stato 'disponibile'")
        
        # 3. Aggiorna tutti gli ODL da "Cura" a "Terminato"
        odl_aggiornati = []
        for odl in odl_list:
            odl.previous_status = odl.status  # Salva stato precedente per eventuale ripristino
            odl.status = "Terminato"
            odl_aggiornati.append(odl.id)
        
        logger.info(f"✅ {len(odl_aggiornati)} ODL aggiornati a stato 'Terminato': {odl_aggiornati}")
        
        # Commit della transazione
        db.commit()
        db.refresh(db_batch)
        
        logger.info(f"🎉 Chiusura batch {batch_id} completata con successo!")
        logger.info(f"📊 Riepilogo:")
        logger.info(f"   - Batch: {db_batch.stato}")
        logger.info(f"   - Autoclave: {autoclave.stato.value}")
        logger.info(f"   - ODL processati: {len(odl_aggiornati)}")
        logger.info(f"   - Chiuso da: {chiuso_da_utente} ({chiuso_da_ruolo})")
        if durata_cura_minuti:
            logger.info(f"   - Durata ciclo: {durata_cura_minuti} minuti")
        
        return db_batch
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Errore durante la chiusura del batch {batch_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Si è verificato un errore durante la chiusura del batch nesting: {str(e)}"
        ) 