import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload

from api.database import get_db
from schemas.odl_monitoring import (
    ODLMonitoringRead,
    ODLMonitoringSummary,
    ODLMonitoringStats,
    ODLLogCreate,
    ODLLogRead
)
from schemas.odl_alerts import ODLAlertsResponse
from services.odl_monitoring_service import ODLMonitoringService
from services.odl_log_service import ODLLogService
from services.odl_alerts_service import ODLAlertsService

# Configurazione logger
logger = logging.getLogger(__name__)

# Creazione router
router = APIRouter(
    prefix="/monitoring",
    tags=["Monitoraggio ODL"],
    responses={404: {"description": "Risorsa non trovata"}}
)

@router.get("/stats", response_model=ODLMonitoringStats,
            summary="Ottiene statistiche generali del monitoraggio ODL")
def get_monitoring_stats(db: Session = Depends(get_db)):
    """
    Restituisce statistiche generali del monitoraggio ODL:
    - Numero totale di ODL
    - Conteggio per stato
    - ODL in ritardo
    - ODL completati oggi
    - Tempo medio di completamento
    """
    try:
        stats = ODLMonitoringService.ottieni_statistiche_monitoraggio(db)
        return stats
    except Exception as e:
        logger.error(f"Errore durante il recupero delle statistiche: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero delle statistiche di monitoraggio"
        )



@router.get("/", response_model=List[ODLMonitoringSummary],
            summary="Ottiene lista riassuntiva del monitoraggio ODL")
def get_monitoring_list(
    skip: int = Query(0, ge=0, description="Numero di elementi da saltare"),
    limit: int = Query(50, ge=1, le=200, description="Numero massimo di elementi da restituire"),
    status_filter: Optional[str] = Query(None, description="Filtro per stato ODL"),
    priorita_min: Optional[int] = Query(None, ge=1, description="Priorità minima"),
    solo_attivi: bool = Query(True, description="Se True, esclude ODL completati"),
    db: Session = Depends(get_db)
):
    """
    Restituisce una lista riassuntiva del monitoraggio ODL con:
    - Informazioni base dell'ODL
    - Stato nesting e autoclave
    - Ultimo evento registrato
    - Tempo nello stato corrente
    
    Supporta filtri per stato, priorità e inclusione/esclusione ODL completati.
    """
    try:
        monitoring_list = ODLMonitoringService.ottieni_lista_monitoraggio(
            db=db,
            skip=skip,
            limit=limit,
            status_filter=status_filter,
            priorita_min=priorita_min,
            solo_attivi=solo_attivi
        )
        
        logger.info(f"Restituiti {len(monitoring_list)} elementi di monitoraggio ODL")
        return monitoring_list
        
    except Exception as e:
        logger.error(f"Errore durante il recupero della lista monitoraggio: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero della lista di monitoraggio"
        )



@router.get("/{odl_id}", response_model=ODLMonitoringRead,
            summary="Ottiene monitoraggio completo di un ODL specifico")
def get_odl_monitoring_detail(odl_id: int, db: Session = Depends(get_db)):
    """
    Restituisce il monitoraggio completo di un ODL specifico con:
    - Tutte le informazioni base dell'ODL
    - Dettagli nesting, autoclave e ciclo di cura
    - Log completo di avanzamento
    - Statistiche temporali dettagliate
    - Informazioni schedulazione
    """
    try:
        monitoring_detail = ODLMonitoringService.ottieni_odl_monitoraggio_completo(
            db=db,
            odl_id=odl_id
        )
        
        if not monitoring_detail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ODL con ID {odl_id} non trovato"
            )
        
        logger.info(f"Restituito monitoraggio completo per ODL {odl_id}")
        return monitoring_detail
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Errore durante il recupero del monitoraggio ODL {odl_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero del monitoraggio ODL"
        )

@router.get("/{odl_id}/logs", response_model=List[ODLLogRead],
            summary="Ottiene i log di un ODL specifico")
def get_odl_logs(
    odl_id: int,
    limit: Optional[int] = Query(None, ge=1, le=100, description="Limite numero di log da restituire"),
    db: Session = Depends(get_db)
):
    """
    Restituisce i log di avanzamento di un ODL specifico, ordinati per timestamp decrescente.
    """
    try:
        logs = ODLLogService.ottieni_logs_odl(db=db, odl_id=odl_id, limit=limit)
        
        # Arricchisci i log con informazioni correlate
        logs_arricchiti = []
        for log in logs:
            log_dict = {
                "id": log.id,
                "odl_id": log.odl_id,
                "evento": log.evento,
                "stato_precedente": log.stato_precedente,
                "stato_nuovo": log.stato_nuovo,
                "descrizione": log.descrizione,
                "responsabile": log.responsabile,
                "nesting_id": log.nesting_id,
                "autoclave_id": log.autoclave_id,
                "schedule_entry_id": log.schedule_entry_id,
                "timestamp": log.timestamp,
                "nesting_stato": None,
                "autoclave_nome": None
            }
            
            # Aggiungi informazioni correlate se disponibili
            if log.nesting and hasattr(log, 'nesting'):
                log_dict["nesting_stato"] = log.nesting.stato
            
            if log.autoclave and hasattr(log, 'autoclave'):
                log_dict["autoclave_nome"] = log.autoclave.nome
            
            logs_arricchiti.append(ODLLogRead(**log_dict))
        
        logger.info(f"Restituiti {len(logs_arricchiti)} log per ODL {odl_id}")
        return logs_arricchiti
        
    except Exception as e:
        logger.error(f"Errore durante il recupero dei log ODL {odl_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero dei log ODL"
        )

@router.post("/{odl_id}/logs", response_model=ODLLogRead, status_code=status.HTTP_201_CREATED,
             summary="Crea un nuovo log evento per un ODL")
def create_odl_log(
    odl_id: int,
    log_data: ODLLogCreate,
    db: Session = Depends(get_db)
):
    """
    Crea un nuovo log evento per un ODL specifico.
    
    Questo endpoint permette di registrare manualmente eventi specifici
    per un ODL, utile per integrazioni esterne o eventi manuali.
    """
    try:
        # Verifica che l'ODL esista
        from models.odl import ODL
        odl = db.query(ODL).filter(ODL.id == odl_id).first()
        if not odl:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ODL con ID {odl_id} non trovato"
            )
        
        # Assicurati che l'odl_id nel log corrisponda al parametro URL
        log_data.odl_id = odl_id
        
        # Crea il log
        new_log = ODLLogService.crea_log_evento(
            db=db,
            odl_id=log_data.odl_id,
            evento=log_data.evento,
            stato_nuovo=log_data.stato_nuovo,
            stato_precedente=log_data.stato_precedente,
            descrizione=log_data.descrizione,
            responsabile=log_data.responsabile,
            nesting_id=log_data.nesting_id,
            autoclave_id=log_data.autoclave_id,
            schedule_entry_id=log_data.schedule_entry_id
        )
        
        # Prepara la risposta
        response_dict = {
            "id": new_log.id,
            "odl_id": new_log.odl_id,
            "evento": new_log.evento,
            "stato_precedente": new_log.stato_precedente,
            "stato_nuovo": new_log.stato_nuovo,
            "descrizione": new_log.descrizione,
            "responsabile": new_log.responsabile,
            "nesting_id": new_log.nesting_id,
            "autoclave_id": new_log.autoclave_id,
            "schedule_entry_id": new_log.schedule_entry_id,
            "timestamp": new_log.timestamp,
            "nesting_stato": None,
            "autoclave_nome": None
        }
        
        logger.info(f"Creato nuovo log '{log_data.evento}' per ODL {odl_id}")
        return ODLLogRead(**response_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Errore durante la creazione del log per ODL {odl_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante la creazione del log ODL"
        )



@router.get("/{odl_id}/timeline", 
            summary="Ottiene timeline completa per un ODL con statistiche temporali")
def get_odl_timeline(odl_id: int, db: Session = Depends(get_db)):
    """
    Restituisce una timeline completa degli eventi di un ODL con:
    - Dati temporali per ogni stato
    - Statistiche di durata
    - Log dettagliati con informazioni correlate
    - Calcoli di efficienza
    """
    try:
        from models.odl import ODL
        from models.parte import Parte
        from models.tool import Tool
        from models.autoclave import Autoclave
        from models.nesting_result import NestingResult
        from datetime import datetime, timedelta
        
        # Recupera l'ODL con le relazioni
        odl = db.query(ODL).options(
            joinedload(ODL.parte),
            joinedload(ODL.tool),
            joinedload(ODL.logs)
        ).filter(ODL.id == odl_id).first()
        
        if not odl:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ODL con ID {odl_id} non trovato"
            )
        
        # Recupera i log ordinati per timestamp
        logs = ODLLogService.ottieni_logs_odl(db=db, odl_id=odl_id)
        
        # Arricchisci i log con informazioni correlate
        logs_arricchiti = []
        for log in logs:
            log_dict = {
                "id": log.id,
                "evento": log.evento,
                "stato_precedente": log.stato_precedente,
                "stato_nuovo": log.stato_nuovo,
                "descrizione": log.descrizione,
                "responsabile": log.responsabile,
                "timestamp": log.timestamp.isoformat(),
                "nesting_stato": None,
                "autoclave_nome": None,
                "nesting_id": log.nesting_id,
                "autoclave_id": log.autoclave_id,
                "schedule_entry_id": log.schedule_entry_id
            }
            
            # Aggiungi informazioni correlate se disponibili
            if log.nesting_id:
                nesting = db.query(NestingResult).filter(NestingResult.id == log.nesting_id).first()
                if nesting:
                    log_dict["nesting_stato"] = nesting.stato
            
            if log.autoclave_id:
                autoclave = db.query(Autoclave).filter(Autoclave.id == log.autoclave_id).first()
                if autoclave:
                    log_dict["autoclave_nome"] = autoclave.nome
            
            logs_arricchiti.append(log_dict)
        
        # Calcola le durate per stato
        durata_per_stato = {}
        timestamps_stati = []
        
        # Raggruppa i log per transizioni di stato
        for i, log in enumerate(logs):
            if i < len(logs) - 1:
                next_log = logs[i + 1]
                durata_minuti = int((next_log.timestamp - log.timestamp).total_seconds() / 60)
                
                if log.stato_nuovo not in durata_per_stato:
                    durata_per_stato[log.stato_nuovo] = 0
                durata_per_stato[log.stato_nuovo] += durata_minuti
                
                # Aggiungi timestamp per la barra di progresso
                timestamps_stati.append({
                    "stato": log.stato_nuovo,
                    "inizio": log.timestamp.isoformat(),
                    "fine": next_log.timestamp.isoformat(),
                    "durata_minuti": durata_minuti
                })
            else:
                # Ultimo log - stato corrente
                if odl.status != 'Finito':
                    durata_corrente = int((datetime.now() - log.timestamp).total_seconds() / 60)
                    if log.stato_nuovo not in durata_per_stato:
                        durata_per_stato[log.stato_nuovo] = 0
                    durata_per_stato[log.stato_nuovo] += durata_corrente
                    
                    timestamps_stati.append({
                        "stato": log.stato_nuovo,
                        "inizio": log.timestamp.isoformat(),
                        "fine": None,
                        "durata_minuti": durata_corrente
                    })
        
        # Calcola statistiche
        durata_totale_minuti = sum(durata_per_stato.values())
        numero_transizioni = len(logs) - 1 if len(logs) > 1 else 0
        
        # Calcola tempo medio per transizione
        tempo_medio_per_transizione = {}
        if numero_transizioni > 0:
            for stato, durata in durata_per_stato.items():
                tempo_medio_per_transizione[stato] = durata
        
        # Stima efficienza (basata su tempi standard se disponibili)
        efficienza_stimata = None
        if durata_totale_minuti > 0:
            # Tempo stimato base (esempio: 8 ore per un ODL completo)
            tempo_stimato_base = 8 * 60  # 480 minuti
            efficienza_stimata = min(100, int((tempo_stimato_base / durata_totale_minuti) * 100))
        
        # Prepara la risposta completa
        timeline_data = {
            "odl_id": odl_id,
            "parte_nome": odl.parte.descrizione_breve,
            "tool_nome": odl.tool.part_number_tool,
            "status_corrente": odl.status,
            "created_at": odl.created_at.isoformat(),
            "updated_at": odl.updated_at.isoformat(),
            "logs": logs_arricchiti,
            "timestamps": timestamps_stati,
            "statistiche": {
                "durata_totale_minuti": durata_totale_minuti,
                "durata_per_stato": durata_per_stato,
                "tempo_medio_per_transizione": tempo_medio_per_transizione,
                "numero_transizioni": numero_transizioni,
                "efficienza_stimata": efficienza_stimata
            }
        }
        
        logger.info(f"Restituita timeline completa per ODL {odl_id} con {len(logs_arricchiti)} eventi")
        return timeline_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Errore durante il recupero della timeline ODL {odl_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero della timeline ODL"
        )

@router.get("/{odl_id}/progress", 
            summary="Ottiene dati di progresso per la barra temporale di un ODL")
def get_odl_progress(odl_id: int, db: Session = Depends(get_db)):
    """
    Restituisce i dati ottimizzati per la visualizzazione della barra di progresso temporale.
    Include solo i timestamp degli stati e le durate necessarie per il rendering.
    """
    try:
        from models.odl import ODL
        from datetime import datetime
        
        # Recupera l'ODL
        odl = db.query(ODL).filter(ODL.id == odl_id).first()
        if not odl:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ODL con ID {odl_id} non trovato"
            )
        
        # Recupera i log ordinati per timestamp
        logs = ODLLogService.ottieni_logs_odl(db=db, odl_id=odl_id)
        
        # Calcola i timestamp per ogni stato
        timestamps_stati = []
        
        for i, log in enumerate(logs):
            if i < len(logs) - 1:
                next_log = logs[i + 1]
                durata_minuti = int((next_log.timestamp - log.timestamp).total_seconds() / 60)
                
                timestamps_stati.append({
                    "stato": log.stato_nuovo,
                    "inizio": log.timestamp.isoformat(),
                    "fine": next_log.timestamp.isoformat(),
                    "durata_minuti": durata_minuti
                })
            else:
                # Ultimo log - stato corrente
                if odl.status != 'Finito':
                    durata_corrente = int((datetime.now() - log.timestamp).total_seconds() / 60)
                    timestamps_stati.append({
                        "stato": log.stato_nuovo,
                        "inizio": log.timestamp.isoformat(),
                        "fine": None,
                        "durata_minuti": durata_corrente
                    })
                else:
                    # ODL finito
                    timestamps_stati.append({
                        "stato": log.stato_nuovo,
                        "inizio": log.timestamp.isoformat(),
                        "fine": log.timestamp.isoformat(),
                        "durata_minuti": 0
                    })
        
        # Calcola tempo totale stimato (se disponibile)
        tempo_totale_stimato = None
        if len(timestamps_stati) > 0:
            tempo_totale_stimato = sum(t["durata_minuti"] for t in timestamps_stati)
        
        progress_data = {
            "id": odl_id,
            "status": odl.status,
            "created_at": odl.created_at.isoformat(),
            "updated_at": odl.updated_at.isoformat(),
            "timestamps": timestamps_stati,
            "tempo_totale_stimato": tempo_totale_stimato
        }
        
        logger.info(f"Restituiti dati di progresso per ODL {odl_id}")
        return progress_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Errore durante il recupero dei dati di progresso ODL {odl_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero dei dati di progresso ODL"
        )

@router.post("/generate-missing-logs", 
             summary="Genera log mancanti per ODL esistenti")
def generate_missing_logs(db: Session = Depends(get_db)):
    """
    Genera automaticamente log di creazione per ODL esistenti che non hanno log.
    
    Questo endpoint è utile per inizializzare il sistema di monitoraggio
    su un database esistente con ODL già presenti.
    """
    try:
        logs_creati = ODLLogService.genera_logs_mancanti_per_odl_esistenti(db)
        
        logger.info(f"Generati {logs_creati} log mancanti")
        return {
            "message": f"Generati {logs_creati} log di creazione per ODL esistenti",
            "logs_creati": logs_creati
        }
        
    except Exception as e:
        logger.error(f"Errore durante la generazione dei log mancanti: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante la generazione dei log mancanti"
        )