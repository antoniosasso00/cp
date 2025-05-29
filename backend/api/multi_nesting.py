"""
API endpoints per la gestione del nesting multiplo con batch e assegnazione di autoclavi.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
import logging

# Importazioni locali
from models.db import get_db
from services.multi_nesting_service import MultiNestingService
from models.nesting_batch import NestingBatch

# Configurazione logging
logger = logging.getLogger(__name__)

# Router per gli endpoint del nesting multiplo
router = APIRouter(prefix="/api/multi-nesting", tags=["Multi Nesting"])


# Schemi Pydantic per le richieste e risposte
class NestingParametersRequest(BaseModel):
    """Schema per i parametri di nesting"""
    distanza_minima_tool_cm: float = Field(default=2.0, ge=0.5, le=10.0)
    padding_bordo_autoclave_cm: float = Field(default=1.5, ge=0.5, le=5.0)
    margine_sicurezza_peso_percent: float = Field(default=10.0, ge=0.0, le=50.0)
    priorita_minima: int = Field(default=1, ge=1, le=10)
    efficienza_minima_percent: float = Field(default=60.0, ge=30.0, le=95.0)


class BatchPreviewRequest(BaseModel):
    """Schema per la richiesta di preview del batch"""
    parametri_nesting: Optional[NestingParametersRequest] = None
    priorita_minima: int = Field(default=1, ge=1, le=10)
    nome_batch: Optional[str] = None


class BatchSaveRequest(BaseModel):
    """Schema per il salvataggio del batch"""
    batch_preview: Dict
    creato_da_ruolo: Optional[str] = None


class BatchResponse(BaseModel):
    """Schema per la risposta del batch"""
    id: int
    nome: str
    descrizione: Optional[str]
    stato: str
    numero_autoclavi: int
    numero_odl_totali: int
    peso_totale_kg: float
    efficienza_media: float
    created_at: str
    creato_da_ruolo: Optional[str]


@router.get("/gruppi-odl", summary="Raggruppa ODL per ciclo di cura")
async def raggruppa_odl_per_ciclo_cura(
    priorita_minima: int = Query(default=1, ge=1, le=10, description="Priorità minima degli ODL"),
    db: Session = Depends(get_db)
):
    """
    Raggruppa gli ODL in attesa per ciclo di cura compatibile.
    
    Questo endpoint analizza tutti gli ODL in stato "In Coda" e li raggruppa
    per ciclo di cura compatibile, considerando solo quelli con priorità >= priorita_minima.
    """
    try:
        service = MultiNestingService(db)
        gruppi = service.raggruppa_odl_per_ciclo_cura(priorita_minima)
        
        # Converte i gruppi in formato JSON serializzabile
        gruppi_serializzabili = {}
        for ciclo_key, odl_list in gruppi.items():
            gruppi_serializzabili[ciclo_key] = [
                {
                    'id': odl.id,
                    'parte_nome': odl.parte.nome if odl.parte else "Sconosciuta",
                    'tool_nome': odl.tool.nome if odl.tool else "Sconosciuto",
                    'priorita': odl.priorita,
                    'status': odl.status,
                    'categoria': odl.parte.catalogo.categoria if odl.parte and odl.parte.catalogo else "Sconosciuta",
                    'sotto_categoria': odl.parte.catalogo.sotto_categoria if odl.parte and odl.parte.catalogo else "Sconosciuta"
                }
                for odl in odl_list
            ]
        
        return {
            'success': True,
            'message': f'Trovati {len(gruppi)} gruppi di ODL compatibili',
            'gruppi_odl': gruppi_serializzabili,
            'statistiche': {
                'numero_gruppi': len(gruppi),
                'odl_totali': sum(len(odl_list) for odl_list in gruppi.values()),
                'priorita_minima_utilizzata': priorita_minima
            }
        }
        
    except Exception as e:
        logger.error(f"Errore nel raggruppamento ODL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Errore nel raggruppamento ODL: {str(e)}")


@router.get("/autoclavi-disponibili", summary="Lista autoclavi disponibili")
async def get_autoclavi_disponibili(db: Session = Depends(get_db)):
    """
    Recupera tutte le autoclavi disponibili per il nesting multiplo.
    
    Restituisce le autoclavi in stato "DISPONIBILE" ordinate per capacità.
    """
    try:
        service = MultiNestingService(db)
        autoclavi = service.get_autoclavi_disponibili()
        
        autoclavi_data = [
            {
                'id': autoclave.id,
                'nome': autoclave.nome,
                'area_piano': autoclave.area_piano,
                'capacita_peso': autoclave.capacita_peso,
                'lunghezza': autoclave.lunghezza,
                'larghezza_piano': autoclave.larghezza_piano,
                'stato': autoclave.stato.value if autoclave.stato else "Sconosciuto"
            }
            for autoclave in autoclavi
        ]
        
        return {
            'success': True,
            'message': f'Trovate {len(autoclavi)} autoclavi disponibili',
            'autoclavi': autoclavi_data
        }
        
    except Exception as e:
        logger.error(f"Errore nel recupero autoclavi: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Errore nel recupero autoclavi: {str(e)}")


@router.post("/preview-batch", summary="Crea preview batch nesting multiplo")
async def crea_batch_preview(
    request: BatchPreviewRequest,
    db: Session = Depends(get_db)
):
    """
    Crea un preview del batch di nesting multiplo senza salvare nel database.
    
    Questo endpoint:
    1. Raggruppa gli ODL per ciclo di cura
    2. Calcola l'assegnazione ottimale alle autoclavi
    3. Restituisce un preview completo del batch con statistiche
    """
    try:
        service = MultiNestingService(db)
        
        # Converte i parametri Pydantic in dizionario
        parametri_dict = None
        if request.parametri_nesting:
            parametri_dict = request.parametri_nesting.dict()
        
        # Crea il preview del batch
        risultato = service.crea_batch_preview(
            parametri_nesting=parametri_dict,
            priorita_minima=request.priorita_minima,
            nome_batch=request.nome_batch
        )
        
        if not risultato['success']:
            raise HTTPException(status_code=400, detail=risultato['message'])
        
        return risultato
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Errore nella creazione preview batch: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Errore nella creazione preview batch: {str(e)}")


@router.post("/salva-batch", summary="Salva batch nel database")
async def salva_batch(
    request: BatchSaveRequest,
    db: Session = Depends(get_db)
):
    """
    Salva un batch di nesting nel database basandosi sul preview.
    
    Questo endpoint:
    1. Crea il record NestingBatch
    2. Crea i record NestingResult per ogni assegnazione
    3. Associa gli ODL ai nesting results
    """
    try:
        service = MultiNestingService(db)
        
        # Salva il batch
        batch = service.salva_batch(
            batch_preview=request.batch_preview,
            creato_da_ruolo=request.creato_da_ruolo
        )
        
        return {
            'success': True,
            'message': f'Batch {batch.nome} salvato con successo',
            'batch_id': batch.id,
            'batch': {
                'id': batch.id,
                'nome': batch.nome,
                'descrizione': batch.descrizione,
                'stato': batch.stato,
                'numero_autoclavi': batch.numero_autoclavi,
                'numero_odl_totali': batch.numero_odl_totali,
                'peso_totale_kg': batch.peso_totale_kg,
                'efficienza_media': batch.efficienza_media,
                'created_at': batch.created_at.isoformat(),
                'creato_da_ruolo': batch.creato_da_ruolo
            }
        }
        
    except Exception as e:
        logger.error(f"Errore nel salvataggio batch: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Errore nel salvataggio batch: {str(e)}")


@router.get("/batch", summary="Lista batch di nesting")
async def get_batch_list(
    stato: Optional[str] = Query(None, description="Filtro per stato del batch"),
    db: Session = Depends(get_db)
):
    """
    Recupera la lista dei batch di nesting con filtro opzionale per stato.
    """
    try:
        service = MultiNestingService(db)
        batch_list = service.get_batch_list(stato)
        
        batch_data = [
            {
                'id': batch.id,
                'nome': batch.nome,
                'descrizione': batch.descrizione,
                'stato': batch.stato,
                'numero_autoclavi': batch.numero_autoclavi,
                'numero_odl_totali': batch.numero_odl_totali,
                'peso_totale_kg': batch.peso_totale_kg,
                'efficienza_media': batch.efficienza_media,
                'created_at': batch.created_at.isoformat(),
                'creato_da_ruolo': batch.creato_da_ruolo
            }
            for batch in batch_list
        ]
        
        return {
            'success': True,
            'message': f'Trovati {len(batch_list)} batch',
            'batch_list': batch_data
        }
        
    except Exception as e:
        logger.error(f"Errore nel recupero lista batch: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Errore nel recupero lista batch: {str(e)}")


@router.get("/batch/{batch_id}", summary="Dettagli batch specifico")
async def get_batch_dettagli(
    batch_id: int,
    db: Session = Depends(get_db)
):
    """
    Recupera i dettagli completi di un batch specifico.
    
    Include:
    - Informazioni del batch
    - Nesting results per autoclave
    - Lista completa degli ODL
    """
    try:
        service = MultiNestingService(db)
        dettagli = service.get_batch_dettagli(batch_id)
        
        if not dettagli:
            raise HTTPException(status_code=404, detail=f"Batch con ID {batch_id} non trovato")
        
        # Converte le date in formato ISO
        dettagli['batch']['created_at'] = dettagli['batch']['created_at'].isoformat()
        
        return {
            'success': True,
            'message': f'Dettagli batch {batch_id} recuperati con successo',
            'dettagli': dettagli
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Errore nel recupero dettagli batch {batch_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Errore nel recupero dettagli batch: {str(e)}")


@router.put("/batch/{batch_id}/stato", summary="Aggiorna stato batch")
async def aggiorna_stato_batch(
    batch_id: int,
    nuovo_stato: str = Query(..., description="Nuovo stato del batch"),
    db: Session = Depends(get_db)
):
    """
    Aggiorna lo stato di un batch.
    
    Stati validi: Pianificazione, Pronto, In Esecuzione, Completato, Annullato
    """
    try:
        # Verifica che il batch esista
        batch = db.query(NestingBatch).filter(NestingBatch.id == batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail=f"Batch con ID {batch_id} non trovato")
        
        # Verifica che il nuovo stato sia valido
        stati_validi = ["Pianificazione", "Pronto", "In Esecuzione", "Completato", "Annullato"]
        if nuovo_stato not in stati_validi:
            raise HTTPException(status_code=400, detail=f"Stato non valido. Stati validi: {', '.join(stati_validi)}")
        
        # Aggiorna lo stato
        batch.stato = nuovo_stato
        
        # Aggiorna i timestamp se necessario
        if nuovo_stato == "In Esecuzione" and not batch.data_inizio_effettiva:
            from datetime import datetime
            batch.data_inizio_effettiva = datetime.now()
        elif nuovo_stato == "Completato" and not batch.data_fine_effettiva:
            from datetime import datetime
            batch.data_fine_effettiva = datetime.now()
        
        db.commit()
        
        return {
            'success': True,
            'message': f'Stato batch {batch_id} aggiornato a "{nuovo_stato}"',
            'batch': {
                'id': batch.id,
                'nome': batch.nome,
                'stato': batch.stato,
                'data_inizio_effettiva': batch.data_inizio_effettiva.isoformat() if batch.data_inizio_effettiva else None,
                'data_fine_effettiva': batch.data_fine_effettiva.isoformat() if batch.data_fine_effettiva else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Errore nell'aggiornamento stato batch {batch_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Errore nell'aggiornamento stato batch: {str(e)}")


@router.delete("/batch/{batch_id}", summary="Elimina batch")
async def elimina_batch(
    batch_id: int,
    db: Session = Depends(get_db)
):
    """
    Elimina un batch e tutti i suoi nesting results associati.
    
    ATTENZIONE: Questa operazione è irreversibile!
    """
    try:
        # Verifica che il batch esista
        batch = db.query(NestingBatch).filter(NestingBatch.id == batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail=f"Batch con ID {batch_id} non trovato")
        
        # Verifica che il batch non sia in esecuzione
        if batch.stato == "In Esecuzione":
            raise HTTPException(status_code=400, detail="Impossibile eliminare un batch in esecuzione")
        
        nome_batch = batch.nome
        
        # Elimina il batch (i nesting results vengono eliminati automaticamente per cascade)
        db.delete(batch)
        db.commit()
        
        return {
            'success': True,
            'message': f'Batch "{nome_batch}" eliminato con successo'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Errore nell'eliminazione batch {batch_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Errore nell'eliminazione batch: {str(e)}") 